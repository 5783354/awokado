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
   from awokado.db import DATABASE_URL
   from sqlalchemy import create_engine
   from sqlalchemy.ext.declarative import declarative_base


   Base = declarative_base()


   class Book(BaseModel):
       __tablename__ = "books"

       id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
       author_id = sa.Column(
           sa.Integer,
           sa.ForeignKey("authors.id", onupdate="CASCADE", ondelete="SET NULL"),
           index=True,
       )

       description = sa.Column(sa.Text)
       title = sa.Column(sa.Text)

   class Author(BaseModel):
       __tablename__ = "authors"

       id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
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
   from awokado import custom_fields
   from awokado.consts import CREATE, READ, UPDATE
   from awokado.resource import BaseResource
   from awokado.utils import ReadContext
   from marshmallow import fields

   import models as m

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

So finally here are the methods where we add logic for getting connected entities.

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
                    self.fields.get("name")
                    .metadata["model_field"]
                    .label("name"),
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

.. code-block:: python
   :linenos:

      curl localhost:8000/v1/author --data-binary '{"author":{"last_name": "B","first_name": "Sier"}}' --compressed -v | python -m json.tool

      {
          "author": [
              {
                  "books": [],
                  "books_count": 0,
                  "id": 1,
                  "name": "Sier B"
              }
          ]
      }

      curl localhost:8000/v1/book --data-binary '{"book":{"title":"some_title","description":"some_description", "author":"1"}}' --compressed -v | python -m json.tool

      {
          "book": [
              {
                  "author": 1,
                  "description": "some_description",
                  "id": 1,
                  "title": "some_title"
              }
          ]
      }

      curl localhost:8000/v1/author?include=books | python -m json.tool

      {
          "meta": {
              "total": 1
          },
          "payload": {
              "author": [
                  {
                      "books": [
                          1
                      ],
                      "books_count": 1,
                      "id": 1,
                      "name": "Sier B"
                  }
              ],
              "book": [
                  {
                      "description": "some_description",
                      "id": 1,
                      "title": "some_title"
                  }
              ]
          }
      }

      curl localhost:8000/v1/book?include=author | python -m json.tool

      {
          "meta": {
              "total": 1
          },
          "payload": {
              "author": [
                  {
                      "books_count": 1,
                      "id": 1,
                      "name": "Sier B"
                  }
              ],
              "book": [
                  {
                      "author": 1,
                      "description": "some_description",
                      "id": 1,
                      "title": "some_title"
                  }
              ]
          }
      }



