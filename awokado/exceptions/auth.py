import falcon

from awokado.exceptions.bad_request import BadRequest
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


class DataError(BadRequest):
    def __init__(self, code="data-error", details="Data error"):
        super().__init__(code=code, details=details)


class BadPhone(DataError):
    def __init__(self, code="bad-phone", details="Bad phone number"):
        BadRequest.__init__(self, code=code, details=details)


class BadEmail(DataError):
    def __init__(self, code="bad-email", details="Bad email"):
        BadRequest.__init__(self, code=code, details=details)


class BadPassword(DataError):
    def __init__(self, code="bad-password", details="Bad password"):
        BadRequest.__init__(self, code=code, details=details)


class PasswordMismatch(AuthError):
    def __init__(
        self,
        code="password-mismatch",
        details="Provided password doesn't match",
    ):
        super().__init__(code=code, details=details)


class UserNotFound(AuthError):
    def __init__(
        self, code: str = "user-not-found", details: str = "User not found"
    ):
        super().__init__(code=code, details=details)


class IdentificationFailed(AuthError):
    def __init__(
        self, code="identification-failed", details="Identification failed"
    ):
        super().__init__(code=code, details=details)


class BadPhoneVerificationCode(DataError):
    def __init__(
        self,
        code="bad-phone-verification-code",
        details="Bad phone verification code",
    ):
        BadRequest.__init__(self, code=code, details=details)


class PhoneVerificationFailed(AuthError):
    def __init__(
        self,
        code="phone-verification-failed",
        details="Phone verification failed",
    ):
        super().__init__(code=code, details=details)


class PhoneNotVerified(AuthError):
    code = "phone-not-verified"

    def __init__(self, phone=None, details=None):
        d = (
            f"Phone{f' {phone} ' if phone else ' '}is not verified."
            f"{f' {details}' if details else ''}"
        )

        super().__init__(code=self.code, details=d)


class PasswordResetFailed(AuthError):
    def __init__(
        self, code="password-reset-failed", details="Password reset failed"
    ):
        super().__init__(code=code, details=details)
