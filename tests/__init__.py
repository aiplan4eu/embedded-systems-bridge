"""This module contains the example plans that are used for testing purposes.""" ""
from typing import List, Union

from unified_planning.plans import SequentialPlan, TimeTriggeredPlan
from unified_planning.shortcuts import OperatorKind, get_environment
from unified_planning.test.examples import get_example_problems

available_plans = [
    "basic",
    "basic_conditional",
    "basic_oversubscription",
    "complex_conditional",
    "basic_without_negative_preconditions",
    "basic_nested_conjunctions",
    "basic_exists",
    "basic_forall",
    "temporal_conditional",
    "basic_with_costs",
    "counter",
    "counter_to_50",
    "basic_with_object_constant",
    "robot",
    "robot_fluent_of_user_type",
    "robot_no_negative_preconditions",
    "robot_decrease",
    "robot_loader",
    "robot_loader_mod",
    "robot_loader_adv",
    "robot_locations_connected",
    "robot_locations_visited",
    "charge_discharge",
    "matchcellar",
    "timed_connected_locations",
    "hierarchical_blocks_world",
    "robot_with_static_fluents_duration",
    "travel",
    "robot_real_constants",
    "robot_int_battery",
    "robot_fluent_of_user_type_with_int_id",
    "robot_locations_connected_without_battery",
    "hierarchical_blocks_world_exists",
    "hierarchical_blocks_world_object_as_root",
    "hierarchical_blocks_world_with_object",
    "travel_with_consumptions",
    "matchcellar_static_duration",
    "locations_connected_visited_oversubscription",
    "locations_connected_cost_minimize",
    "htn-go",
    "htn-go-temporal",
]

# TODO: The following plans are not supported yet
# MINUS, EXISTS, FORALL
# INCREASED_EFFECT, DECREASED_EFFECT
PLANS_WITH_UNSUPPORTED_OPERATORS = [
    "basic_nested_conjunctions",
    "basic_exists",
    "basic_forall",
    "counter",
    "robot",
    "robot_locations_connected",
    "charge_discharge",
    "timed_connected_locations",
    "robot_real_constants",
    "robot_int_battery",
    "robot_locations_connected_without_battery",
    "travel_with_consumptions",
    "travel",
]

# TODO: Hierarchical plans are not supported yet
UNSUPPORTED_PLANS = [
    "htn-go",
    "htn-go-temporal",
]

available_plans = list(set(available_plans) - set(PLANS_WITH_UNSUPPORTED_OPERATORS))
available_plans = list(set(available_plans) - set(UNSUPPORTED_PLANS))


def get_example_plans() -> Union[List[SequentialPlan], List[TimeTriggeredPlan]]:
    """Gain access to the example plans."""
    example_problems = get_example_problems()

    plans = {}
    for element in example_problems:
        if element in available_plans:
            plans[element] = example_problems[element].plan

    return plans


class ContextManager:
    """Convert plan to executable functions for testing purposes."""

    objects_context = {}
    fluents_context = {}
    actions_context = {}
    plan: Union[SequentialPlan, TimeTriggeredPlan]

    @classmethod
    def get_actions_context(cls, returns: bool = True):
        """Get the actions context."""

        if isinstance(cls.plan, TimeTriggeredPlan):
            return cls._translate_context(cls.plan.timed_actions, returns=returns)
        else:
            return cls._translate_context(cls.plan.actions, returns=returns)

    @classmethod
    def get_objects_context(cls):
        """Get the objects context."""

        actions = []
        if isinstance(cls.plan, TimeTriggeredPlan):
            actions = cls.plan.timed_actions
            actions = [action[1] for action in actions]
        else:
            actions = cls.plan.actions

        for action in actions:
            for param in action.actual_parameters:
                cls.objects_context[str(param)] = cls._generate_class(
                    param, str(param), returns=True
                )

        return cls.objects_context

    @classmethod
    def get_fluents_context(cls):
        """Get the fluents context."""
        manager = get_environment().expression_manager

        conditions = []
        if isinstance(cls.plan, TimeTriggeredPlan):
            for action in cls.plan.timed_actions:
                for preconditions in action[1].action.conditions.values():
                    for condition in preconditions:
                        conditions.append(condition)
                for effects in action[1].action.effects.values():
                    for effect in effects:
                        conditions.append(effect.fluent)
        else:
            for action in cls.plan.actions:
                conditions.extend(action.action.preconditions)
                conditions.extend([effect.fluent for effect in action.action.effects])

        for condition in conditions:
            expression = manager.auto_promote(condition)
            # TODO: Refactor this
            for exp in expression:
                if exp.node_type is not OperatorKind.FLUENT_EXP:
                    args = exp.args
                    for arg in args:
                        if arg.node_type is OperatorKind.FLUENT_EXP:
                            arg_name = str(arg).split("(", maxsplit=1)[0]
                            cls.fluents_context[arg_name] = cls._generate_function(
                                arg, arg_name, returns=True
                            )
                else:
                    exp_name = str(exp).split("(", maxsplit=1)[0]
                    cls.fluents_context[exp_name] = cls._generate_function(
                        exp, exp_name, returns=True
                    )

        return cls.fluents_context

    @classmethod
    def _translate_context(cls, actions, returns: bool = True):
        """Translate the actions context."""
        for action in actions:
            action_name = ""
            if isinstance(cls.plan, TimeTriggeredPlan):
                action_name = action[1].action.name
            else:
                action_name = action.action.name
            func = cls._generate_function(action, action_name, returns=returns)
            setattr(cls, action_name, func)
            cls.actions_context[action_name] = func

        return cls.actions_context

    @classmethod
    def _generate_function(cls, expression, expression_name, returns: bool = True):
        def function(*args, **kwargs):
            return returns

        function.__name__ = expression_name

        return function

    @classmethod
    def _generate_class(cls, expression, expression_name, returns: bool = True):
        class GeneratedClass:
            """Generated class."""

            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def __call__(self, *args, **kwargs):
                return returns

        GeneratedClass.__name__ = expression_name

        return GeneratedClass
