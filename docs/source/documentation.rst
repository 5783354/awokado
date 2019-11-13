=============
Documentation
=============

Awokado allows to generate documentation for a project using swagger(3rd version).
To generate documentation you need to import add route with
`SwaggerResource <documentation.html#awokado.documentation.SwaggerResource>`_
after adding all other routes. Also, you can choose UI for swagger
(`SwaggerUI <https://swagger.io/tools/swagger-ui/>`_ or `Redoc <https://github.com/Redocly/redoc>`_)
by adding route for resoruces
`SwaggerUIResource <documentation.html#awokado.documentation.SwaggerUIResource>`_ or `RedocViewResource <documentation.html#awokado.documentation.RedocViewResource>`_


.. autoclass:: awokado.documentation.SwaggerResource()
   :members: __init__
   
.. autoclass:: awokado.documentation.SwaggerUIResource()
   :members:
   
.. autoclass:: awokado.documentation.RedocViewResource()
   :members:


Examples
--------

.. code-block:: python
   :linenos:

    from awokado.documentation import generate_documentation
    from dynaconf import settings
    from api.routes import api
    
    api.add_route(
        "/swagger.yaml", 
        ApiResource(
            api=api, 
            project_name="Example Documentation",
            api_host=('http://example.com/api', '/'),
            api_version="4.2.0",
            description="Some api description and introducing words"
        )
    )

    # You can choose one
    api.add_route("/doc", SwaggerUIResource("/swagger.yaml"))
    api.add_route("/redoc", RedocViewResource("/swagger.yaml"))
