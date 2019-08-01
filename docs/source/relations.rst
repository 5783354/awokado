Relations
*********

Here is a more complicated version of simple awokado usage.
Awokado provides you with the possibility to easily build relations between entities.



Let's take the Authors-Books one-to-many relation, for example.


Firstly, we need models:

.. code-block:: python
   :linenos:

   #models.py

   import sqlalchemy as sa
   from sqlalchemy.ext.declarative import declarative_base


   Base = declarative_base()


   class Book(BaseModel):
       __tablename__ = "books"

       id = Model.PK()
       author_id = sa.Column(
           sa.Integer,
           sa.ForeignKey("authors.id", onupdate="CASCADE", ondelete="SET NULL"),
           index=True,
       )

       description = sa.Column(sa.Text)
       title = sa.Column(sa.Text)

   class Author(BaseModel):
       __tablename__ = "authors"

       id = Model.PK()
       first_name = sa.Column(sa.Text, nullable=False)
       last_name = sa.Column(sa.Text, nullable=False)

   e = create_engine(DATABASE_URL)
   Base.metadata.create_all(e)


Secondly, we write resources for each entity connected with their models.


Bind Book to Author using the ToOne awokado custom_field. Resource argument
is the name field of Meta class in Author resource we're connecting to, model_field argument is the
field in Book model where Author unique identifier is stored.

.. code-block:: python
   :linenos:

   #resources.py

   import sqlalchemy as sa
   from marshmallow import fields

   import models as m
   from awokado import custom_fields
   from awokado.consts import CREATE, READ, UPDATE
   from awokado.utils import ReadContext
   from awokado.resource import BaseResource

   class BookResource(BaseResource):
    class Meta:
        model = m.Book
        name = "book"
        methods = (CREATE, READ, UPDATE)

    id = fields.Int(model_field=m.Book.id)
    title = fields.String(model_field=m.Book.title, required=True)
    description = fields.String(model_field=m.Book.description)
    author = custom_fields.ToOne(
        resource="author", model_field=m.Book.author_id
    )

The continuation of building the connection is in the Author resource.
Here we define another end of connection by the ToMany field.

.. code-block:: python
   :linenos:

   class AuthorResource(Resource):
    class Meta:
        model = m.Author
        name = "author"
        methods = (CREATE, READ, UPDATE)
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

So finally here are the functions where we add logic for getting connected entities.

.. code-block:: python
   :linenos:

    #BookResource

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


    #AuthorResource

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


Add routes, so resources can handle requests:

.. code-block:: python
   :linenos:

   app = falcon.API()
   api.add_route("/v1/author/", AuthorResource())
   api.add_route("/v1/author/{resource_id}", AuthorResource())
   api.add_route("/v1/book/", BookResource())
   api.add_route("/v1/book/{resource_id}", BookResource())


Test it using curl in terminal:

.. code-block::
   :linenos:

   curl localhost:8000/v1/book?include=user | python -m json.tool

   curl localhost:8000/v1/user?include=book | python -m json.tool

