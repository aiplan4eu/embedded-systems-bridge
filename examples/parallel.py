import time

import matplotlib.pyplot as plt
import networkx as nx
import unified_planning as up
from networkx.drawing.nx_agraph import graphviz_layout
from unified_planning.shortcuts import *
from unified_planning.model import StartTiming, EndTiming

from up_bridge.bridge import Bridge


#################### 1. Define the domain ####################
class Robot:
    location = ""

    def __init__(self, cls):
        cls.location = "l1"

    def move(self, l_to):
        self.location = l_to


class Location:
    def __init__(self, name):
        self.name = name

    def __repr__(self) -> str:
        return self.name


class Area:
    def __init__(self, x_from, x_to, y_from, y_to):
        self.x_from = x_from
        self.x_to = x_to
        self.y_from = y_from
        self.y_to = y_to

    def __repr__(self) -> str:
        return f"Area-{self.x_from}-{self.x_to}-{self.y_from}-{self.y_to}"


class Move:
    def __init__(self):
        self.l_from = ""
        self.l_to = ""

    def __call__(self, *args, **kwargs):
        self.l_from = str(args[0])
        self.l_to = str(args[1])
        print(f"Moving from {self.l_from} to {self.l_to}")
        time.sleep(5)

    def __repr__(self) -> str:
        return "Move"


class Survey:
    def __init__(self):
        self.x_from = ""
        self.x_to = ""
        self.y_from = ""
        self.y_to = ""

    def __call__(self, *args, **kwargs):
        area = str(args[0])
        print(f"Surveying area {area}")
        time.sleep(5)


class SendInfo:
    def __init__(self):
        self.location = ""

    def __call__(self, location: Location):
        self.location = location
        print(f"Sending info about {location}")


def robot_at_fun(l: Location):
    return Robot().location == l


def visited_fun(l: Location):
    return Robot().location == l


def is_surveyed_fun():
    return True


def info_sent_fun(l: Location):
    return True


#################### 2. Define the problem ####################


def define_problem():
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
    area = bridge.create_object("area", Area(0, 10, 0, 10))

    move, [l_from, l_to] = bridge.create_action(
        "Move", callable=Move, l_from=Location, l_to=Location, duration=5
    )
    move.add_condition(StartTiming(), info_sent(l_from))
    move.add_condition(StartTiming(), info_sent(l_to))
    move.add_condition(StartTiming(), robot_at(l_from))
    move.add_effect(StartTiming(), robot_at(l_from), False)
    move.add_effect(EndTiming(), robot_at(l_to), True)
    move.add_effect(EndTiming(), visited(l_to), True)

    survey, [a] = bridge.create_action("Survey", callable=Survey, area=Area, duration=5)
    survey.add_effect(EndTiming(), is_surveyed(), True)

    send_info, [l] = bridge.create_action("SendInfo", callable=SendInfo, location=Location)
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
    up.shortcuts.get_env().credits_stream = None
    bridge, problem = define_problem()

    with OneshotPlanner(name="aries") as planner:
        result = planner.solve(problem)
        print("*** Result ***")
        for action_instance in result.plan.timed_actions:
            print(action_instance)
        print("*** End of result ***")
        plan = result.plan

    # TODO: Move to Bridge
    graph_executor = bridge.get_executable_graph(plan)
    # for node in graph_executor.nodes(data=True):
    #     if node[0] in ["start", "end"]:
    #         continue
    #     parameters = node[1]["parameters"]
    #     result = node[1]["executor"]()(*parameters)

    # draw graph
    plt.figure(figsize=(10, 10))

    pos = graphviz_layout(graph_executor, prog="dot")
    nx.draw(
        graph_executor, pos, with_labels=True, node_size=2000, node_color="skyblue", font_size=20
    )
    plt.show()


if __name__ == "__main__":
    main()
