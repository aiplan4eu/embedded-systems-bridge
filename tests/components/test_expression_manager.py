import unittest

from unified_planning.shortcuts import *  # pylint: disable=unused-wildcard-import

from up_esb.bridge import Bridge
from up_esb.components.expression_manager import ExpressionManager

# pylint: disable=missing-docstring, line-too-long, eval-used


# Example fluents


class TestObject:
    def __init__(self, value: int):
        """Test object."""
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __str__(self) -> str:
        return "TestObject"


def fluent_bool_1_fun():
    """Fluent bool 1."""
    return True


def fluent_bool_2_fun():
    """Fluent bool 2."""
    return False


def fluent_int_1_fun():
    """Fluent int 1."""
    return 1


def fluent_real_1_fun():
    """Fluent real 1."""
    return 1.0


def fluent_arg_bool_1_fun(arg: bool):
    """Fluent real 1."""
    return arg


def fluent_arg_int_1_fun(arg: int):
    """Fluent real 1."""
    return arg


def fluent_arg_object(arg: TestObject) -> TestObject:
    """Fluent real 1."""
    return arg


class TestExpressionManager(unittest.TestCase):
    """Test conversion of FNode to AST tree."""

    def setUp(self) -> None:
        self.bridge = Bridge()
        self._fluent_bool_1 = self.bridge.create_fluent_from_function(fluent_bool_1_fun)
        self._fluent_bool_2 = self.bridge.create_fluent_from_function(fluent_bool_2_fun)
        self._fluent_int_1 = self.bridge.create_fluent_from_function(fluent_int_1_fun)
        self._fluent_real_1 = self.bridge.create_fluent_from_function(fluent_real_1_fun)

        self._fluent_arg_bool_1 = self.bridge.create_fluent_from_function(fluent_arg_bool_1_fun)
        self._fluent_arg_int_1 = self.bridge.create_fluent_from_function(fluent_arg_int_1_fun)

        self.bridge.create_types([TestObject])
        self._fluent_arg_object = self.bridge.create_fluent_from_function(fluent_arg_object)

        self.ast = ExpressionManager()

    def test_simple_fluents(self):
        """Test simple fluents."""
        result = self.ast.convert(Not(self._fluent_bool_1))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, False)

        result = self.ast.convert(And(self._fluent_bool_1, self._fluent_bool_2))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, False)

        result = self.ast.convert(Or(self._fluent_bool_1, self._fluent_bool_2))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, True)

    def test_simple_nested_fluents(self):
        result = self.ast.convert(Not(And(self._fluent_int_1, self._fluent_int_1)))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, False)

        result = self.ast.convert(Not(And(self._fluent_real_1, self._fluent_real_1)))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, False)

        result = self.ast.convert(Not(And(self._fluent_bool_1, self._fluent_bool_2)))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, True)

        result = self.ast.convert(Not(And(self._fluent_bool_1, self._fluent_bool_1)))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, False)

    def test_simple_fluents_with_args(self):
        result = self.ast.convert(self._fluent_arg_bool_1(True))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, True)

        result = self.ast.convert(Not(self._fluent_arg_bool_1(False)))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, True)

        result = self.ast.convert(Not(self._fluent_arg_int_1(1)))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, False)

    def test_simple_nested_fluents_with_args(self):
        result = self.ast.convert(Not(And(self._fluent_arg_int_1(1), self._fluent_arg_int_1(1))))
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, False)

        result = self.ast.convert(
            Not(And(self._fluent_arg_bool_1(True), self._fluent_arg_bool_1(False)))
        )
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, True)

        result = self.ast.convert(
            Not(And(self._fluent_arg_bool_1(True), self._fluent_arg_bool_1(True)))
        )
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, False)

        obj = self.bridge.create_object("obj", TestObject(1))
        result = self.ast.convert(
            Equals(self._fluent_arg_object(obj), self._fluent_arg_object(obj))
        )
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, True)

        obj1 = self.bridge.create_object("obj1", TestObject(2))
        result = self.ast.convert(
            Equals(self._fluent_arg_object(obj), self._fluent_arg_object(obj1))
        )
        actual = eval(compile(result, filename="<ast>", mode="eval"))
        self.assertEqual(actual, False)


if __name__ == "__main__":
    t = TestExpressionManager()
    t.setUp()
    t.test_simple_fluents()
    t.test_simple_nested_fluents()
    t.test_simple_fluents_with_args()
    t.test_simple_nested_fluents_with_args()
