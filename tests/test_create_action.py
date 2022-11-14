#!/usr/bin/env python3
from typing import Optional
from enum import Enum
from unified_planning.model import Problem
from unified_planning.shortcuts import And, Not, OneshotPlanner
import unified_planning as up
from up_bridge import Bridge

"""
Examples for different ways to define actions on the application side and how to use the up_bridge
 to create UP representations from them.
"""


class Location(Enum):
    A = 'A'
    B = 'B'
    C = 'C'


class Item:
    def __init__(self, name: str) -> None:
        self.name = name
        self.location: Optional[Location] = Location.A

    def __repr__(self) -> str:
        return self.name


class Robot:
    def __init__(self, name: str, location: Location) -> None:
        self.name = name
        self.location = location
        self.item: Optional[Item] = None

    def __repr__(self) -> str:
        return self.name

    def move(self, location_from: Location, location_to: Location) -> None:
        self.location = location_to
        print(f"{self} moves from {location_from} to {location_to}.")


def place_item_onto_robot(robot: Robot, item: Item, location: Location) -> None:
    assert robot.location == item.location == location
    assert robot.item is None
    robot.item = item
    item.location = None
    print(f"{item} is placed on {robot} at {location}.")


class ActionDefinition:
    """Example stub for an action definition superclass."""


class PassItemAction(ActionDefinition):
    def __call__(self, robot_from: Robot, robot_to: Robot, item: Item) -> None:
        """Let robot_from pass item to robot_to."""
        assert robot_from.item == item
        assert robot_to.item == None
        robot_from.item = None
        robot_to.item = item
        print(f"{robot_from} passes {item} to {robot_to}.")


class ActionDefinitionsExample(Bridge):
    def __init__(self) -> None:
        super().__init__()
        self.create_types([Location, Item, Robot])
        self.A, self.B, self.C = self.locations = self.create_enum_objects(Location)
        self.api_tool = Item("tool")
        self.tool = self.create_object("tool", self.api_tool)
        self.items = [self.tool]
        self.api_robot1 = Robot("robot1", Location.A)
        self.api_robot2 = Robot("robot2", Location.B)
        self.robot1, self.robot2 = self.robots = self.create_objects(robot1=self.api_robot1, robot2=self.api_robot2)
        self.item_at = self.create_fluent_from_function(self.get_item_at)
        self.robot_at = self.create_fluent_from_function(self.get_robot_at)
        self.robot_has = self.create_fluent_from_function(self.get_robot_has)

        # Create action from a class method:
        self.move, (robot, location_from, location_to) \
            = self.create_action(*self.get_action_parameters(Robot.move))
        self.set_api_actions([Robot.move])
        # The purpose of the set_api_actions() method is to make action declaration independent of
        #  its implementation. For example, the later can be implemented in a subclass of the former.
        # The following command would achieve the same in one step:
        # self.move, (robot, location_from, location_to) \
        #     = self.create_action(*self.get_action_parameters(Robot.move), Robot.move)
        self.move.add_precondition(self.robot_at(robot, location_from))
        self.move.add_precondition(And(Not(self.robot_at(robot, location_to))
            for robot in self.robots))
        self.move.add_effect(self.robot_at(robot, location_from), False)
        self.move.add_effect(self.robot_at(robot, location_to), True)

        # Create action from a function:
        self.place, (robot, item, location) = self.create_action_from_function(place_item_onto_robot)
        # For functions which do not use self as parameter, create_action_from_function() is the
        #  same as any one of the following commands:
        # self.place, (robot, item, location) = self.create_action(*self.get_action_parameters(place_item_onto_robot),
        #     place_item_onto_robot)
        # self.place, (robot, item, location) = self.create_action("place",
        #     place_item_onto_robot.__annotations__, place_item_onto_robot)
        self.place.add_precondition(self.item_at(item, location))
        self.place.add_precondition(self.robot_at(robot, location))
        self.place.add_precondition(And(Not(self.robot_has(robot, item)) for item in self.items))
        self.place.add_effect(self.item_at(item, location), False)
        self.place.add_effect(self.robot_has(robot, item), True)

        # Create action from a class instance:
        self.pass_item, (robot_from, robot_to, item) = self.create_action("pass_item",
            PassItemAction.__call__.__annotations__, PassItemAction())
        # In this case, you need to provide the signature of the __call_ method explicitly.
        # As before, providing the callable PassItemAction() can be done later than at action declaration.
        self.pass_item.add_precondition(self.robot_has(robot_from, item))
        self.pass_item.add_precondition(And(Not(self.robot_has(robot_to, item))
            for item in self.items))
        self.pass_item.add_effect(self.robot_has(robot_from, item), False)
        self.pass_item.add_effect(self.robot_has(robot_to, item), True)

    @staticmethod
    def get_item_at(item: Item, location: Location) -> bool:
        return location == item.location

    @staticmethod
    def get_robot_at(robot: Robot, location: Location) -> bool:
        return location == robot.location

    @staticmethod
    def get_robot_has(robot: Robot, item: Item) -> bool:
        return item == robot.item

    def test(self) -> None:
        problem = Problem()
        problem.add_objects(self.locations)
        problem.add_object(self.tool)
        problem.add_objects(self.robots)
        problem.add_fluent(self.item_at, default_initial_value=False)
        problem.set_initial_value(self.item_at(self.tool, self.A), True)
        problem.add_fluent(self.robot_at, default_initial_value=False)
        problem.set_initial_value(self.robot_at(self.robot1, self.A), True)
        problem.set_initial_value(self.robot_at(self.robot2, self.B), True)
        problem.add_fluent(self.robot_has, default_initial_value=False)
        problem.add_actions([self.move, self.place, self.pass_item])

        problem.add_goal(self.robot_has(self.robot2, self.tool))
        problem.add_goal(self.robot_at(self.robot2, self.C))
        with OneshotPlanner(problem_kind=problem.kind) as planner:
            result = planner.solve(problem)
            for action in result.plan.actions:
                callable, parameters = self.get_executable_action(action)
                callable(*parameters)
        assert self.get_robot_has(self.api_robot2, self.api_tool)
        assert self.get_robot_at(self.api_robot2, Location.C)


def test_create_action() -> None:
    up.shortcuts.get_env().credits_stream = None
    ActionDefinitionsExample().test()


if __name__ == '__main__':
    test_create_action()
