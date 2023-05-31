# Copyright 2022 Sebastian Stock, DFKI GmbH
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

import unittest

import unified_planning as up
from unified_planning.plans import SequentialPlan, TimeTriggeredPlan
from unified_planning.plans.partial_order_plan import PartialOrderPlan
from unified_planning.shortcuts import *  # pylint: disable=unused-wildcard-import
from unified_planning.test.examples import get_example_problems
from unified_planning.test.examples.realistic import get_example_problems

from up_esb.components.graph import plan_to_dependency_graph

# pylint: disable=all


class TestPartialOrderPlanGeneration(unittest.TestCase):
    def test_partial_order_plan_to_dependency_graph(self):
        example_problems = get_example_problems()
        problem, plan = example_problems["robot_fluent_of_user_type"]
        pop = plan.convert_to(PlanKind.PARTIAL_ORDER_PLAN, problem)
        assert isinstance(pop, PartialOrderPlan)
        dep_graph = plan_to_dependency_graph(pop)

        # Partial Orders are not ordered in the graph. Therefore, we can only check if all actions are in the graph
        actions = [str(action) for action in plan.actions] + ["start", "end"]
        for node in dep_graph.nodes(data=True):
            self.assertTrue(node[1]["node_name"] in actions)


class TestSequentialPlanTranslation(unittest.TestCase):
    def test_simple_translation(self):
        problems = get_example_problems()

        for _, plan in problems.values():
            if isinstance(plan, SequentialPlan):
                dep_graph = plan_to_dependency_graph(plan)
                actions = ["start"] + [str(action) for action in plan.actions] + ["end"]
                graph_actions = []
                for node in dep_graph.nodes(data=True):
                    graph_actions.append(node[1]["node_name"])

                # Check if all actions are ordered correctly
                self.assertEqual(actions, graph_actions)

    def test_special_cases(self):
        """Test translation for special cases."""
        Location = UserType("Location")
        robot_at = Fluent("robot_at", BoolType(), position=Location)
        battery_charge = Fluent("battery_charge", RealType(0, 100))
        move = InstantaneousAction("move", l_from=Location, l_to=Location)
        l_from = move.parameter("l_from")
        l_to = move.parameter("l_to")
        move.add_precondition(GE(battery_charge, 10))
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(robot_at(l_from))
        move.add_precondition(Not(robot_at(l_to)))
        move.add_effect(robot_at(l_from), False)
        move.add_effect(robot_at(l_to), True)
        move.add_effect(battery_charge, Minus(battery_charge, 10))
        l1 = Object("l1", Location)
        l2 = Object("l2", Location)

        plan = up.plans.SequentialPlan(
            [
                up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
                up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
            ]
        )

        dep_graph = plan_to_dependency_graph(plan)
        actions = ["start"] + [str(action) for action in plan.actions] + ["end"]
        graph_actions = []
        for node in dep_graph.nodes(data=True):
            graph_actions.append(node[1]["node_name"])

        self.assertEqual(actions, graph_actions)
        self.assertEqual(len(dep_graph.nodes()), 4)

    def test_all(self):
        self.test_simple_translation()
        self.test_special_cases()


class TestTimeTriggeredPlanTrasnslation(unittest.TestCase):
    def test_simple_translation(self):
        problems = get_example_problems()

        for _, plan in problems.values():
            if isinstance(plan, TimeTriggeredPlan):
                dep_graph = plan_to_dependency_graph(plan)
                actions = ["start"] + [str(action) for _, action, _ in plan.timed_actions] + ["end"]
                graph_actions = []
                for node in dep_graph.nodes(data=True):
                    node_name = node[1]["node_name"]
                    if node_name not in ["start", "end"]:
                        node_name = node[1]["node_name"].split(")")[0] + ")"
                    graph_actions.append(node_name)

                self.assertEqual(actions, graph_actions)

    def test_special_cases(self):
        Location = UserType("Location")
        is_connected = Fluent("is_connected", BoolType(), location_1=Location, location_2=Location)
        is_at = Fluent("is_at", BoolType(), position=Location)
        dur_move = DurativeAction("move", l_from=Location, l_to=Location)
        l_from = dur_move.parameter("l_from")
        l_to = dur_move.parameter("l_to")
        dur_move.set_fixed_duration(1)
        dur_move.add_condition(StartTiming(), is_at(l_from))
        dur_move.add_condition(StartTiming(), Not(is_at(l_to)))
        mid_location = Variable("mid_loc", Location)

        dur_move.add_condition(
            ClosedTimeInterval(StartTiming(), EndTiming()),
            Exists(
                And(
                    Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                    Or(
                        is_connected(l_from, mid_location),
                        is_connected(mid_location, l_from),
                    ),
                    Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to)),
                ),
                mid_location,
            ),
        )
        dur_move.add_condition(
            StartTiming(),
            Exists(
                And(
                    Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                    Or(
                        is_connected(l_from, mid_location),
                        is_connected(mid_location, l_from),
                    ),
                    Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to)),
                ),
                mid_location,
            ),
        )
        dur_move.add_effect(StartTiming("1"), is_at(l_from), False)
        dur_move.add_effect(EndTiming("5"), is_at(l_to), True)
        l1 = Object("l1", Location)
        l2 = Object("l2", Location)
        l3 = Object("l3", Location)
        l4 = Object("l4", Location)
        l5 = Object("l5", Location)

        plan = up.plans.TimeTriggeredPlan(
            [
                (
                    Fraction(0, 1),
                    up.plans.ActionInstance(dur_move, (ObjectExp(l1), ObjectExp(l3))),
                    Fraction(1, 1),
                ),
                (
                    Fraction(101, 100),
                    up.plans.ActionInstance(dur_move, (ObjectExp(l3), ObjectExp(l5))),
                    Fraction(1, 1),
                ),
                (
                    Fraction(202, 100),
                    up.plans.ActionInstance(dur_move, (ObjectExp(l5), ObjectExp(l3))),
                    Fraction(1, 1),
                ),
                (
                    Fraction(303, 100),
                    up.plans.ActionInstance(dur_move, (ObjectExp(l3), ObjectExp(l5))),
                    Fraction(1, 1),
                ),
            ]
        )

        dep_graph = plan_to_dependency_graph(plan)
        actions = ["start"] + [str(action) for _, action, _ in plan.timed_actions] + ["end"]
        graph_actions = []
        for node in dep_graph.nodes(data=True):
            node_name = node[1]["node_name"]
            if node_name not in ["start", "end"]:
                node_name = node[1]["node_name"].split(")")[0] + ")"
            graph_actions.append(node_name)

        self.assertEqual(actions, graph_actions)
        self.assertEqual(len(dep_graph.nodes()), 6)

    def test_all(self):
        self.test_simple_translation()
        self.test_special_cases()


if __name__ == "__main__":
    TestPartialOrderPlanGeneration().test_partial_order_plan_to_dependency_graph()
    TestSequentialPlanTranslation().test_all()
    TestTimeTriggeredPlanTrasnslation().test_all()
