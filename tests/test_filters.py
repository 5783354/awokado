from unittest.mock import patch

import sqlalchemy as sa

from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class FiltersTest(BaseAPITest):
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
    def test_filter_eq(self, session_patch):
        self.patch_session(session_patch)
        api_response = self.simulate_get(
            "/v1/book", query_string="title[eq]=first"
        )

        db_result = self.session.execute(
            sa.select([m.Book.id]).where(m.Book.id == self.book1_id)
        ).fetchall()

        self.assertEqual(api_response.status, "200 OK", api_response.text)
        self.assertEqual(len(db_result), 1)
        self.assertEqual(len(api_response.json["payload"]["book"]), 1)
        self.assertEqual(
            self.book1_id, api_response.json["payload"]["book"][0]["id"]
        )

        api_response = self.simulate_get(
            "/v1/book", query_string="title[eq]=xxx"
        )
        self.assertEqual(len(api_response.json["payload"]["book"]), 0)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_filter_in(self, session_patch):
        self.patch_session(session_patch)
        api_response = self.simulate_get(
            "/v1/book", query_string="title[in]=first"
        )

        db_result = self.session.execute(
            sa.select([m.Book.id]).where(m.Book.id == self.book1_id)
        ).fetchall()

        self.assertEqual(api_response.status, "200 OK", api_response.text)
        self.assertEqual(len(db_result), 1)
        self.assertEqual(len(api_response.json["payload"]["book"]), 1)
        self.assertEqual(
            self.book1_id, api_response.json["payload"]["book"][0]["id"]
        )

        api_response = self.simulate_get(
            "/v1/book", query_string="title[in]=first,second"
        )
        self.assertEqual(len(api_response.json["payload"]["book"]), 2)

        api_response = self.simulate_get(
            "/v1/book", query_string=f"id[in]={self.book1_id},{self.book2_id}"
        )
        self.assertEqual(len(api_response.json["payload"]["book"]), 2)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_filter_ilike(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get("/v1/book", query_string="title[ilike]=s")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 2)

        resp = self.simulate_get("/v1/book", query_string="title[ilike]=FiR")
        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 1)

        resp = self.simulate_get("/v1/book", query_string="title[ilike]=xXx")
        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 0)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_filter_ilike(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get("/v1/book", query_string="title[ilike]=s")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 2)

        resp = self.simulate_get("/v1/book", query_string="title[ilike]=FiR")
        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 1)

        resp = self.simulate_get("/v1/book", query_string="title[ilike]=xXx")
        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 0)
