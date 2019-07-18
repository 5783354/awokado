from unittest.mock import patch

import sqlalchemy as sa

from awokado.exceptions import IdFieldMissingError
from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class StoreStatsTest(BaseAPITest):
    def setup_dataset(self):
        self.store_id = self.session.execute(
            sa.insert(m.Store)
            .values({m.Store.name: "bookstore"})
            .returning(m.Store.id)
        ).scalar()
        self.book_id_1 = self.session.execute(
            sa.insert(m.Book)
            .values({m.Book.title: "new", m.Book.store_id: self.store_id})
            .returning(m.Book.id)
        ).scalar()
        self.book_id_2 = self.session.execute(
            sa.insert(m.Book)
            .values({m.Book.title: "new 2", m.Book.store_id: self.store_id})
            .returning(m.Book.id)
        ).scalar()

    def setUp(self):
        super().setUp()
        self.app = api
        self.setup_dataset()

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read(self, session_patch):
        self.patch_session(session_patch)

        api_response = self.simulate_get(f"/v1/store_stats/{self.store_id}")
        self.assertEqual(
            api_response.status, "400 Bad Request", api_response.text
        )
        self.assertEqual(
            api_response.json["detail"], IdFieldMissingError().details
        )

        api_response = self.simulate_get("/v1/store_stats/")
        self.assertEqual(
            api_response.status, "400 Bad Request", api_response.text
        )
        self.assertEqual(
            api_response.json["detail"], IdFieldMissingError().details
        )
