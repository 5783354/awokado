import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado import custom_fields
from awokado.consts import CREATE, READ, BULK_CREATE
from awokado.utils import ReadContext
from tests.test_app.resources.base import Resource


class StoreResource(Resource):
    class Meta:
        model = m.Store
        name = "store"
        methods = (CREATE, BULK_CREATE, READ)
        select_from = sa.outerjoin(
            m.Store, m.Book, m.Store.id == m.Book.store_id
        )

    id = fields.Int(model_field=m.Store.id)
    book_ids = custom_fields.ToMany(
        fields.Int(), resource="book", model_field=m.Book.id
    )
    name = fields.String(model_field=m.Store.name, required=True)

    def get_by_book_ids(
        self, session, ctx: ReadContext, field: sa.Column = None
    ):
        q = (
            sa.select(
                [
                    m.Store.id.label("id"),
                    m.Store.name.label("name"),
                    sa.func.array_agg(m.Book.id).label("book_ids"),
                ]
            )
            .select_from(
                sa.outerjoin(m.Store, m.Book, m.Store.id == m.Book.store_id)
            )
            .where(m.Book.id.in_(ctx.obj_ids))
            .group_by(m.Store.id)
        )

        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)
        return serialized_objs
