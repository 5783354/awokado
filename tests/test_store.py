from unittest.mock import patch

import sqlalchemy as sa

from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class StoreTest(BaseAPITest):
    def setup_dataset(self):
        self.store_id = self.session.execute(
            sa.insert(m.Store)
            .values({m.Store.name: "bookstore"})
            .returning(m.Store.id)
        ).scalar()
        self.book_id = self.session.execute(
            sa.insert(m.Book)
            .values({m.Book.title: "new", m.Book.store_id: self.store_id})
            .returning(m.Book.id)
        ).scalar()

    def setUp(self):
        super().setUp()
        self.app = api
        self.setup_dataset()

    @patch("awokado.resource.Transaction", autospec=True)
    def test_create(self, session_patch):
        self.patch_session(session_patch)
        payload = {"store": [{"name": "bestbooks"}]}
        api_response = self.simulate_post("/v1/store", json=payload)
        self.assertEqual(api_response.status, "200 OK", api_response.text)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_bad_schema(self, session_patch):
        self.patch_session(session_patch)
        payload = {"bad_name_store": [{"name": "bestbooks"}]}
        api_response = self.simulate_post("/v1/store", json=payload)
        self.assertEqual(
            api_response.status, "400 Bad Request", api_response.text
        )
        self.assertIn("Invalid schema", api_response.text)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_update(self, session_patch):
        self.patch_session(session_patch)
        payload = {"store": [{"id": self.store_id, "name": "new name"}]}

        api_response = self.simulate_patch("/v1/store/", json=payload)
        self.assertEqual(
            api_response.status, "405 Method Not Allowed", api_response.text
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_delete(self, session_patch):
        self.patch_session(session_patch)

        api_response = self.simulate_delete(f"/v1/store/{self.store_id}")
        self.assertEqual(
            api_response.status, "405 Method Not Allowed", api_response.text
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_notnullablelist_field(self, session_patch):
        self.patch_session(session_patch)

        api_response = self.simulate_get(f"/v1/store/{self.store_id}")
        self.assertEqual(api_response.status, "200 OK", api_response.text)

        payload = api_response.json["store"][0]
        self.assertEqual(payload["book_ids"], [self.book_id])

        payload = {"store": {"name": "bestbooks"}}
        api_response = self.simulate_post("/v1/store", json=payload)
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        store_id = api_response.json["store"][0]["id"]

        api_response = self.simulate_get(f"/v1/store/{store_id}")
        self.assertEqual(api_response.status, "200 OK", api_response.text)

        payload = api_response.json["store"][0]
        self.assertEqual(payload["book_ids"], [])
