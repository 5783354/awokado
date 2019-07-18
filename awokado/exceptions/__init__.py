from .auth import (
    AuthError,
    BadEmail,
    BadPassword,
    BadPhone,
    BadPhoneVerificationCode,
    DataError,
    IdentificationFailed,
    PasswordMismatch,
    PasswordResetFailed,
    PhoneVerificationFailed,
    UserNotFound,
)
from .bad_request import (
    BadFilter,
    BadLimitOffset,
    BadRequest,
    InvalidBarcode,
    MethodNotAllowed,
    UnsupportedMethod,
    UnsupportedRequestAttr,
    IdFieldMissingError,
)
from .base import BaseApiException
from .forbidden import (
    CreateResourceForbidden,
    DeleteResourceForbidden,
    Forbidden,
    ReadResourceForbidden,
    UpdateResourceForbidden,
)
from .not_found import NotFound, RelationNotFound, ResourceNotFound
