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

"""Create a set of problems for the unified planning domain."""
import unified_planning as up
from unified_planning.shortcuts import EndTiming, Not, StartTiming

from up_esb.bridge import Bridge
from up_esb.plexmo import PlanDispatcher


class Location:
    """Location class for the robot example"""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Location({self.name})"

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Location):
            return self.name == __value.name
        return False


class Area:
    """Area class for the robot example"""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Area({self.name})"

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Area):
            return self.name == __value.name
        return False


class Robot:
    """Robot class."""

    location = Location("base_station")
    surveyed = False
    plates = False
    distance_optimized = False
    locations_inspected = []

    @classmethod
    def move(cls, l_from: Location, l_to: Location):
        """Move the robot from one location to another."""

        print(f"Moving from {l_from} to {l_to}")
        Robot.location = l_to

        return True

    @classmethod
    def survey(cls, area: Area, l_from: Location):
        """Survey the area from a location."""
        print(f"Surveying area {area} from location {l_from}")
        Robot.surveyed = True
        return True

    @classmethod
    def send_info(cls):
        """Send the information to the base station."""
        print("Sending information to the base station")
        Robot.plates = True
        return True

    @classmethod
    def acquire_plates_order(cls):
        """Send the information to the base station."""
        print("Acquiring plates order")
        Robot.distance_optimized = True
        return True

    @classmethod
    def inspect_plate(cls, l: Location):
        """Inspect the plate at a location."""
        print(f"Inspecting plate at location {l}")
        Robot.locations_inspected.append(l)
        return True


# Fluent definitions
def robot_at_fun(l: Location):
    """Check if the robot is at a location."""
    return Robot.location == l


def is_surveyed_fun():
    """Check if the area is surveyed."""
    return Robot.surveyed


def has_plates_fun():
    """Check if the robot has plates."""
    return Robot.plates


def is_distance_optimized_fun():
    """Check if the robot has plates."""
    return Robot.distance_optimized


def is_base_station_fun(l: Location):
    """Check if the robot is at a location."""
    return l.name == "base_station"


def is_location_inspected_fun(l: Location):
    """Check if the robot is at a location."""
    return l in Robot.locations_inspected


def is_plate_inspected_fun(l: Location):
    """Check if the robot is at a location."""
    return l in Robot.locations_inspected


def define_problem():
    """Create a simple station verification application"""

    bridge = Bridge()

    bridge.create_types([Location, Area, Robot])

    # Fluent definitions
    robot_at = bridge.create_fluent_from_function(robot_at_fun)
    is_surveyed = bridge.create_fluent_from_function(is_surveyed_fun)
    is_base_station = bridge.create_fluent_from_function(is_base_station_fun)
    has_plates = bridge.create_fluent_from_function(has_plates_fun)
    is_distance_optimized = bridge.create_fluent_from_function(is_distance_optimized_fun)
    is_location_inspected = bridge.create_fluent_from_function(is_location_inspected_fun)
    is_plate_inspected = bridge.create_fluent_from_function(is_plate_inspected_fun)

    # Default objects
    robot = bridge.create_object("r1", Robot())
    l1 = bridge.create_object("l1", Location("l1"))
    l2 = bridge.create_object("l2", Location("l2"))
    l3 = bridge.create_object("l3", Location("l3"))
    l4 = bridge.create_object("l4", Location("l4"))
    base_station = bridge.create_object("base_station", Location("base_station"))
    charging_station = bridge.create_object("charging_station", Location("charging_station"))
    area = bridge.create_object("area", Area("area"))

    # Action definitions
    survey, [area, l_from] = bridge.create_action(
        "survey", _callable=Robot.survey, area=Area, l_from=Location, duration=10
    )
    survey.add_condition(StartTiming(), Not(is_surveyed()))
    survey.add_condition(StartTiming(), is_base_station(l_from))
    survey.add_condition(StartTiming(), Not(has_plates()))
    survey.add_effect(EndTiming(), is_surveyed(), True)

    send_info, [] = bridge.create_action("send_info", _callable=Robot.send_info)
    send_info.add_precondition(is_surveyed())
    send_info.add_precondition(Not(has_plates()))
    send_info.add_effect(has_plates(), True)

    move, [l_from, l_to] = bridge.create_action(
        "move", _callable=Robot.move, l_from=Location, l_to=Location, duration=1
    )
    move.add_condition(StartTiming(), robot_at(l_from))
    move.add_condition(StartTiming(), Not(robot_at(l_to)))
    move.add_condition(StartTiming(), has_plates())
    move.add_condition(StartTiming(), is_distance_optimized())
    move.add_effect(StartTiming(), robot_at(l_from), False)
    move.add_effect(EndTiming(), robot_at(l_to), True)

    acquire_plates_order, [] = bridge.create_action(
        "acquire_plates_order", _callable=Robot.acquire_plates_order
    )
    acquire_plates_order.add_precondition(has_plates())
    acquire_plates_order.add_precondition(Not(is_distance_optimized()))
    acquire_plates_order.add_effect(is_distance_optimized(), True)

    inspect_plate, [l] = bridge.create_action(
        "inspect_plate", _callable=Robot.inspect_plate, l=Location, duration=2
    )
    inspect_plate.add_condition(StartTiming(), robot_at(l))
    inspect_plate.add_condition(StartTiming(), has_plates())
    inspect_plate.add_condition(StartTiming(), is_distance_optimized())
    inspect_plate.add_effect(EndTiming(), is_location_inspected(l), True)
    inspect_plate.add_effect(EndTiming(), is_plate_inspected(l), True)

    problem = bridge.define_problem()
    bridge.set_initial_values(problem)

    problem.set_initial_value(robot_at(base_station), True)
    problem.set_initial_value(is_base_station(base_station), True)

    problem.add_goal(is_surveyed())
    problem.add_goal(has_plates())
    problem.add_goal(is_distance_optimized())
    problem.add_goal(is_location_inspected(l1))
    problem.add_goal(is_location_inspected(l2))
    problem.add_goal(is_location_inspected(l3))
    problem.add_goal(is_location_inspected(l4))
    problem.add_goal(is_plate_inspected(l1))
    problem.add_goal(is_plate_inspected(l2))
    problem.add_goal(is_plate_inspected(l3))
    problem.add_goal(is_plate_inspected(l4))
    problem.add_goal(robot_at(charging_station))

    return problem, bridge


def main():
    up.shortcuts.get_environment().credits_stream = None
    problem, bridge = define_problem()
    dispatcher = PlanDispatcher()

    plan = bridge.solve(problem, planner_name="aries", optimize_with_default_metric=False)
    print("*" * 10)
    print("* Plan *")
    for action in plan.timed_actions:
        print(action)
    print("*" * 10)

    graph_executor = bridge.get_executable_graph(plan)
    dispatcher.execute_plan(plan, graph_executor, dry_run=True)

    print("*" * 10)
    print(dispatcher.monitor_status)
    print(dispatcher.status)
    print("*" * 10)


if __name__ == "__main__":
    main()
