Quickstart
**********

`Install <installation.html>`_ awokado before it's too late.

Awokado uses `dynaconf <https://github.com/rochacbruno/dynaconf/>`_ for loading it settings.
So store them in settings.toml, for example:

.. code-block:: python
   :linenos:

    #settings.toml

    [default]
         DATABASE_PASSWORD='your_password'
         DATABASE_HOST='localhost'
         DATABASE_USER='your_user'
         DATABASE_PORT=5432
         DATABASE_DB='try_awokado'


Simple example
------------------

Awokado based on Falcon, so we use the REST architectural style. That means we're talking about resources.
Resources are simply all the things in your API or application that can be accessed by a URL.


First of all, we need to create a model to further be connected with a resource.

This model will act as a link to a database entity.
Read more about it `here <https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/basic_use.html?highlight=declarative_base>`_.

At this point, the database should be already created.

.. code-block:: python
   :linenos:

    #books.py

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

Resources are represented as classes inherited from awocado BaseResource,
that gives an opportunity to use get, create, delete, update methods.

.. code-block:: python
   :linenos:

    class BookResource(BaseResource):
        class Meta:
            model = Book
            name = "book"
            methods = (CREATE, READ, UPDATE, DELETE)

        id = fields.Int(model_field=Book.id)
        title = fields.String(model_field=Book.title, required=True)
        description = fields.String(model_field=Book.description)


Add routes, so resources can handle requests:

.. code-block:: python
   :linenos:

    api = falcon.API(middleware=[HttpMiddleware()])

    api.add_route("/v1/book/", BookResource())
    api.add_route("/v1/book/{resource_id}", BookResource())

The final file version should look like `this one <https://gitlab.com/5783354/awokado/blob/generate_documentation/docs/source/_static/examples/books.py>`_.

Now we're ready to run the above example. You can use the uwsgi server.

.. code-block:: python
   :linenos:

    pip install uwsgi
    uwsgi --http :8000 --wsgi-file books.py --callable api

Test it using curl in another terminal:

.. code-block:: python
   :linenos:

    curl localhost:8000/v1/book --data-binary '{"book":{"title":"some_title","description":"some_description"}}' --compressed -v | python -m json.tool

    {
        "book": [
            {
                "description": "some_description",
                "id": 1,
                "title": "some_title"
            }
        ]
    }

   curl localhost:8000/v1/book | python -m json.tool

    {
        "meta": {
            "total": 1
        },
        "payload": {
            "book": [
                {
                    "description": "some_description",
                    "id": 1,
                    "title": "some_title"
                }
            ]
        }
    }





