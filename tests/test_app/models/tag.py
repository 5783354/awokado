import sqlalchemy as sa

from .base import Model


class Tag(Model):
    __tablename__ = "tags"

    id = Model.PK()
    name = sa.Column(sa.Text)
