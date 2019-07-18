from unittest.mock import patch

import sqlalchemy as sa

from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class TagStatsTest(BaseAPITest):
    def setup_dataset(self):
        self.store_id = self.session.execute(
            sa.insert(m.Store)
            .values({m.Store.name: "bookstore"})
            .returning(m.Store.id)
        ).scalar()
        self.tag1_name = "Fantastic"
        self.tag1_id = self.create_tag(self.tag1_name)
        self.tag2_name = "Science"
        self.tag2_id = self.create_tag(self.tag2_name)
        self.tag3_name = "Leisure"
        self.tag3_id = self.create_tag(self.tag3_name)
        self.book1_id = self.session.execute(
            sa.insert(m.Book)
            .values({m.Book.title: "first", m.Book.store_id: self.store_id})
            .returning(m.Book.id)
        ).scalar()
        self.book2_id = self.session.execute(
            sa.insert(m.Book)
            .values({m.Book.title: "second", m.Book.store_id: self.store_id})
            .returning(m.Book.id)
        ).scalar()
        self.session.execute(
            sa.insert(m.M2M_Book_Tag).values(
                [
                    {
                        m.M2M_Book_Tag.c.book_id: self.book1_id,
                        m.M2M_Book_Tag.c.tag_id: self.tag1_id,
                    },
                    {
                        m.M2M_Book_Tag.c.book_id: self.book1_id,
                        m.M2M_Book_Tag.c.tag_id: self.tag2_id,
                    },
                    {
                        m.M2M_Book_Tag.c.book_id: self.book2_id,
                        m.M2M_Book_Tag.c.tag_id: self.tag2_id,
                    },
                    {
                        m.M2M_Book_Tag.c.book_id: self.book2_id,
                        m.M2M_Book_Tag.c.tag_id: self.tag3_id,
                    },
                ]
            )
        )

    def setUp(self):
        super().setUp()
        self.app = api
        self.setup_dataset()

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read(self, session_patch):
        self.patch_session(session_patch)
        api_response = self.simulate_get(f"/v1/tag_stats/{self.tag1_name}")
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        self.assertEqual(
            api_response.json["tag_stats"][0],
            {"name": self.tag1_name, "books_count": 1},
        )

        api_response = self.simulate_get(f"/v1/tag_stats/")
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        self.assertEqual(
            self.sort_by_name(api_response.json["payload"]["tag_stats"]),
            self.sort_by_name(
                [
                    {"name": self.tag3_name, "books_count": 1},
                    {"name": self.tag2_name, "books_count": 2},
                    {"name": self.tag1_name, "books_count": 1},
                ]
            ),
        )

    @staticmethod
    def sort_by_name(list_of_dicts):
        return sorted(list_of_dicts, key=lambda d: d["name"])
