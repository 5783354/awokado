Quickstart
**********

`Install <installation.html>`_ awokado before it's too late.


Simple example
------------------

Awokado based on Falcon, so we use REST architectural style. That means we're talking about resources.
Resources are simply all the things in your API or application that can be accessed by a URL.

Resources are represented as classes inherited from awocado BaseResource,
that gives an opportunity to use get, create, delete, update methods.


.. code-block:: python
   :linenos:

    #books.py

    import falcon
    import sqlalchemy as sa

    from sqlalchemy.ext.declarative import declarative_base
    from marshmallow import fields
    from awokado.consts import CREATE, READ, UPDATE, DELETE
    from awokado.resource import BaseResource
    from awokado.middleware import HttpMiddleware


    class BookResource(BaseResource):
        class Meta:
            model = Book
            name = "book"
            methods = (CREATE, READ, UPDATE, DELETE)
            auth = None

        id = fields.Int(model_field=m.Book.id)
        title = fields.String(model_field=m.Book.title, required=True)
        description = fields.String(model_field=m.Book.description)


In options in Meta class we pointed model that connected with resource:

.. code-block:: python
   :linenos:

    Base = declarative_base()


    class Book(Base):
        __tablename__ = "books"

        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
        description = sa.Column(sa.Text)
        title = sa.Column(sa.Text)

    Base.metadata.create_all(engine)


Add routes, so resources can handle requests:

.. code-block:: python
   :linenos:

    api = falcon.API(middleware=[HttpMiddleware()])

    api.add_route("/v1/book/", BookResource())
    api.add_route("/v1/book/{resource_id}", BookResource())

Now we're ready to run the above example. You can use uwsgi server.

.. code-block:: python
   :linenos:

    pip install uwsgi
    uwsgi --http :8000 --wsgi-file routes.py --callable api

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
            "total": 2
        },
        "payload": {
            "book": [
                {
                    "description": "some_description",
                    "id": 1,
                    "title": "some_title"
                },
                {
                    "description": "some_description1",
                    "id": 2,
                    "title": "some_title1"
                }
            ]
        }
    }





