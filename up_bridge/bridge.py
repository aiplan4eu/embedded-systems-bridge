# Copyright 2022 Alexander Sung, DFKI
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

import itertools
import sys
import typing
from collections import OrderedDict
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from unified_planning.engines import OptimalityGuarantee
from unified_planning.model import (Fluent, InstantaneousAction, Object,
                                    Parameter, Problem, Type)
from unified_planning.plans import ActionInstance
from unified_planning.shortcuts import (BoolType, IntType, OneshotPlanner,
                                        RealType, UserType)


class Bridge:
    """Generic bridge between application and planning domains"""

    def __init__(self) -> None:
        # Note: Map from type instead of str to recognize subclasses.
        self._types: Dict[type, Type] = {
            bool: BoolType(),
            int: IntType(),
            float: RealType(),
        }
        self._fluents: Dict[str, Fluent] = {}
        self._fluent_functions: Dict[str, Callable[..., object]] = {}
        self._actions: Dict[str, InstantaneousAction] = {}
        self._api_actions: Dict[str, Callable[..., object]] = {}
        self._objects: Dict[str, Object] = {}
        self._api_objects: Dict[str, object] = {}

    @property
    def objects(self) -> Dict[str, Object]:
        return self._objects

    def create_types(self, api_types: Iterable[type]) -> None:
        """Create UP user types based on api_types."""
        for api_type in api_types:
            assert api_type not in self._types.keys()
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

    def create_fluent(
        self,
        name: str,
        result_api_type: Optional[type] = None,
        signature: Optional[Dict[str, type]] = None,
        callable: Optional[Callable[..., object]] = None,
        **kwargs: type,
    ) -> Fluent:
        """
        Create UP fluent with name using the UP types corresponding to the api_types in signature
         updated by kwargs. By default, use BoolType() as result_api_type.
        Optionally, provide a callable which calculates the fluent's values in the application
         domain for problem initialization. Otherwise, you must set it separately.
        """
        assert name not in self._fluents.keys()
        self._fluents[name] = Fluent(
            name,
            self.get_type(result_api_type) if result_api_type else BoolType(),
            OrderedDict(
                (parameter_name, self.get_type(api_type))
                for parameter_name, api_type in (dict(signature, **kwargs) if signature else kwargs).items()
            ),
        )
        if callable:
            self._fluent_functions[name] = callable
        return self._fluents[name]

    def create_fluent_from_function(self, function: Callable[..., object]) -> Fluent:
        """
        Create UP fluent based on function, which calculates the fluent's values
         in the application domain for problem initialization.
        """
        annotations = function.__annotations__
        return self.create_fluent(
            function.__name__,
            annotations['return'],
            OrderedDict((parameter_name, api_type) for parameter_name, api_type in list(annotations.items())
                if parameter_name != 'return'),
            callable=function,
        )

    def set_fluent_functions(self, functions: Iterable[Callable[..., object]]) -> None:
        """Set functions as fluent functions in the application domain. Their __name__ must match with fluent creation."""
        for function in functions:
            name = function.__name__
            assert name not in self._fluent_functions.keys()
            self._fluent_functions[name] = function

    def create_action(
        self,
        name: str,
        signature: Optional[Dict[str, type]] = None,
        callable: Optional[Callable[..., object]] = None,
        **kwargs: type,
    ) -> Tuple[InstantaneousAction, List[Parameter]]:
        """
        Create UP InstantaneousAction with name based on signature updated by kwargs.
         Optionally, provide a callable for action execution. Otherwise, you must set it separately.
        Return the InstantaneousAction with its parameters for convenient definition of its
         preconditions and effects in the UP domain.
        """
        assert name not in self._actions.keys()
        action = InstantaneousAction(
            name,
            # Use signature's types, without its return type.
            OrderedDict(
                (parameter_name, self.get_type(api_type))
                for parameter_name, api_type in list((dict(signature, **kwargs) if signature else kwargs).items())
                    if parameter_name != 'return'
            ),
        )
        self._actions[name] = action
        if callable:
            self._api_actions[name] = callable
        return action, action.parameters

    def create_action_from_function(
        self, function: Callable[..., object], set_callable: bool=True
    ) -> Tuple[InstantaneousAction, List[Parameter]]:
        """
        Create UP InstantaneousAction based on function.
        By default, also set function as the action's callable. To avoid this, set_callable=False.
        Return the InstantaneousAction with its parameters for convenient definition of its
         preconditions and effects.
        """
        return self.create_action(function.__name__, function.__annotations__,
            callable=function if set_callable else None)

    def get_name_and_signature(self, method: Callable[..., object]) -> Tuple[str, Dict[str, type]]:
        """
        Return name and API signature from class method. Implicitly return its defining class as
         first parameter if it exists.
        """
        signature: Dict[str, Type] = OrderedDict()
        if hasattr(method, '__qualname__') and '.' in method.__qualname__:
            # Add defining class of method to parameters.
            namespace = sys.modules[method.__module__]
            for name in method.__qualname__.split('.')[:-1]:
                # Note: Use "context" to resolve potential relay to Python source file.
                namespace = (
                    namespace.__dict__["context"][name]
                    if "context" in namespace.__dict__.keys()
                    else namespace.__dict__[name]
                )
            assert isinstance(namespace, type)
            signature[method.__qualname__.rsplit('.', maxsplit=1)[0]] = namespace
        for parameter_name, api_type in method.__annotations__.items():
            signature[parameter_name] = api_type
        return method.__name__, signature

    def set_api_actions(self, functions: Iterable[Callable[..., object]]) -> None:
        """
        Set API functions as executable actions. Their __name__ must match with action creation.
        """
        for function in functions:
            name = function.__name__
            assert name not in self._api_actions.keys()
            self._api_actions[name] = function

    def get_executable_action(self, action: ActionInstance) -> Tuple[Callable[..., object], List[object]]:
        """Return API callable and parameters corresponding to the given action."""
        if action.action.name not in self._api_actions.keys():
            raise ValueError(f"No corresponding action defined for {action}!")

        return (
            self._api_actions[action.action.name],
            [
                self._api_objects[parameter.object().name]
                for parameter in action.actual_parameters
            ],
        )

    def create_object(self, name: str, api_object: object) -> Object:
        """Create UP object with name based on api_object."""
        assert name not in self._objects.keys()
        self._objects[name] = Object(name, self.get_object_type(api_object))
        self._api_objects[name] = api_object
        return self._objects[name]

    def create_objects(
        self, api_objects: Optional[Dict[str, object]] = None, **kwargs: object
    ) -> List[Object]:
        """Create UP objects based on api_objects and kwargs."""
        return [
            self.create_object(name, api_object)
            for name, api_object in (
                dict(api_objects, **kwargs) if api_objects else kwargs
            ).items()
        ]

    def create_enum_objects(self, enum: typing.Type[Enum]) -> List[Object]:
        """Create UP objects based on enum."""
        return [self.create_object(member.name, member) for member in enum]

    def get_object(self, api_object: object) -> Object:
        """Return UP object corresponding to api_object if it exists, else api_object itself."""
        name = (
            getattr(api_object, "name")
            if hasattr(api_object, "name")
            else str(api_object)
        )
        return self._objects[name] if name in self._objects.keys() else api_object

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
        """Set all initial values using the functions corresponding to this problem's fluents."""
        type_objects: Dict[type, List[Object]] = {}
        # Collect objects in problem for all parameters of all fluents.
        for fluent in problem.fluents:
            for parameter in fluent.signature:
                # Avoid redundancy.
                if parameter.type not in type_objects.keys():
                    type_objects[parameter.type] = list(problem.objects(parameter.type))
        for fluent in problem.fluents:
            # Loop through all parameter value combinations.
            for parameters in itertools.product(*[type_objects[parameter.type] for parameter in fluent.signature]):
                # Use the fluent function to calculate the initial values.
                value = self.get_object(self._fluent_functions[fluent.name](*[self._api_objects[parameter.name] for parameter in parameters]))
                problem.set_initial_value(fluent(*parameters), value)

    def solve(self, problem: Problem, planner_name: Optional[str]=None) -> Optional[List[ActionInstance]]:
        """Solve planning problem and return list of UP actions."""
        result = OneshotPlanner(
            name=planner_name,
            problem_kind=problem.kind,
            optimality_guarantee=OptimalityGuarantee.SOLVED_OPTIMALLY,
        ).solve(problem)
        return result.plan.actions if result.plan else None
