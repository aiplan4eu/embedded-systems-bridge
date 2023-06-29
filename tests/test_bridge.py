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

from typing import Callable, Dict

import pytest
from unified_planning.shortcuts import Equals, Not, OneshotPlanner

from tests import ContextManager, get_example_plans
from up_esb.bridge import Bridge
from up_esb.components import ActionDefinition

# pylint: disable=all
############################################################################################################
######################################### ESSENTIALS #######################################################
############################################################################################################


class Location:
    def __init__(self, name, x, y, z, yaw):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw

    def __repr__(self) -> str:
        return self.name


class Area:
    def __init__(self, name, xmin, xmax, ymin, ymax, z, yaw):
        self.name = name
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.z = z
        self.yaw = yaw

    def __repr__(self) -> str:
        return self.name


class Fluents:
    @staticmethod
    def robot_at(location: Location) -> bool:
        return True

    @staticmethod
    def verify_station_at(location: Location) -> bool:
        return True

    @staticmethod
    def is_surveyed(area: Area) -> bool:
        return True

    @staticmethod
    def is_location_surveyed(area: Area, location: Location) -> bool:
        return True

    @staticmethod
    def is_within_area(area: Area, location: Location) -> bool:
        return True


class Move(ActionDefinition):
    def __call__(self, area: Area, l_from: Location, l_to: Location) -> bool:
        return True


class CapturePhoto(ActionDefinition):
    def __call__(self, area: Area, location: Location) -> bool:
        return True


class Survey(ActionDefinition):
    def __call__(self, area: Area) -> bool:
        return True


class GatherInfo(ActionDefinition):
    def __call__(self, area: Area, location: Location) -> bool:
        return True


class Actions:
    @staticmethod
    def move(area: Area, l_from: Location, l_to: Location) -> bool:
        return True

    @staticmethod
    def capture_photo(area: Area, location: Location) -> bool:
        return True

    @staticmethod
    def survey(area: Area) -> bool:
        return True

    @staticmethod
    def gather_info(area: Area, location: Location) -> bool:
        return True


class Application:
    # Fluents
    robot_at = Fluents.robot_at
    verify_station_at = Fluents.verify_station_at
    is_surveyed = Fluents.is_surveyed
    is_location_surveyed = Fluents.is_location_surveyed
    is_within_area = Fluents.is_within_area

    # Objects
    l1 = Location("l1", x=3.5, y=3.5, z=1.0, yaw=0.0)
    l2 = Location("l2", x=-2.5, y=1.5, z=1.0, yaw=0.0)
    l3 = Location("l3", x=1.5, y=-2.5, z=1.0, yaw=0.0)
    l4 = Location("l4", x=-1.5, y=-3.5, z=1.0, yaw=0.0)
    home = Location("home", x=0.0, y=0.0, z=1.0, yaw=0.0)
    area = Area("area", xmin=-4.0, xmax=4.0, ymin=-4.0, ymax=4.0, z=3.0, yaw=0.0)

    # Actions
    move = Move
    capture_photo = CapturePhoto
    survey = Survey
    gather_info = GatherInfo


############################################################################################################
######################################### PROBLEM ##########################################################
############################################################################################################


class ProblemDeclaration(Application):
    def get_parameterizer(self):
        """Get pytest parameterizer for test case."""
        # TODO: Add generatives
        self.fluent_declarations = [self.create_fluents_from_functions]
        self.object_declarations = [self.create_objects]
        self.action_declarations = [
            self.create_action_kwargs,
            self.create_action_without_execution,
            self.create_actions_from_functions,
            self.create_actions_from_signatures,
        ]

    def create_fluents_from_functions(self, bridge: Bridge):
        f_robot_at = bridge.create_fluent_from_function(ProblemDeclaration.robot_at)
        f_verified_station_at = bridge.create_fluent_from_function(
            ProblemDeclaration.verify_station_at
        )
        f_is_surveyed = bridge.create_fluent_from_function(ProblemDeclaration.is_surveyed)
        f_is_location_surveyed = bridge.create_fluent_from_function(
            ProblemDeclaration.is_location_surveyed
        )
        f_is_within_area = bridge.create_fluent_from_function(ProblemDeclaration.is_within_area)

        return {
            "f_robot_at": f_robot_at,
            "f_verified_station_at": f_verified_station_at,
            "f_is_surveyed": f_is_surveyed,
            "f_is_location_surveyed": f_is_location_surveyed,
            "f_is_within_area": f_is_within_area,
        }

    def create_action_kwargs(self, bridge: Bridge, fluents):
        """Actions with executable function."""
        move, (a, l_from, l_to) = bridge.create_action(
            "Move", _callable=self.move, area=Area, l_from=Location, l_to=Location
        )
        move.add_precondition(fluents["f_is_surveyed"](a))
        move.add_precondition(fluents["f_is_location_surveyed"](a, l_to))
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(fluents["f_robot_at"](l_from))
        move.add_precondition(Not(fluents["f_robot_at"](l_to)))
        move.add_effect(fluents["f_robot_at"](l_from), False)
        move.add_effect(fluents["f_robot_at"](l_to), True)

        capture_photo, (a, l) = bridge.create_action(
            "CapturePhoto", _callable=self.capture_photo, area=Area, l=Location
        )
        capture_photo.add_precondition(fluents["f_is_surveyed"](a))
        capture_photo.add_precondition(fluents["f_is_location_surveyed"](a, l))
        capture_photo.add_precondition(fluents["f_robot_at"](l))
        capture_photo.add_effect(fluents["f_verified_station_at"](l), True)
        capture_photo.add_effect(
            fluents["f_robot_at"](l), True
        )  # Since using instantaneous actions

        survey, [a] = bridge.create_action("Survey", _callable=self.survey, area=Area)
        survey.add_precondition(Not(fluents["f_is_surveyed"](a)))
        survey.add_effect(fluents["f_is_surveyed"](a), True)

        gather_info, (a, l) = bridge.create_action(
            "GatherInfo", _callable=self.gather_info, area=Area, l=Location
        )
        gather_info.add_precondition(fluents["f_is_surveyed"](a))
        gather_info.add_precondition(fluents["f_is_within_area"](a, l))
        gather_info.add_effect(fluents["f_is_location_surveyed"](a, l), True)

    def create_action_without_execution(self, bridge: Bridge, fluents):
        """Actions without execution."""
        move, (a, l_from, l_to) = bridge.create_action(
            "Move", area=Area, l_from=Location, l_to=Location
        )
        move.add_precondition(fluents["f_is_surveyed"](a))
        move.add_precondition(fluents["f_is_location_surveyed"](a, l_to))
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(fluents["f_robot_at"](l_from))
        move.add_precondition(Not(fluents["f_robot_at"](l_to)))
        move.add_effect(fluents["f_robot_at"](l_from), False)
        move.add_effect(fluents["f_robot_at"](l_to), True)

        capture_photo, (a, l) = bridge.create_action("CapturePhoto", area=Area, l=Location)
        capture_photo.add_precondition(fluents["f_is_surveyed"](a))
        capture_photo.add_precondition(fluents["f_is_location_surveyed"](a, l))
        capture_photo.add_precondition(fluents["f_robot_at"](l))
        capture_photo.add_effect(fluents["f_verified_station_at"](l), True)
        capture_photo.add_effect(
            fluents["f_robot_at"](l), True
        )  # Since using instantaneous actions

        survey, [a] = bridge.create_action("Survey", area=Area)
        survey.add_precondition(Not(fluents["f_is_surveyed"](a)))
        survey.add_effect(fluents["f_is_surveyed"](a), True)

        gather_info, (a, l) = bridge.create_action("GatherInfo", area=Area, l=Location)
        gather_info.add_precondition(fluents["f_is_surveyed"](a))
        gather_info.add_precondition(fluents["f_is_within_area"](a, l))
        gather_info.add_effect(fluents["f_is_location_surveyed"](a, l), True)

    def create_actions_from_functions(self, bridge: Bridge, fluents):
        """Input type as class functions."""
        move, (a, l_from, l_to) = bridge.create_action_from_function(function=Actions.move)
        move.add_precondition(fluents["f_is_surveyed"](a))
        move.add_precondition(fluents["f_is_location_surveyed"](a, l_to))
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(fluents["f_robot_at"](l_from))
        move.add_precondition(Not(fluents["f_robot_at"](l_to)))
        move.add_effect(fluents["f_robot_at"](l_from), False)
        move.add_effect(fluents["f_robot_at"](l_to), True)

        capture_photo, (a, l) = bridge.create_action_from_function(function=Actions.capture_photo)
        capture_photo.add_precondition(fluents["f_is_surveyed"](a))
        capture_photo.add_precondition(fluents["f_is_location_surveyed"](a, l))
        capture_photo.add_precondition(fluents["f_robot_at"](l))
        capture_photo.add_effect(fluents["f_verified_station_at"](l), True)
        capture_photo.add_effect(
            fluents["f_robot_at"](l), True
        )  # Since using instantaneous actions

        survey, [a] = bridge.create_action_from_function(function=Actions.survey)
        survey.add_precondition(Not(fluents["f_is_surveyed"](a)))
        survey.add_effect(fluents["f_is_surveyed"](a), True)

        gather_info, (a, l) = bridge.create_action_from_function(function=Actions.gather_info)
        gather_info.add_precondition(fluents["f_is_surveyed"](a))
        gather_info.add_precondition(fluents["f_is_within_area"](a, l))
        gather_info.add_effect(fluents["f_is_location_surveyed"](a, l), True)

    def create_actions_from_methods(self, bridge: Bridge, fluents):
        """Input types as class methods."""
        move, (a, l_from, l_to) = bridge.create_action_from_method(method=self.move.__call__)
        move.add_precondition(fluents["f_is_surveyed"](a))
        move.add_precondition(fluents["f_is_location_surveyed"](a, l_to))
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(fluents["f_robot_at"](l_from))
        move.add_precondition(Not(fluents["f_robot_at"](l_to)))
        move.add_effect(fluents["f_robot_at"](l_from), False)
        move.add_effect(fluents["f_robot_at"](l_to), True)

        capture_photo, (a, l) = bridge.create_action_from_function(
            name="CapturePhoto", function=self.capture_photo.__call__
        )
        capture_photo.add_precondition(fluents["f_is_surveyed"](a))
        capture_photo.add_precondition(fluents["f_is_location_surveyed"](a, l))
        capture_photo.add_precondition(fluents["f_robot_at"](l))
        capture_photo.add_effect(fluents["f_verified_station_at"](l), True)
        capture_photo.add_effect(
            fluents["f_robot_at"](l), True
        )  # Since using instantaneous actions

        survey, [a] = bridge.create_action_from_function(
            name="Survey", function=self.survey.__call__
        )
        survey.add_precondition(Not(fluents["f_is_surveyed"](a)))
        survey.add_effect(fluents["f_is_surveyed"](a), True)

        gather_info, (a, l) = bridge.create_action_from_function(
            name="GatherInfo", function=self.gather_info.__call__
        )
        gather_info.add_precondition(fluents["f_is_surveyed"](a))
        gather_info.add_precondition(fluents["f_is_within_area"](a, l))
        gather_info.add_effect(fluents["f_is_location_surveyed"](a, l), True)

    def create_actions_from_signatures(self, bridge: Bridge, fluents):
        """Input type as dict."""
        move, (a, l_from, l_to) = bridge.create_action(
            "Move", signature={"area": Area, "l_from": Location, "l_to": Location}
        )
        move.add_precondition(fluents["f_is_surveyed"](a))
        move.add_precondition(fluents["f_is_location_surveyed"](a, l_to))
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(fluents["f_robot_at"](l_from))
        move.add_precondition(Not(fluents["f_robot_at"](l_to)))
        move.add_effect(fluents["f_robot_at"](l_from), False)
        move.add_effect(fluents["f_robot_at"](l_to), True)

        capture_photo, (a, l) = bridge.create_action(
            "CapturePhoto", signature={"area": Area, "l": Location}
        )
        capture_photo.add_precondition(fluents["f_is_surveyed"](a))
        capture_photo.add_precondition(fluents["f_is_location_surveyed"](a, l))
        capture_photo.add_precondition(fluents["f_robot_at"](l))
        capture_photo.add_effect(fluents["f_verified_station_at"](l), True)
        capture_photo.add_effect(
            fluents["f_robot_at"](l), True
        )  # Since using instantaneous actions

        survey, [a] = bridge.create_action("Survey", signature={"area": Area})
        survey.add_precondition(Not(fluents["f_is_surveyed"](a)))
        survey.add_effect(fluents["f_is_surveyed"](a), True)

        gather_info, (a, l) = bridge.create_action(
            "GatherInfo", signature={"area": Area, "l": Location}
        )
        gather_info.add_precondition(fluents["f_is_surveyed"](a))
        gather_info.add_precondition(fluents["f_is_within_area"](a, l))
        gather_info.add_effect(fluents["f_is_location_surveyed"](a, l), True)

    def create_objects(self, bridge: Bridge):
        o_l1 = bridge.create_object(str(self.l1), self.l1)
        o_l2 = bridge.create_object(str(self.l2), self.l2)
        o_l3 = bridge.create_object(str(self.l3), self.l3)
        o_l4 = bridge.create_object(str(self.l4), self.l4)
        o_home = bridge.create_object(str(self.home), self.home)
        o_area = bridge.create_object(str(self.area), self.area)

        return {
            "o_l1": o_l1,
            "o_l2": o_l2,
            "o_l3": o_l3,
            "o_l4": o_l4,
            "o_home": o_home,
            "o_area": o_area,
        }

    def declare_problem(
        self,
        bridge: Bridge,
        dec_fluents: Callable[[Bridge], Dict[str, Callable[..., object]]],
        dec_objects: Callable[[Bridge], Dict[str, Callable[..., object]]],
        dec_actions: Callable[
            [Bridge, Dict[str, Callable[..., object]]], Dict[str, Callable[..., object]]
        ],
    ):
        fluents = dec_fluents(bridge)
        objects = dec_objects(bridge)
        actions = dec_actions(bridge, fluents)

        problem = bridge.define_problem()
        problem.set_initial_value(fluents["f_robot_at"](objects["o_home"]), True)
        problem.set_initial_value(fluents["f_robot_at"](objects["o_l1"]), False)
        problem.set_initial_value(fluents["f_robot_at"](objects["o_l2"]), False)
        problem.set_initial_value(fluents["f_robot_at"](objects["o_l3"]), False)
        problem.set_initial_value(fluents["f_robot_at"](objects["o_l4"]), False)

        problem.set_initial_value(fluents["f_verified_station_at"](objects["o_home"]), True)
        problem.set_initial_value(fluents["f_verified_station_at"](objects["o_l1"]), False)
        problem.set_initial_value(fluents["f_verified_station_at"](objects["o_l2"]), False)
        problem.set_initial_value(fluents["f_verified_station_at"](objects["o_l3"]), False)
        problem.set_initial_value(fluents["f_verified_station_at"](objects["o_l4"]), False)

        problem.set_initial_value(fluents["f_is_surveyed"](objects["o_area"]), False)
        problem.set_initial_value(
            fluents["f_is_within_area"](objects["o_area"], objects["o_home"]), True
        )
        problem.set_initial_value(
            fluents["f_is_within_area"](objects["o_area"], objects["o_l1"]), True
        )
        problem.set_initial_value(
            fluents["f_is_within_area"](objects["o_area"], objects["o_l2"]), True
        )
        problem.set_initial_value(
            fluents["f_is_within_area"](objects["o_area"], objects["o_l3"]), True
        )
        problem.set_initial_value(
            fluents["f_is_within_area"](objects["o_area"], objects["o_l4"]), True
        )
        problem.set_initial_value(
            fluents["f_is_location_surveyed"](objects["o_area"], objects["o_home"]),
            True,
        )
        problem.set_initial_value(
            fluents["f_is_location_surveyed"](objects["o_area"], objects["o_l1"]), False
        )
        problem.set_initial_value(
            fluents["f_is_location_surveyed"](objects["o_area"], objects["o_l2"]), False
        )
        problem.set_initial_value(
            fluents["f_is_location_surveyed"](objects["o_area"], objects["o_l3"]), False
        )
        problem.set_initial_value(
            fluents["f_is_location_surveyed"](objects["o_area"], objects["o_l4"]), False
        )

        problem.add_goal(fluents["f_is_surveyed"](objects["o_area"]))
        problem.add_goal(fluents["f_is_location_surveyed"](objects["o_area"], objects["o_l1"]))
        problem.add_goal(fluents["f_is_location_surveyed"](objects["o_area"], objects["o_l2"]))
        problem.add_goal(fluents["f_is_location_surveyed"](objects["o_area"], objects["o_l3"]))
        problem.add_goal(fluents["f_is_location_surveyed"](objects["o_area"], objects["o_l4"]))
        problem.add_goal(fluents["f_verified_station_at"](objects["o_l1"]))
        problem.add_goal(fluents["f_verified_station_at"](objects["o_l2"]))
        problem.add_goal(fluents["f_verified_station_at"](objects["o_l3"]))
        problem.add_goal(fluents["f_verified_station_at"](objects["o_l4"]))
        problem.add_goal(fluents["f_robot_at"](objects["o_home"]))

        return problem


############################################################################################################
######################################### TEST CASE ########################################################
############################################################################################################
problem = ProblemDeclaration()
problem.get_parameterizer()


class TestBridge:
    def test_bridge_setup(self) -> None:
        self.bridge = Bridge()

    @pytest.mark.parametrize("dec_fluents", problem.fluent_declarations)
    def test_fluents(self, dec_fluents) -> None:
        bridge = Bridge()
        bridge.create_types([Location, Area])

        fluents = dec_fluents(bridge)

    @pytest.mark.parametrize("dec_objects", problem.object_declarations)
    def test_objects(self, dec_objects) -> None:
        bridge = Bridge()
        bridge.create_types([Location, Area])

        objects = dec_objects(bridge)

    @pytest.mark.parametrize("dec_fluents", problem.fluent_declarations)
    @pytest.mark.parametrize("dec_actions", problem.action_declarations)
    def test_actions(self, dec_fluents, dec_actions) -> None:
        bridge = Bridge()
        bridge.create_types([Location, Area])

        fluents = dec_fluents(bridge)
        actions = dec_actions(bridge, fluents)

    @pytest.mark.parametrize("dec_fluents", problem.fluent_declarations)
    @pytest.mark.parametrize("dec_objects", problem.object_declarations)
    @pytest.mark.parametrize("dec_actions", problem.action_declarations)
    @pytest.mark.parametrize("dec_problem", [problem.declare_problem])
    def test_problem(self, dec_fluents, dec_objects, dec_actions, dec_problem) -> None:
        bridge = Bridge()
        bridge.create_types([Location, Area])

        problem = dec_problem(bridge, dec_fluents, dec_objects, dec_actions)

        with OneshotPlanner(problem_kind=problem.kind) as planner:
            result = planner.solve(problem)

            if result is None:
                raise Exception("No solution found")

            print("*** Result ***")
            for action_instance in result.plan.actions:
                print(action_instance)
            print("*** End of result ***")


class TestBridgeExecutableGraph:
    @pytest.mark.parametrize("plan_name, plan", get_example_plans().items())
    def test_bridge_executable_graph(self, plan_name, plan):
        bridge = Bridge()
        ContextManager.plan = plan

        bridge._api_actions = ContextManager.get_actions_context()
        bridge._fluent_functions = ContextManager.get_fluents_context()
        bridge._api_objects = ContextManager.get_objects_context()

        bridge.get_executable_graph(plan)

    @pytest.mark.parametrize("plan_name, plan", get_example_plans().items())
    def test_bridge_executable_action(self, plan_name, plan):
        bridge = Bridge()
        ContextManager.plan = plan

        bridge._api_actions = ContextManager.get_actions_context()
        bridge._fluent_functions = ContextManager.get_fluents_context()
        bridge._api_objects = ContextManager.get_objects_context()

        graph = bridge.get_executable_graph(plan)

        for _, node in graph.nodes(data=True):
            if node["action"] in ["start", "end"]:
                continue

            node["context"][node["action"]](**node["parameters"])

    @pytest.mark.parametrize("plan_name, plan", get_example_plans().items())
    def test_bridge_executable_preconditions(self, plan_name, plan):
        bridge = Bridge()
        ContextManager.plan = plan

        bridge._api_actions = ContextManager.get_actions_context()
        bridge._fluent_functions = ContextManager.get_fluents_context()
        bridge._api_objects = ContextManager.get_objects_context()

        graph = bridge.get_executable_graph(plan)

        for _, node in graph.nodes(data=True):
            if node["action"] in ["start", "end"]:
                continue
            print(node["node_name"])

            import ast

            for preconditions in node["preconditions"].values():
                for expression in preconditions:
                    print(ast.dump(ast.parse(expression)))
                    eval(compile(expression, "<ast>", "eval"), node["context"])

    @pytest.mark.parametrize("plan_name, plan", get_example_plans().items())
    def test_bridge_executable_postconditions(self, plan_name, plan):
        bridge = Bridge()
        ContextManager.plan = plan

        bridge._api_actions = ContextManager.get_actions_context()
        bridge._fluent_functions = ContextManager.get_fluents_context()
        bridge._api_objects = ContextManager.get_objects_context()

        graph = bridge.get_executable_graph(plan)

        for _, node in graph.nodes(data=True):
            if node["action"] in ["start", "end"]:
                continue

            for post_conditions in node["postconditions"].values():
                for expression, _ in post_conditions:
                    eval(compile(expression, "<ast>", "eval"), node["context"])
