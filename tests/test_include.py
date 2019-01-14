from unittest.mock import patch

import sqlalchemy as sa

from awokado.exceptions import RelationNotFound, NotFound
from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class IncludeTest(BaseAPITest):
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
    def test_include(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get("/v1/book", query_string="include=store")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 3)
        self.assertEqual(len(resp.json["payload"]["store"]), 1)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_include_not_found(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get("/v1/book", query_string="include=xXx")

        self.assertEqual(resp.status, "404 Not Found", resp.text)
        self.assertEqual(resp.json["code"], "relation-not-found")

    @patch("awokado.resource.Transaction", autospec=True)
    def test_include_empty(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get(
            "/v1/book", query_string="include=store&title[eq]=xXx"
        )

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 0)
