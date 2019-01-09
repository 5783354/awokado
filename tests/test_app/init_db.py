from sqlalchemy import create_engine

from settings import (
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_DB,
)
from .models import Model

DATABASE_URL = "postgresql://{}:{}@{}:{}".format(
    DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT
)

e = create_engine(DATABASE_URL)
conn = e.connect()
conn.execute("commit")
conn.execute(f"drop database if exists {DATABASE_DB}")
conn.execute("commit")
conn.execute(f"create database {DATABASE_DB}")
conn.execute("commit")
conn.close()

e = create_engine(DATABASE_URL)
Model.metadata.create_all(e)
