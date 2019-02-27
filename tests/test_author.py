from unittest.mock import patch

import sqlalchemy as sa

from tests.base import BaseAPITest
from .test_app import models as m
from .test_app.routes import api


class AuthorTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.app = api

    @patch("awokado.resource.Transaction", autospec=True)
    def test_create(self, session_patch):
        self.patch_session(session_patch)

        payload = {"author": {"name": "Steven King"}}

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

        author_id = self.session.execute(
            sa.insert(m.Author)
            .values({m.Author.name: "Steven"})
            .returning(m.Author.id)
        ).scalar()

        payload = {"author": [{"id": author_id, "name": "Steven King"}]}

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

        author_id = self.session.execute(
            sa.insert(m.Author)
            .values({m.Author.name: "Steven"})
            .returning(m.Author.id)
        ).scalar()

        api_response = self.simulate_delete(f"/v1/author/{author_id}")
        self.assertEqual(api_response.status, "200 OK", api_response.json)

        self.assertDictEqual(api_response.json, dict())
