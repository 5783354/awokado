import sqlalchemy as sa

from .base import Model


class Store(Model):
    __tablename__ = "stores"

    id = Model.PK()

    name = sa.Column(sa.Text)
