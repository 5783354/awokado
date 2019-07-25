Quickstart
**********

`Install <installation.html>`_ awokado before it's too late.

`Falcon <https://github.com/falconry/falcon>`_ , `Marshmallow <https://github.com/marshmallow-code/marshmallow/>`_ and `SQLAlchemy Core <https://docs.sqlalchemy.org/en/13/core/>`_ is also needed.


Simple example
------------------

Awokado based on Falcon, so we use REST architectural style. That means we're talking about resources.
Resources are simply all the things in your API or application that can be accessed by a URL.

Resources are represented as classes inherited from awocado BaseResource,
that gives an opportunity to use get, create, delete, update methods.

In class Meta we declare different resource's options:
    * name - used for two resources connection by relation
    * madel - represents sqlalchemy model
    * methods - tuple of methods you want to use
    * disable_totals - set false, if you don't need to know returning objects amount in read-requests
    * auth - awokado BaseAuth object for embedding authentication logic
    * select_from - provide data source here if your resource use another's model fields(for example sa.outerjoin(FirstModel, SecondModel, FirstModel.id == SecondModel.first_model_id))
    * skip_doc - set true if you don't need to add resource to documentation


.. code-block:: python
   :linenos:

    from marshmallow import fields

    import models as m
    from awokado.consts import CREATE, READ, UPDATE, DELETE
    from awokado.resource import BaseResource


    class BookResource(BaseResource):
        class Meta:
            model = m.Book
            name = "book"
            methods = (CREATE, READ, UPDATE, DELETE)
            auth = None

        id = fields.Int(model_field=m.Book.id)
        title = fields.String(model_field=m.Book.title, required=True)
        description = fields.String(model_field=m.Book.description)


In options in Meta class we pointed model that connected with resource:

.. code-block:: python
   :linenos:

    import sqlalchemy as sa
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()


    class Book(Base):
        __tablename__ = "books"

        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
        description = sa.Column(sa.Text)
        title = sa.Column(sa.Text)

Use sqlalchemy declarative_base for tables to be created after connecting to db:

.. code-block:: python
   :linenos:

    from sqlalchemy import create_engine

    from awokado.db import (
        DATABASE_PASSWORD,
        DATABASE_HOST,
        DATABASE_USER,
        DATABASE_PORT,
        DATABASE_DB,
        DATABASE_URL,
    )
    from quickstart.models import Base

    DATABASE_URL_MAIN = "postgresql://{}:{}@{}:{}".format(
        DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT
    )

    e = create_engine(DATABASE_URL_MAIN)
    conn = e.connect()
    conn.execute("commit")
    conn.execute(f"drop database if exists {DATABASE_DB}")
    conn.execute("commit")
    conn.execute(f"create database {DATABASE_DB}")
    conn.execute("commit")
    conn.close()

    e = create_engine(DATABASE_URL)
    Base.metadata.create_all(e)

Add routes, so resources can handle requests:

.. code-block:: python
   :linenos:

    import falcon
    from resources.book import BookResource
    from awokado.middleware import HttpMiddleware

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

   curl localhost:8000/v1/book

   curl localhost:8000/v1/book --data-binary '{"book":{"title":"some_title","description":"some_description"}}' --compressed -v



