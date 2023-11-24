# Copyright 2022, 2023 DFKI GmbH
# Copyright 2023 LAAS-CNRS
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
#
# Authors:
# - Alexander Sung, DFKI
# - Sebastian Stock, DFKI
# - Selvakumar H S, LAAS-CNRS
"""Bridge between application and planning domains"""

import itertools
import sys
import typing
from collections import OrderedDict
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

import networkx as nx
from unified_planning.engines import OptimalityGuarantee
from unified_planning.model import (
    DurativeAction,
    Fluent,
    InstantaneousAction,
    Object,
    Parameter,
    Problem,
    Type,
)
from unified_planning.model.metrics import MinimizeSequentialPlanLength
from unified_planning.plans import (
    ActionInstance,
    PartialOrderPlan,
    Plan,
    SequentialPlan,
    TimeTriggeredPlan,
)
from unified_planning.shortcuts import BoolType, IntType, OneshotPlanner, RealType, UserType

from up_esb.components import ExpressionManager
from up_esb.components.graph import plan_to_dependency_graph


class Bridge:
    """Generic bridge between application and planning domains"""

    def __init__(self) -> None:
        # Note: Map from type instead of str to recognize subclasses.
        self._fluents: Dict[str, Fluent] = {}
        self._fluent_functions: Dict[str, Callable[..., object]] = {}
        self._api_function_names: Set[str] = set()
        self._actions: Dict[str, InstantaneousAction] = {}
        self._api_actions: Dict[str, Callable[..., object]] = {}
        self._objects: Dict[str, Object] = {}
        self._api_objects: Dict[str, object] = {}

        self._int_bounds: Tuple[int, int] = (0, 100)
        self._real_bounds: Tuple[float, float] = (0, 100)
        self._types: Dict[type, Type] = {
            bool: BoolType(),
            int: IntType(lower_bound=self._int_bounds[0], upper_bound=self._int_bounds[1]),
            float: RealType(lower_bound=self._real_bounds[0], upper_bound=self._real_bounds[1]),
        }

    @property
    def int_bounds(self) -> Tuple[int, int]:
        """Return bounds for int type."""
        return self._int_bounds

    @int_bounds.setter
    def int_bounds(self, bounds: Tuple[int, int]) -> None:
        """Set bounds for int type."""
        self._int_bounds = bounds
        assert bounds[0] <= bounds[1], f"Invalid bounds {bounds}!"
        self._types[int] = IntType(lower_bound=bounds[0], upper_bound=bounds[1])

    @property
    def real_bounds(self) -> Tuple[float, float]:
        """Return bounds for real type."""
        return self._real_bounds

    @real_bounds.setter
    def real_bounds(self, bounds: Tuple[float, float]) -> None:
        """Set bounds for real type."""
        self._real_bounds = bounds
        assert bounds[0] <= bounds[1], f"Invalid bounds {bounds}!"
        self._types[float] = RealType(lower_bound=bounds[0], upper_bound=bounds[1])

    @property
    def objects(self) -> Dict[str, Object]:
        """Return all UP objects."""
        return self._objects

    def create_types(self, api_types: Iterable[type]) -> None:
        """Create UP user types based on api_types."""
        for api_type in api_types:
            assert api_type not in self._types, f"Type {api_type} already created!"
            self._types[api_type] = UserType(api_type.__name__)

    def get_type(self, api_type: type) -> Type:
        """Return UP user type corresponding to api_type or its superclasses."""
        for check_type, user_type in self._types.items():
            if issubclass(api_type, check_type):
                return user_type

        raise ValueError(f"No corresponding UserType defined for {api_type}!")

    def get_object_type(self, api_object: object) -> Type:
        """Return UP user type corresponding to api_object's type."""
        for api_type, user_type in self._types.items():
            if isinstance(api_object, api_type):
                return user_type

        raise ValueError(f"No corresponding UserType defined for {api_object}!")

    def get_name_and_signature(
        self, function: Callable[..., object]
    ) -> Tuple[str, Dict[str, type]]:
        """
        Return name and API signature of function. If function is a class method and a
         corresponding UP representation exists for its defining class, implicitly return the later
         as first parameter of the signature.
        """
        signature: Dict[str, Type] = OrderedDict()
        if hasattr(function, "__qualname__") and "." in function.__qualname__:
            # Determine defining class of function.
            api_type = sys.modules[function.__module__]
            for name in function.__qualname__.split(".")[:-1]:
                # Note: Use "context" to resolve potential relay to Python source file.
                api_type = (
                    api_type.__dict__["context"][name]
                    if "context" in api_type.__dict__.keys()
                    else api_type.__dict__[name]
                )
            assert isinstance(api_type, type), f"{api_type} is not a type!"
            # If defining class of function is a subclass of any class for which a UP representation
            #  has been created, add it as first parameter of signature.
            if any(issubclass(api_type, check_api_type) for check_api_type in self._types):
                signature[function.__qualname__.rsplit(".", maxsplit=1)[0]] = api_type
        for parameter_name, api_type in function.__annotations__.items():
            signature[parameter_name] = api_type
        return function.__name__, signature

    def create_fluent(
        self,
        name: str,
        result_api_type: Optional[type] = None,
        signature: Optional[Dict[str, type]] = None,
        _callable: Optional[Callable[..., object]] = None,
        **kwargs: type,
    ) -> Fluent:
        """
        Create UP fluent with name using the UP types corresponding to the api_types in signature
         updated by kwargs. By default, use BoolType() as result_api_type if it is not provided
         and no return type is given in signature.
        Optionally, provide a callable which calculates the fluent's values for problem
         initialization. Otherwise, you must set it later.
        """
        assert name not in self._fluents, f"Fluent {name} already exists!"
        self._fluents[name] = Fluent(
            name,
            self.get_type(result_api_type)
            if result_api_type
            else self.get_type(signature["return"])
            if signature and "return" in signature.keys()
            else BoolType(),
            OrderedDict(
                (parameter_name, self.get_type(api_type))
                for parameter_name, api_type in (
                    dict(signature, **kwargs) if signature else kwargs
                ).items()
                if parameter_name != "return"
            ),
        )
        if _callable:
            self._fluent_functions[name] = _callable
            self.set_if_api_signature(name, dict(signature, **kwargs) if signature else kwargs)
        return self._fluents[name]

    def create_fluent_from_function(
        self, function: Callable[..., object], set_callable: bool = True
    ) -> Fluent:
        """
        Create UP fluent based on function, which calculates the fluent's values
         for problem initialization. If function is a class method and a corresponding UP
         representation exists for its defining class, implicitly use the later as first parameter.
        If set_callable is True, also set function as the fluent function's callable. Otherwise,
         you must set it later.
        """
        name, signature = self.get_name_and_signature(function)
        return self.create_fluent(
            name, signature=signature, _callable=function if set_callable else None
        )

    def set_fluent_functions(self, functions: Iterable[Callable[..., object]]) -> None:
        """Set fluent functions. Their __name__ must match with fluent creation."""
        for function in functions:
            name = function.__name__
            assert name not in self._fluent_functions, f"Fluent {name} already set!"
            self._fluent_functions[name] = function
            self.set_if_api_signature(name, function.__annotations__)

    def set_if_api_signature(self, name: str, signature: Dict[str, type]) -> None:
        """
        Determine and store if any parameter in signature of function with name
        has a type in the application domain.
        """
        if any(
            not issubclass(parameter_type, Object)
            for parameter_name, parameter_type in signature.items()
            if parameter_name != "return"
        ):
            self._api_function_names.add(name)

    def create_action(
        self,
        name: str,
        signature: Optional[Dict[str, type]] = None,
        _callable: Optional[Callable[..., object]] = None,
        **kwargs: type,
    ) -> Tuple[InstantaneousAction, List[Parameter]]:
        """
        Create UP InstantaneousAction with name based on signature updated by kwargs.
         Optionally, provide a callable for action execution. Otherwise, you must set it later.
        Return the InstantaneousAction with its parameters for convenient definition of its
         preconditions and effects in the UP domain.
        """
        assert name not in self._actions, f"Action {name} already exists!"
        # Combine signature with kwargs.
        if signature:
            kwargs = dict(signature, **kwargs)
        duration = kwargs.get("duration")
        # Use signature's types, without its return type and the duration parameter.
        parameters = OrderedDict(
            (parameter_name, self.get_type(api_type))
            for parameter_name, api_type in kwargs.items()
            if parameter_name not in {"return", "duration"}
        )
        if duration is not None:
            action = DurativeAction(name, parameters)
            action.set_fixed_duration(duration)
        else:
            action = InstantaneousAction(name, parameters)
        self._actions[name] = action
        if _callable:
            self._api_actions[name] = _callable
        return action, action.parameters

    def create_action_from_function(
        self, function: Callable[..., object], set_callable: bool = True
    ) -> Tuple[InstantaneousAction, List[Parameter]]:
        """
        Create UP InstantaneousAction based on function. If function is a class method and a
         corresponding UP representation exists for its defining class, implicitly use the later
         as first action parameter.
        If set_callable is True, also set function as the executable action's callable. Otherwise,
         you must set it later.
        Return the InstantaneousAction with its parameters for convenient definition of its
         preconditions and effects in the UP domain.
        """
        return self.create_action(
            *self.get_name_and_signature(function), function if set_callable else None
        )

    def set_api_actions(self, functions: Iterable[Callable[..., object]]) -> None:
        """
        Set API functions as executable actions. Their __name__ must match with action creation.
        """
        for function in functions:
            name = function.__name__
            assert name not in self._api_actions, f"Action {name} already exists!"
            self._api_actions[name] = function

    def get_executable_action(
        self, action: ActionInstance
    ) -> Tuple[Callable[..., object], List[object]]:
        """Return API callable and parameters corresponding to the given action."""
        if action.action.name not in self._api_actions:
            raise ValueError(f"No corresponding action defined for {action}!")

        return self._api_actions[action.action.name], [
            self._api_objects[parameter.object().name] for parameter in action.actual_parameters
        ]

    def create_object(self, name: str, api_object: object) -> Object:
        """Create UP object with name based on api_object."""
        assert name not in self._objects, f"Object {name} already exists!"
        self._objects[name] = Object(name, self.get_object_type(api_object))
        self._api_objects[name] = api_object
        return self._objects[name]

    def create_objects(
        self, api_objects: Optional[Dict[str, object]] = None, **kwargs: object
    ) -> List[Object]:
        """Create UP objects based on api_objects and kwargs."""
        return [
            self.create_object(name, api_object)
            for name, api_object in (dict(api_objects, **kwargs) if api_objects else kwargs).items()
        ]

    def create_enum_objects(self, enum: typing.Type[Enum]) -> List[Object]:
        """Create UP objects based on enum."""
        return [self.create_object(member.name, member) for member in enum]

    def get_object(self, api_object: object) -> Object:
        """Return UP object corresponding to api_object if it exists, else api_object itself."""
        name = getattr(api_object, "name") if hasattr(api_object, "name") else str(api_object)
        return self._objects[name] if name in self._objects else api_object

    def define_problem(
        self,
        fluents: Optional[Iterable[Fluent]] = None,
        actions: Optional[Iterable[InstantaneousAction]] = None,
        objects: Optional[Iterable[Object]] = None,
    ) -> Problem:
        """Define UP problem by its (potential subsets of) fluents, actions, and objects."""
        # Note: Reset goals and initial values to reuse this problem.
        problem = Problem()
        problem.add_fluents(self._fluents.values() if fluents is None else fluents)
        problem.add_actions(self._actions.values() if actions is None else actions)
        problem.add_objects(self._objects.values() if objects is None else objects)
        return problem

    def set_initial_values(self, problem: Problem) -> None:
        """
        Set all initial values using the functions corresponding to this problem's fluents.

        Note: This will update all values for all parameter combinations for each fluent.
         Its intended usage is to update the planning problem by the current system state
         with one single function call.
        """
        type_objects: Dict[type, List[Object]] = {}
        # Collect objects in problem for all parameters of all fluents.
        for fluent in problem.fluents:
            for parameter in fluent.signature:
                # Avoid redundancy.
                if parameter.type not in type_objects:
                    type_objects[parameter.type] = list(problem.objects(parameter.type))
        for fluent in problem.fluents:
            # Loop through all parameter value combinations.
            for parameters in itertools.product(
                *[type_objects[parameter.type] for parameter in fluent.signature]
            ):
                # Use the fluent function to calculate the initial values.
                value = (
                    self.get_object(
                        self._fluent_functions[fluent.name](
                            *[self._api_objects[parameter.name] for parameter in parameters]
                        )
                    )
                    if fluent.name in self._api_function_names
                    else self._fluent_functions[fluent.name](*parameters)
                )
                problem.set_initial_value(fluent(*parameters), value)

    @staticmethod
    def solve(
        problem: Problem, planner_name: Optional[str] = None, optimize_with_default_metric=True
    ) -> Optional[Plan]:
        """Solve planning problem and return a UP Plan, if possible."""
        if optimize_with_default_metric:
            if not any(
                isinstance(metric, MinimizeSequentialPlanLength)
                for metric in problem.quality_metrics
            ):
                problem.add_quality_metric(MinimizeSequentialPlanLength())
            planner = OneshotPlanner(
                problem_kind=problem.kind, optimality_guarantee=OptimalityGuarantee.SOLVED_OPTIMALLY
            )
        else:
            planner = OneshotPlanner(name=planner_name, problem_kind=problem.kind)
        return planner.solve(problem).plan

    def get_executable_graph(
        self, plan: Union[SequentialPlan, TimeTriggeredPlan, PartialOrderPlan]
    ) -> nx.DiGraph:
        """Get executable graph from plan."""
        executable_graph = plan_to_dependency_graph(plan)

        # Add elements and functions as a context for the executable graph
        context = {}
        context.update(self._api_objects)
        context.update(self._api_actions)
        context.update(self._fluent_functions)

        for node in executable_graph.nodes(data=True):
            node_id = node[0]
            action = node[1]["action"]
            action_parameters = node[1]["parameters"]
            if action in ["start", "end"]:
                continue  # TODO: Handle start and end nodes.
            if action not in self._api_actions:
                raise ValueError(f"Action {action} not defined in API!")

            # Parameters
            parameters = {}
            for param, actual_param in action_parameters.items():
                actual_param = str(actual_param)
                if actual_param not in self._api_objects:
                    raise ValueError(f"Object {actual_param} not defined in API!")
                parameters[param] = self._api_objects[str(actual_param)]
            executable_graph.nodes[node_id]["parameters"] = parameters

            exp_manager = ExpressionManager()

            # Action Preconditions
            executable_preconditions: Dict[str, List[Callable]] = {}
            for interval, preconditions in executable_graph.nodes[node_id]["preconditions"].items():
                # Interval is start for instantaneous actions, and (start, end) for timed actions.
                executable_preconditions[interval] = (
                    []
                    if interval not in executable_preconditions
                    else executable_preconditions[interval]
                )

                for precondition in preconditions:
                    executable_preconditions[interval].append(
                        exp_manager.convert(precondition, parameters=action_parameters)
                    )
            executable_graph.nodes[node_id]["preconditions"] = executable_preconditions

            # Action Effects
            executable_effects: Dict[str, List[Tuple[Callable, typing.Any]]] = {}
            for interval, effects in executable_graph.nodes[node_id]["postconditions"].items():
                executable_effects[interval] = (
                    [] if interval not in executable_effects else executable_effects[interval]
                )

                for effect in effects:
                    executable_effects[interval].append(
                        (
                            exp_manager.convert(effect.fluent, parameters=action_parameters),
                            exp_manager.convert(effect.value, parameters=action_parameters),
                        )
                    )
            executable_graph.nodes[node_id]["postconditions"] = executable_effects

            # Finally setup execution context to the nodes
            executable_graph.nodes[node_id]["context"] = context

        return executable_graph
