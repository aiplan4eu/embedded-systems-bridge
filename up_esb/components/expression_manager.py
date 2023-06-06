import ast

from unified_planning.shortcuts import FNode, get_environment


class ExpressionManager:
    """Convert the unified planning FNode expression to an AST tree."""

    def __init__(self):
        self._expression = None
        self._manager = get_environment().expression_manager

    def convert(self, expression: FNode):
        """Walk the tree."""
        self._expression = expression
        tree = self._create_tree(expression)
        return tree

    def _create_tree(self, expression: FNode):
        return self._map_expression(expression)

    def _map_expression(self, expression: FNode):
        expression = self._manager.auto_promote(expression)

        for exp in expression:
            if exp.is_not():
                if exp.arg(0).fluent():
                    return ast.UnaryOp(op=ast.Not(), operand=self._map_expression(exp.arg(0)))
            elif exp.is_and():
                if exp.args[0].fluent():
                    return ast.BoolOp(
                        op=ast.And(),
                        values=[self._map_expression(arg) for arg in exp.args],
                    )
            elif exp.is_or():
                if exp.args[0].fluent():
                    return ast.BoolOp(
                        op=ast.Or(),
                        values=[self._map_expression(arg) for arg in exp.args],
                    )
            elif exp.is_equals():
                assert len(exp.args) == 2

                if exp.args[0].fluent():
                    return ast.Compare(
                        op=ast.Eq(),
                        left=self._map_expression(exp.args[0]),
                        right=self._map_expression(exp.args[1]),
                    )
            elif exp.is_le():
                assert len(exp.args) == 2

                if exp.args[0].fluent():
                    return ast.Compare(
                        op=ast.LtE(),
                        left=self._map_expression(exp.args[0]),
                        right=self._map_expression(exp.args[1]),
                    )
            elif exp.is_lt():
                assert len(exp.args) == 2

                if exp.args[0].fluent():
                    return ast.Compare(
                        op=ast.Lt(),
                        left=self._map_expression(exp.args[0]),
                        right=self._map_expression(exp.args[1]),
                    )

            elif exp.is_constant():
                if exp.constant().is_bool():
                    return ast.Constant(value=exp.constant().bool_value())
                elif exp.constant().is_int():
                    return ast.Constant(value=exp.constant().int_value())
                elif exp.constant().is_real():
                    return ast.Constant(value=exp.constant().real_value())

            elif exp.fluent:
                return ast.Name(id=exp.fluent().name, ctx=ast.Load())
