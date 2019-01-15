from typing import List

import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado import custom_fields
from awokado.consts import CREATE, READ, UPDATE, BULK_UPDATE, DELETE, OP_IN
from awokado.filter_parser import OPERATORS_MAPPING, FilterItem
from tests.test_app.resources.base import Resource


class AuthorResource(Resource):
    class Meta:
        model = m.Author
        name = "author"
        methods = (CREATE, READ, UPDATE, BULK_UPDATE, DELETE)
        auth = None

    id = fields.Int(model_field=m.Author.id)
    books = custom_fields.ToMany(fields.Int(), resource="book")
    books_count = fields.Int(
        dump_only=True, model_field=sa.func.count(m.Book.id)
    )
    name = fields.String(model_field=m.Author.name, required=True)

    def create(self, session, payload: dict, user_id: int) -> dict:
        # prepare data to insert
        data = payload[self.Meta.name]
        result = self.load(data)
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
        books_count = self.fields.get("books_count").metadata["model_field"]
        q = (
            sa.select(
                [
                    m.Author.id.label("id"),
                    m.Author.name.label("name"),
                    books_count.label("books_count"),
                ]
            )
            .select_from(
                sa.outerjoin(m.Author, m.Book, m.Author.id == m.Book.author_id)
            )
            .group_by(m.Author.id)
        )

        if not ctx.is_list:
            q = q.where(m.Author.id == ctx.resource_id)

        ctx.q = q

    def update(
        self, session, payload: dict, user_id: int, resource_id: int = None
    ) -> dict:
        # prepare data for update
        data = payload[self.Meta.name]

        result = self.load(data, many=True, partial=True)
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

    def get_by_book_ids(
        self, session, user_id: int, obj_ids: List[int], field: sa.Column = None
    ):
        books_count = self.fields.get("books_count").metadata["model_field"]
        q = (
            sa.select(
                [
                    m.Author.id.label("id"),
                    m.Author.name.label("name"),
                    books_count.label("books_count"),
                ]
            )
            .select_from(
                sa.outerjoin(m.Author, m.Book, m.Author.id == m.Book.author_id)
            )
            .where(m.Book.id.in_(obj_ids))
            .group_by(m.Author.id)
        )
        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)
        return serialized_objs
