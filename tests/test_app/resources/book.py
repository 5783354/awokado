from typing import List

import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado import custom_fields
from awokado.consts import CREATE, READ, UPDATE, BULK_UPDATE, DELETE, OP_IN
from awokado.filter_parser import OPERATORS_MAPPING, FilterItem
from awokado.resource import BaseResource


class BookResource(BaseResource):
    class Meta:
        model = m.Book
        name = "book"
        methods = (CREATE, READ, UPDATE, BULK_UPDATE, DELETE)
        auth = None

    id = fields.Int(model_field=m.Book.id)
    title = fields.String(model_field=m.Book.title, required=True)
    description = fields.String(model_field=m.Book.description)
    author = custom_fields.ToOne(
        resource="author", model_field=m.Book.author_id
    )

    def create(self, session, payload: dict, user_id: int) -> dict:
        # prepare data to insert
        data = payload[self.Meta.name]
        result, errors = self.load(data)
        data_to_insert = self._to_create(result)

        # insert to DB
        resource_id = session.execute(
            sa.insert(self.Meta.model)
            .values(data_to_insert)
            .returning(self.Meta.model.id)
        ).scalar()

        result = self.read_handler(
            session=session, user_id=user_id, resource_id=resource_id
        )

        return result

    def read__query(self, ctx):
        q = (
            sa.select(
                [
                    m.Book.id.label("id"),
                    m.Book.title.label("title"),
                    m.Book.description.label("description"),
                    m.Book.author_id.label("author"),
                ]
            )
            .select_from(
                sa.outerjoin(m.Book, m.Author, m.Author.id == m.Book.author_id)
            )
            .group_by(m.Book.id)
        )

        if not ctx.is_list:
            q = q.where(m.Book.id == ctx.resource_id)

        ctx.q = q

    def update(
        self, session, payload: dict, user_id: int, resource_id: int = None
    ) -> dict:
        # prepare data for update
        data = payload[self.Meta.name]

        result, errors = self.load(data, many=True)
        data_to_update = self._to_update(result)

        ids = [d.get(self.Meta.model.id.key) for d in data_to_update]

        session.bulk_update_mappings(self.Meta.model, data_to_update)
        op = OPERATORS_MAPPING[OP_IN]
        result = self.read_handler(
            session=session,
            user_id=user_id,
            filters=[FilterItem("id", op[0], op[1], ids)],
        )

        return result

    def delete(self, session, user_id: int, resource_id: int):
        session.execute(
            sa.delete(self.Meta.model).where(self.Meta.model.id == resource_id)
        )
        return {}

    def get_by_author_ids(
        self, session, user_id: int, obj_ids: List[int], field: sa.Column = None
    ):
        authors = sa.func.array_remove(
            sa.func.array_agg(m.Author.id), None
        ).label("authors")
        q = (
            sa.select(
                [
                    m.Book.id.label("id"),
                    m.Book.title.label("title"),
                    m.Book.description.label("description"),
                    authors,
                ]
            )
            .select_from(
                sa.outerjoin(m.Book, m.Author, m.Author.id == m.Book.author_id)
            )
            .where(m.Book.id.in_(obj_ids))
            .group_by(m.Book.id)
        )
        result = session.execute(q).fetchall()
        serialized_objs, errors = self.dump(result, many=True)
        return serialized_objs

    def auth(self, *args, **kwargs):
        return None, None

    def audit_log(self, *args, **kwargs):
        ...
