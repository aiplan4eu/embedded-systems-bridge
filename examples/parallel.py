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
"""Example for parallel plan execution."""
import time

import unified_planning as up
from unified_planning.model import EndTiming, StartTiming

from up_esb.bridge import Bridge
from up_esb.execution.parallel_executor import Executor


# TODO: Better example
#################### 1. Define the domain ####################
class Location:
    """Location class."""

    def __init__(self, name):
        self.name = name

    def __repr__(self) -> str:
        return self.name


class Area:
    """Area class."""

    def __init__(self, x_from, x_to, y_from, y_to):
        self.x_from = x_from
        self.x_to = x_to
        self.y_from = y_from
        self.y_to = y_to

    def __repr__(self) -> str:
        return f"Area-{self.x_from}-{self.x_to}-{self.y_from}-{self.y_to}"


class Robot:
    """Robot class."""

    location = "l1"

    @classmethod
    def move(cls, l_from: Location, l_to: Location):
        """Move the robot from one location to another."""

        print(f"Moving from {l_from} to {l_to}")
        Robot.location = l_to
        time.sleep(2)

    @classmethod
    def survey(cls, area: Area):
        """Survey the area."""
        print(f"Surveying area {area}")
        time.sleep(5)

    @classmethod
    def send_info(cls, location: Location):
        """Send info about the location."""
        print(f"Sending info about {location}")
        Robot.l_to = location


def robot_at_fun(l: Location):
    """Check if the robot is at the location."""
    return Robot.location == l


def visited_fun(l: Location):
    """Check if the location is visited."""
    return Robot.location == l


def is_surveyed_fun():
    """Check if the area is surveyed."""
    return True


def info_sent_fun(_: Location):
    """Send info about the location."""
    return True


#################### 2. Define the problem ####################


def define_problem():
    """Define the problem."""
    bridge = Bridge()

    bridge.create_types([Location, Area, Robot])

    robot_at = bridge.create_fluent_from_function(robot_at_fun)
    visited = bridge.create_fluent_from_function(visited_fun)
    is_surveyed = bridge.create_fluent_from_function(is_surveyed_fun)
    info_sent = bridge.create_fluent_from_function(info_sent_fun)

    l1 = bridge.create_object("l1", Location("l1"))
    l2 = bridge.create_object("l2", Location("l2"))
    l3 = bridge.create_object("l3", Location("l3"))
    l4 = bridge.create_object("l4", Location("l4"))
    _ = bridge.create_object("area", Area(0, 10, 0, 10))

    move, [l_from, l_to] = bridge.create_action(
        "Move", _callable=Robot.move, l_from=Location, l_to=Location, duration=5
    )
    move.add_condition(StartTiming(), info_sent(l_from))
    move.add_condition(StartTiming(), info_sent(l_to))
    move.add_condition(StartTiming(), robot_at(l_from))
    move.add_effect(StartTiming(), robot_at(l_from), False)
    move.add_effect(EndTiming(), robot_at(l_to), True)
    move.add_effect(EndTiming(), visited(l_to), True)

    survey, [_] = bridge.create_action("Survey", _callable=Robot.survey, area=Area, duration=5)
    survey.add_effect(EndTiming(), is_surveyed(), True)

    send_info, [l] = bridge.create_action("SendInfo", _callable=Robot.send_info, location=Location)
    send_info.add_precondition(is_surveyed())
    send_info.add_effect(info_sent(l), True)

    problem = bridge.define_problem()
    problem.set_initial_value(is_surveyed(), False)
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
    """Main function"""
    up.shortcuts.get_environment().credits_stream = None
    bridge, problem = define_problem()
    executor = Executor()

    plan = bridge.solve(problem, planner_name="aries", optimize_with_default_metric=False)
    print("*" * 10)
    print("* Plan *")
    for action in plan.timed_actions:
        print(action)
    print("*" * 10)

    graph_executor = bridge.get_executable_graph(plan)
    executor.execute(graph_executor)

    # TODO: Add visualization


if __name__ == "__main__":
    main()
