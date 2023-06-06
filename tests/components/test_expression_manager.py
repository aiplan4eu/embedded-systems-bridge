import ast
import unittest

from unified_planning.shortcuts import *  # pylint: disable=unused-wildcard-import

from up_esb.bridge import Bridge
from up_esb.components.expression_manager import ExpressionManager


# Example fluents
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


class TestExpressionManager(unittest.TestCase):
    """Test conversion of FNode to AST tree."""

    def setUp(self) -> None:
        self.bridge = Bridge()
        self._fluent_bool_1 = self.bridge.create_fluent_from_function(fluent_bool_1_fun)
        self._fluent_bool_2 = self.bridge.create_fluent_from_function(fluent_bool_2_fun)
        self._fluent_int_1 = self.bridge.create_fluent_from_function(fluent_int_1_fun)
        self._fluent_real_1 = self.bridge.create_fluent_from_function(fluent_real_1_fun)

        self.ast = ExpressionManager()

    def test_simple_fluents(self):
        result = self.ast.convert(Not(self._fluent_bool_1))
        self.assertEqual(
            ast.dump(result), "UnaryOp(op=Not(), operand=Name(id='fluent_bool_1_fun', ctx=Load()))"
        )

        result = self.ast.convert(And(self._fluent_bool_1, self._fluent_bool_2))
        self.assertEqual(
            ast.dump(result),
            "BoolOp(op=And(), values=[Name(id='fluent_bool_1', ctx=Load()), Name(id='fluent_bool_2_fun', ctx=Load())])",
        )


if __name__ == "__main__":
    t = TestExpressionManager()
    t.setUp()
    t.test_simple_fluents()
