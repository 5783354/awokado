import sqlalchemy as sa

from tests.test_app.models.base import Model

M2M_Book_Tag = sa.Table(
    "m2m_books_tags",
    Model.metadata,
    sa.Column("book_id", sa.Integer, nullable=False, index=True),
    sa.Column("tag_id", sa.Integer, nullable=False, index=True),
    sa.ForeignKeyConstraint(
        ("book_id",), ["books.id"], onupdate="CASCADE", ondelete="CASCADE"
    ),
    sa.ForeignKeyConstraint(
        ("tag_id",), ["tags.id"], onupdate="CASCADE", ondelete="CASCADE"
    ),
)
