import sqlalchemy as sa
from marshmallow import fields
from sqlalchemy.sql import Selectable

import tests.test_app.models as m
from awokado import custom_fields
from awokado.auth import BaseAuth
from awokado.consts import CREATE, READ, UPDATE, BULK_UPDATE, DELETE
from awokado.meta import ResourceMeta
from awokado.request import ReadContext
from awokado.resource import BaseResource


class AuthorAuth(BaseAuth):
    @classmethod
    def can_create(cls, session, payload, user_id: int, skip_exc=False):
        return True

    @classmethod
    def can_read(cls, ctx, query: Selectable, skip_exc=False):
        return query

    @classmethod
    def can_update(cls, session, user_id: int, obj_ids: list, skip_exc=False):
        return True

    @classmethod
    def can_delete(cls, session, user_id: int, obj_ids: list, skip_exc=False):
        return True

    @classmethod
    def _get_read_query(cls, ctx, query: Selectable):
        return query


class AuthorResource(BaseResource):
    Meta = ResourceMeta(
        model=m.Author,
        name="author",
        methods=(CREATE, READ, UPDATE, BULK_UPDATE, DELETE),
        auth=AuthorAuth,
        select_from=sa.outerjoin(
            m.Author, m.Book, m.Author.id == m.Book.author_id
        ),
    )

    id = fields.Int(model_field=m.Author.id)
    books = custom_fields.ToMany(
        fields.Int(),
        resource="book",
        model_field=m.Book.id,
        description="Authors Books",
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
    last_name = fields.String(
        model_field=m.Author.last_name, required=True, load_only=True
    )
    first_name = fields.String(
        model_field=m.Author.first_name, required=True, load_only=True
    )

    field_without_model_field = fields.String(load_only=True)

    def get_by_book_ids(
        self, session, ctx: ReadContext, field: sa.Column = None
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
            .where(m.Book.id.in_(ctx.obj_ids))
            .group_by(m.Author.id)
        )
        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)
        return serialized_objs
