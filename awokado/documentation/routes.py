import functools
from collections import namedtuple

METHOD_MAPPING = {
    "POST": "create",
    "GET": "read",
    "PATCH": "update",
    "DELETE": "delete",
}


def collect_routes(falcon_app):
    raw_routes = []
    for root_r in falcon_app._router._roots:
        for children_r in root_r.children:
            raw_routes.append(
                (
                    children_r.uri_template,
                    children_r.var_name,
                    children_r.method_map,
                    children_r.resource,
                )
            )

            for a in children_r.children:

                if a.children:
                    for a2 in a.children:
                        raw_routes.append(
                            (
                                a2.uri_template,
                                a2.var_name,
                                a2.method_map,
                                a2.resource,
                            )
                        )
                raw_routes.append(
                    (a.uri_template, a.var_name, a.method_map, a.resource)
                )

    routes = []
    new_route = namedtuple(
        "route", ["route", "uri", "method_name", "method", "resource"]
    )

    for r_name, var_name, methods, resource in raw_routes:
        if not methods:
            continue

        for method_name, method in methods.items():
            if (
                not METHOD_MAPPING.get(method_name, None)
                in resource.Meta.methods
            ):
                continue

            if not isinstance(method, functools.partial):
                r = new_route(
                    r_name, var_name, method_name.lower(), method, resource
                )
                routes.append(r)

    return routes
