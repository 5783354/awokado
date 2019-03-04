import os
from unittest.mock import patch

from awokado.documentation import generate_documentation
from tests.base import BaseAPITest
from tests.test_app.routes import api


class DocumentationTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.app = api

    def tearDown(self):
        os.remove(f"{os.getcwd()}/swagger.yaml")

    @patch("awokado.documentation.generate.get_readme", autospec=True)
    def test_create_documentation(self, patch_template_path):
        patch_template_path.return_value = "My description"
        generate_documentation(
            api=self.app,
            api_host="host",
            project_name="Example Documentation",
            template_absolute_path="path/to/template",
            output_dir=os.getcwd(),
        )
        with open(f"{os.getcwd()}/swagger.yaml", "r") as f:
            test_set = set()
            doc_list = f.readlines()
            for line in doc_list:
                line = line.strip(" ").strip("\n").strip(":")
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
            },
        )
