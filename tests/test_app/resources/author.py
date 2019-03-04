from typing import List

import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado import custom_fields
from awokado.consts import CREATE, READ, UPDATE, BULK_UPDATE, DELETE
from awokado.utils import OuterJoin
from tests.test_app.resources.base import Resource


class AuthorResource(Resource):
    class Meta:
        model = m.Author
        name = "author"
        methods = (CREATE, READ, UPDATE, BULK_UPDATE, DELETE)
        auth = None

    id = fields.Int(model_field=m.Author.id)
    books = custom_fields.ToMany(
        fields.Int(),
        resource="book",
        model_field=m.Book.id,
        join=OuterJoin(m.Author, m.Book, m.Author.id == m.Book.author_id),
    )
    books_count = fields.Int(
        dump_only=True, model_field=sa.func.count(m.Book.id)
    )
    name = fields.String(
        model_field=sa.func.concat(
            m.Author.first_name, " ", m.Author.last_name
        ),
        dump_only=True,
    )
    last_name = fields.String(model_field=m.Author.last_name, required=True)
    first_name = fields.String(model_field=m.Author.first_name, required=True)

    def get_by_book_ids(
        self, session, user_id: int, obj_ids: List[int], field: sa.Column = None
    ):
        books_count = self.fields.get("books_count").metadata["model_field"]
        q = (
            sa.select(
                [
                    m.Author.id.label("id"),
                    self.fields.name.metadata["model_field"].label("name"),
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
