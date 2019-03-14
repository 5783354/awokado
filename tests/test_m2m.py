from unittest.mock import patch

import sqlalchemy as sa
from falcon import status_codes as status

from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class M2MTest(BaseAPITest):
    def setup_dataset(self):
        self.store_id = self.session.execute(
            sa.insert(m.Store)
            .values({m.Store.name: "bookstore"})
            .returning(m.Store.id)
        ).scalar()
        self.tag1_id = self.create_tag("Fantastic")
        self.tag2_id = self.create_tag("Science")
        self.tag3_id = self.create_tag("Leisure")
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
        self.session.execute(
            sa.insert(m.M2M_Book_Tag).values(
                [
                    {
                        m.M2M_Book_Tag.c.book_id: self.book1_id,
                        m.M2M_Book_Tag.c.tag_id: self.tag1_id,
                    },
                    {
                        m.M2M_Book_Tag.c.book_id: self.book1_id,
                        m.M2M_Book_Tag.c.tag_id: self.tag2_id,
                    },
                    {
                        m.M2M_Book_Tag.c.book_id: self.book2_id,
                        m.M2M_Book_Tag.c.tag_id: self.tag2_id,
                    },
                    {
                        m.M2M_Book_Tag.c.book_id: self.book2_id,
                        m.M2M_Book_Tag.c.tag_id: self.tag3_id,
                    },
                ]
            )
        )

    def setUp(self):
        super().setUp()
        self.app = api
        self.setup_dataset()

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read_include(self, session_patch):
        self.patch_session(session_patch)
        api_response = self.simulate_get(
            f"/v1/book/{self.book1_id}", query_string="include=tags"
        )
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        self.assertEqual(
            api_response.json["book"][0],
            {
                "id": self.book1_id,
                "tags": [self.tag1_id, self.tag2_id],
                "description": None,
                "author": None,
                "store": self.store_id,
                "title": "first",
            },
        )
        self.assertEqual(
            api_response.json["tag"],
            [
                {"name": "Fantastic", "id": self.tag1_id},
                {"name": "Science", "id": self.tag2_id},
            ],
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_create(self, session_patch):
        self.patch_session(session_patch)
        author_id = self.create_author("Steven King")
        payload = {
            "book": {
                "title": "The Dead Zone",
                "author": author_id,
                "tags": [self.tag1_id, self.tag2_id],
            }
        }

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
                "description": None,
                "store": None,
                "tags": [self.tag1_id, self.tag2_id],
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_update(self, session_patch):
        self.patch_session(session_patch)

        payload = {
            "book": [
                {
                    "id": self.book1_id,
                    "tags": [self.tag1_id, self.tag2_id, self.tag3_id],
                }
            ]
        }

        api_response = self.simulate_patch("/v1/book/", json=payload)
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        self.assertDictEqual(
            api_response.json["payload"]["book"][0],
            {
                "id": self.book1_id,
                "title": "first",
                "author": None,
                "description": None,
                "store": self.store_id,
                "tags": [self.tag1_id, self.tag2_id, self.tag3_id],
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_create_auto_save_m2m(self, session_patch):
        self.patch_session(session_patch)
        tags = self.session.execute(
            sa.insert(m.Tag)
            .values([{"name": "#testtag0001"}, {"name": "#testtag0002"}])
            .returning(m.Tag.id)
        ).fetchall()

        book_data = {
            "book": {
                "title": "test cookbook",
                "description": "some description",
                "tags": [tag.id for tag in tags],
            }
        }
        api_response = self.simulate_post("/v1/book", json=book_data)
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        instance_id = api_response.json.get("book")[0].get("id")
        book_tags = self.session.execute(
            sa.select([m.Tag.id, m.M2M_Book_Tag.c.book_id])
            .select_from(
                sa.join(
                    m.Tag, m.M2M_Book_Tag, m.Tag.id == m.M2M_Book_Tag.c.tag_id
                )
            )
            .where(m.M2M_Book_Tag.c.book_id == instance_id)
        ).fetchall()
        expected_result = {item.id for item in tags}
        actual_result = {item.id for item in book_tags}
        self.assertEqual(expected_result, actual_result)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_update_auto_save_m2m(self, session_patch):
        self.patch_session(session_patch)
        tags = self.session.execute(
            sa.insert(m.Tag)
            .values([{"name": "#testtag0001"}, {"name": "#testtag0002"}])
            .returning(m.Tag.id)
        ).fetchall()

        other_tags = self.session.execute(
            sa.insert(m.Tag)
            .values([{"name": "#testtag0003"}, {"name": "#testtag0004"}])
            .returning(m.Tag.id)
        ).fetchall()

        book = self.session.execute(
            sa.insert(m.Book)
            .values(
                {"title": "test cookbook", "description": "some description"}
            )
            .returning(m.Book.id)
        ).fetchone()

        self.session.execute(
            sa.insert(m.M2M_Book_Tag).values(
                [
                    {
                        m.M2M_Book_Tag.c.tag_id: tag.id,
                        m.M2M_Book_Tag.c.book_id: book.id,
                    }
                    for tag in tags
                ]
            )
        )

        book_data = {
            "book": [
                {
                    "id": book.id,
                    "title": "v2 test cookbook",
                    "description": "v2 some description",
                    "tags": [tag.id for tag in other_tags],
                }
            ]
        }

        api_response = self.simulate_patch("/v1/book/", json=book_data)
        self.assertEqual(api_response.status, "200 OK", api_response.text)
        instance_id = book.id
        book_tags = self.session.execute(
            sa.select([m.Tag.id, m.M2M_Book_Tag.c.book_id])
            .select_from(
                sa.join(
                    m.Tag, m.M2M_Book_Tag, m.Tag.id == m.M2M_Book_Tag.c.tag_id
                )
            )
            .where(m.M2M_Book_Tag.c.book_id == instance_id)
        ).fetchall()
        expected_result = {item.id for item in other_tags}
        actual_result = {item.id for item in book_tags}
        self.assertEqual(expected_result, actual_result)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_fail_create_within_auto_save_m2m(self, session_patch):
        self.patch_session(session_patch)
        tags = [1001, 1002, 1003]
        book_data = {
            "book": {
                "title": "test cookbook",
                "description": "some description",
                "tags": tags,
            }
        }
        api_response = self.simulate_post("/v1/book", json=book_data)
        self.assertEqual(
            api_response.status, status.HTTP_BAD_REQUEST, api_response.text
        )
        self.assertIn("detail", api_response.json)
        self.assertIn("tags", api_response.json.get("detail"))

    @patch("awokado.resource.Transaction", autospec=True)
    def test_fail_update_within_auto_save_m2m(self, session_patch):
        self.patch_session(session_patch)
        tags = [1001, 1002, 1003]
        book = self.session.execute(
            sa.insert(m.Book)
            .values(
                {"title": "test cookbook", "description": "some description"}
            )
            .returning(m.Book.id)
        ).fetchone()

        book_data = {
            "book": [
                {
                    "id": book.id,
                    "title": "v2 test cookbook",
                    "description": "v2 some description",
                    "tags": tags,
                }
            ]
        }
        api_response = self.simulate_patch("/v1/book", json=book_data)
        self.assertEqual(
            api_response.status, status.HTTP_BAD_REQUEST, api_response.text
        )
        self.assertIn("detail", api_response.json)
        self.assertIn("tags", api_response.json.get("detail"))
