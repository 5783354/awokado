from collections import OrderedDict
from decimal import Decimal

import falcon
import pyaml
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.ext.marshmallow.openapi import DEFAULT_FIELD_MAPPING

from awokado import custom_fields
from awokado.consts import BULK_UPDATE
from awokado.documentation.readme import get_readme
from awokado.documentation.routes import collect_routes
from awokado.documentation.utils import parse_doc_string
from awokado.resource import BaseResource
from awokado.utils import log

DEFAULT_FIELD_MAPPING.update(
    {
        custom_fields.ToOne: ("integer", None),
        custom_fields.ToMany: ("array", None),
        custom_fields.Choice: ("string", "string"),
    }
)

INNER_METHOD_MAP = {
    "patch": "update",
    "post": "create",
    "get": "on_get",  # not taking here
    "delete": "delete",
}


class APIDocs(object):
    def __init__(
        self,
        routes: list,
        models: dict,
        host,
        public_resources: frozenset = frozenset(),
    ):
        self.doc = models
        self.routes = routes
        self.host = host
        self.public_resources = public_resources

    def collect_path_info(self, r):
        result = {}
        resource_ext = r.route.split("/")[2]
        resource_name = resource_ext.replace("-", "_")
        route_method = r.method_name.lower()
        is_patch = route_method == "patch"
        is_post = route_method == "post"
        is_bulk = False
        route_w_id = "resource_id" in r.route

        if is_patch:
            is_bulk = BULK_UPDATE in r.resource.Meta.methods and not route_w_id
        if not route_w_id and is_patch and not is_bulk:
            log.info(
                f"skip bulk patch with resource id "
                f"{r.route}:{resource_name}:{route_method}"
            )
            return None, None

        if route_w_id and is_post:
            log.info(
                f"skip post with resource id "
                f"{r.route}:{resource_name}:{route_method}"
            )
            return None, None

        path_info = self.get_common_info(r, resource_name)
        path_info[r.route][r.method_name]["parameters"] = self.get_parameters(
            route_method, route_w_id, resource_name
        )

        if is_patch or is_post:
            rb = OrderedDict(
                [
                    ("required", True),
                    (
                        "content",
                        {
                            "application/json": {
                                "schema": {
                                    "$ref": (
                                        "#/components/schemas/" + resource_name
                                    )
                                }
                            }
                        },
                    ),
                ]
            )
            path_info[r.route][r.method_name]["requestBody"] = rb

        if resource_name not in self.public_resources:
            security = path_info[r.route][r.method_name]["security"] = []
            security.append({"bearerAuth": []})
        if isinstance(result.get(r.route), dict):
            result[r.route].update(path_info[r.route])
        else:
            result.update(path_info)
        return r.route, result[r.route]

    def get_common_info(self, r, name):
        inner_method = INNER_METHOD_MAP[r.method_name.lower()]
        method_doc_str = getattr(r.resource, inner_method).__doc__
        if not method_doc_str:
            method_doc_str = r.method.__doc__

        summary, description = parse_doc_string(method_doc_str)
        if description:
            description = description.replace("---", "")
        path_info = {
            r.route: {
                r.method_name: {
                    "summary": summary,
                    "description": description,
                    "responses": {
                        200: {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": ("#/components/schemas/" + name)
                                    }
                                }
                            },
                        }
                    },
                }
            }
        }
        return path_info

    def get_parameters(self, route_method, route_with_id, resource_name):
        parameters = []
        if route_with_id:
            p = OrderedDict(
                [
                    ("name", "resource_id"),
                    ("in", "path"),
                    ("description", "ID of resource"),
                    ("required", True),
                    (
                        "schema",
                        OrderedDict([("type", "integer"), ("format", "int64")]),
                    ),
                ]
            )
            parameters.append(p)
        else:
            if route_method == "get":
                params_description = (
                    ("limit", "The numbers of items to return", "integer"),
                    (
                        "offset",
                        "The number of items to skip before "
                        "starting to collect the result set",
                        "integer",
                    ),
                    (
                        "sort",
                        "Sorting fields. Use '-' before field name "
                        "to use DESC sorting example: full_name,-birth_date",
                        "string",
                    ),
                )
                for name, description, q_type in params_description:
                    p = OrderedDict(
                        [
                            ("name", f"{name}"),
                            ("in", "query"),
                            ("description", f"{description}"),
                            ("schema", {"type": f"{q_type}"}),
                        ]
                    )
                    parameters.append(p)

        return parameters

    def set_servers(self):
        self.doc["servers"] = [{"url": self.host}]

    def set_components(self):
        if "components" in self.doc:
            self.doc["components"]["securitySchemes"] = {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        else:
            self.doc["components"] = {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                }
            }

    def run(self):
        for r in self.routes:
            route_key, route_result = self.collect_path_info(r)

            if not route_result:
                continue

            if route_key not in self.doc["paths"]:
                self.doc["paths"][route_key] = route_result
            else:
                self.doc["paths"][route_key].update(route_result)

        self.set_components()
        self.set_servers()
        return self.doc


def decimal_presenter(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


def generate_documentation(
    api: falcon.API,
    api_host: str,
    project_name: str,
    output_dir: str,
    api_version: str = "1.0.0",
    template_absolute_path: str = None,
):
    public_resources = set()
    spec = APISpec(
        title=project_name,
        version=api_version,
        openapi_version="3.0.2",
        info=dict(description=get_readme(template_absolute_path)),
        plugins=[MarshmallowPlugin()],
    )

    for resource_name, resource in BaseResource.RESOURCES.items():
        if resource.Meta.auth is None:
            public_resources.add(resource_name)

        if hasattr(resource.Meta, "skip_doc") and resource.Meta.skip_doc:
            continue

        spec.components.schema(resource_name, schema=resource)

    routes = collect_routes(api)
    models_definition = spec.to_dict()
    d = APIDocs(
        routes, models_definition, api_host, frozenset(public_resources)
    )
    data = d.run()

    pyaml.add_representer(Decimal, decimal_presenter)

    output_dir = output_dir.rstrip("/")

    with open(f"{output_dir}/swagger.yaml", "w") as f:
        result = pyaml.dump(data, safe=True)
        f.write(result)
