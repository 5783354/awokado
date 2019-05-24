from unittest.mock import patch

import sqlalchemy as sa

from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class ExceptionTest(BaseAPITest):
    def setup_dataset(self):
        self.store_id = self.session.execute(
            sa.insert(m.Store)
            .values({m.Store.name: "bookstore"})
            .returning(m.Store.id)
        ).scalar()
        self.book1_id = self.session.execute(
            sa.insert(m.Book)
            .values(
                {
                    m.Book.title: "first",
                    m.Book.store_id: self.store_id,
                    m.Book.description: "description1",
                }
            )
            .returning(m.Book.id)
        ).scalar()
        self.book2_id = self.session.execute(
            sa.insert(m.Book)
            .values(
                {
                    m.Book.title: "second",
                    m.Book.store_id: self.store_id,
                    m.Book.description: "description2",
                }
            )
            .returning(m.Book.id)
        ).scalar()
        self.book3_id = self.session.execute(
            sa.insert(m.Book)
            .values(
                {
                    m.Book.title: "third",
                    m.Book.store_id: self.store_id,
                    m.Book.description: "description3",
                }
            )
            .returning(m.Book.id)
        ).scalar()

    def setUp(self):
        super().setUp()
        self.app = api
        self.setup_dataset()

    @patch("awokado.resource.Transaction", autospec=True)
    def test_wrong_route(self, session_patch):
        """
        404 Not Found. Route not found
        """
        self.patch_session(session_patch)
        resp = self.simulate_get("/v1/wrong-resource-name/")

        self.assertEqual(resp.status, "404 Not Found", resp.text)
        self.assertEqual(resp.status_code, 404, resp.text)
        self.assertEqual(
            resp.json["error"], "/v1/wrong-resource-name/ not found"
        )

        resp = self.simulate_get("/")

        self.assertEqual(resp.status, "404 Not Found", resp.text)
        self.assertEqual(resp.status_code, 404, resp.text)
        self.assertEqual(resp.json["error"], "/ not found")

    @patch("awokado.resource.Transaction", autospec=True)
    def test_bad_request_delete(self, session_patch):
        """
        400 Bad Request. Incorrect delete
        """
        self.patch_session(session_patch)
        resp = self.simulate_delete("/v1/book/")

        self.assertEqual(resp.status, "400 Bad Request", resp.text)
        self.assertEqual(resp.status_code, 400, resp.text)
        self.assertEqual(
            resp.json,
            {
                "status": "400 Bad Request",
                "title": "400 Bad Request",
                "code": "bad-request",
                "detail": (
                    "It should be a bulk delete (?ids=1,2,3) or delete"
                    " of a single resource (v1/resource/1)"
                ),
            },
        )

        query = f"ids={self.book1_id},{self.book2_id}"
        resp = self.simulate_delete(
            f"/v1/book/{self.book1_id}", query_string=query
        )

        self.assertEqual(resp.status, "400 Bad Request", resp.text)
        self.assertEqual(resp.status_code, 400, resp.text)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_Method_Not_Allowed(self, session_patch):
        """
        405 Method Not Allowed. Method doesn't exist in resource
        """
        self.patch_session(session_patch)
        resp = self.simulate_delete("/v1/store/1")

        self.assertEqual(resp.status, "405 Method Not Allowed", resp.text)
        self.assertEqual(resp.status_code, 405, resp.text)
        self.assertEqual(
            resp.json,
            {
                "status": "405 Method Not Allowed",
                "title": "405 Method Not Allowed",
                "code": "method-not-allowed",
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_bad_request(self, session_patch):
        """
        test resource fields validation
        """
        self.patch_session(session_patch)
        author_id = self.create_author("Steven King")

        payload = {"book": {"author": author_id}}

        api_response = self.simulate_post("/v1/book", json=payload)
        self.assertEqual(
            api_response.status, "400 Bad Request", api_response.text
        )
        self.assertEqual(api_response.status_code, 400, api_response.text)
        self.assertDictEqual(
            api_response.json,
            {
                "status": "400 Bad Request",
                "title": "400 Bad Request",
                "code": "bad-request",
                "detail": {"title": ["Missing data for required field."]},
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_internal_server_error(self, session_patch):
        """
        test 500 errors
        """
        self.patch_session(session_patch)

        api_response = self.simulate_post("/v1/healthcheck", json={})
        self.assertEqual(
            api_response.status, "500 Internal Server Error", api_response.text
        )
        self.assertEqual(api_response.status_code, 500, api_response.text)
        self.assertTrue(
            api_response.json["error"].startswith("Traceback"),
            api_response.text,
        )
