import json
import sys
from typing import Dict, List, Optional, Tuple, Union, Type

import bulky
import falcon
import sqlalchemy as sa
from cached_property import cached_property
from clavis import Transaction
from marshmallow import utils, Schema, ValidationError
from sqlalchemy.orm import Session

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
from awokado.filter_parser import FilterItem
from awokado.meta import ResourceMeta
from awokado.request import ReadContext
from awokado.response import Response
from awokado.utils import (
    get_ids_from_payload,
    get_read_params,
    get_id_field,
    M2MMapping,
    AuthBundle,
)


class BaseResource(Schema):
    RESOURCES: Dict[str, Type["BaseResource"]] = {}
    Response = Response
    Meta: ResourceMeta

    def __new__(cls: Type["BaseResource"]):
        if cls.Meta.name not in ("base_resource", "_resource"):
            cls.RESOURCES[cls.Meta.name] = cls

        return super().__new__(cls)

    def __init__(self):
        super().__init__()
        cls_name = self.__class__.__name__

        class_meta = getattr(self, "Meta", None)
        if isinstance(class_meta, type):
            print(
                "resourse.Meta as class will be deprecated soon",
                file=sys.stderr,
            )
            self.Meta = ResourceMeta.from_class(class_meta)

        if not isinstance(self.Meta, ResourceMeta):
            raise Exception(
                f"{cls_name}.Meta must inherit from ResourceMeta class"
            )

        if not self.Meta.name or self.Meta.name in (
            "base_resource",
            "_resource",
        ):
            raise Exception(f"{cls_name} must have Meta.name")

        resource_id_name = get_id_field(self, name_only=True, skip_exc=True)
        if resource_id_name:
            resource_id_field = self.fields.get(resource_id_name)
            resource_id_field = resource_id_field.metadata.get("model_field")
            if not resource_id_field:
                raise Exception(
                    f"Resource's {cls_name} id field {resource_id_name}"
                    f" must have model_field."
                )

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

        if not data:
            raise BadRequest(
                f"Invalid schema, resource name is missing at the top level. "
                f"Your POST request has to look like: "
                f'{{"{self.Meta.name}": [{{"field_name": "field_value"}}] '
                f'or {{"field_name": "field_value"}} }}'
            )

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
        This is where authentication takes place
        (if auth class is pointed in `resource <#awokado.meta.ResourceMeta>`_)
        Then update method is run.
        """
        with Transaction(DATABASE_URL, engine=persistent_engine) as t:
            session = t.session
            user_id, _ = self.auth(session, req, resp)

            self.validate_update_request(req)

            payload = req.stream

            data = payload[self.Meta.name]

            ids = get_ids_from_payload(self.Meta.model, data)

            if self.Meta.auth:
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
        This is where authentication takes place
        (if auth class is pointed in `resource <#awokado.meta.ResourceMeta>`_)
        Then create method is run.
        """
        with Transaction(DATABASE_URL, engine=persistent_engine) as t:
            session = t.session
            user_id, token = self.auth(session, req, resp)

            self.validate_create_request(req)

            payload = req.stream

            if self.Meta.auth:
                self.Meta.auth.can_create(
                    session, payload, user_id, skip_exc=False
                )

            self.audit_log(
                f"Create: {self.Meta.name}", payload, user_id, AUDIT_DEBUG
            )

            result = self.create(session, payload, user_id)

        resp.body = json.dumps(result, default=str)

    def on_get(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        resource_id: int = None,
    ):
        """
        Falcon method. GET-request entry point.

        Here is a database transaction opening.
        This is where authentication takes place
        (if auth class is pointed in `resource <#awokado.meta.ResourceMeta>`_)
        Then read_handler method is run.
        It's responsible for the whole read workflow.
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
        This is where authentication takes place
        (if auth class is pointed in `resource <#awokado.meta.ResourceMeta>`_)
        Then delete method is run.
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

            if self.Meta.auth:
                self.Meta.auth.can_delete(session, user_id, ids_to_delete)

            result = self.delete(session, user_id, ids_to_delete)

        resp.body = json.dumps(result, default=str)

    def auth(self, *args, **kwargs) -> AuthBundle:
        """This method should return (user_id, token) tuple"""
        return AuthBundle(0, "")

    def audit_log(self, *args, **kwargs):
        return

    def _check_model_exists(self):
        if not self.Meta.model:
            raise Exception(
                f"{self.__class__.__name__}.Meta.model field not set"
            )

    ###########################################################################
    # Resource methods
    ###########################################################################

    def update(
        self, session: Session, payload: dict, user_id: int, *args, **kwargs
    ) -> dict:
        """
        First of all, data is prepared for updating:
        Marshmallow load method for data structure deserialization and then preparing data for SQLAlchemy update query.

        Updates data with bulk_update_mappings sqlalchemy method. Saves many-to-many relationships.

        Returns updated resources with the help of read_handler method.
        """
        self._check_model_exists()

        data = payload[self.Meta.name]

        data_to_update = self._to_update(data)

        ids = get_ids_from_payload(self.Meta.model, data_to_update)

        session.bulk_update_mappings(self.Meta.model, data_to_update)
        self._save_m2m(session, data, update=True)

        result = self.read_handler(
            session=session,
            user_id=user_id,
            filters=[FilterItem.create("id", OP_IN, ids)],
        )

        return result

    def create(self, session: Session, payload: dict, user_id: int) -> dict:
        """
        Create method

        You can override it to add your logic.

        First of all, data is prepared for creating:
        Marshmallow load method for data structure deserialization and then preparing data for SQLAlchemy create a query.

        Inserts data to the database
        (Uses bulky library if there is more than one entity to create). Saves many-to-many relationships.

        Returns created resources with the help of read_handler method.

        """
        self._check_model_exists()

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

    def bulk_create(self, session: Session, user_id: int, data: list) -> dict:
        self._check_model_exists()

        data_to_insert = [self._to_create(i) for i in data]

        # insert to DB
        resource_ids = bulky.insert(
            session,
            self.Meta.model,
            data_to_insert,
            returning=[self.Meta.model.id],
        )
        ids = [r.id for r in resource_ids]

        result = self.read_handler(
            session=session,
            user_id=user_id,
            filters=[FilterItem.create("id", OP_IN, ids)],
        )

        return result

    def delete(self, session: Session, user_id: int, obj_ids: list):
        """
        Simply deletes objects with passed identifiers
        """
        self._check_model_exists()

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
        session: Session,
        user_id: int,
        include: list = None,
        filters: Optional[List[FilterItem]] = None,
        sort: list = None,
        resource_id: int = None,
        limit: int = None,
        offset: int = None,
    ) -> dict:

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

    def read__serializing(self, ctx: ReadContext) -> dict:
        return ctx.read__serializing()

    def get_related_model(self, field: Union[ToOne, ToMany]):
        resource_name = field.metadata["resource"]
        resource = self.RESOURCES[resource_name]
        return resource.Meta.model

    def _process_to_many_field(self, field: ToMany) -> M2MMapping:
        related_model = self.get_related_model(field)
        resource_model = self.Meta.model
        model_field = field.metadata["model_field"]

        field_obj = M2MMapping(related_model=related_model)

        if not isinstance(model_field, sa.Column):
            model_field = getattr(
                model_field.parent.persist_selectable.c, model_field.key
            )

        if related_model.__table__ == model_field.table:
            for fk in model_field.table.foreign_keys:
                if fk.column.table == resource_model.__table__:
                    field_obj.left_fk_field = fk.parent
                    break
        else:
            field_obj.secondary = model_field.table
            for fk in model_field.table.foreign_keys:
                if fk.column.table == related_model.__table__:
                    field_obj.right_fk_field = fk.parent
                elif fk.column.table == resource_model.__table__:
                    field_obj.left_fk_field = fk.parent

        return field_obj

    @cached_property
    def _to_many_fields(self) -> List[Tuple[str, M2MMapping]]:
        return [
            (field_name, self._process_to_many_field(field))
            for field_name, field in self.fields.items()
            if isinstance(field, ToMany)
        ]

    @staticmethod
    def check_exists(
        session: Session, table: sa.Table, ids: list, field_name: str
    ):
        result = session.execute(
            sa.select([table.c.id]).where(table.c.id.in_(ids))
        )

        missed = set(ids) - {item.id for item in result}
        if missed:
            raise BadRequest(
                {
                    field_name: f"objects with id {','.join(map(str, missed))} does not exist"
                }
            )

    @staticmethod
    def _get_m2m(field: M2MMapping, field_name: str, data) -> List[dict]:
        m2m = []
        for obj in data:
            rel_ids = obj.get(field_name) or ()
            for rel_id in rel_ids:
                m2m.append(
                    {
                        field.left_fk_field: obj.get("id"),
                        field.right_fk_field: rel_id,
                    }
                )
        return m2m

    def _save_m2m(
        self, session: Session, data: Union[list, dict], update: bool = False
    ) -> None:
        data = data if utils.is_collection(data) else [data]

        for field_name, field in self._to_many_fields:
            if field.secondary is not None:
                if update:
                    session.execute(
                        sa.delete(field.secondary).where(
                            field.left_fk_field.in_(
                                [obj.get("id") for obj in data]
                            )
                        )
                    )

                many_2_many = self._get_m2m(field, field_name, data)

                if many_2_many:
                    self.check_exists(
                        session,
                        field.related_model.__table__,
                        [obj[field.right_fk_field] for obj in many_2_many],
                        field_name,
                    )
                    session.execute(
                        sa.insert(field.secondary).values(many_2_many)
                    )
