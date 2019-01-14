from unittest.mock import patch

import sqlalchemy as sa

from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class SortTest(BaseAPITest):
    def setup_dataset(self):
        self.store_id = self.session.execute(
            sa.insert(m.Store)
            .values({m.Store.name: "bookstore"})
            .returning(m.Store.id)
        ).scalar()
        self.book1_id = self.session.execute(
            sa.insert(m.Book)
            .values(
                {
                    m.Book.title: "first",
                    m.Book.store_id: self.store_id,
                    m.Book.description: "description1",
                }
            )
            .returning(m.Book.id)
        ).scalar()
        self.book2_id = self.session.execute(
            sa.insert(m.Book)
            .values(
                {
                    m.Book.title: "second",
                    m.Book.store_id: self.store_id,
                    m.Book.description: "description2",
                }
            )
            .returning(m.Book.id)
        ).scalar()
        self.book3_id = self.session.execute(
            sa.insert(m.Book)
            .values(
                {
                    m.Book.title: "third",
                    m.Book.store_id: self.store_id,
                    m.Book.description: "description3",
                }
            )
            .returning(m.Book.id)
        ).scalar()

    def setUp(self):
        super().setUp()
        self.app = api
        self.setup_dataset()

    @patch("awokado.resource.Transaction", autospec=True)
    def test_asc_sort(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get("/v1/book/", query_string="sort=title")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 3)
        self.assertEqual(resp.json["payload"]["book"][0]["title"], "first")
        self.assertEqual(resp.json["payload"]["book"][1]["title"], "second")
        self.assertEqual(resp.json["payload"]["book"][2]["title"], "third")

    @patch("awokado.resource.Transaction", autospec=True)
    def test_desc_sort(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get("/v1/book/", query_string="sort=-title")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 3)
        self.assertEqual(resp.json["payload"]["book"][2]["title"], "first")
        self.assertEqual(resp.json["payload"]["book"][1]["title"], "second")
        self.assertEqual(resp.json["payload"]["book"][0]["title"], "third")

    @patch("awokado.resource.Transaction", autospec=True)
    def test_multi_field_sort(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get(
            "/v1/book/", query_string="sort=title,description"
        )

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 3)
        self.assertEqual(resp.json["payload"]["book"][0]["title"], "first")
        self.assertEqual(resp.json["payload"]["book"][1]["title"], "second")
        self.assertEqual(resp.json["payload"]["book"][2]["title"], "third")

    @patch("awokado.resource.Transaction", autospec=True)
    def test_sort_wrong_field(self, session_patch):
        self.patch_session(session_patch)
        # TODO: add exception
        resp = self.simulate_get("/v1/book/", query_string="sort=xxx")
