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


class InvalidBarcode(BadRequest):
    def __init__(self, details="Invalid barcode"):
        BadRequest.__init__(self, code="invalid-barcode", details=details)


class UnsupportedMethod(BadRequest):
    def __init__(self, method=None, details=None):
        if not details:
            if method:
                details = f"Method {method} is not supported"
            else:
                details = "Method is not supported"
        BadRequest.__init__(self, code="unsupported-method", details=details)


class UnsupportedRequestAttr(BadRequest):
    def __init__(self, attr=None, details=None):
        if not details:
            if attr:
                details = f"Request attr {attr} is not supported"
            else:
                details = "Request attr is not supported"
        BadRequest.__init__(
            self, code="unsupported-request-attr", details=details
        )


class MethodNotAllowed(BaseApiException):
    def __init__(self, details="", code="method-not-allowed"):
        BaseApiException.__init__(
            self,
            status=falcon.HTTP_METHOD_NOT_ALLOWED,
            title=falcon.HTTP_METHOD_NOT_ALLOWED,
            code=code,
            details=details,
        )
