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
        self._options = None
        self._manager = get_environment().expression_manager

    def convert(self, expression: FNode, **options):
        """Walk the tree."""
        self._expression = expression
        self._options = options
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
                    ops=[ast.Eq()],
                    left=self._map_expression(exp.args[0]),
                    comparators=[self._map_expression(exp.args[1])],
                )
            elif exp.is_le():
                assert len(exp.args) == 2

                return ast.Compare(
                    ops=[ast.LtE()],
                    left=self._map_expression(exp.args[0]),
                    comparators=[self._map_expression(exp.args[1])],
                )
            elif exp.is_lt():
                assert len(exp.args) == 2

                return ast.Compare(
                    ops=[ast.Lt()],
                    left=self._map_expression(exp.args[0]),
                    comparators=[self._map_expression(exp.args[1])],
                )

            elif exp.is_constant():
                if exp.is_bool_constant():
                    return ast.Constant(value=exp.bool_constant_value())
                elif exp.is_int_constant():
                    return ast.Constant(value=exp.int_constant_value())
                elif exp.is_real_constant():
                    return ast.Constant(value=exp.real_constant_value())
                elif exp.is_object_exp():
                    return ast.Name(id=str(exp.object().name), ctx=ast.Load())

                raise ValueError(f"Constant `{str(exp)}` not supported.")

            elif exp.is_parameter_exp():
                parameters = self._options.get("parameters")
                if parameters is None:
                    raise ValueError("Parameters options are expected but not provided.")

                if exp.parameter().name not in parameters:
                    raise ValueError(f"Parameter `{exp.parameter().name}` not found.")

                actual_parameter = parameters[exp.parameter().name]
                return ast.Name(id=str(actual_parameter), ctx=ast.Load())

            elif exp.fluent:
                # Arguments in fluents are expected to be grounded
                function = ast.Name(id=exp.fluent().name, ctx=ast.Load())
                return ast.Call(
                    func=function,
                    args=[self._map_expression(arg) for arg in exp.args],
                    keywords=[],
                )

            raise NotImplementedError(
                f"Expression `{str(exp)}` not implemented. \n"
                "Supported operators are: Not, And, Or, Equals, Le, Lt, Constant, Fluent."
            )
