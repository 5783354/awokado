from contextlib import contextmanager
from dataclasses import dataclass
from logging import getLogger
from urllib.parse import urlparse

from sqlalchemy import create_engine, MetaData

log = getLogger("db_helper")


@dataclass
class Database:
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_DB: str
    DATABASE_PORT: str = "8123"

    @classmethod
    def from_url(cls, url: str):
        result = urlparse(url)

        data = {
            "DATABASE_USER": result.username,
            "DATABASE_PASSWORD": result.password,
            "DATABASE_DB": result.path[1:],
            "DATABASE_HOST": result.hostname,
        }

        if result.port:
            data["DATABASE_PORT"] = str(result.port)

        if result.scheme != "postgresql" or not all(data.values()):
            raise Exception(f"Invalid url: {url}")

        return cls(**data)

    @classmethod
    def from_config(cls, config):
        url = config.get("DATABASE_URL", None)

        db_params = {
            "DATABASE_PASSWORD": config.get("DATABASE_PASSWORD", None),
            "DATABASE_HOST": config.get("DATABASE_HOST", None),
            "DATABASE_USER": config.get("DATABASE_USER", None),
            "DATABASE_DB": config.get("DATABASE_DB", None),
        }

        port = config.get("DATABASE_PORT", None)
        if port:
            db_params["DATABASE_PORT"] = str(port)

        if any(db_params.values()):
            if url:
                raise Exception(
                    "Cannot specify DATABASE_URL and any of other database params"
                    " together! (Other database params are: DATABASE_PASSWORD,"
                    " DATABASE_HOST, DATABASE_USER, DATABASE_PORT, DATABASE_DB)"
                )
            return cls(**db_params)
        elif url:
            return cls.from_url(url)
        else:
            raise Exception(
                "Please, specify DATABASE_URL or database params "
                "(DATABASE_PASSWORD, DATABASE_HOST, DATABASE_USER, DATABASE_PORT, DATABASE_DB)"
            )

    @property
    def url(self) -> str:
        if self.DATABASE_PORT:
            host = f"{self.DATABASE_HOST}:{self.DATABASE_PORT}"
        else:
            host = f"{self.DATABASE_HOST}"

        return (
            f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{host}"
        )

    @property
    def db_url(self) -> str:
        return f"{self.url}/{self.DATABASE_DB}"

    @contextmanager
    def conn(self):
        e = create_engine(self.url)
        conn = e.connect()
        try:
            yield conn
        finally:
            conn.close()

    def drop(self):
        log.info(f"Drop database: {self.DATABASE_DB}")
        with self.conn() as conn:
            conn.execute("commit")
            conn.execute(f"drop database if exists {self.DATABASE_DB}")
            conn.execute("commit")

    def create(self):
        log.info(f"Create database: {self.DATABASE_DB}")
        with self.conn() as conn:
            conn.execute("commit")
            conn.execute(f"create database {self.DATABASE_DB}")
            conn.execute("commit")

    def recreate(self):
        self.drop()
        self.create()

    def create_models(self, md: MetaData):
        log.info(f"Create models: {self.DATABASE_DB}")
        e = create_engine(self.db_url)
        md.create_all(e)

    def __str__(self):
        return self.db_url
