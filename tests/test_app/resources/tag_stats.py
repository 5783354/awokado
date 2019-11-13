import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado.consts import READ
from awokado.meta import ResourceMeta
from awokado.resource import BaseResource


class TagStatsResource(BaseResource):
    Meta = ResourceMeta(
        model=m.Tag,
        name="tag_stats",
        methods=(READ,),
        disable_total=True,
        select_from=sa.outerjoin(
            m.Tag, m.M2M_Book_Tag, m.Tag.id == m.M2M_Book_Tag.c.tag_id
        ).outerjoin(m.Book, m.M2M_Book_Tag.c.book_id == m.Book.id),
        id_field="name",
    )

    name = fields.String(model_field=m.Tag.name)
    books_count = fields.Int(
        dump_only=True, model_field=sa.func.count(m.Book.id)
    )
