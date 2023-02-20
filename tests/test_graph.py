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

from unified_planning.plans.partial_order_plan import PartialOrderPlan
from unified_planning.shortcuts import PlanKind
from unified_planning.test.examples import get_example_problems

from up_bridge.components.graph import plan_to_dependency_graph


class TestPartialOrderPlanGeneration(unittest.TestCase):
    def test_partial_order_plan_to_dependency_graph(self):
        example_problems = get_example_problems()
        problem, plan = example_problems["robot_fluent_of_user_type"]
        pop = plan.convert_to(PlanKind.PARTIAL_ORDER_PLAN, problem)
        assert isinstance(pop, PartialOrderPlan)
        dep_graph = plan_to_dependency_graph(pop)
        self.assertTrue(dep_graph.has_node("start"))
        self.assertTrue(dep_graph.has_node("end"))
        self.assertTrue(dep_graph.has_edge("start", plan.actions[0]))
        self.assertTrue(dep_graph.has_edge("start", plan.actions[1]))
        self.assertTrue(dep_graph.has_edge(plan.actions[0], "end"))
        self.assertTrue(dep_graph.has_edge(plan.actions[1], "end"))


if __name__ == "__main__":
    test = TestPartialOrderPlanGeneration()
    test.test_partial_order_plan_to_dependency_graph()
