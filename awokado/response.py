from typing import Dict, Optional, List


class Response:
    """
    Response class helps to collect your data
    and prepare it in a readable format for the Frontend (or another API Client)

    You can override it in your resource to change response format::

        class MyResponse(Response):
            PAYLOAD_KEYWORD = "data"

        class MyBaseResource(BaseResource):
            Response = MyResponse

    Default serialization for list requests (``/v1/book/``)::

        {
          "payload": {
            "book": [
              {
                "name": "My Book",
                "authors": [1, 2]
              }
            ]
          },
          "meta": {
            "total": 1
          }
        }

    Default serialization for single object (``/v1/book/123``)::

        {
          "book": [
            {
              "name": "My Book",
              "authors": [1, 2]
            }
          ]
        }

    """

    PAYLOAD_KEYWORD = "payload"
    META_KEYWORD = "meta"
    TOTAL_KEYWORD = "total"

    def __init__(self, resource, is_list: bool = False):
        """
        # :param resource: resource.BaseResource
        """
        self.is_list = is_list
        self.resource = resource

        self.payload: Dict = {}
        self.related_payload: Optional[Dict] = None
        self.include_total = False
        self.total = 0

        if resource:
            self.include_total = not resource.Meta.disable_total

    def serialize(self) -> Dict:
        if self.related_payload and self.payload:
            self.payload.update(self.related_payload)

        if self.is_list:
            return self._serialize_list()
        else:
            return self._serialize_single()

    def set_parent_payload(self, parent_payload: Optional[List] = None) -> None:
        if not parent_payload:
            parent_payload = []

        payload = {self.resource.Meta.name: parent_payload}
        self.payload = payload

    def set_related_payload(self, related_payload: Optional[Dict]) -> None:
        self.related_payload = related_payload

    def set_total(self, total_objects_count: int):
        self.total = total_objects_count

    def _serialize_single(self) -> Dict:
        if not self.payload:
            self.set_parent_payload()

        response: Dict = self.payload
        return response

    def _serialize_list(self) -> Dict:
        if not self.payload:
            self.set_parent_payload()

        response = {self.PAYLOAD_KEYWORD: self.payload}

        if self.include_total:
            response[self.META_KEYWORD] = {self.TOTAL_KEYWORD: self.total}
        else:
            response[self.META_KEYWORD] = None  # type: ignore

        return response
