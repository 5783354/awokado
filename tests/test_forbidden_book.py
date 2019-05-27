import sqlalchemy as sa
from unittest.mock import patch

from tests.base import BaseAPITest
from .test_app import models as m
from .test_app.resources.forbidden_book import ForbiddenBookResource
from .test_app.routes import api


class ForbiddenBookTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.app = api

    @patch("awokado.resource.Transaction", autospec=True)
    def test_create(self, session_patch):
        self.patch_session(session_patch)

        payload = {"forbidden_book": {"title": "None"}}

        api_response = self.simulate_post("/v1/forbidden_book", json=payload)

        self.assertEqual(
            api_response.status, "403 Forbidden", api_response.text
        )
        self.assertEqual(api_response.status_code, 403, api_response.text)
        self.assertEqual(
            api_response.json,
            {
                "status": "403 Forbidden",
                "title": "403 Forbidden",
                "code": "create-forbidden",
                "detail": "The creation of a resource forbidden",
            },
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
            "forbidden_book": [
                {
                    "id": book_id,
                    "description": (
                        "Waking up from a five-year coma after "
                        "a car accident, former schoolteacher"
                    ),
                }
            ]
        }

        api_response = self.simulate_patch("/v1/forbidden_book/", json=payload)

        self.assertEqual(
            api_response.status, "403 Forbidden", api_response.text
        )
        self.assertEqual(api_response.status_code, 403, api_response.text)
        self.assertEqual(
            api_response.json,
            {
                "status": "403 Forbidden",
                "title": "403 Forbidden",
                "code": "update-forbidden",
                "detail": "Change the resource is forbidden",
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_delete(self, session_patch):
        self.patch_session(session_patch)
        author_id = self.create_author("Steven King")
        book_id = self.session.execute(
            sa.insert(m.Book)
            .values(
                {m.Book.title: "The Dead Zone", m.Book.author_id: author_id}
            )
            .returning(m.Book.id)
        ).scalar()

        api_response = self.simulate_delete(f"/v1/forbidden_book/{book_id}")

        self.assertEqual(
            api_response.status, "403 Forbidden", api_response.text
        )
        self.assertEqual(api_response.status_code, 403, api_response.text)
        self.assertEqual(
            api_response.json,
            {
                "status": "403 Forbidden",
                "title": "403 Forbidden",
                "code": "delete-forbidden",
                "detail": "Delete the resource is forbidden",
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read(self, session_patch):
        self.patch_session(session_patch)
        author_id = self.create_author("Steven King")
        book_id = self.session.execute(
            sa.insert(m.Book)
            .values(
                {m.Book.title: "The Dead Zone", m.Book.author_id: author_id}
            )
            .returning(m.Book.id)
        ).scalar()

        api_response = self.simulate_get("/v1/forbidden_book/")

        self.assertEqual(
            api_response.status, "403 Forbidden", api_response.text
        )
        self.assertEqual(api_response.status_code, 403, api_response.text)
        self.assertEqual(
            api_response.json,
            {
                "status": "403 Forbidden",
                "title": "403 Forbidden",
                "code": "read-forbidden",
                "detail": "Read the resource is forbidden",
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_forbidden_auth_skip_exception(self, session_patch):
        self.assertFalse(
            ForbiddenBookResource.Meta.auth.can_create(
                None, None, None, skip_exc=True
            )
        )
        self.assertFalse(
            ForbiddenBookResource.Meta.auth.can_read(None, None, skip_exc=True)
        )
        self.assertFalse(
            ForbiddenBookResource.Meta.auth.can_update(
                None, None, None, skip_exc=True
            )
        )
        self.assertFalse(
            ForbiddenBookResource.Meta.auth.can_delete(
                None, None, None, skip_exc=True
            )
        )
