from typing import List

import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado import custom_fields
from awokado.consts import CREATE, READ, UPDATE, BULK_UPDATE, DELETE
from awokado.request import ReadContext
from tests.test_app.resources.base import Resource


class BookResource(Resource):
    class Meta:
        model = m.Book
        name = "book"
        methods = (CREATE, READ, UPDATE, BULK_UPDATE, DELETE)
        auth = None
        select_from = sa.outerjoin(
            m.Book, m.M2M_Book_Tag, m.Book.id == m.M2M_Book_Tag.c.book_id
        )

    id = fields.Int(model_field=m.Book.id)
    title = fields.String(model_field=m.Book.title, required=True)
    description = fields.String(model_field=m.Book.description)
    author = custom_fields.ToOne(
        resource="author", model_field=m.Book.author_id
    )
    store = custom_fields.ToOne(
        resource="store",
        model_field=m.Book.store_id,
        description="Store selling book",
    )
    tags = custom_fields.ToMany(
        fields.Int(), resource="tag", model_field=m.M2M_Book_Tag.c.tag_id
    )

    def get_by_author_ids(
        self, session, ctx: ReadContext, field: sa.Column = None
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
                    m.Book.store_id.label("store"),
                    authors,
                ]
            )
            .select_from(
                sa.outerjoin(m.Book, m.Author, m.Author.id == m.Book.author_id)
            )
            .where(m.Book.author_id.in_(ctx.obj_ids))
            .group_by(m.Book.id)
        )
        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)
        return serialized_objs

    def get_by_tag_ids(
        self, session, ctx: ReadContext, field: sa.Column = None
    ):
        q = (
            sa.select(
                [
                    m.Book.id.label("id"),
                    m.Book.title.label("title"),
                    m.Book.description.label("description"),
                    m.Book.store_id.label("store"),
                ],
                distinct=True,
            )
            .select_from(
                sa.join(
                    m.M2M_Book_Tag,
                    m.Book,
                    m.M2M_Book_Tag.c.book_id == m.Book.id,
                )
            )
            .where(m.M2M_Book_Tag.c.tag_id.in_(ctx.obj_ids))
        )

        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)

        return serialized_objs
