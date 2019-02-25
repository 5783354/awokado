import sqlalchemy as sa
from sqlalchemy.pool import QueuePool

import clavis
from dynaconf import settings

DATABASE_PASSWORD = settings.DATABASE_PASSWORD
DATABASE_HOST = settings.DATABASE_HOST
DATABASE_USER = settings.DATABASE_USER
DATABASE_PORT = settings.DATABASE_PORT
DATABASE_DB = settings.DATABASE_DB

DATABASE_URL = (
    f"postgresql://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/"
    f"{DATABASE_DB}"
)

clavis.configure(DATABASE_URL)

persistent_engine = sa.create_engine(
    DATABASE_URL,
    encoding="utf-8",
    echo=settings.get("DB_ECHO", False),
    poolclass=QueuePool,
    pool_size=settings.get("DB_CONN_POOL_SIZE", 10),
    max_overflow=settings.get("DB_CONN_MAX_OVERFLOW", 5),
)
