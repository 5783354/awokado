import falcon

from .base import BaseApiException


class BadRequest(BaseApiException):
    def __init__(self, details="", code="bad-request"):
        BaseApiException.__init__(
            self,
            status=falcon.HTTP_BAD_REQUEST,
            title=falcon.HTTP_BAD_REQUEST,
            code=code,
            details=details,
        )


class BadLimitOffset(BadRequest):
    def __init__(self, details="Limit or offset out of range"):
        BadRequest.__init__(self, code="bad-limit-offset", details=details)


class BadFilter(BadRequest):
    def __init__(self, filter=None, details=None):
        if not details:
            if filter:
                details = f"Filter {filter} is not supported"
            else:
                details = "Filter is not supported"
        BadRequest.__init__(self, code="bad-filter", details=details)


class MethodNotAllowed(BaseApiException):
    def __init__(self, details="", code="method-not-allowed"):
        BaseApiException.__init__(
            self,
            status=falcon.HTTP_METHOD_NOT_ALLOWED,
            title=falcon.HTTP_METHOD_NOT_ALLOWED,
            code=code,
            details=details,
        )


class IdFieldMissingError(BadRequest):
    def __init__(
        self, details="Resource has no id field. This action is impossible."
    ):
        BadRequest.__init__(self, code="id-field-missing", details=details)
