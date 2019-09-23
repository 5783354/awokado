from unittest import TestCase

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
from awokado.filter_parser import (
    filter_value_to_python,
    parse_filters,
    FilterItem,
)
from tests.test_app.resources.author import AuthorResource


class FilterParserTest(TestCase):
    def test_filter_value_to_python(self):
        self.assertEqual([1, 2, 3], filter_value_to_python([1, 2, 3]))
        self.assertEqual(
            ["1", "2", "3"], filter_value_to_python(["1", "2", "3"])
        )
        self.assertEqual(123, filter_value_to_python(123))
        self.assertEqual(True, filter_value_to_python("true"))
        self.assertEqual(True, filter_value_to_python(True))
        self.assertEqual(False, filter_value_to_python("false"))
        self.assertEqual(False, filter_value_to_python(False))
        self.assertEqual(None, filter_value_to_python("null"))
        self.assertEqual(None, filter_value_to_python(None))
        self.assertEqual("Line", filter_value_to_python("Line"))

    def test_parse_filters(self):
        self.assertFilterItems(
            [FilterItem("id", "__eq__", lambda v: v, "1")],
            parse_filters({f"id[{OP_EQ}]": "1"}, AuthorResource),
        )

        self.assertFilterItems(
            [FilterItem("id", "in_", lambda v: v, ["1"])],
            parse_filters(
                {
                    f"id[{OP_IN}]": "1",
                    f"last_name[{OP_EQ}]": "",
                    f"non_existent_field[{OP_EQ}]": "val",
                },
                AuthorResource,
            ),
        )

        with self.assertRaises(BadFilter):
            parse_filters({"id[nonexistentop]": "1"}, AuthorResource),

        self.assertFilterItems(
            [
                FilterItem("id", "__ge__", lambda v: v, "2"),
                FilterItem("last_name", OP_ILIKE, lambda v: f"%{v}%", "name"),
            ],
            parse_filters(
                {f"id[{OP_GTE}]": "2", f"last_name[{OP_ILIKE}]": "name"},
                AuthorResource,
            ),
        )

        self.assertFilterItems(
            [
                FilterItem("first_name", "is_", lambda v: None, "true"),
                FilterItem("id", "__le__", lambda v: v, "2"),
                FilterItem("last_name", OP_CONTAINS, lambda v: v, ["name"]),
            ],
            parse_filters(
                {
                    f"id[{OP_LTE}]": "2",
                    f"last_name[{OP_CONTAINS}]": "name",
                    f"first_name[{OP_EMPTY}]": "true",
                },
                AuthorResource,
            ),
        )

        self.assertFilterItems(
            [
                FilterItem("first_name", "isnot", lambda v: None, "false"),
                FilterItem("id", "in_", lambda v: v, ["2", "3", "4"]),
                FilterItem("last_name", "in_", lambda v: v, ["name1", "name2"]),
            ],
            parse_filters(
                {
                    f"id[{OP_IN}]": "2,3,4",
                    f"last_name[{OP_IN}]": ["name1", "name2"],
                    f"first_name[{OP_EMPTY}]": "false",
                },
                AuthorResource,
            ),
        )

        self.assertFilterItems(
            [
                FilterItem("id", "__gt__", lambda v: v, "2"),
                FilterItem("last_name", OP_CONTAINS, lambda v: v, ["name"]),
            ],
            parse_filters(
                {f"id[{OP_GT}]": "2", f"last_name[{OP_CONTAINS}]": "name"},
                AuthorResource,
            ),
        )

        self.assertFilterItems(
            [
                FilterItem("id", "__lt__", lambda v: v, "2"),
                FilterItem("last_name", OP_ILIKE, lambda v: f"%{v}%", "name"),
            ],
            parse_filters(
                {f"id[{OP_LT}]": "2", f"last_name[{OP_ILIKE}]": "name"},
                AuthorResource,
            ),
        )

    def assertFilterItems(self, first_list, second_list):
        first_list = sorted(first_list, key=lambda i: i.field)
        second_list = sorted(second_list, key=lambda i: i.field)

        for first, second in zip(first_list, second_list):
            self.assertEqual(first.field, second.field, "field is different")
            self.assertEqual(first.op, second.op, "op is different")
            self.assertEqual(first.value, second.value, "value is different")
            self.assertEqual(
                first.wrapper(first.value),
                second.wrapper(second.value),
                "wrapped value is different",
            )
