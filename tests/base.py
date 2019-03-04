import unittest
from unittest import mock

import sqlalchemy as sa
from clavis import Transaction
from falcon import testing
from sqlalchemy.orm import Session as _Session
from sqlalchemy.pool import NullPool

import awokado.db
from tests.test_app import models as m


class Session(_Session):
    def commit(self):
        self.flush()
        self.expire_all()

    def rollback(self):
        raise AssertionError("rollback is not supported within test run")


class DbTest(unittest.TestCase):
    longMessage = True  # XXX: assertXXX() message will be APPENDED to default

    def __setup_engine(self):
        self._engine = sa.create_engine(
            awokado.db.DATABASE_URL, poolclass=NullPool
        )

    def setUp(self):
        import warnings

        warnings.filterwarnings("error")

        super(DbTest, self).setUp()
        self.__setup_engine()
        self.__db_conn = self._engine.connect()

        try:
            self.__db_txn = self.__db_conn.begin()

            if not hasattr(self, "__session") or not self.__session:
                self.__session = Session(bind=self.__db_conn)

        except:
            self.__db_conn.close()
            raise

    def tearDown(self):
        try:
            try:
                self.__db_txn.rollback()
            finally:
                self.__db_conn.close()
        finally:
            super(DbTest, self).tearDown()

    @property
    def session(self):
        return self.__session


class BaseAPITest(testing.TestCase, DbTest):
    def patch_session(self, session_patch):
        class X:
            session = self.session

        mock_client = mock.MagicMock(spec=Transaction)
        mock_client.__enter__.return_value = X
        session_patch.return_value = mock_client

    def create_author(self, name):
        first_name, last_name = name.split()
        author_id = self.session.execute(
            sa.insert(m.Author)
            .values(
                {m.Author.first_name: first_name, m.Author.last_name: last_name}
            )
            .returning(m.Author.id)
        ).scalar()
        return author_id

    def create_tag(self, name):
        tag_id = self.session.execute(
            sa.insert(m.Tag).values({m.Tag.name: name}).returning(m.Tag.id)
        ).scalar()
        return tag_id
