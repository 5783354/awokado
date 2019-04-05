import json
from typing import Union

import bulky
import falcon
import sqlalchemy as sa
from clavis import Transaction
from marshmallow import utils, Schema
from marshmallow.fields import List
from marshmallow.schema import SchemaMeta

from awokado.auth import BaseAuth
from awokado.consts import (
    AUDIT_DEBUG,
    UPDATE,
    BULK_CREATE,
    BULK_UPDATE,
    CREATE,
    OP_IN,
    DELETE,
)
from awokado.custom_fields import ToMany, ToOne
from awokado.db import DATABASE_URL, persistent_engine
from awokado.exceptions import (
    BadRequest,
    BadFilter,
    MethodNotAllowed,
    RelationNotFound,
)
from awokado.filter_parser import (
    filter_value_to_python,
    FilterItem,
    OPERATORS_MAPPING,
)
from awokado.utils import (
    get_sort_way,
    empty_response,
    get_read_params,
    ReadContext,
    has_resource_auth,
    cached_property,
)


class ResourceMeta(SchemaMeta):
    def __new__(mcs, cls_name=None, superclasses=None, attributes=None):
        new_resource = super(ResourceMeta, mcs).__new__(
            mcs, cls_name, superclasses, attributes
        )
        new_resource.RESOURCES[new_resource.Meta.name] = new_resource
        res_meta = new_resource.Meta

        if res_meta.name == "base_resource":
            return new_resource
        elif res_meta.name == "_resource":
            return new_resource

        if not hasattr(res_meta, "methods") or not res_meta.methods:
            raise Exception(f"{cls_name} must have Meta.methods")
        if not hasattr(res_meta, "name") or not res_meta.name:
            raise Exception(f"{cls_name} must have Meta.name")
        if not hasattr(res_meta, "auth"):
            raise Exception(f"{cls_name} must have Meta.auth")

        if not hasattr(res_meta, "disable_total"):
            res_meta.disable_total = False

        return new_resource


class BaseResource(Schema, metaclass=ResourceMeta):
    RESOURCES = {}

    class Meta:
        name = "base_resource"
        methods = tuple()
        model = None
        auth = BaseAuth
        skip_doc = True
        disable_total = False

    ###########################################################################
    # Marshmallow validation methods
    ###########################################################################

    def validate_create_request(
        self,
        req: falcon.request.Request,
        resp: falcon.response.Response,
        is_bulk=False,
    ):
        methods = self.Meta.methods
        payload = json.load(req.stream)

        if isinstance(payload.get(self.Meta.name), list):
            request_method = BULK_CREATE
            is_bulk = True
        else:
            request_method = CREATE

        if request_method not in methods:
            raise MethodNotAllowed()

        errors = self.validate(payload.get(self.Meta.name), many=is_bulk)

        if errors:
            raise BadRequest(errors)

        req.stream = payload

    def validate_update_request(
        self, req: falcon.request.Request, resp: falcon.response.Response
    ):
        methods = self.Meta.methods
        if UPDATE not in methods and BULK_UPDATE not in methods:
            raise MethodNotAllowed()

        payload = json.load(req.stream)
        errors = self.validate(
            payload.get(self.Meta.name), partial=True, many=True
        )

        if errors:
            raise BadRequest(errors)

        req.stream = payload

    ###########################################################################
    # Falcon methods
    ###########################################################################

    def on_patch(
        self,
        req: falcon.request.Request,
        resp: falcon.response.Response,
        *args,
        **kwargs,
    ):
        """
        Bulk Update
        """

        with Transaction(DATABASE_URL, engine=persistent_engine) as t:
            session = t.session
            user_id, _ = self.auth(session, req, resp)

            self.validate_update_request(req, resp)

            payload = req.stream

            data = payload[self.Meta.name]
            ids = [d.get(self.Meta.model.id.key) for d in data]

            if hasattr(self.Meta, "auth") and self.Meta.auth is not None:
                self.Meta.auth.can_update(session, user_id, ids)

            self.audit_log(
                f"Update: {self.Meta.name}", payload, user_id, AUDIT_DEBUG
            )

            result = self.update(session, payload, user_id)

        resp.body = json.dumps(result, default=str)

    def on_post(
        self, req: falcon.request.Request, resp: falcon.response.Response
    ):
        """
        Create
        """

        with Transaction(DATABASE_URL, engine=persistent_engine) as t:
            session = t.session
            user_id, token = self.auth(session, req, resp)

            self.validate_create_request(req, resp)

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

    def auth(self, *args, **kwargs):
        raise NotImplementedError("auth method not found")

    def audit_log(self, *args, **kwargs):
        raise NotImplementedError("audit_log method not found")

    def on_get(
        self,
        req: falcon.request.Request,
        resp: falcon.response.Response,
        resource_id: int = None,
    ):
        """
        Read

        :param req: falcon.request.Request
        :param resp: falcon.response.Response
        """
        with Transaction(DATABASE_URL, engine=persistent_engine) as t:
            session = t.session
            user_id, token = self.auth(session, req, resp)
            params = get_read_params(req, self.__class__)

            result = self.read_handler(
                session, user_id, **params, resource_id=resource_id
            )

        resp.body = json.dumps(result, default=str)

    def on_delete(
        self,
        req: falcon.request.Request,
        resp: falcon.response.Response,
        resource_id: int = None,
    ):
        """
        Delete
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
    ) -> dict:
        # prepare data for update
        data = payload[self.Meta.name]

        result = self.load(data, many=True, partial=True)
        data_to_update = self._to_update(result)

        ids = [_i.get(self.Meta.model.id.key) for _i in data_to_update]

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
        # prepare data to insert
        data = payload[self.Meta.name]

        if isinstance(data, list):
            result = self.bulk_create(session, user_id, data)
            return result

        result = self.load(data)

        data_to_insert = self._to_create(result)

        # insert to DB
        resource_id = session.execute(
            sa.insert(self.Meta.model)
            .values(data_to_insert)
            .returning(self.Meta.model.id)
        ).scalar()

        data["id"] = resource_id
        self._save_m2m(session, data)

        result = self.read_handler(
            session=session, user_id=user_id, resource_id=resource_id
        )

        return result

    def bulk_create(self, session, user_id: int, data: list) -> dict:
        result = self.load(data, many=True)

        data_to_insert = []
        for item in result:
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
        filters: [FilterItem] = None,
        sort: list = None,
        resource_id: int = None,
        limit: int = None,
        offset: int = None,
    ) -> dict:

        ctx = ReadContext(
            session,
            type(self),
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
        self.read__execute_query(session, ctx)

        if not ctx.obj_ids:
            if ctx.is_list:
                return empty_response(self, ctx.is_list)
            else:
                raise BadRequest("Object Not Found")

        self.read__includes(session, ctx)
        serialized_data = self.read__serializing(ctx)
        return serialized_data

    def read__filtering(self, ctx: ReadContext):
        if not ctx.query:
            return

        resource_fields = self.fields
        filters_to_apply = []

        for f in ctx.query:
            resource_field = resource_fields.get(f.field)

            # if not resource_field:
            #     raise BadFilter(
            #         details="Filed <{}> doesn't exist".format(f.field)
            #     )

            model_field = resource_field.metadata.get("model_field")

            if model_field is None:
                raise BadFilter(filter=f.field)

            value = f.wrapper(f.value)
            value = filter_value_to_python(value)

            list_deserialization = isinstance(value, list) and not isinstance(
                resource_field, List
            )

            if value is not None:
                if list_deserialization:
                    value = [resource_field.deserialize(item) for item in value]
                else:
                    value = resource_field.deserialize(value)

            field_expr = getattr(model_field, f.op)(value)
            filters_to_apply.append(field_expr)

        ctx.q = ctx.q.where(sa.and_(*filters_to_apply))

    def read__sorting(self, ctx: ReadContext):
        if ctx.sort:
            # TODO: add support for routes
            # example: (xxx.names.display_name)
            for sort_item in ctx.sort:
                sort_route, sort_way = get_sort_way(sort_item)

                if sort_route in self.fields.keys():
                    r_field = self.fields.get(sort_route)
                    ctx.q = ctx.q.order_by(
                        sort_way(r_field.metadata.get("model_field"))
                    )

    def read__pagination(self, ctx: ReadContext):
        limit = ctx.limit
        offset = ctx.offset
        if limit:
            ctx.q = ctx.q.limit(limit)
        if offset:
            ctx.q = ctx.q.offset(offset)

    def read__query(self, ctx):
        fields_to_select = {}

        for field_name, field in self.fields.items():
            model_field = field.metadata.get("model_field")
            if model_field is None:
                raise Exception(
                    f"{self.Meta.name}.{field_name} field must have "
                    f"'model_field' argument"
                )

            if isinstance(field, ToMany):
                fields_to_select[field_name] = sa.func.array_remove(
                    sa.func.array_agg(model_field), None
                )
            elif isinstance(field, ToOne):
                fields_to_select[field_name] = model_field
            else:
                fields_to_select[field_name] = model_field

        q = sa.select([clm.label(lbl) for lbl, clm in fields_to_select.items()])

        joins = getattr(self.Meta, "select_from", None)
        if joins is not None:
            q = q.select_from(joins)

        if not ctx.is_list:
            q = q.where(self.Meta.model.id == ctx.resource_id)

        if has_resource_auth(self):
            q = self.Meta.auth.can_read(ctx, q)

        if joins is not None:
            q = q.group_by(self.Meta.model.id)

        ctx.q = q

    def read__includes(self, session, ctx: ReadContext):
        for i in ctx.include or []:
            if "." in i:
                raise BadRequest()

            elif not isinstance(self.fields.get(i), (ToOne, ToMany)):
                raise RelationNotFound(f"Relation <{i}> not found")

            else:
                related_resource_name = self.fields[i].metadata["resource"]
                related_res = self.RESOURCES[related_resource_name]
                related_field = self.fields[i].metadata.get("model_field")
                method_name = f"get_by_{self.Meta.name.lower()}_ids"

                if not hasattr(related_res, method_name):
                    raise BadRequest(
                        f"Relation {related_resource_name} doesn't ready yet. "
                        f"Ask developers to add {method_name} method "
                        f"to {related_resource_name} resource"
                    )

                related_res_obj = related_res()
                related_data = getattr(related_res_obj, method_name)(
                    session, ctx, related_field
                )
                self.__add_related_payload(ctx, related_res, related_data)

    @staticmethod
    def __add_related_payload(
        ctx: ReadContext, related_res, related_data: list
    ):
        if related_res.Meta.name in ctx.related_payload:
            existing_record_ids = [
                rec["id"] for rec in ctx.related_payload[related_res.Meta.name]
            ]
            for rec in related_data:
                if rec["id"] not in existing_record_ids:
                    ctx.related_payload[related_res.Meta.name].append(rec)
        else:
            ctx.related_payload[related_res.Meta.name] = related_data

    def read__serializing(self, ctx: ReadContext):
        response = {self.Meta.name: ctx.parent_payload}

        response.update(ctx.related_payload)

        if ctx.is_list:
            response = {"payload": response, "meta": None}

            if not self.Meta.disable_total:
                response["meta"] = {"total": ctx.total or 0}

        return response

    def read__execute_query(self, session, ctx: ReadContext):
        if not self.Meta.disable_total:
            ctx.q.append_column(sa.func.count().over().label("total"))

        result = session.execute(ctx.q).fetchall()

        serialized_data = self.dump(result, many=True)

        ctx.obj_ids.extend([_i["id"] for _i in serialized_data])
        ctx.parent_payload = serialized_data

        if serialized_data and not self.Meta.disable_total:
            ctx.total = result[0].total

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

    def _save_m2m(self, session, data: Union[list, dict], update: bool = False):
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
