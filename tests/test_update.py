import sqlalchemy as sa

from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class UpdateTest(BaseAPITest):
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

    def test_wrong_field_type_update(self):
        payload = {"book": [{"id": self.book1_id, "title": 123}]}

        api_response = self.simulate_patch("/v1/book/", json=payload)
        self.assertEqual(
            api_response.status, "400 Bad Request", api_response.json
        )
        self.assertEqual(
            api_response.json["detail"],
            {"0": {"title": ["Not a valid string."]}},
        )

        payload = {
            "book": [
                {"id": self.book1_id, "title": 123},
                {"id": self.book2_id, "title": 456},
            ]
        }

        api_response = self.simulate_patch("/v1/book/", json=payload)
        self.assertEqual(
            api_response.status, "400 Bad Request", api_response.json
        )

        self.assertDictEqual(
            api_response.json["detail"],
            {
                "0": {"title": ["Not a valid string."]},
                "1": {"title": ["Not a valid string."]},
            },
        )

    def test_wrong_ids_bulk_update(self):
        payload = {"book": [{"id": None, "title": 456}]}

        api_response = self.simulate_patch("/v1/book/", json=payload)
        self.assertEqual(
            api_response.status, "400 Bad Request", api_response.json
        )
        print(api_response.json)
        self.assertDictEqual(
            api_response.json["detail"],
            {
                "0": {
                    "id": ["Field may not be null."],
                    "title": ["Not a valid string."],
                }
            },
        )
