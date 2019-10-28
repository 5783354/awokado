from dataclasses import dataclass, field
from typing import Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.selectable import Select

from awokado.custom_fields import ToMany, ToOne
from awokado.exceptions import BadFilter, BadRequest, RelationNotFound
from awokado.filter_parser import filter_value_to_python, FilterItem
from awokado.utils import get_id_field, get_sort_way, has_resource_auth

if False:
    from awokado.resource import BaseResource


@dataclass
class ReadContext:
    session: Session
    resource: "BaseResource"
    uid: int

    # request vars
    include: Optional[List]
    query: Optional[List[FilterItem]]
    sort: Optional[list]
    resource_id: Optional[int]
    limit: Optional[int]
    offset: Optional[int]

    # runtime vars
    q: Select = field(default_factory=Select)
    obj_ids: List[int] = field(default_factory=list)
    parent_payload: List = field(default_factory=list)
    related_payload: Dict = field(default_factory=dict)
    total: int = 0

    # for Aggregation Resources
    time_scale = None

    @property
    def is_list(self):
        return not bool(self.resource_id)

    def read__filtering(self):
        if not self.query:
            return

        filters_to_apply = []

        for f in self.query:
            resource_field = self.resource.fields.get(f.field)

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

        self.q = self.q.where(sa.and_(*filters_to_apply))

    def read__sorting(self):
        if self.sort:
            # TODO: add support for routes
            # example: (xxx.names.display_name)
            for sort_item in self.sort:
                sort_route, sort_way = get_sort_way(sort_item)

                if sort_route in self.resource.fields:
                    self.q = self.q.order_by(
                        sort_way(
                            self.resource.fields[sort_route].metadata.get(
                                "model_field"
                            )
                        )
                    )

    def read__pagination(self):
        if self.limit:
            self.q = self.q.limit(self.limit)
        if self.offset:
            self.q = self.q.offset(self.offset)

    def read__query(self):
        fields_to_select = {}
        to_group_by = []

        for field_name, field in self.resource.fields.items():
            model_field = field.metadata.get("model_field")
            if field.load_only:
                continue

            if model_field is None:
                raise Exception(
                    f"{self.resource.Meta.name}.{field_name} field must have "
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
                if (
                    isinstance(model_field, InstrumentedAttribute)
                    and model_field.class_ is not self.resource.Meta.model
                ):
                    to_group_by.append(model_field)

        q = sa.select([clm.label(lbl) for lbl, clm in fields_to_select.items()])

        joins = getattr(self.resource.Meta, "select_from", None)
        if joins is not None:
            q = q.select_from(joins)

        if not self.is_list:
            model_id = get_id_field(self.resource)
            q = q.where(model_id == self.resource_id)

        if has_resource_auth(self.resource):
            q = self.resource.Meta.auth.can_read(self, q)

        if joins is not None:
            model_id = get_id_field(self.resource)
            q = q.group_by(model_id, *to_group_by)

        self.q = q

    def __add_related_payload(self, related_res, related_data: list):
        if related_res.Meta.name in self.related_payload:
            related_res = related_res()
            related_res_id_field = get_id_field(related_res, name_only=True)
            existing_record_ids = [
                rec[related_res_id_field]
                for rec in self.related_payload[related_res.Meta.name]
            ]
            for rec in related_data:
                if rec[related_res_id_field] not in existing_record_ids:
                    self.related_payload[related_res.Meta.name].append(rec)
        else:
            self.related_payload[related_res.Meta.name] = related_data

    def read__includes(self):
        for i in self.include or []:
            if "." in i:
                raise BadRequest()

            elif not isinstance(self.resource.fields.get(i), (ToOne, ToMany)):
                raise RelationNotFound(f"Relation <{i}> not found")

            related_resource_name = self.resource.fields[i].metadata["resource"]
            related_res = self.resource.RESOURCES[related_resource_name]
            related_field = self.resource.fields[i].metadata.get("model_field")
            method_name = f"get_by_{self.resource.Meta.name.lower()}_ids"

            if not hasattr(related_res, method_name):
                raise BadRequest(
                    f"Relation {related_resource_name} doesn't ready yet. "
                    f"Ask developers to add {method_name} method "
                    f"to {related_resource_name} resource"
                )

            related_res_obj = related_res()
            related_data = getattr(related_res_obj, method_name)(
                self.session, self, related_field
            )
            self.__add_related_payload(related_res, related_data)

    def read__serializing(self) -> Dict:
        response = self.resource.Response(self.resource, self.is_list)
        response.set_parent_payload(self.parent_payload)
        response.set_related_payload(self.related_payload)
        response.set_total(self.total)
        serialized_response = response.serialize()
        return serialized_response

    def read__execute_query(self):
        if not self.resource.Meta.disable_total:
            self.q.append_column(sa.func.count().over().label("total"))

        result = self.session.execute(self.q).fetchall()

        serialized_data = self.resource.dump(result, many=True)

        id_field = get_id_field(self.resource, name_only=True)
        self.obj_ids.extend([_i[id_field] for _i in serialized_data])
        self.parent_payload = serialized_data

        if serialized_data and not self.resource.Meta.disable_total:
            self.total = result[0].total
