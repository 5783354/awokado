import json
from unittest.mock import patch

import sqlalchemy as sa

from awokado.response import Response
from tests.base import BaseAPITest
from tests.test_app import models as m
from tests.test_app.routes import api


class ReadTest(BaseAPITest):
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

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read_by_id(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get(f"/v1/book/{self.book1_id}")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["book"]), 1)
        self.assertEqual(resp.json["book"][0]["id"], self.book1_id)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read_empty_list(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get(f"/v1/author/")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertDictEqual(
            resp.json,
            {
                Response.PAYLOAD_KEYWORD: {"author": []},
                Response.META_KEYWORD: {Response.TOTAL_KEYWORD: 0},
            },
        )

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get(f"/v1/book")

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 3)
        self.assertEqual(resp.json["meta"]["total"], 3)

        resp = self.simulate_get(
            f"/v1/book", query_string="limit=1&offset=1&sort=title"
        )

        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(len(resp.json["payload"]["book"]), 1)
        self.assertEqual(resp.json["meta"]["total"], 3)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read_wrong_resource(self, session_patch):
        self.patch_session(session_patch)

        resp = self.simulate_get(f"/v1/BADbook")
        self.assertEqual(resp.status, "404 Not Found", resp.text)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_read_by_wrong_id(self, session_patch):
        self.patch_session(session_patch)
        resp = self.simulate_get(f"/v1/book/42423423")
        # TODO: change to 404 Not Found
        self.assertEqual(resp.status, "400 Bad Request", resp.text)
        self.assertEqual(resp.json["detail"], "Object Not Found")

    @patch("awokado.resource.Transaction", autospec=True)
    def test_disable_total(self, session_patch):
        self.patch_session(session_patch)
        self.create_tag("Fantastic")
        self.create_tag("Fantastic 2")
        self.create_tag("Fantastic 3")
        tags = self.session.execute(
            sa.select([sa.func.count(m.Tag.id)])
        ).scalar()
        self.assertTrue(tags == 3)

        resp = self.simulate_get("/v1/tag")
        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(
            len(resp.json["payload"]["tag"]), 3, json.dumps(resp.json, indent=4)
        )
        self.assertEqual(resp.json["meta"], None, resp.json)

    @patch("awokado.resource.Transaction", autospec=True)
    def test_join_list(self, session_patch):
        self.patch_session(session_patch)
        tag1_id = self.create_tag("Fantastic")
        tag2_id = self.create_tag("Science")
        tag3_id = self.create_tag("Leisure")
        unused_tag = self.create_tag("XXX")

        self.session.execute(
            sa.insert(m.M2M_Book_Tag).values(
                [
                    {
                        m.M2M_Book_Tag.c.book_id: self.book1_id,
                        m.M2M_Book_Tag.c.tag_id: tag1_id,
                    },
                    {
                        m.M2M_Book_Tag.c.book_id: self.book1_id,
                        m.M2M_Book_Tag.c.tag_id: tag2_id,
                    },
                    {
                        m.M2M_Book_Tag.c.book_id: self.book2_id,
                        m.M2M_Book_Tag.c.tag_id: tag2_id,
                    },
                    {
                        m.M2M_Book_Tag.c.book_id: self.book2_id,
                        m.M2M_Book_Tag.c.tag_id: tag3_id,
                    },
                ]
            )
        )
        resp = self.simulate_get("/v1/tag", query_string="sort=name")
        self.assertEqual(resp.status, "200 OK", resp.text)
        self.assertEqual(
            len(resp.json["payload"]["tag"]), 4, json.dumps(resp.json, indent=4)
        )
        self.assertEqual(
            set(resp.json["payload"]["tag"][2]["book_titles"]),
            {"first", "second"},
            json.dumps(resp.json, indent=4),
        )
        self.assertEqual(
            set(resp.json["payload"]["tag"][0]["book_titles"]),
            {"first"},
            json.dumps(resp.json, indent=4),
        )
        self.assertEqual(
            resp.json["payload"]["tag"][3]["book_titles"],
            [],
            json.dumps(resp.json, indent=4),
        )
