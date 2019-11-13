from tests.base import BaseAPITest
from tests.test_app.routes import api


class DocumentationTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.app = api

    def test_create_documentation(self):
        response = self.simulate_get("/swagger.yaml")
        test_set = set()

        for line in response.text.split("\n"):
            line = line.strip(" ").strip(":")
            if "book" in line:
                test_set.add(line)

        self.assertSetEqual(
            test_set,
            {
                "/v1/book/",
                "$ref: '#/components/schemas/book'",
                "/v1/book/{resource_id}",
                "description: IDs of related resource (book). Authors Books",
                "description: IDs of related resource (book).",
                "books_count",
                "books",
                "book",
                "book_ids",
                "book_titles",
                "description: ID of related resource (store) Store selling book",
                "/v1/forbidden_book/",
                "$ref: '#/components/schemas/forbidden_book'",
                "/v1/forbidden_book/{resource_id}",
                "forbidden_book",
                "- /v1/forbidden_book/",
                "- /v1/book/",
            },
        )
