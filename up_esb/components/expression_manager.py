# Copyright 2022 Selvakumar H S, LAAS-CNRS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Convert the unified planning FNode expression to an AST tree."""
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
        ast_expression = self._map_expression(expression)
        if ast_expression is not None:
            # Convert to executable code
            ast.fix_missing_locations(ast_expression)
            return ast.Expression(body=ast_expression)

        raise ValueError(f"Unable to parse expression {expression}")

    def _map_expression(self, expression: FNode):
        expression = self._manager.auto_promote(expression)

        for exp in expression:
            if exp.is_not():
                return ast.UnaryOp(op=ast.Not(), operand=self._map_expression(exp.arg(0)))
            elif exp.is_and():
                return ast.BoolOp(
                    op=ast.And(),
                    values=[self._map_expression(arg) for arg in exp.args],
                )
            elif exp.is_or():
                return ast.BoolOp(
                    op=ast.Or(),
                    values=[self._map_expression(arg) for arg in exp.args],
                )
            elif exp.is_equals():
                assert len(exp.args) == 2

                return ast.Compare(
                    op=ast.Eq(),
                    left=self._map_expression(exp.args[0]),
                    right=self._map_expression(exp.args[1]),
                )
            elif exp.is_le():
                assert len(exp.args) == 2

                return ast.Compare(
                    op=ast.LtE(),
                    left=self._map_expression(exp.args[0]),
                    right=self._map_expression(exp.args[1]),
                )
            elif exp.is_lt():
                assert len(exp.args) == 2

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
                function = ast.Name(id=exp.fluent().name, ctx=ast.Load())
                return ast.Call(func=function, args=[], keywords=[])  # TODO: Check with arguments

            raise NotImplementedError(
                f"Expression {exp} not implemented. \n"
                "Supported operators are: Not, And, Or, Equals, Le, Lt, Constant, Fluent."
            )
