from typing import List

import sqlalchemy as sa
from marshmallow import fields

import tests.test_app.models as m
from awokado import custom_fields
from awokado.consts import CREATE, READ, UPDATE, BULK_UPDATE, DELETE, OP_IN
from awokado.filter_parser import FilterItem, OPERATORS_MAPPING
from tests.test_app.resources.base import Resource


class BookResource(Resource):
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
    store = custom_fields.ToOne(resource="store", model_field=m.Book.store_id)
    tags = custom_fields.ToMany(fields.Int(), resource="tag")

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

    def read__query(self, ctx):
        tags = sa.func.array_remove(
            sa.func.array_agg(m.M2M_Book_Tag.c.tag_id), None
        ).label("tags")

        q = (
            sa.select(
                [
                    m.Book.id.label("id"),
                    m.Book.title.label("title"),
                    m.Book.description.label("description"),
                    m.Book.author_id.label("author"),
                    m.Book.store_id.label("store"),
                    tags,
                ]
            )
            .select_from(
                sa.outerjoin(
                    m.Book, m.Author, m.Author.id == m.Book.author_id
                ).outerjoin(
                    m.M2M_Book_Tag, m.Book.id == m.M2M_Book_Tag.c.book_id
                )
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
        book_ids_to_clear_m2m = []
        for data in result:
            id_ = data["id"]
            tag_ids = data.get("tags")
            if tag_ids is None:
                continue

            # If tag_ids is not None, can be empty list.
            # If empty list, nullify all m2m relations. If not empty,
            # nullify old relations, insert new.
            # If store is getting created, nullification is not required.
            for tag_id in tag_ids:
                m2m_to_insert.append(
                    {
                        m.M2M_Book_Tag.c.book_id: id_,
                        m.M2M_Book_Tag.c.tag_id: tag_id,
                    }
                )

            book_ids_to_clear_m2m.append(id_)

        if book_ids_to_clear_m2m and not from_create:
            session.execute(
                sa.delete(m.M2M_Book_Tag).where(
                    m.M2M_Book_Tag.c.book_id.in_(book_ids_to_clear_m2m)
                )
            )

        if m2m_to_insert:
            session.execute(sa.insert(m.M2M_Book_Tag).values(m2m_to_insert))

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
                    m.Book.store_id.label("store"),
                    authors,
                ]
            )
            .select_from(
                sa.outerjoin(m.Book, m.Author, m.Author.id == m.Book.author_id)
            )
            .where(m.Book.author_id.in_(obj_ids))
            .group_by(m.Book.id)
        )
        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)
        return serialized_objs

    def get_by_tag_ids(
        self, session, user_id: int, obj_ids: List[int], field: sa.Column = None
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
            .where(m.M2M_Book_Tag.c.tag_id.in_(obj_ids))
        )

        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)

        return serialized_objs
