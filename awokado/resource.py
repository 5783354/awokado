import json
from typing import Any, Dict, List, Optional, Tuple, Union

import bulky
import falcon
import sqlalchemy as sa
from cached_property import cached_property
from clavis import Transaction
from marshmallow import utils, Schema, ValidationError
from marshmallow.schema import SchemaMeta

from awokado.auth import BaseAuth
from awokado.consts import (
    AUDIT_DEBUG,
    BULK_CREATE,
    BULK_UPDATE,
    CREATE,
    DELETE,
    OP_IN,
    UPDATE,
)
from awokado.custom_fields import ToMany, ToOne
from awokado.db import DATABASE_URL, persistent_engine
from awokado.exceptions import BadRequest, MethodNotAllowed
from awokado.filter_parser import FilterItem, OPERATORS_MAPPING
from awokado.request import ReadContext
from awokado.response import Response
from awokado.utils import (
    get_id_field,
    get_ids_from_payload,
    get_read_params,
    has_resource_auth,
)


class ResourceMeta(SchemaMeta):
    def __new__(mcs, cls_name=None, superclasses=None, attributes=None):
        new_resource = super(ResourceMeta, mcs).__new__(
            mcs, cls_name, superclasses, attributes
        )
        new_resource.RESOURCES[new_resource.Meta.name] = new_resource
        res_meta = new_resource.Meta

        if res_meta.name in ("base_resource", "_resource"):
            return new_resource

        if not getattr(res_meta, "methods", None):
            raise Exception(f"{cls_name} must have Meta.methods")
        if not getattr(res_meta, "name", None):
            raise Exception(f"{cls_name} must have Meta.name")

        new_resource_obj = new_resource()
        resource_id_name = get_id_field(
            new_resource_obj, name_only=True, skip_exc=True
        )
        if resource_id_name:
            resource_id_field = new_resource_obj.fields.get(resource_id_name)
            resource_id_field = resource_id_field.metadata.get("model_field")
            if not resource_id_field:
                raise Exception(
                    f"Resource's {cls_name} id field {resource_id_name}"
                    f" must have model_field."
                )

        if not hasattr(res_meta, "disable_total"):
            res_meta.disable_total = False

        return new_resource


class BaseResource(Schema, metaclass=ResourceMeta):
    RESOURCES: Dict[str, "BaseResource"] = {}
    Response = Response

    class Meta:
        """
        :param name:  used for two resources connection by relation
        :param model: represents sqlalchemy model or cte
        :param methods:  tuple of methods you want to allow
        :param auth: awokado `BaseAuth <reference.html#awokado.auth.BaseAuth>`_  class for embedding authentication logic
        :param skip_doc:  set true if you don't need to add the resource to documentation
        :param disable_total: set false, if you don't need to know returning objects amount in read-requests
        :param select_from: provide data source here if your resource use another's model fields (for example sa.outerjoin(FirstModel, SecondModel, FirstModel.id == SecondModel.first_model_id))
        """

        name = "base_resource"
        methods: Union[Tuple[str], Tuple] = tuple()
        model: Any = None  # type: ignore
        auth = BaseAuth
        skip_doc = True
        disable_total = False
        id_field = None

    ###########################################################################
    # Marshmallow validation methods
    ###########################################################################

    def validate_create_request(self, req: falcon.Request, is_bulk=False):
        methods = self.Meta.methods
        payload = json.load(req.bounded_stream)

        if isinstance(payload.get(self.Meta.name), list):
            request_method = BULK_CREATE
            is_bulk = True
        else:
            request_method = CREATE

        if request_method not in methods:
            raise MethodNotAllowed()

        data = payload.get(self.Meta.name)

        try:
            deserialized = self.load(data, many=is_bulk)
        except ValidationError as exc:
            if exc.messages == {"_schema": ["Invalid input type."]}:
                raise BadRequest(
                    f"Invalid schema, resource name is missing at the top level. "
                    f"Your POST request has to look like: "
                    f'{{"{self.Meta.name}": [{{"field_name": "field_value"}}] '
                    f'or {{"field_name": "field_value"}} }}'
                )
            raise BadRequest(exc.messages)

        try:
            deserialized = self.load(data, many=is_bulk)
        except ValidationError as exc:
            raise BadRequest(exc.messages)

        req.stream = {self.Meta.name: deserialized}

    def validate_update_request(self, req: falcon.Request):
        methods = self.Meta.methods
        if UPDATE not in methods and BULK_UPDATE not in methods:
            raise MethodNotAllowed()

        payload = json.load(req.bounded_stream)
        data = payload.get(self.Meta.name)
        try:
            deserialized = self.load(data, partial=True, many=True)
        except ValidationError as exc:
            raise BadRequest(exc.messages)

        req.stream = {self.Meta.name: deserialized}

    ###########################################################################
    # Falcon methods
    ###########################################################################

    def on_patch(
        self, req: falcon.Request, resp: falcon.Response, *args, **kwargs
    ):
        """
        Falcon method. PATCH-request entry point.

        Here is a database transaction opening.
        This is where authentication takes place (if auth class is pointed in `resource <reference.html#awokado.resource.BaseResource.Meta>`_)
        Then update method is run.

        :param req: falcon.Request
        :param resp: falcon.Response
        """
        with Transaction(DATABASE_URL, engine=persistent_engine) as t:
            session = t.session
            user_id, _ = self.auth(session, req, resp)

            self.validate_update_request(req)

            payload = req.stream

            data = payload[self.Meta.name]

            ids = get_ids_from_payload(self.Meta.model, data)

            if has_resource_auth(self):
                self.Meta.auth.can_update(session, user_id, ids)

            self.audit_log(
                f"Update: {self.Meta.name}", payload, user_id, AUDIT_DEBUG
            )

            result = self.update(session, payload, user_id)

        resp.body = json.dumps(result, default=str)

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        """
        Falcon method. POST-request entry point.

        Here is a database transaction opening.
        This is where authentication takes place (if auth class is pointed in `resource <reference.html#awokado.resource.BaseResource.Meta>`_)
        Then create method is run.

        :param req: falcon.Request
        :param resp: falcon.Response
        """
        with Transaction(DATABASE_URL, engine=persistent_engine) as t:
            session = t.session
            user_id, token = self.auth(session, req, resp)

            self.validate_create_request(req)

            payload = req.stream

            if has_resource_auth(self):
                self.Meta.auth.can_create(
                    session, payload, user_id, skip_exc=False
                )

            self.audit_log(
                f"Create: {self.Meta.name}", payload, user_id, AUDIT_DEBUG
            )

            result = self.create(session, payload, user_id)

        resp.body = json.dumps(result, default=str)

    def auth(self, *args, **kwargs) -> Tuple[int, str]:
        """
        this method should return (user_id, token) tuple
        """
        return 0, ""

    def audit_log(self, *args, **kwargs):
        return

    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        resource_id: int = None,
    ):
        """
        Falcon method. GET-request entry point.

        Here is a database transaction opening.
        This is where authentication takes place (if auth class is pointed in `resource <reference.html#awokado.resource.BaseResource.Meta>`_)
        Then read_handler method is run. It's responsible for the whole read workflow.

        :param req: falcon.Request
        :param resp: falcon.Response
        """
        with Transaction(DATABASE_URL, engine=persistent_engine) as t:
            session = t.session
            user_id, token = self.auth(session, req, resp)
            params = get_read_params(req, self.__class__)
            params["resource_id"] = resource_id

            result = self.read_handler(session, user_id, **params)

        resp.body = json.dumps(result, default=str)

    def on_delete(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        resource_id: int = None,
    ):
        """
        Falcon method. DELETE-request entry point.

        Here is a database transaction opening.
        This is where authentication takes place (if auth class is pointed in `resource <reference.html#awokado.resource.BaseResource.Meta>`_)
        Then delete method is run.

        :param req: falcon.Request
        :param resp: falcon.Response
        """

        with Transaction(DATABASE_URL, engine=persistent_engine) as t:
            session = t.session
            user_id, token = self.auth(session, req, resp)

            if DELETE not in self.Meta.methods:
                raise MethodNotAllowed()

            ids_to_delete = req.get_param_as_list("ids")

            data = [ids_to_delete, resource_id]
            if not any(data) or all(data):
                raise BadRequest(
                    details=(
                        "It should be a bulk delete (?ids=1,2,3) or delete"
                        " of a single resource (v1/resource/1)"
                    )
                )

            if not ids_to_delete:
                ids_to_delete = [resource_id]

            if has_resource_auth(self):
                self.Meta.auth.can_delete(session, user_id, ids_to_delete)

            result = self.delete(session, user_id, ids_to_delete)

        resp.body = json.dumps(result, default=str)

    ###########################################################################
    # Resource methods
    ###########################################################################

    def update(
        self, session, payload: dict, user_id: int, *args, **kwargs
    ) -> Dict:
        """

        First of all, data is prepared for updating:
        Marshmallow load method for data structure deserialization and then preparing data for SQLAlchemy update query.

        Updates data with bulk_update_mappings sqlalchemy method. Saves many-to-many relationships.

        Returns updated resources with the help of read_handler method.
        """
        data = payload[self.Meta.name]

        data_to_update = self._to_update(data)

        ids = get_ids_from_payload(self.Meta.model, data_to_update)

        session.bulk_update_mappings(self.Meta.model, data_to_update)
        self._save_m2m(session, data, update=True)

        op = OPERATORS_MAPPING[OP_IN]
        result = self.read_handler(
            session=session,
            user_id=user_id,
            filters=[FilterItem("id", op[0], op[1], ids)],
        )

        return result

    def create(self, session, payload: dict, user_id: int) -> dict:
        """

        Create method.

        You can override it to add your logic.

        First of all, data is prepared for creating:
        Marshmallow load method for data structure deserialization and then preparing data for SQLAlchemy create a query.

        Inserts data to the database (Uses bulky library if there is more than one entity to create). Saves many-to-many relationships.

        Returns created resources with the help of read_handler method.

        """
        # prepare data to insert
        data = payload[self.Meta.name]

        if isinstance(data, list):
            return self.bulk_create(session, user_id, data)

        data_to_insert = self._to_create(data)

        # insert to DB
        resource_id = session.execute(
            sa.insert(self.Meta.model)
            .values(data_to_insert)
            .returning(self.Meta.model.id)
        ).scalar()

        data["id"] = resource_id
        self._save_m2m(session, data)

        return self.read_handler(
            session=session, user_id=user_id, resource_id=resource_id
        )

    def bulk_create(self, session, user_id: int, data: list) -> dict:
        data_to_insert = []
        for item in data:
            data_to_insert.append(self._to_create(item))

        # insert to DB
        resource_ids = bulky.insert(
            session,
            self.Meta.model,
            data_to_insert,
            returning=[self.Meta.model.id],
        )
        ids = [r.id for r in resource_ids]

        op = OPERATORS_MAPPING[OP_IN]
        result = self.read_handler(
            session=session,
            user_id=user_id,
            filters=[FilterItem("id", op[0], op[1], ids)],
        )

        return result

    def delete(self, session, user_id: int, obj_ids: list):
        """

        Simply deletes objects with passed identifiers.

        """
        session.execute(
            sa.delete(self.Meta.model).where(self.Meta.model.id.in_(obj_ids))
        )
        return {}

    def _to_update(self, data: list) -> list:
        """
        Prepare resource data for SQLAlchemy update query
        """
        to_update_list = []
        for data_line in data:
            to_update = {}
            for fn, v in data_line.items():
                f = self.fields[fn]
                if isinstance(f, ToMany):
                    continue
                model_field = f.metadata.get("model_field")
                if not model_field:
                    continue
                to_update[model_field.key] = v

            to_update_list.append(to_update)

        return to_update_list

    def _to_create(self, data: dict) -> dict:
        """
        Prepare resource data for SQLAlchemy create query
        """
        to_create = {}
        for fn, v in data.items():
            f = self.fields[fn]
            if isinstance(f, ToMany):
                continue
            model_field = f.metadata["model_field"]
            to_create[model_field.key] = v

        return to_create

    def read_handler(
        self,
        session,
        user_id: int,
        include: list = None,
        filters: Optional[List[FilterItem]] = None,
        sort: list = None,
        resource_id: int = None,
        limit: int = None,
        offset: int = None,
    ) -> Dict:

        ctx = ReadContext(
            session,
            self,
            user_id,
            include,
            filters,
            sort,
            resource_id,
            limit,
            offset,
        )

        self.read__query(ctx)
        self.read__filtering(ctx)
        self.read__sorting(ctx)

        self.read__pagination(ctx)
        self.read__execute_query(ctx)

        if not ctx.obj_ids:
            if ctx.is_list:
                response = self.Response(self, is_list=ctx.is_list)
                return response.serialize()
            else:
                raise BadRequest("Object Not Found")

        self.read__includes(ctx)
        return self.read__serializing(ctx)

    def read__query(self, ctx: ReadContext):
        return ctx.read__query()

    def read__filtering(self, ctx: ReadContext):
        return ctx.read__filtering()

    def read__sorting(self, ctx: ReadContext):
        return ctx.read__sorting()

    def read__pagination(self, ctx: ReadContext):
        return ctx.read__pagination()

    def read__execute_query(self, ctx: ReadContext):
        return ctx.read__execute_query()

    def read__includes(self, ctx: ReadContext):
        return ctx.read__includes()

    def read__serializing(self, ctx: ReadContext) -> Dict:
        return ctx.read__serializing()

    def get_related_model(self, field: Union[ToOne, ToMany]):
        resource_name = field.metadata.get("resource")
        resource = self.RESOURCES[resource_name]
        return resource.Meta.model

    def _process_to_many_field(
        self, field_name: str, field: Union[ToOne, ToMany]
    ):
        related_model = self.get_related_model(field)
        resource_model = self.Meta.model
        model_field = field.metadata.get("model_field")

        if not isinstance(model_field, sa.Column):
            model_field = getattr(
                model_field.parent.persist_selectable.c, model_field.key
            )

        if related_model.__table__ == model_field.table:
            for fk in model_field.table.foreign_keys:
                if fk.column.table == resource_model.__table__:
                    setattr(field, "left_fk_field", fk.parent)
                    break
        else:
            setattr(field, "secondary", model_field.table)
            for fk in model_field.table.foreign_keys:
                if fk.column.table == related_model.__table__:
                    setattr(field, "right_fk_field", fk.parent)

                if fk.column.table == resource_model.__table__:
                    setattr(field, "left_fk_field", fk.parent)

        setattr(field, "related_model", related_model)
        return field_name, field

    @cached_property
    def _to_many_fields(self) -> list:
        return [
            self._process_to_many_field(field_name, field)
            for field_name, field in self.fields.items()
            if isinstance(field, ToMany)
        ]

    @staticmethod
    def check_exists(session, table: sa.Table, ids: list, field_name: str):
        result = session.execute(
            sa.select([table.c.id]).where(table.c.id.in_(ids))
        )

        missed = set(ids) - {item.id for item in result}
        if missed:
            err_msg = "objects with id {ids} does not exist".format(
                ids=",".join(map(str, missed))
            )
            raise BadRequest({field_name: err_msg})

    def _save_m2m(
        self, session, data: Union[list, dict], update: bool = False
    ) -> None:
        data = data if utils.is_collection(data) else [data]

        for field_name, field in self._to_many_fields:
            if hasattr(field, "secondary"):
                many_2_many = []
                for obj in data:
                    if field_name in obj:
                        many_2_many.extend(
                            [
                                {
                                    field.left_fk_field: obj.get("id"),
                                    field.right_fk_field: rel_id,
                                }
                                for rel_id in obj.get(field_name)
                            ]
                        )

                if update:
                    session.execute(
                        sa.delete(field.secondary).where(
                            field.left_fk_field.in_(
                                [obj.get("id") for obj in data]
                            )
                        )
                    )

                if many_2_many:
                    self.check_exists(
                        session,
                        field.related_model.__table__,
                        [obj.get(field.right_fk_field) for obj in many_2_many],
                        field_name,
                    )
                    session.execute(
                        sa.insert(field.secondary).values(many_2_many)
                    )
