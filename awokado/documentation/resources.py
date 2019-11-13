from decimal import Decimal
from typing import Union, Sequence

import falcon
import pyaml
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from awokado.documentation.generate import APIDocs
from awokado.documentation.routes import collect_routes


class SwaggerResource:
    def __init__(
        self,
        api: falcon.API,
        project_name: str,
        api_hosts: Union[str, Sequence[str]] = "/",
        api_version: str = "1.0.0",
        description: str = "",
    ):
        """Resource for '/swagger.yaml'

        :param api: Your falcon.API instance
        :param project_name: Title for your documentation
        :param api_hosts: List of places where api can be
        :param api_version: String with number of version of you project
        :param description: Absolute path to template with description of your project
        """
        public_resources = set()
        spec = APISpec(
            title=project_name,
            version=api_version,
            openapi_version="3.0.2",
            info={"description": description},
            plugins=[MarshmallowPlugin()],
        )
        routes = collect_routes(api)

        for resource in {type(route.resource) for route in routes}:
            if resource.Meta.skip_doc:
                continue

            if resource.Meta.auth:
                public_resources.add(resource)

            spec.components.schema(resource.Meta.name, schema=resource)

        models_definition = spec.to_dict()
        docs = APIDocs(
            routes, models_definition, api_hosts, frozenset(public_resources)
        )
        docs_data = docs.run()

        pyaml.add_representer(
            Decimal,
            lambda dumper, data: dumper.represent_scalar(
                "tag:yaml.org,2002:str", str(data)
            ),
        )

        self.data = pyaml.dump(docs_data, safe=True)

    def on_get(
        self, req: falcon.Request, resp: falcon.Response, resource_id=None
    ):
        resp.body = self.data
        resp.content_type = falcon.MEDIA_YAML


class SwaggerUIResource:
    def __init__(
        self,
        openapi_url: str,
        *,
        title: str = "API Documentation",
        swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
        swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
        swagger_favicon_url: str = "https://awokado.readthedocs.io/en/latest/_static/avocado.png",
    ):
        self.html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
            <link rel="shortcut icon" href="{swagger_favicon_url}">
            <title>{title}</title>
            </head>
            <body>
            <div id="swagger-ui">
            </div>
            <script src="{swagger_js_url}"></script>
            <!-- `SwaggerUIBundle` is now available on the page -->
            <script>
            const ui = SwaggerUIBundle({{
                url: '{openapi_url}',
                dom_id: '#swagger-ui',
                presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true
            }})
            </script>
            </body>
            </html>
        """.strip()

    def on_get(
        self, req: falcon.Request, resp: falcon.Response, resource_id=None
    ):
        resp.body = self.html
        resp.content_type = falcon.MEDIA_HTML
        resp.status = falcon.HTTP_200


class RedocViewResource:
    def __init__(
        self,
        openapi_url: str,
        *,
        title: str = "API Documentation",
        redoc_js_url: str = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url: str = "https://awokado.readthedocs.io/en/latest/_static/avocado.png",
        with_google_fonts: bool = True,
    ):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <title>{title}</title>
        <!-- needed for adaptive design -->
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        """
        if with_google_fonts:
            html += """
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        """
        html += f"""
        <link rel="shortcut icon" href="{redoc_favicon_url}">
        <!--
        ReDoc doesn't change outer page styles
        -->
        <style>
          body {{
            margin: 0;
            padding: 0;
          }}
        </style>
        </head>
        <body>
        <redoc spec-url="{openapi_url}"></redoc>
        <script src="{redoc_js_url}"> </script>
        </body>
        </html>
        """.strip()
        self.html = html

    def on_get(
        self, req: falcon.Request, resp: falcon.Response, resource_id=None
    ):
        resp.body = self.html
        resp.content_type = falcon.MEDIA_HTML
        resp.status = falcon.HTTP_200
