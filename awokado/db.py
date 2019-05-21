import sqlalchemy as sa
from sqlalchemy.pool import QueuePool

import clavis
from dynaconf import settings

DATABASE_PASSWORD = settings.get("DATABASE_PASSWORD", None)
DATABASE_HOST = settings.get("DATABASE_HOST", None)
DATABASE_USER = settings.get("DATABASE_USER", None)
DATABASE_PORT = settings.get("DATABASE_PORT", None)
DATABASE_DB = settings.get("DATABASE_DB", None)

DATABASE_URL = settings.get("DATABASE_URL", None)

separated_db_params_flag = any(
    [
        DATABASE_PASSWORD,
        DATABASE_HOST,
        DATABASE_USER,
        DATABASE_PORT,
        DATABASE_DB,
    ]
)

if separated_db_params_flag:
    if DATABASE_URL:
        raise Exception(
            "Cannot specify DATABASE_URL and any of other database params"
            " together! (Other database params are: DATABASE_PASSWORD,"
            " DATABASE_HOST, DATABASE_USER, DATABASE_PORT, DATABASE_DB)"
        )

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
