from unittest import TestCase

from awokado.utils import cached_property


class CachedPropertyTest(TestCase):
    class Foo(object):
        execution_counter = 0

        @cached_property
        def test_property(self):
            self.execution_counter += 1
            return "test"

    def test_get_cached_property(self):
        foo = self.Foo()
        self.assertEqual(foo.execution_counter, 0)
        rv = foo.test_property
        self.assertEqual(foo.execution_counter, 1)
        rv = foo.test_property
        self.assertEqual(foo.execution_counter, 1)
        self.assertEqual(rv, "test")

    def test_set_cached_property(self):
        foo = self.Foo()
        foo.test_property = "foo_test"
        self.assertEqual(foo.execution_counter, 0)
        rv = foo.test_property
        self.assertEqual(foo.execution_counter, 0)
        self.assertEqual(rv, "foo_test")

    def test_none_object(self):
        @cached_property
        def test():
            return "test"

        self.assertIsInstance(test, cached_property)
