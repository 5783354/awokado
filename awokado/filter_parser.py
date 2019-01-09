import re
from collections import namedtuple
from typing import Iterable

from awokado.consts import (
    OP_LTE,
    OP_EQ,
    OP_GTE,
    OP_ILIKE,
    OP_IN,
    OP_EMPTY,
    OP_CONTAINS,
)
from awokado.exceptions.bad_request import BadFilter

OPERATORS_MAPPING = {
    OP_LTE: ("__le__", lambda v: v),
    OP_EQ: ("__eq__", lambda v: v),
    OP_GTE: ("__ge__", lambda v: v),
    OP_ILIKE: (OP_ILIKE, lambda v: f"%{v}%"),
    OP_IN: ("in_", lambda v: v),
    OP_EMPTY: ("is_", lambda v: None),
    OP_CONTAINS: (OP_CONTAINS, lambda v: v),
}
FilterItem = namedtuple("FilterItem", ("field", "op", "wrapper", "value"))


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


def parse_filters(req_params, resource) -> Iterable[FilterItem]:
    result = []
    r = resource()
    filter_expr = r"(?P<field>({res_fields}))" r"\[" r"(?P<op>[a-z]+)" r"\]"

    res_field_names = "|".join(r.fields.keys())
    filter_expr = filter_expr.format(res_fields=res_field_names)

    for p, v in req_params.items():
        re_result = re.match(filter_expr, p)
        if not re_result:
            continue

        field_name = re_result.group("field")
        op_name = re_result.group("op")
        value = v

        if not all([field_name, op_name, value]):
            continue

        op = OPERATORS_MAPPING.get(op_name)

        if not op:
            raise BadFilter(details="Operator {} doesn't exist".format(op_name))

        if op[0] == "in_" or op[0] == OP_CONTAINS:
            if isinstance(value, list):
                value = value
            elif "," in value:
                value = value.split(",")
            else:
                value = [value]

        if op[0] == "is_" and value == "false":
            op = ("isnot", lambda val: None)

        result.append(FilterItem(field_name, op[0], op[1], value))
    return result
