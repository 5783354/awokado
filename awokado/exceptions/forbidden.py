import falcon

from awokado.exceptions import BaseApiException


class Forbidden(BaseApiException):
    def __init__(self, details="", code="forbidden"):
        BaseApiException.__init__(
            self,
            status=falcon.HTTP_403,
            title=falcon.HTTP_403,
            code=code,
            details=details,
        )


class CreateResourceForbidden(Forbidden):
    def __init__(self, details="The creation of a resource forbidden"):
        Forbidden.__init__(self, code="create-forbidden", details=details)


class UpdateResourceForbidden(Forbidden):
    def __init__(self, details="Change the resource is forbidden"):
        Forbidden.__init__(self, code="update-forbidden", details=details)


class DeleteResourceForbidden(Forbidden):
    def __init__(self, details="Delete the resource is forbidden"):
        Forbidden.__init__(self, code="delete-forbidden", details=details)


class ReadResourceForbidden(Forbidden):
    def __init__(self, details="Read the resource is forbidden"):
        Forbidden.__init__(self, code="read-forbidden", details=details)
