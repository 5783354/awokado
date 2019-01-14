from unittest.mock import patch

import sqlalchemy as sa

from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class ReadTest(BaseAPITest):
    def setup_dataset(self):
        self.store_id = self.session.execute(
            sa.insert(m.Store)
            .values({m.Store.name: "bookstore"})
            .returning(m.Store.id)
        ).scalar()
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
        self.book3_id = self.session.execute(
            sa.insert(m.Book)
            .values({m.Book.title: "third", m.Book.store_id: self.store_id})
            .returning(m.Book.id)
        ).scalar()

    def setUp(self):
        super().setUp()
        self.app = api
        self.setup_dataset()

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read_by_id(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get(f"/v1/book/{self.book1_id}")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["book"]), 1)
        self.assertEqual(resp.json["book"][0]["id"], self.book1_id)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get(f"/v1/book")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 3)
        self.assertEqual(resp.json["meta"]["total"], 3)

        resp = self.simulate_get(
            f"/v1/book", query_string="limit=1&offset=1&sort=title"
        )

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 1)
        self.assertEqual(resp.json["meta"]["total"], 3)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read_wrong_resource(self, session_patch):
        self.patch_session(session_patch)

        resp = self.simulate_get(f"/v1/BADbook")
        self.assertEqual(resp.status, "404 Not Found", resp.text)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read_by_wrong_id(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get(f"/v1/book/42423423")
        # TODO: change to 404 Not Found
        self.assertEqual(resp.status, "400 Bad Request", resp.text)
        self.assertEqual(resp.json["detail"], "Object Not Found")
