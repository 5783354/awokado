from unittest.mock import patch

import sqlalchemy as sa

from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class BookTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.app = api

    @patch("awokado.resource.Transaction", autospec=True)
    def test_create(self, session_patch):
        self.patch_session(session_patch)
        author_id = self.create_author("Steven King")

        payload = {"book": {"title": "The Dead Zone", "author": author_id}}

        api_response = self.simulate_post("/v1/book", json=payload)
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        book_id = api_response.json["book"][0]["id"]
        self.assertIsNotNone(book_id)
        self.assertDictEqual(
            api_response.json["book"][0],
            {
                "id": book_id,
                "title": "The Dead Zone",
                "author": author_id,
                "author_name": "Steven",
                "description": None,
                "store": None,
                "tags": [],
            },
        )

        payload = {"book": [{"title": "The Dead Zone", "author": author_id}]}

        api_response = self.simulate_post("/v1/book", json=payload)
        self.assertEqual(
            api_response.status, "405 Method Not Allowed", api_response.text
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_update(self, session_patch):
        self.patch_session(session_patch)
        author_id = self.create_author("Steven King")
        book_id = self.session.execute(
            sa.insert(m.Book)
            .values(
                {m.Book.title: "The Dead Zone", m.Book.author_id: author_id}
            )
            .returning(m.Book.id)
        ).scalar()

        payload = {
            "book": [
                {
                    "id": book_id,
                    "description": (
                        "Waking up from a five-year coma after "
                        "a car accident, former schoolteacher"
                    ),
                }
            ]
        }

        api_response = self.simulate_patch("/v1/book/", json=payload)
        self.assertEqual(api_response.status, "200 OK", api_response.json)

        self.assertDictEqual(
            api_response.json["payload"]["book"][0],
            {
                "id": book_id,
                "title": "The Dead Zone",
                "description": (
                    "Waking up from a five-year coma after "
                    "a car accident, former schoolteacher"
                ),
                "author": author_id,
                "author_name": "Steven",
                "store": None,
                "tags": [],
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_delete(self, session_patch):
        self.patch_session(session_patch)

        book_id = self.session.execute(
            sa.insert(m.Book)
            .values({m.Book.title: "The Dead Zone"})
            .returning(m.Book.id)
        ).scalar()

        api_response = self.simulate_delete(f"/v1/book/{book_id}")
        self.assertEqual(api_response.status, "200 OK", api_response.json)
        self.assertDictEqual(api_response.json, dict())

        author_id = self.create_author("Param Pam")
        payload = {"book": {"title": "Man", "author": author_id}}
        api_response = self.simulate_post("/v1/book", json=payload)
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        book_id1 = api_response.json["book"][0]["id"]

        payload = {"book": {"title": "Women", "author": author_id}}
        api_response = self.simulate_post("/v1/book", json=payload)
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        book_id2 = api_response.json["book"][0]["id"]

        query = f"ids={book_id1},{book_id2}"

        api_response = self.simulate_delete(
            f"/v1/book/{book_id1}", query_string=query
        )
        self.assertEqual(
            api_response.status, "400 Bad Request", api_response.json
        )

        api_response = self.simulate_delete("/v1/book", query_string=query)
        self.assertEqual(api_response.status, "200 OK", api_response.json)

        api_response = self.simulate_get("/v1/book")
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        self.assertEqual(len(api_response.json["payload"]["book"]), 0)
