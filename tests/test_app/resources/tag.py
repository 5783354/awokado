import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado import custom_fields
from awokado.consts import CREATE, READ, UPDATE, BULK_UPDATE, DELETE
from awokado.utils import ReadContext, OuterJoin
from tests.test_app.resources.base import Resource


class TagResource(Resource):
    class Meta:
        model = m.Tag
        name = "tag"
        methods = (CREATE, READ, UPDATE, BULK_UPDATE, DELETE)
        auth = None
        disable_total = True

    id = fields.Int(model_field=m.Tag.id)
    name = fields.String(model_field=m.Tag.name)
    books = custom_fields.ToMany(
        fields.Int(),
        resource="book",
        model_field=m.M2M_Book_Tag.c.book_id,
        # Join Tag with M2M_Book_Tag already made in book_titles field,
        # no need to duplicate it here
        # join=OuterJoin(
        #     m.Tag, m.M2M_Book_Tag, m.Tag.id == m.M2M_Book_Tag.c.tag_id
        # ),
    )
    book_titles = fields.List(
        fields.Str(),
        resource="author",
        model_field=sa.func.array_remove(sa.func.array_agg(m.Book.title), None),
        join=[
            OuterJoin(
                m.Tag, m.M2M_Book_Tag, m.Tag.id == m.M2M_Book_Tag.c.tag_id
            ),
            OuterJoin(
                m.M2M_Book_Tag, m.Book, m.M2M_Book_Tag.c.book_id == m.Book.id
            ),
        ],
    )

    def get_by_book_ids(self, session, ctx: ReadContext, field: str = None):
        """
        :param user_id:     User id
        :return:            serialized JSON response
        """
        q = (
            sa.select([m.Tag.id.label("id"), m.Tag.name.label("name")])
            .select_from(
                sa.join(
                    m.M2M_Book_Tag, m.Tag, m.M2M_Book_Tag.c.tag_id == m.Tag.id
                )
            )
            .where(m.M2M_Book_Tag.c.book_id.in_(ctx.obj_ids))
        )

        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)

        return serialized_objs
