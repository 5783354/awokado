import json
import logging
import random
import string
import sys
import traceback
from dataclasses import dataclass
from json import JSONDecodeError
from typing import List, Dict, Any, Type, Tuple, Callable, Optional

import falcon
from dynaconf import settings
from sqlalchemy import desc, asc

from awokado.consts import DEFAULT_ACCESS_CONTROL_HEADERS
from awokado.exceptions import BaseApiException, IdFieldMissingError, BadRequest
from awokado.filter_parser import FilterItem
import sqlalchemy as sa

if False:
    from awokado.resource import BaseResource

log = logging.getLogger("awokado")


@dataclass
class AuthBundle:
    user_id: int
    auth_token: str

    def __iter__(self):
        yield self.user_id
        yield self.auth_token


@dataclass
class M2MMapping:
    related_model: sa.Table
    left_fk_field: Optional[sa.Column] = None
    right_fk_field: Optional[sa.Column] = None
    secondary: Optional[sa.Table] = None


def rand_string(size=8, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def get_sort_way(sort_route: str) -> Tuple[str, Callable]:
    if sort_route.startswith("-"):
        sort_route = sort_route[1:]

        def sort_way(sort_field):
            return desc(sort_field).nullslast()

    else:

        def sort_way(sort_field):
            return asc(sort_field).nullsfirst()

    return sort_route, sort_way


def get_read_params(
    req: falcon.Request, resource: Type["BaseResource"]
) -> dict:
    params = {
        "include": req.get_param_as_list("include"),
        "sort": req.get_param_as_list("sort"),
        "limit": req.get_param_as_int("limit"),
        "offset": req.get_param_as_int("offset"),
        "filters": FilterItem.parse(req._params, resource),
    }
    return params


def json_error_serializer(
    req: falcon.Request, resp: falcon.Response, exception: BaseApiException
):
    # Serialize exception
    resp.body = exception.to_json()

    # Set content type
    resp.content_type = "application/json"
    resp.append_header("Vary", "Accept")
    resp.status = exception.status

    # Setup CORS
    origin = req.headers.get("HTTP_ORIGIN")
    origin2 = req.headers.get("ORIGIN")
    origin = origin2 or origin
    headers = {}

    if settings.get("AWOKADO_DEBUG") or (
        origin and origin in settings.ORIGIN_HOSTS
    ):
        headers["Access-Control-Allow-Origin"] = origin

    headers_to_set = settings.get(
        "AWOKADO_ACCESS_CONTROL_HEADERS", DEFAULT_ACCESS_CONTROL_HEADERS
    )
    for k, v in headers_to_set:
        headers[k] = v

    resp.set_headers(headers)


def api_exception_handler(error, req, resp, params):
    if isinstance(error, BaseApiException):
        resp.status = error.status

        if error.headers is not None:
            resp.set_headers(error.headers)

        if error.has_representation:
            json_error_serializer(req, resp, error)

        if settings.get("AWOKADO_LOG_USERS_EXCEPTIONS", False):
            exc_info = sys.exc_info()
            log.error("User error: ", exc_info=exc_info)

    elif isinstance(error, falcon.HTTPNotFound):
        resp.status = "404 Not Found"
        resp.content_type = "application/json"
        resp.body = json.dumps({"error": f"{req.path} not found"})
        resp.append_header("Vary", "Accept")

    else:
        resp.status = "500 Internal Server Error"
        exc_info = sys.exc_info()
        log.error("api_exception_handler", exc_info=exc_info)

        if settings.get("AWOKADO_DEBUG"):

            if hasattr(error, "to_dict"):
                resp.body = json.dumps({"error": error.to_dict()})

            elif hasattr(error, "to_json"):
                json_data = error.to_json()

                try:
                    json_data = json.loads(json_data)
                except (TypeError, JSONDecodeError):
                    json_data = json_data

                resp.body = json.dumps({"error": json_data})

            else:
                exc_data = "".join(traceback.format_exception(*sys.exc_info()))
                resp.body = json.dumps({"error": exc_data})

        else:
            resp.body = json.dumps({"error": resp.status})

        # Set content type
        resp.content_type = "application/json"
        resp.append_header("Vary", "Accept")


def get_id_field(resource: "BaseResource", name_only=False, skip_exc=False):
    resource_id_field_name = resource.Meta.id_field
    if resource_id_field_name not in resource.fields:
        if skip_exc:
            return False

        raise IdFieldMissingError()

    if name_only:
        return resource_id_field_name

    resource_id_field = resource.fields[resource_id_field_name]
    resource_id_model_field = resource_id_field.metadata.get("model_field")
    return resource_id_model_field


def get_ids_from_payload(model: Any, payload: List[Dict]) -> List:
    if model and hasattr(model, "id"):
        ids = [d.get(model.id.key) for d in payload]
    else:
        raise BadRequest("Model's ID field doesn't specified")

    return ids
