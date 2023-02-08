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
from random import randint

import matplotlib.pyplot as plt
import networkx as nx
import unified_planning as up
from networkx.drawing.nx_agraph import graphviz_layout
from unified_planning.model import EndTiming, StartTiming
from unified_planning.shortcuts import ClosedTimeInterval, Not, OneshotPlanner

from up_bridge.bridge import Bridge
from up_bridge.plexmo import PlanDispatcher


#################### 1. Define the domain ####################
class Match:
    """Match class."""

    def __init__(self, name):
        self.name = name


class Fuse:
    """Fuse class."""

    def __init__(self, name):
        self.name = name


class LightMatch:
    """Light match action."""

    def __init__(self):
        self.m = None

    def __call__(self, m: Match):
        print(f"Lighting match {m}")
        time.sleep(5)
        return True


class MendFuse:
    """Mend fuse action."""

    def __init__(self):
        self.f = None

    def __call__(self, f: Fuse):
        print(f"Mending fuse {f}")
        time.sleep(3)
        return True


def handsfree_fun():
    """Check if hands are free."""
    return True


def light_fun():
    """Check if lighted."""
    return True


def match_used_fun(m: Match):  # pylint: disable=unused-argument
    """Check if match is used."""
    return bool(randint(0, 1))


def fuse_mended_fun(f: Fuse):  # pylint: disable=unused-argument
    """Fuse mended?"""
    return bool(randint(0, 1))


def light_match_fun(m: Match):  # pylint: disable=unused-argument
    """Light match?"""
    return bool(randint(0, 1))


#################### 2. Define the problem ####################
def define_problem():
    """Define the problem."""
    bridge = Bridge()

    bridge.create_types([Match, Fuse])

    handsfree = bridge.create_fluent_from_function(handsfree_fun)
    light = bridge.create_fluent_from_function(light_fun)
    match_used = bridge.create_fluent_from_function(match_used_fun)
    fuse_mended = bridge.create_fluent_from_function(fuse_mended_fun)

    f1 = bridge.create_object("f1", Fuse("f1"))
    f2 = bridge.create_object("f2", Fuse("f2"))
    f3 = bridge.create_object("f3", Fuse("f3"))
    m1 = bridge.create_object("m1", Match("m1"))
    m2 = bridge.create_object("m2", Match("m2"))
    m3 = bridge.create_object("m3", Match("m3"))

    light_match, [m] = bridge.create_action("LightMatch", _callable=LightMatch, m=Match, duration=5)
    light_match.add_condition(StartTiming(), Not(match_used(m)))
    light_match.add_effect(StartTiming(), match_used(m), True)
    light_match.add_effect(StartTiming(), light, True)
    light_match.add_effect(EndTiming(), light, False)

    mend_fuse, [f] = bridge.create_action("MendFuse", _callable=MendFuse, f=Fuse, duration=3)
    mend_fuse.add_condition(StartTiming(), handsfree)
    mend_fuse.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), light)
    mend_fuse.add_effect(StartTiming(), handsfree, False)
    mend_fuse.add_effect(EndTiming(), fuse_mended(f), True)
    mend_fuse.add_effect(EndTiming(), handsfree, True)

    problem = bridge.define_problem()
    problem.set_initial_value(light, False)
    problem.set_initial_value(handsfree, True)
    problem.set_initial_value(match_used(m1), False)
    problem.set_initial_value(match_used(m2), False)
    problem.set_initial_value(match_used(m3), False)
    problem.set_initial_value(fuse_mended(f1), False)
    problem.set_initial_value(fuse_mended(f2), False)
    problem.set_initial_value(fuse_mended(f3), False)
    problem.add_goal(fuse_mended(f1))
    problem.add_goal(fuse_mended(f2))
    problem.add_goal(fuse_mended(f3))

    return bridge, problem


def main():
    """Main function"""
    up.shortcuts.get_env().credits_stream = None
    bridge, problem = define_problem()
    dispatcher = PlanDispatcher()

    with OneshotPlanner(name="aries") as planner:
        result = planner.solve(problem)
        print("*** Result ***")
        for action_instance in result.plan.timed_actions:
            print(action_instance)
        print("*** End of result ***")
        plan = result.plan

    graph_executor = bridge.get_executable_graph(plan)
    dispatcher.execute_plan(graph_executor)

    # draw graph
    plt.figure(figsize=(10, 10))

    pos = graphviz_layout(graph_executor, prog="dot")
    nx.draw(
        graph_executor,
        pos,
        with_labels=True,
        node_size=1000,
        node_color="skyblue",
        font_size=20,
    )
    plt.show()


if __name__ == "__main__":
    main()
