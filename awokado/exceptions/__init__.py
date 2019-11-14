from .auth import AuthError
from .base import BaseApiException
from .not_found import NotFound, RelationNotFound, ResourceNotFound

from .bad_request import (
    BadFilter,
    BadLimitOffset,
    BadRequest,
    MethodNotAllowed,
    IdFieldMissingError,
)

from .forbidden import (
    CreateResourceForbidden,
    DeleteResourceForbidden,
    Forbidden,
    ReadResourceForbidden,
    UpdateResourceForbidden,
)
