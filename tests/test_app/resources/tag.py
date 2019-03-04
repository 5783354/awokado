from typing import List

import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado import custom_fields
from awokado.consts import CREATE, READ, UPDATE, BULK_UPDATE, DELETE, OP_IN
from awokado.filter_parser import OPERATORS_MAPPING, FilterItem
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
        join=OuterJoin(
            m.Tag, m.M2M_Book_Tag, m.Tag.id == m.M2M_Book_Tag.c.tag_id
        ),
    )

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
        result["id"] = resource_id
        self._update_m2m_book_tag_records(session, result, from_create=True)

        result = self.read_handler(
            session=session, user_id=user_id, resource_id=resource_id
        )

        return result

    def update(
        self, session, payload: dict, user_id: int, resource_id: int = None
    ) -> dict:
        # prepare data for update
        data = payload[self.Meta.name]

        result = self.load(data, many=True, partial=True)
        data_to_update = self._to_update(result)

        ids = [d.get(self.Meta.model.id.key) for d in data_to_update]

        session.bulk_update_mappings(self.Meta.model, data_to_update)
        self._update_m2m_book_tag_records(session, result, from_create=False)

        op = OPERATORS_MAPPING[OP_IN]
        result = self.read_handler(
            session=session,
            user_id=user_id,
            filters=[FilterItem("id", op[0], op[1], ids)],
        )

        return result

    def _update_m2m_book_tag_records(self, session, result, from_create=False):
        if from_create:
            result = [result]

        # update m2m store brand from brands field
        m2m_to_insert = []
        tag_ids_to_clear_m2m = []
        for data in result:
            id_ = data["id"]
            book_ids = data.get("books")
            if book_ids is None:
                continue

            # If tag_ids is not None, can be empty list.
            # If empty list, nullify all m2m relations. If not empty,
            # nullify old relations, insert new.
            # If store is getting created, nullification is not required.
            for book_id in book_ids:
                m2m_to_insert.append(
                    {
                        m.M2M_Book_Tag.c.tag_id: id_,
                        m.M2M_Book_Tag.c.book_id: book_id,
                    }
                )

            tag_ids_to_clear_m2m.append(id_)

        if tag_ids_to_clear_m2m and not from_create:
            session.execute(
                sa.delete(m.M2M_Book_Tag).where(
                    m.M2M_Book_Tag.c.book_id.in_(tag_ids_to_clear_m2m)
                )
            )

        if m2m_to_insert:
            session.execute(sa.insert(m.M2M_Book_Tag).values(m2m_to_insert))

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
