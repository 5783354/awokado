from unittest.mock import patch

from tests.base import BaseAPITest
from .test_app.routes import api


class AuthorTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.app = api

    @patch("awokado.resource.Transaction", autospec=True)
    def test_create(self, session_patch):
        self.patch_session(session_patch)

        payload = {"author": {"first_name": "Steven", "last_name": "King"}}

        api_response = self.simulate_post("/v1/author", json=payload)
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        id_ = api_response.json["author"][0]["id"]
        self.assertIsNotNone(id_)
        self.assertDictEqual(
            api_response.json["author"][0],
            {"id": id_, "name": "Steven King", "books_count": 0, "books": []},
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_update(self, session_patch):
        self.patch_session(session_patch)

        author_id = self.create_author("Steven X")

        payload = {
            "author": [
                {"id": author_id, "first_name": "Steven", "last_name": "King"}
            ]
        }

        api_response = self.simulate_patch("/v1/author/", json=payload)
        self.assertEqual(api_response.status, "200 OK", api_response.json)

        self.assertDictEqual(
            api_response.json["payload"]["author"][0],
            {
                "id": author_id,
                "name": "Steven King",
                "books_count": 0,
                "books": [],
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_delete(self, session_patch):
        self.patch_session(session_patch)

        author_id = self.create_author("Steven X")

        api_response = self.simulate_delete(f"/v1/author/{author_id}")
        self.assertEqual(api_response.status, "200 OK", api_response.json)

        self.assertDictEqual(api_response.json, dict())

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read(self, session_patch):
        self.patch_session(session_patch)

        author_id = self.create_author("Steven X")

        api_response = self.simulate_get("/v1/author/")
        self.assertEqual(api_response.status, "200 OK", api_response.json)

        self.assertDictEqual(
            api_response.json["payload"]["author"][0],
            {
                "id": author_id,
                "name": "Steven X",
                "books_count": 0,
                "books": [],
            },
        )
