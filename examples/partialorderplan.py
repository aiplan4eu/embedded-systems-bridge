# Copyright 2022, 2023 LAAS-CNRS
# Copyright 2023 DFKI GmbH
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
# - Sebastian Stock, DFKI
# - Selvakumar H S, LAAS-CNRS
"""Example for parallel execution of a partial order plan."""
import matplotlib.pyplot as plt
import networkx as nx
import unified_planning as up
from parallel import (
    Area,
    Location,
    Move,
    Robot,
    SendInfo,
    Survey,
    info_sent_fun,
    is_surveyed_fun,
    robot_at_fun,
    visited_fun,
)
from unified_planning.plans import SequentialPlan
from unified_planning.shortcuts import OneshotPlanner, PlanKind

from up_bridge.bridge import Bridge
from up_bridge.executor import Executor

# Define the problem. The domain is re-used from examples/parallel.py


def define_problem():
    """Define the problem."""
    bridge = Bridge()
    bridge.create_types([Location, Area, Robot])

    robot_at = bridge.create_fluent_from_function(robot_at_fun)
    visited = bridge.create_fluent_from_function(visited_fun)
    is_surveyed = bridge.create_fluent_from_function(is_surveyed_fun)
    info_sent = bridge.create_fluent_from_function(info_sent_fun)

    # Instead of the example in paralle.py, we use instantanious actions
    move, [l_from, l_to] = bridge.create_action(
        "Move", _callable=Move, l_from=Location, l_to=Location
    )
    move.add_precondition(info_sent(l_from))
    move.add_precondition(info_sent(l_to))
    move.add_precondition(robot_at(l_from))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(visited(l_to), True)

    survey, [a] = bridge.create_action(  # pylint: disable=unused-variable
        "Survey", _callable=Survey, area=Area
    )
    survey.add_effect(is_surveyed(), True)

    send_info, [l] = bridge.create_action("SendInfo", _callable=SendInfo, location=Location)
    # send_info.add_precondition(is_surveyed())
    send_info.add_effect(info_sent(l), True)

    l1 = bridge.create_object("l1", Location("l1"))
    l2 = bridge.create_object("l2", Location("l2"))
    l3 = bridge.create_object("l3", Location("l3"))
    l4 = bridge.create_object("l4", Location("l4"))

    problem = bridge.define_problem()
    problem.set_initial_value(is_surveyed(), True)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(robot_at(l3), False)
    problem.set_initial_value(robot_at(l4), False)
    problem.set_initial_value(visited(l1), True)
    problem.set_initial_value(visited(l2), False)
    problem.set_initial_value(visited(l3), False)
    problem.set_initial_value(visited(l4), False)
    problem.set_initial_value(info_sent(l1), False)
    problem.set_initial_value(info_sent(l2), False)
    problem.set_initial_value(info_sent(l3), False)
    problem.set_initial_value(info_sent(l4), False)
    problem.add_goal(visited(l2))
    problem.add_goal(visited(l3))
    problem.add_goal(visited(l4))
    problem.add_goal(robot_at(l4))
    return bridge, problem


def main():
    """Main function."""
    up.shortcuts.get_environment().credits_stream = None
    bridge, problem = define_problem()

    with OneshotPlanner(problem_kind=problem.kind) as planner:
        print(problem.kind)
        print(planner)
        result = planner.solve(problem)
        print("*** Result ***")
        print(result.plan)
        print("*** End of result ***")

    plan = result.plan
    if plan.kind == PlanKind.SEQUENTIAL_PLAN:
        print("Converting SequentialPlan to PartialOrderPlan")
        plan = plan.convert_to(PlanKind.PARTIAL_ORDER_PLAN, problem)
        print(plan.get_adjacency_list)

    dependency_graph = bridge.get_executable_graph(plan)
    print(dependency_graph.adj)
    executor = Executor()
    executor.execute(dependency_graph)

    # draw graph
    plt.figure(figsize=(10, 10))

    pos = nx.nx_pydot.pydot_layout(dependency_graph, prog="dot")
    nx.draw(
        dependency_graph, pos, with_labels=True, node_size=2000, node_color="skyblue", font_size=20
    )
    plt.show()


if __name__ == "__main__":
    main()
