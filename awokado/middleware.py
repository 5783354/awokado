import cProfile
import datetime
import marshal
import pstats
import random
import string

import boto3
from dynaconf import settings

from awokado.consts import DEFAULT_ACCESS_CONTROL_HEADERS
from awokado.utils import rand_string


class HttpMiddleware:
    def process_request(self, req, resp):
        """Process the request before routing it.

        Args:
            req: Request object that will eventually be
                routed to an on_* responder method.
            resp: Response object that will be routed to
                the on_* responder.
        """
        # Set content type
        resp.content_type = "application/json"

        if not req.headers:
            return

        # Update https headers
        origin = req.headers.get("HTTP_ORIGIN")
        origin2 = req.headers.get("ORIGIN")
        origin = origin2 or origin

        if settings.AWOKADO_DEBUG:
            resp.append_header(name="Access-Control-Allow-Origin", value=origin)
        else:
            if origin and origin in settings.ORIGIN_HOSTS:
                resp.append_header(
                    name="Access-Control-Allow-Origin", value=origin
                )

        resp.set_headers(
            settings.get(
                "AWOKADO_ACCESS_CONTROL_HEADERS", DEFAULT_ACCESS_CONTROL_HEADERS
            )
        )

    def process_resource(self, req, resp, resource, params):
        """Process the request and resource *after* routing.

        Note:
            This method is only called when the request matches
            a route to a resource.

        Args:
            req: Request object that will be passed to the
                routed responder.
            resp: Response object that will be passed to the
                responder.
            resource: Resource object to which the request was
                routed. May be None if no route was found for
                the request.
            params: A dict-like object representing any
                additional params derived from the route's URI
                template fields, that will be passed to the
                resource's responder method as keyword
                arguments.
        """
        if not settings.get("AWOKADO_DEBUG"):
            return

        profiling_enabled = req.get_param_as_bool("profiling")
        if profiling_enabled:
            profile = cProfile.Profile()
            profile.enable()
            req.profile = profile

        debugger_enabled = req.get_param_as_bool("debug")
        if debugger_enabled:
            from pudb.remote import set_trace

            set_trace(term_size=(100, 50))

    def process_response(self, req, resp, resource, req_succeeded):
        """Post-processing of the response (after routing).

        Args:
            req: Request object.
            resp: Response object.
            resource: Resource object to which the request was
                routed. May be None if no route was found
                for the request.
            req_succeeded: True if no exceptions were raised
                while the awokado processed and routed the
                request; otherwise False.
        """
        if not settings.get("AWOKADO_DEBUG"):
            return

        profiling_enabled = req.get_param_as_bool("profiling")
        if profiling_enabled:
            req.profile.disable()
            save_debug_proiling(req.profile)


def save_debug_proiling(profile):
    if settings.AWOKADO_ENABLE_UPLOAD_DEBUG_PROFILING_TO_S3:
        upload_profiling_info_to_s3(profile)
    else:
        save_profiling_info_to_file(profile)


def save_profiling_info_to_file(profile):
    stats = pstats.Stats(profile)
    marshaled_stats = marshal.dumps(stats.stats)

    now = datetime.datetime.now()
    key = (
        f"{now.strftime('%Y-%m-%d')}"
        f"/ {now.strftime('%Y-%m-%dT%H-%M-%S')}"
        f"- {rand_string()}.prof"
    )
    with open(key, "w") as f:
        f.write(marshaled_stats.decode(encoding="utf-8"))


def upload_profiling_info_to_s3(profile):
    stats = pstats.Stats(profile)
    marshaled_stats = marshal.dumps(stats.stats)
    s3client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWOKADO_AWS_S3_DEBUG_PROFILING_ACCESS_KEY,
        aws_secret_access_key=settings.AWOKADO_AWS_S3_DEBUG_PROFILING_SECRET_KEY,
    )

    now = datetime.datetime.now()
    rand_str = "".join(random.choice(string.ascii_lowercase) for _ in range(10))
    key = (
        f"profiling"
        f"/{now.strftime('%Y-%m-%d')}"
        f"/{now.strftime('%Y-%m-%dT%H-%M-%S')}-{rand_str}"
        f".prof"
    )
    kwargs = dict(
        Body=marshaled_stats,
        Bucket=settings.AWOKADO_AWS_S3_DEBUG_PROFILING_BUCKET_NAME,
        Key=key,
    )

    s3client.put_object(**kwargs)
