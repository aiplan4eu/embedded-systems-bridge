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

"""This is an example of how to use the unified planning bridge.

The problem defined in this example will try to survey a given area with a drone,
localize some objects, take a closer inspection of the objects and then return to the base station.
"""
from unified_planning.shortcuts import *

from up_bridge.bridge import Bridge
from up_bridge.components import ActionDefinition, UserTypeDefinition


class Location(UserTypeDefinition):
    def __init__(self, name, x, y, z, yaw):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw

    def __repr__(self) -> str:
        return self.name


class Area(UserTypeDefinition):
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
        print(f"Robot is at {location}")
        return True

    @staticmethod
    def verify_station_at(location: Location) -> bool:
        print(f"{location} Location is verified")
        return True

    @staticmethod
    def is_surveyed(area: Area) -> bool:
        print(f"{area} Area is surveyed")
        return True

    @staticmethod
    def is_location_surveyed(area: Area, location: Location) -> bool:
        print(f"{location} Location is surveyed")
        return True

    @staticmethod
    def is_within_area(area: Area, location: Location) -> bool:
        print(f"{location} is within {area}")
        return True


class Move:
    def __call__(self, area: Area, l_from: Location, l_to: Location) -> bool:
        print(f"Moving from {l_from} to {l_to}")
        return True


class CapturePhoto:
    def __call__(self, area: Area, location: Location) -> bool:
        print(f"Capturing photo at {location}")
        return True


class Survey:
    def __call__(self, area: Area) -> bool:
        print(f"Surveying {area}")
        return True


class GatherInfo:
    def __call__(self, area: Area, location: Location) -> bool:
        print(f"Gathering info at {location}")
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

    def __init__(self) -> None:
        self.instance = self


class VerifyStationProblem(Application):
    def __init__(self, bridge: Bridge) -> None:
        assert isinstance(bridge, Bridge), "bridge must be a Generic Bridge instance"
        self.bridge = bridge

    def start_execution(self, action_instances: list, **kwargs):
        self.app = Application()

        results = []
        for action in action_instances:
            (executor, parameters) = self.bridge.get_executable_action(action)
            execute_action = executor(**kwargs)
            result = execute_action(*parameters)

            results.append(result)

        if all(results):
            print("All actions executed successfully")

    def get_problem(self):

        self.bridge.create_types([Location, Area])

        f_robot_at = self.bridge.create_fluent_from_function(self.robot_at)
        f_verified_station_at = self.bridge.create_fluent_from_function(self.verify_station_at)
        f_is_surveyed = self.bridge.create_fluent_from_function(self.is_surveyed)
        f_is_location_surveyed = self.bridge.create_fluent_from_function(self.is_location_surveyed)
        f_is_within_area = self.bridge.create_fluent_from_function(self.is_within_area)

        o_l1 = self.bridge.create_object(str(self.l1), self.l1)
        o_l2 = self.bridge.create_object(str(self.l2), self.l2)
        o_l3 = self.bridge.create_object(str(self.l3), self.l3)
        o_l4 = self.bridge.create_object(str(self.l4), self.l4)
        o_home = self.bridge.create_object(str(self.home), self.home)
        o_area = self.bridge.create_object(str(self.area), self.area)

        move, (a, l_from, l_to) = self.bridge.create_action(
            "Move", callable=self.move, area=Area, l_from=Location, l_to=Location
        )
        move.add_precondition(f_is_surveyed(a))
        move.add_precondition(f_is_location_surveyed(a, l_to))
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(f_robot_at(l_from))
        move.add_precondition(Not(f_robot_at(l_to)))
        move.add_effect(f_robot_at(l_from), False)
        move.add_effect(f_robot_at(l_to), True)

        capture_photo, (a, l) = self.bridge.create_action(
            "CapturePhoto", callable=self.capture_photo, area=Area, l=Location
        )
        capture_photo.add_precondition(f_is_surveyed(a))
        capture_photo.add_precondition(f_is_location_surveyed(a, l))
        capture_photo.add_precondition(f_robot_at(l))
        capture_photo.add_effect(f_verified_station_at(l), True)
        capture_photo.add_effect(f_robot_at(l), True)  # Since using instantaneous actions

        survey, a = self.bridge.create_action("Survey", callable=self.survey, area=Area)
        survey.add_precondition(Not(f_is_surveyed(a)))
        survey.add_effect(f_is_surveyed(a), True)

        gather_info, (a, l) = self.bridge.create_action(
            "GatherInfo", callable=self.gather_info, area=Area, l=Location
        )
        gather_info.add_precondition(f_is_surveyed(a))
        gather_info.add_precondition(f_is_within_area(a, l))
        gather_info.add_effect(f_is_location_surveyed(a, l), True)

        problem = self.bridge.define_problem()
        problem.set_initial_value(f_robot_at(o_home), True)
        problem.set_initial_value(f_robot_at(o_l1), False)
        problem.set_initial_value(f_robot_at(o_l2), False)
        problem.set_initial_value(f_robot_at(o_l3), False)
        problem.set_initial_value(f_robot_at(o_l4), False)

        problem.set_initial_value(f_verified_station_at(o_home), True)
        problem.set_initial_value(f_verified_station_at(o_l1), False)
        problem.set_initial_value(f_verified_station_at(o_l2), False)
        problem.set_initial_value(f_verified_station_at(o_l3), False)
        problem.set_initial_value(f_verified_station_at(o_l4), False)

        problem.set_initial_value(f_is_surveyed(o_area), False)
        problem.set_initial_value(f_is_within_area(o_area, o_home), True)
        problem.set_initial_value(f_is_within_area(o_area, o_l1), True)
        problem.set_initial_value(f_is_within_area(o_area, o_l2), True)
        problem.set_initial_value(f_is_within_area(o_area, o_l3), True)
        problem.set_initial_value(f_is_within_area(o_area, o_l4), True)
        problem.set_initial_value(f_is_location_surveyed(o_area, o_home), True)
        problem.set_initial_value(f_is_location_surveyed(o_area, o_l1), False)
        problem.set_initial_value(f_is_location_surveyed(o_area, o_l2), False)
        problem.set_initial_value(f_is_location_surveyed(o_area, o_l3), False)
        problem.set_initial_value(f_is_location_surveyed(o_area, o_l4), False)

        problem.add_goal(f_is_surveyed(o_area))
        problem.add_goal(f_is_location_surveyed(o_area, o_l1))
        problem.add_goal(f_is_location_surveyed(o_area, o_l2))
        problem.add_goal(f_is_location_surveyed(o_area, o_l3))
        problem.add_goal(f_is_location_surveyed(o_area, o_l4))
        problem.add_goal(f_verified_station_at(o_l1))
        problem.add_goal(f_verified_station_at(o_l2))
        problem.add_goal(f_verified_station_at(o_l3))
        problem.add_goal(f_verified_station_at(o_l4))
        problem.add_goal(f_robot_at(o_home))

        return problem


def main():
    """Main Function."""
    actions = []
    bridge = Bridge()
    demo = VerifyStationProblem(bridge)
    problem = demo.get_problem()
    print("=== Problem ===")
    with OneshotPlanner(name="aries") as planner:
        # Aries planner is currently available at: https://github.com/aiplan4eu/up-aries
        result = planner.solve(problem)
        print("*** Result ***")
        for action_instance in result.plan.timed_actions:
            print(action_instance)
            actions.append(action_instance[1])
        print("*** End of result ***")

    # Execute the plan
    print("=== Executing the plan ===")
    demo.start_execution(actions)


if __name__ == "__main__":
    main()
