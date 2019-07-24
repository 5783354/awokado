Quickstart
**********

`Install <installation.html>`_ awokado before it's too late.


Simple example
------------------

Awokado based on Falcon, so we use REST architectural style. That means we're talking about resources.
Resources are simply all the things in your API or application that can be accessed by a URL.

.. code-block:: python
   :linenos:

   from typing import List

   import sqlalchemy as sa
   from marshmallow import fields

   import tests.test_app.models as m
   from awokado import custom_fields
   from awokado.consts import CREATE, READ, UPDATE
   from awokado.utils import ReadContext
   from awokado.resource import BaseResource

   # resources are represented as classes inherited from awocado BaseResource,
   # that gives an opportunity to use get, create, delete, update methods.
   class BookResource(BaseResource):
   # TODO: include some comments about marshmallow Schema class and aptions class Meta?
    class Meta:
        model = m.Book
        name = "book"
        methods = (CREATE, READ, UPDATE)
        auth = None

    id = fields.Int(model_field=m.Book.id)
    title = fields.String(model_field=m.Book.title, required=True)
    description = fields.String(model_field=m.Book.description)
    #custom_fields to represent relationships
    author = custom_fields.ToOne(
        resource="author", model_field=m.Book.author_id
    )

    def get_by_author_ids(
        self, session, ctx: ReadContext, field: sa.Column = None
    ):
        authors = sa.func.array_remove(
            sa.func.array_agg(m.Author.id), None
        ).label("authors")
        q = (
            sa.select(
                [
                    m.Book.id.label("id"),
                    m.Book.title.label("title"),
                    m.Book.description.label("description"),
                    m.Book.store_id.label("store"),
                    authors,
                ]
            )
            .select_from(
                sa.outerjoin(m.Book, m.Author, m.Author.id == m.Book.author_id)
            )
            .where(m.Book.author_id.in_(ctx.obj_ids))
            .group_by(m.Book.id)
        )
        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)
        return serialized_objs


   class AuthorResource(Resource):
    class Meta:
        model = m.Author
        name = "author"
        methods = (CREATE, READ, UPDATE)
        auth = None
        select_from = sa.outerjoin(
            m.Author, m.Book, m.Author.id == m.Book.author_id
        )

    id = fields.Int(model_field=m.Author.id)
    books = custom_fields.ToMany(
        fields.Int(),
        resource="book",
        model_field=m.Book.id,
        description="Authors Books",
    )
    books_count = fields.Int(
        dump_only=True, model_field=sa.func.count(m.Book.id)
    )
    name = fields.String(
        model_field=sa.func.concat(
            m.Author.first_name, " ", m.Author.last_name
        ),
        dump_only=True,
    )
    last_name = fields.String(
        model_field=m.Author.last_name, required=True, load_only=True
    )
    first_name = fields.String(
        model_field=m.Author.first_name, required=True, load_only=True
    )

    field_without_model_field = fields.String(load_only=True)

    def get_by_book_ids(
        self, session, ctx: ReadContext, field: sa.Column = None
    ):
        books_count = self.fields.get("books_count").metadata["model_field"]
        q = (
            sa.select(
                [
                    m.Author.id.label("id"),
                    self.fields.name.metadata["model_field"].label("name"),
                    books_count.label("books_count"),
                ]
            )
            .select_from(
                sa.outerjoin(m.Author, m.Book, m.Author.id == m.Book.author_id)
            )
            .where(m.Book.id.in_(ctx.obj_ids))
            .group_by(m.Author.id)
        )
        result = session.execute(q).fetchall()
        serialized_objs = self.dump(result, many=True)
        return serialized_objs


Add routes, so resources can handle requests

.. code-block:: python
   :linenos:

   app = falcon.API()
   api.add_route("/v1/author/", AuthorResource())
   api.add_route("/v1/author/{resource_id}", AuthorResource())
   api.add_route("/v1/book/", BookResource())
   api.add_route("/v1/book/{resource_id}", BookResource())


