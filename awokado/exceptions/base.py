import json

ERROR_STATUS = "status"
ERROR_CODE = "code"
ERROR_TITLE = "title"
ERROR_DETAIL = "detail"


class BaseApiException(Exception):
    def __init__(self, status, title, code=None, details="", headers=None):
        self.status = status
        self.title = title
        self.code = code
        self.details = details
        self.headers = headers

    def __repr__(self):
        return self.__str__()

    def has_representation(self):
        return True

    def __str__(self):
        details = ". {}".format(self.details) if self.details else self.details
        return "{status}{details}".format(status=self.status, details=details)

    def to_json(self):
        """
        :type self BaseApiException
        """
        obj = self.to_dict()
        return json.dumps(obj, ensure_ascii=False)

    def to_dict(self):
        """
        :type self BaseApiException
        """
        result = {ERROR_STATUS: self.status, ERROR_TITLE: self.title}
        if self.code:
            result[ERROR_CODE] = self.code
        if self.details:
            result[ERROR_DETAIL] = self.details
        return result

    @staticmethod
    def handle(ex, req, resp, params):

        raise ex
