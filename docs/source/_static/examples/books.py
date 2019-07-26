import falcon
import sqlalchemy as sa
from awokado.consts import CREATE, READ, UPDATE, DELETE
from awokado.db import DATABASE_URL
from awokado.middleware import HttpMiddleware
from awokado.resource import BaseResource
from marshmallow import fields
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Book(Base):
    __tablename__ = "books"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    description = sa.Column(sa.Text)
    title = sa.Column(sa.Text)


e = create_engine(DATABASE_URL)
Base.metadata.create_all(e)


class BookResource(BaseResource):
    class Meta:
        model = Book
        name = "book"
        methods = (CREATE, READ, UPDATE, DELETE)
        auth = None

    id = fields.Int(model_field=Book.id)
    title = fields.String(model_field=Book.title, required=True)
    description = fields.String(model_field=Book.description)


api = falcon.API(middleware=[HttpMiddleware()])

api.add_route("/v1/book/", BookResource())
api.add_route("/v1/book/{resource_id}", BookResource())
