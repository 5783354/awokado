from unittest.mock import patch

from tests.base import BaseAPITest
from .test_app.routes import api


class BotoClientMock:
    def __init__(self, *args, **kwargs):
        self.put_object_data = None

    def __call__(self, *args, **kwargs):
        return self

    def put_object(self, **kwargs):
        self.put_object_data = kwargs


class OpenMock:
    def __init__(self, *args, **kwargs):
        self.write_data = None
        self.key = None

    def __call__(self, key, *args, **kwargs):
        self.key = key
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def write(self, stats):
        self.write_data = stats


class ProfilingMiddlewareTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.app = api

    @patch(
        "awokado.middleware.settings"
        ".AWOKADO_ENABLE_UPLOAD_DEBUG_PROFILING_TO_S3",
        True,
    )
    @patch("awokado.resource.Transaction", autospec=True)
    def test_upload_profiling_info_to_s3(self, session_patch):
        self.patch_session(session_patch)

        author_id = self.create_author("Steven X")

        boto_patch = BotoClientMock()

        self.assertIsNone(boto_patch.put_object_data)

        with patch("awokado.middleware.boto3.client", boto_patch):
            api_response = self.simulate_get(
                "/v1/author/", query_string="profiling=true"
            )

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

        self.assertTrue("Body" in boto_patch.put_object_data)
        self.assertTrue("Bucket" in boto_patch.put_object_data)
        self.assertTrue("Key" in boto_patch.put_object_data)

    @patch(
        "awokado.middleware.settings"
        ".AWOKADO_ENABLE_UPLOAD_DEBUG_PROFILING_TO_S3",
        False,
    )
    @patch("awokado.resource.Transaction", autospec=True)
    def test_save_profiling_info_to_file(self, session_patch):
        self.patch_session(session_patch)

        author_id = self.create_author("Steven X")

        open_patch = OpenMock()

        self.assertIsNone(open_patch.write_data)

        with patch("awokado.middleware.open", open_patch):
            api_response = self.simulate_get(
                "/v1/author/", query_string="profiling=true"
            )

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

        self.assertTrue(open_patch.key.endswith(".prof"))
        self.assertIsNotNone(open_patch.write_data)
