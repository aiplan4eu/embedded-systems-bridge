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
"""Example for time triggered plan execution."""

import time

import unified_planning as up
from unified_planning.model import EndTiming, StartTiming
from unified_planning.shortcuts import Not

from up_esb.bridge import Bridge
from up_esb.plexmo import PlanDispatcher


#################### 1. Define the domain ####################
class Location:
    """Location class."""

    def __init__(self, name):
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, other):
        return self.name == other.name


class Robot:
    """Robot class."""

    location = Location("l1")

    @classmethod
    def move(cls, l_from: Location, l_to: Location):
        """Move the robot from one location to another."""

        print(f"Moving from {l_from} to {l_to}")
        Robot.location = l_to
        time.sleep(2)

        return True


def robot_at_fun(l: Location):
    """Check if the robot is at a location."""
    return Robot.location == l


def visited_fun(l: Location):
    """Check if the location is visited."""
    return Robot.location == l


def is_connected_fun(l1: Location, l2: Location):
    """Check if two locations are connected."""
    # TODO: Bridge cannot handle initial states at the moment
    return l1 != l2  # Dummy condition


#################### 2. Define the problem ####################
def define_problem():
    """Define the problem."""
    bridge = Bridge()

    bridge.create_types([Robot, Location])

    robot_at = bridge.create_fluent_from_function(robot_at_fun)
    visited = bridge.create_fluent_from_function(visited_fun)
    is_connected = bridge.create_fluent_from_function(is_connected_fun)

    l1 = bridge.create_object("l1", Location("l1"))
    l2 = bridge.create_object("l2", Location("l2"))
    l3 = bridge.create_object("l3", Location("l3"))
    l4 = bridge.create_object("l4", Location("l4"))
    l5 = bridge.create_object("l5", Location("l5"))
    r1 = bridge.create_object("r1", Robot())

    dur_move, [l_from, l_to] = bridge.create_action(
        "Move", _callable=Robot.move, l_from=Location, l_to=Location, duration=10
    )
    dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
    dur_move.add_condition(StartTiming(), robot_at(l_from))
    dur_move.add_condition(StartTiming(), Not(robot_at(l_to)))
    dur_move.add_effect(EndTiming(), robot_at(l_to), True)
    dur_move.add_effect(EndTiming(), robot_at(l_from), False)
    dur_move.add_effect(EndTiming(), visited(l_to), True)

    problem = bridge.define_problem()
    bridge.set_initial_values(problem)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(visited(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.add_goal(visited(l2))
    problem.add_goal(visited(l3))
    problem.add_goal(visited(l4))
    problem.add_goal(visited(l5))
    return bridge, problem


def main():
    """Main function"""
    up.shortcuts.get_environment().credits_stream = None
    bridge, problem = define_problem()
    dispatcher = PlanDispatcher()

    plan = bridge.solve(problem, planner_name="aries", optimize_with_default_metric=False)
    print("*" * 10)
    print("* Plan *")
    for action in plan.timed_actions:
        print(action)
    print("*" * 10)

    graph_executor = bridge.get_executable_graph(plan)
    dispatcher.execute_plan(plan, graph_executor)

    # TODO: Add visualization


if __name__ == "__main__":
    main()
