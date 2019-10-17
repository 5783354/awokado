import sqlalchemy as sa
from sqlalchemy.pool import QueuePool

import clavis
from dynaconf import settings

from awokado.db_helper import Database


database = Database.from_config(settings)

DATABASE_URL = database.db_url
DATABASE_PASSWORD = database.DATABASE_PASSWORD
DATABASE_HOST = database.DATABASE_HOST
DATABASE_USER = database.DATABASE_USER
DATABASE_PORT = database.DATABASE_PORT
DATABASE_DB = database.DATABASE_DB

clavis.configure(DATABASE_URL)

persistent_engine = sa.create_engine(
    DATABASE_URL,
    encoding="utf-8",
    echo=settings.get("DB_ECHO", False),
    poolclass=QueuePool,
    pool_size=settings.get("DB_CONN_POOL_SIZE", 10),
    max_overflow=settings.get("DB_CONN_MAX_OVERFLOW", 5),
)
