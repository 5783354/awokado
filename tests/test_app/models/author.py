import sqlalchemy as sa

from .base import Model


class Author(Model):
    __tablename__ = "authors"

    id = Model.PK()
    name = sa.Column(sa.Text, nullable=False)
