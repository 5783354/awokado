from typing import Optional, List, Dict, Union

from awokado.filter_parser import FilterItem
from sqlalchemy.sql.selectable import Select


class ReadContext:
    def __init__(
        self,
        session,
        resource,
        user_id: int,
        include: Optional[List],
        filters: Optional[List[FilterItem]],
        sort: Optional[list],
        resource_id: Optional[int],
        limit: Optional[int],
        offset: Optional[int],
    ):
        self.resource = resource
        self.uid = user_id
        self.session = session

        # runtime vars
        self.q: Select = Select()
        self.obj_ids: List[int] = []
        self.parent_payload: List = []
        self.related_payload: Dict = {}
        self.total: int = 0

        # for Aggregation Resources
        self.time_scale = None

        # request vars
        self.limit = limit
        self.offset = offset
        self.sort = sort
        self.query = filters
        self.include = include
        self.resource_id = resource_id

    @property
    def is_list(self):
        return not bool(self.resource_id)
