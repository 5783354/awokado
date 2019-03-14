import sqlalchemy as sa

from .base import Model


class Book(Model):
    __tablename__ = "books"

    id = Model.PK()
    author_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("authors.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        unique=True,
    )

    description = sa.Column(sa.Text)
    store_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("stores.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    title = sa.Column(sa.Text)
