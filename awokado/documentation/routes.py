import functools
from dataclasses import dataclass
from typing import List, Callable
from falcon import API
from falcon.routing.compiled import CompiledRouterNode

if False:
    from awokado.resource import BaseResource


METHOD_MAPPING = {
    "POST": {"create", "bulk_create"},
    "GET": {"read"},
    "PATCH": {"update", "bulk_update"},
    "DELETE": {"delete"},
}


@dataclass
class Route:
    uri: str
    var_name: str
    method_name: str
    method: Callable
    resource: "BaseResource"


@dataclass
class RawRoute:
    uri: str
    var_name: str
    method_map: dict
    resource: "BaseResource"

    def __init__(self, route: CompiledRouterNode):
        self.uri = route.uri_template
        self.var_name = route.var_name
        self.method_map = route.method_map
        self.resource = route.resource


def get_routes(raw_routes: List[RawRoute]) -> List[Route]:
    routes = []

    for raw_route in raw_routes:
        if not raw_route.method_map:
            continue

        for method_name, method in raw_route.method_map.items():
            if raw_route.resource.Meta.skip_doc:
                continue

            valid_methods = METHOD_MAPPING.get(method_name, ())
            if not any(
                m in raw_route.resource.Meta.methods for m in valid_methods
            ):
                continue

            if not isinstance(method, functools.partial):
                routes.append(
                    Route(
                        uri=raw_route.uri,
                        var_name=raw_route.var_name,
                        method_name=method_name.lower(),
                        method=method,
                        resource=raw_route.resource,
                    )
                )

    return routes


def collect_routes(falcon_app: API) -> List[Route]:
    raw_routes = []
    for root_r in falcon_app._router._roots:
        for children_r in root_r.children:
            raw_routes.append(RawRoute(children_r))

            for a in children_r.children:
                for a2 in a.children or ():
                    raw_routes.append(RawRoute(a2))
                raw_routes.append(RawRoute(a))

    return get_routes(raw_routes)
