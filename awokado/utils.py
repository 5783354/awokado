import datetime
import hashlib
import json
import logging
import random
import string
import sys
import traceback
import uuid
from json import JSONDecodeError
from typing import NamedTuple, Optional

import falcon
from dynaconf import settings
from sqlalchemy import desc, asc

from awokado.consts import DEFAULT_ACCESS_CONTROL_HEADERS
from awokado.exceptions import BaseApiException
from awokado.filter_parser import parse_filters

log = logging.getLogger("awokado")


class AuthBundle(NamedTuple):
    user_id: int
    auth_token: str


def rand_string(size=8, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def get_sort_way(sort_route):
    if sort_route.startswith("-"):
        sort_route = sort_route[1:]

        def sort_way(sort_field):
            return desc(sort_field).nullslast()

    else:

        def sort_way(sort_field):
            return asc(sort_field).nullsfirst()

    return sort_route, sort_way


def empty_response(resource, is_list=False):
    if isinstance(resource, str):
        resource_name = resource
    else:
        resource_name = resource.Meta.name

    if is_list:
        response = {"payload": {resource_name: []}, "meta": None}
        if not resource.Meta.disable_total:
            response["meta"] = {"total": 0}
        return response

    else:
        return {resource_name: []}


def get_read_params(req, resource) -> dict:
    """
    :param req: falcon.Request
    :param resource: api.resources.base.BaseResource
    """

    params = dict(
        include=req.get_param_as_list("include"),
        sort=req.get_param_as_list("sort"),
        limit=req.get_param_as_int("limit"),
        offset=req.get_param_as_int("offset"),
    )

    params["filters"] = parse_filters(req._params, resource)
    return params


def has_resource_auth(resource):
    if not hasattr(resource.Meta, "auth"):
        return False
    if resource.Meta.auth is None:
        return False

    return True


def json_error_serializer(
    req: falcon.request.Request,
    resp: falcon.response.Response,
    exception: BaseApiException,
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

    if settings.AWOKADO_DEBUG:
        headers["Access-Control-Allow-Origin"] = origin
    else:
        if origin and origin in settings.ORIGIN_HOSTS:
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
        resp.body = falcon.json.dumps({"error": f"{req.path} not found"})
        resp.append_header("Vary", "Accept")

    else:
        resp.status = "500 Internal Server Error"
        exc_info = sys.exc_info()
        log.error("api_exception_handler", exc_info=exc_info)

        if settings.get("AWOKADO_DEBUG"):

            if hasattr(error, "to_dict"):
                resp.body = falcon.json.dumps({"error": error.to_dict()})

            elif hasattr(error, "to_json"):
                json_data = error.to_json()

                try:
                    json_data = json.loads(json_data)
                except (TypeError, JSONDecodeError):
                    json_data = json_data

                resp.body = falcon.json.dumps({"error": json_data})

            else:
                exc_data = "".join(traceback.format_exception(*sys.exc_info()))
                resp.body = falcon.json.dumps({"error": exc_data})

        else:
            resp.body = falcon.json.dumps({"error": resp.status})

        # Set content type
        resp.content_type = "application/json"
        resp.append_header("Vary", "Accept")


class ReadContext:
    def __init__(
        self,
        session,
        resource,
        user_id: int,
        include: list,
        filters: Optional[dict],
        sort: Optional[list],
        resource_id: Optional[int],
        limit: Optional[int],
        offset: Optional[int],
    ):
        self.resource = resource
        self.uid = user_id
        self.session = session

        # runtime vars
        self.q = None
        self.obj_ids = []
        self.parent_payload = {}
        self.related_payload = {}
        self.total = None

        # for Aggregation Resources
        self.time_scale = None

        # request vars
        self.limit = limit
        self.offset = offset
        self.sort = sort
        self.query = filters
        self.include = include
        self.resource_id = resource_id

    @property
    def is_list(self):
        return not bool(self.resource_id)


def get_uuid_hash(string):
    return hashlib.md5(
        (
            str(uuid.uuid3(uuid.uuid4(), string))
            + str(datetime.datetime.utcnow())
        ).encode("utf-8")
    ).hexdigest()


class cached_property(property):
    def __init__(self, func, name=None, **kwargs):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.func = func

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = value

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, None)
        if value is None:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value
