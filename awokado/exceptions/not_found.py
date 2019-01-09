import falcon

from awokado.exceptions import BaseApiException


class NotFound(BaseApiException):
    def __init__(self, details="", code="not-found"):
        BaseApiException.__init__(
            self,
            status=falcon.HTTP_NOT_FOUND,
            title=falcon.HTTP_NOT_FOUND,
            code=code,
            details=details,
        )


class ResourceNotFound(NotFound):
    def __init__(self, resource=None, details=None):
        """
        :type resource: str
        :type details: str
        """
        if not details:
            if resource:
                details = 'Resource "{resource_name}" not found'.format(
                    resource_name=resource
                )
            else:
                details = "Resource not found"
        NotFound.__init__(self, code="resource-not-found", details=details)


class RelationNotFound(NotFound):
    def __init__(self, details="Relation not found"):
        NotFound.__init__(self, code="relation-not-found", details=details)
