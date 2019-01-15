import json

import falcon
import sqlalchemy as sa
from marshmallow import Schema
from marshmallow.schema import SchemaMeta
from stairs import Transaction

from awokado.auth import BaseAuth
from awokado.consts import AUDIT_DEBUG
from awokado.custom_fields import ToMany, ToOne
from awokado.db import DATABASE_URL
from awokado.exceptions import (
    BadRequest,
    BadFilter,
    DeleteResourceForbidden,
    MethodNotAllowed,
    RelationNotFound,
    UnsupportedMethod,
)
from awokado.filter_parser import filter_value_to_python, FilterItem
from awokado.utils import (
    get_sort_way,
    empty_response,
    get_read_params,
    ReadContext,
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

        return new_resource


class BaseResource(Schema, metaclass=ResourceMeta):
    RESOURCES = {}

    class Meta:
        name = "base_resource"
        methods = tuple()
        auth = BaseAuth
        skip_doc = True

    ###########################################################################
    # Marshmallow validation methods
    ###########################################################################

    def validate_create_request(
        self,
        req: falcon.request.Request,
        resp: falcon.response.Response,
        is_bulk=False,
    ):
        payload = json.load(req.stream)
        errors = self.validate(payload.get(self.Meta.name), many=is_bulk)

        if errors:
            raise BadRequest(errors)

        req.stream = payload

    def validate_update_request(
        self, req: falcon.request.Request, resp: falcon.response.Response
    ):
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
        resource_id: int = None,
    ):
        """
        Update
        """

        with Transaction(DATABASE_URL) as t:
            session = t.session
            user_id, _ = self.auth(session, req, resp)

            self.validate_update_request(req, resp)

            payload = req.stream

            self.audit_log(
                f"Update: {self.Meta.name}", payload, user_id, AUDIT_DEBUG
            )

            data = payload[self.Meta.name]
            ids = [d.get(self.Meta.model.id.key) for d in data]

            if hasattr(self.Meta, "auth") and self.Meta.auth is not None:
                self.Meta.auth.can_update(session, user_id, ids)

            result = self.update(session, payload, user_id, resource_id)

        resp.body = json.dumps(result, default=str)

    def on_post(
        self, req: falcon.request.Request, resp: falcon.response.Response
    ):
        """
        Create
        """

        with Transaction(DATABASE_URL) as t:
            session = t.session
            user_id, token = self.auth(session, req, resp)

            if hasattr(self.Meta, "auth") and self.Meta.auth is not None:
                self.Meta.auth.can_create(session, user_id, skip_exc=False)

            self.validate_create_request(req, resp)

            payload = req.stream

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
        with Transaction(DATABASE_URL) as t:
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

        with Transaction(DATABASE_URL) as t:
            session = t.session
            user_id, token = self.auth(session, req, resp)

            if not resource_id:
                raise DeleteResourceForbidden(
                    details="Bulk deletion is forbidden"
                )

            if hasattr(self.Meta, "auth") and self.Meta.auth is not None:
                self.Meta.auth.can_delete(session, user_id, [resource_id])

            result = self.delete(session, user_id, resource_id)

        resp.body = json.dumps(result, default=str)

    ###########################################################################
    # Resource methods
    ###########################################################################

    def update(self, session, payload: dict, user_id: int, resource_id: int):
        raise MethodNotAllowed()

    def create(self, session, payload: dict, user_id: int):
        raise MethodNotAllowed()

    def delete(self, session, user_id: int, resource_id: int):
        raise MethodNotAllowed()

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

            if value is not None and not isinstance(value, list):
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
        raise UnsupportedMethod()

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
                        f"Resource {related_resource_name} doesn't ready"
                    )

                related_res_obj = related_res()
                related_data = getattr(related_res_obj, method_name)(
                    session, ctx.uid, ctx.obj_ids, related_field
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
            meta_payload = {"total": ctx.total or 0}
            response = {"meta": meta_payload, "payload": response}

        return response

    def read__execute_query(self, session, ctx: ReadContext):
        ctx.q.append_column(sa.func.count().over().label("total"))
        result = session.execute(ctx.q).fetchall()

        serialized_data = self.dump(result, many=True)

        ctx.obj_ids.extend([_i["id"] for _i in serialized_data])
        ctx.parent_payload = serialized_data

        if serialized_data:
            ctx.total = result[0].total
