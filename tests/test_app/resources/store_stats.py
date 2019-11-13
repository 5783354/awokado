import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado.consts import READ
from awokado.meta import ResourceMeta
from awokado.resource import BaseResource


class StoreStatsResource(BaseResource):
    Meta = ResourceMeta(
        model=m.Store,
        name="store_stats",
        methods=(READ,),
        select_from=sa.outerjoin(
            m.Store, m.Book, m.Store.id == m.Book.store_id
        ),
    )

    name = fields.String(model_field=m.Store.name)
    books_count = fields.Int(
        dump_only=True, model_field=sa.func.count(m.Book.id)
    )
