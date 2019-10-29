import re
from dataclasses import dataclass
from typing import Type, List, Any, Callable, Dict, Tuple

from awokado.consts import (
    OP_LTE,
    OP_EQ,
    OP_GTE,
    OP_ILIKE,
    OP_IN,
    OP_EMPTY,
    OP_CONTAINS,
    OP_LT,
    OP_GT,
)
from awokado.exceptions.bad_request import BadFilter

if False:
    from awokado.resource import BaseResource

OPERATORS_MAPPING: Dict[str, Tuple[str, Callable]] = {
    OP_LTE: ("__le__", lambda v: v),
    OP_EQ: ("__eq__", lambda v: v),
    OP_GTE: ("__ge__", lambda v: v),
    OP_ILIKE: ("ilike", lambda v: f"%{v}%"),
    OP_IN: ("in_", lambda v: v),
    OP_EMPTY: ("is_", lambda v: None),
    OP_CONTAINS: ("contains", lambda v: v),
    OP_LT: ("__lt__", lambda v: v),
    OP_GT: ("__gt__", lambda v: v),
}


@dataclass
class FilterItem:
    field: str
    op: str
    wrapper: Callable
    value: Any

    @classmethod
    def create(cls, field_name: str, op_name: str, value: Any):
        op = OPERATORS_MAPPING.get(op_name)

        if not op:
            raise BadFilter(details=f"Operator {op_name} doesn't exist")

        if isinstance(value, str) and op[0] in ("in_", OP_CONTAINS):
            value = value.split(",")

        if op[0] == "is_" and value == "false":
            op = ("isnot", lambda val: None)

        return cls(field_name, op[0], op[1], value)

    @classmethod
    def parse(
        cls, req_params: dict, resource: Type["BaseResource"]
    ) -> List["FilterItem"]:
        result = []
        filter_expr = r"(?P<field_name>(%s))\[(?P<op_name>[a-z]+)\]" % "|".join(
            resource().fields.keys()
        )

        for p, value in req_params.items():
            re_result = re.match(filter_expr, p)
            if not re_result:
                continue

            field_name = re_result.group("field_name")
            op_name = re_result.group("op_name")

            if not all([field_name, op_name, value]):
                continue

            result.append(cls.create(field_name, op_name, value))

        return result

    @classmethod
    def id_in(cls, ids: List[int], field_name="id"):
        op = OPERATORS_MAPPING[OP_IN]
        return cls(field_name, op[0], op[1], ids)


def filter_value_to_python(value):
    """
    Turn the string `value` into a python object.
    >>> filter_value_to_python([1, 2, 3])
    [1, 2, 3]
    >>> filter_value_to_python(123)
    123
    >>> filter_value_to_python('true')
    True
    >>> filter_value_to_python('False')
    False
    >>> filter_value_to_python('null')
    >>> filter_value_to_python('None')
    >>> filter_value_to_python('Ø')
    u'O'
    """
    if isinstance(value, list):
        return value
    if isinstance(value, int):
        return value

    # Simple values
    if value in ["true", "True", True]:
        value = True
    elif value in ["false", "False", False]:
        value = False
    elif value in ("null", "none", "None", None):
        value = None

    return value


parse_filters = FilterItem.parse
