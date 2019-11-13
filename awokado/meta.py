from dataclasses import dataclass, field
from typing import Union, Tuple, Any, Type, Optional

from sqlalchemy.sql import Join

from awokado.auth import BaseAuth


@dataclass
class ResourceMeta:
    """
    :param name:  Resource name. Used for two resources connection by relation
    :param model: represents sqlalchemy model or cte
    :param methods:  tuple of methods you want to allow
    :param auth: awokado `BaseAuth <#awokado.auth.BaseAuth>`_  class for embedding authentication logic
    :param skip_doc:  set true if you don't need to add the resource to documentation
    :param disable_total: set false, if you don't need to know returning objects amount in read-requests
    :param id_field: you can specify your own primary key if it's different from the 'id' field. Used in reading requests (GET)
    :param select_from: provide data source here if your resource use another's model fields (for example sa.outerjoin(FirstModel, SecondModel, FirstModel.id == SecondModel.first_model_id))
    """

    name: str = "base_resource"
    methods: Tuple[str, ...] = ()
    model: Any = None  # type: ignore
    auth: Optional[Type[BaseAuth]] = None
    skip_doc: bool = False
    disable_total: bool = False
    id_field: str = "id"
    select_from: Optional[Join] = None

    def __post_init__(self):
        if not self.methods and self.name not in ("base_resource", "_resource"):
            raise Exception(
                f"ResourceMeta[{self.name}] object must have methods"
            )

    @classmethod
    def from_class(cls, t: Type):
        return cls(
            **{k: v for k, v in t.__dict__.items() if not k.startswith("_")}
        )
