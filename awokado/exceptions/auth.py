import falcon

from awokado.exceptions.bad_request import BaseApiException


class AuthError(BaseApiException):
    def __init__(self, code="auth-error", details="Authorization error"):
        BaseApiException.__init__(
            self,
            code=code,
            status=falcon.HTTP_UNAUTHORIZED,
            details=details,
            title=falcon.HTTP_UNAUTHORIZED,
        )
