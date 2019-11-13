from typing import Dict, List, Union, FrozenSet, Type, Sequence

from awokado.consts import BULK_UPDATE, BULK_CREATE
from awokado.documentation.routes import Route
from awokado.documentation.utils import parse_doc_string
from awokado.resource import BaseResource
from awokado.utils import log

INNER_METHOD_MAP = {
    "patch": "update",
    "post": "create",
    "get": "on_get",  # not taking here
    "delete": "delete",
}


class APIDocs:
    def __init__(
        self,
        routes: list,
        models: dict,
        servers: Union[str, Sequence[str]] = "/",
        public_resources: FrozenSet[Type[BaseResource]] = frozenset(),
    ):
        self.doc = models
        self.routes = routes
        self.public_resources = public_resources
        self.servers = [servers] if isinstance(servers, str) else servers

    def collect_path_info(self, r: Route):
        resource_ext = r.uri.split("/")[2]
        resource_name = resource_ext.replace("-", "_")
        route_method = r.method_name.lower()
        is_patch = route_method == "patch"
        is_post = route_method == "post"
        is_bulk = False
        route_w_id = "{resource_id}" in r.uri

        if is_patch:
            is_bulk = BULK_UPDATE in r.resource.Meta.methods and not route_w_id

        if not route_w_id and is_patch and not is_bulk:
            log.info(
                f"skip bulk patch with resource id "
                f"{r.uri}:{resource_name}:{route_method}"
            )
            return None, None

        if route_w_id and is_post:
            log.info(
                f"skip post with resource id "
                f"{r.uri}:{resource_name}:{route_method}"
            )
            return None, None

        path_info = self.get_common_info(r, resource_name)
        path_info[r.method_name]["parameters"] = self.get_parameters(
            route_method, route_w_id
        )

        if is_patch or is_post:
            rb = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/" + resource_name
                        }
                    }
                },
            }
            path_info[r.method_name]["requestBody"] = rb

        if type(r.resource) not in self.public_resources:
            security: List[dict] = []
            path_info[r.method_name]["security"] = security
            security.append({"bearerAuth": []})
        return r.uri, path_info

    @staticmethod
    def get_common_info(r: Route, name: str):
        inner_method = INNER_METHOD_MAP[r.method_name.lower()]
        method_doc_str = getattr(r.resource, inner_method).__doc__
        if not method_doc_str:
            method_doc_str = r.method.__doc__

        summary, description = parse_doc_string(method_doc_str)

        if r.method_name == "post" and BULK_CREATE in r.resource.Meta.methods:
            summary += ". Supports bulk create"

        if description:
            description = description.replace("---", "")

        path_info = {
            r.method_name: {
                "tags": [r.uri.replace("{resource_id}", "")],
                "summary": summary,
                "description": description,
                "responses": {
                    200: {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/" + name
                                }
                            }
                        },
                    }
                },
            }
        }

        return path_info

    @staticmethod
    def get_parameters(route_method, route_with_id):
        parameters = []
        if route_with_id:
            parameters.append(
                {
                    "name": "resource_id",
                    "in": "path",
                    "description": "ID of resource",
                    "required": True,
                    "schema": {"type": "integer", "format": "int64"},
                }
            )
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
                    parameters.append(
                        {
                            "name": f"{name}",
                            "in": "query",
                            "description": f"{description}",
                            "schema": {"type": f"{q_type}"},
                        }
                    )

        return parameters

    def set_components(self):
        security_schemes = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
        if "components" in self.doc:
            self.doc["components"]["securitySchemes"] = security_schemes
        else:
            self.doc["components"] = {"securitySchemes": security_schemes}

    def run(self):
        for r in self.routes:
            route_key, route_result = self.collect_path_info(r)

            if not route_result:
                continue

            if route_key not in self.doc["paths"]:
                self.doc["paths"][route_key] = route_result
            else:
                self.doc["paths"][route_key].update(route_result)

        self.doc["servers"] = [{"url": server} for server in self.servers]

        self.set_components()

        return self.doc
