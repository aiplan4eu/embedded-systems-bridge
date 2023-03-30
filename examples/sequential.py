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
"""Example for sequential plan execution."""
import matplotlib.pyplot as plt
import networkx as nx
import unified_planning as up
from unified_planning.shortcuts import OneshotPlanner

from esb.bridge import Bridge
from esb.plexmo import PlanDispatcher


#################### 1. Define the domain ####################
class Robot:
    """Robot class."""

    location = "l1"


class Location:
    """Location class."""

    def __init__(self, name):
        self.name = name

    def __repr__(self) -> str:
        return self.name


class Move:
    """Move Action."""

    def __init__(self):
        self.l_from = ""
        self.l_to = ""

    def __call__(self, *args, **kwargs):
        self.l_from = str(args[0])
        self.l_to = str(args[1])
        print(f"Moving from {self.l_from} to {self.l_to}")
        Robot.location = self.l_to

        return True

    def __repr__(self) -> str:
        return "Move"


def robot_at_fun(l: Location):
    """Check if the robot is at a location."""
    return Robot().location == l


def visited_fun(l: Location):
    """Check if the location is visited."""
    return Robot().location == l


#################### 2. Define the problem ####################


def define_problem():
    """Define the problem."""
    bridge = Bridge()

    bridge.create_types([Location])

    robot_at = bridge.create_fluent_from_function(robot_at_fun)
    visited = bridge.create_fluent_from_function(visited_fun)

    l1 = bridge.create_object("l1", Location("l1"))
    l2 = bridge.create_object("l2", Location("l2"))
    l3 = bridge.create_object("l3", Location("l3"))
    l4 = bridge.create_object("l4", Location("l4"))

    move, [l_from, l_to] = bridge.create_action(
        "Move", _callable=Move, l_from=Location, l_to=Location
    )
    move.add_precondition(robot_at(l_from))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(visited(l_to), True)

    problem = bridge.define_problem()
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(robot_at(l3), False)
    problem.set_initial_value(robot_at(l4), False)
    problem.set_initial_value(visited(l1), True)
    problem.set_initial_value(visited(l2), False)
    problem.set_initial_value(visited(l3), False)
    problem.set_initial_value(visited(l4), False)
    problem.add_goal(visited(l2))
    problem.add_goal(visited(l3))
    problem.add_goal(visited(l4))
    problem.add_goal(robot_at(l4))

    return bridge, problem


def main():
    """Main function"""
    up.shortcuts.get_environment().credits_stream = None
    bridge, problem = define_problem()
    dispatcher = PlanDispatcher()

    with OneshotPlanner(name="pyperplan") as planner:
        result = planner.solve(problem)
        print("*** Result ***")
        for action_instance in result.plan.actions:
            print(action_instance)
        print("*** End of result ***")
        plan = result.plan

    graph_executor = bridge.get_executable_graph(plan)
    dispatcher.execute_plan(graph_executor)

    # draw graph
    plt.figure(figsize=(10, 10))

    pos = nx.nx_pydot.pydot_layout(graph_executor, prog="dot")
    nx.draw(
        graph_executor, pos, with_labels=True, node_size=2000, node_color="skyblue", font_size=20
    )
    plt.show()


if __name__ == "__main__":
    main()
