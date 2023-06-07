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
from unified_planning.model import EndTiming, StartTiming
from unified_planning.shortcuts import ClosedTimeInterval, Not

from up_esb.bridge import Bridge
from up_esb.plexmo import PlanDispatcher


#################### 1. Define the domain ####################
class Match:
    """Match class."""

    def __init__(self, name):
        self.name = name

    def __repr__(self) -> str:
        return self.name


class Fuse:
    """Fuse class."""

    def __init__(self, name):
        self.name = name

    def __repr__(self) -> str:
        return self.name


class TemporalActions:
    """Class for temporal actions."""

    def __init__(self):
        self.m = None
        self.f = None

    def light_match(self, m: Match):
        """Light match action."""
        self.m = m

        print(f"Lighting match {m}")
        time.sleep(5)
        return True

    def mend_fuse(self, f: Fuse):
        """Mend fuse action."""
        self.f = f

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


# Objects
f1, f2, f3 = Fuse("f1"), Fuse("f2"), Fuse("f3")
m1, m2, m3 = Match("m1"), Match("m2"), Match("m3")


#################### 2. Define the problem ####################
def define_problem():
    """Define the problem."""
    bridge = Bridge()
    actions = TemporalActions()

    bridge.create_types([Match, Fuse])

    handsfree = bridge.create_fluent_from_function(handsfree_fun)
    light = bridge.create_fluent_from_function(light_fun)
    match_used = bridge.create_fluent_from_function(match_used_fun)
    fuse_mended = bridge.create_fluent_from_function(fuse_mended_fun)

    obj_f1 = bridge.create_object("f1", f1)
    obj_f2 = bridge.create_object("f2", f2)
    obj_f3 = bridge.create_object("f3", f3)
    obj_m1 = bridge.create_object("m1", m1)
    obj_m2 = bridge.create_object("m2", m2)
    obj_m3 = bridge.create_object("m3", m3)

    light_match, [m] = bridge.create_action(
        "LightMatch", _callable=actions.light_match, m=Match, duration=5
    )
    light_match.add_condition(StartTiming(), Not(match_used(m)))
    light_match.add_effect(StartTiming(), match_used(m), True)
    light_match.add_effect(StartTiming(), light, True)
    light_match.add_effect(EndTiming(), light, False)

    mend_fuse, [f] = bridge.create_action(
        "MendFuse", _callable=actions.mend_fuse, f=Fuse, duration=3
    )
    mend_fuse.add_condition(StartTiming(), handsfree)
    mend_fuse.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), light)
    mend_fuse.add_effect(StartTiming(), handsfree, False)
    mend_fuse.add_effect(EndTiming(), fuse_mended(f), True)
    mend_fuse.add_effect(EndTiming(), handsfree, True)

    problem = bridge.define_problem()
    problem.set_initial_value(light, False)
    problem.set_initial_value(handsfree, True)
    problem.set_initial_value(match_used(obj_m1), False)
    problem.set_initial_value(match_used(obj_m2), False)
    problem.set_initial_value(match_used(obj_m3), False)
    problem.set_initial_value(fuse_mended(obj_f1), False)
    problem.set_initial_value(fuse_mended(obj_f2), False)
    problem.set_initial_value(fuse_mended(obj_f3), False)
    problem.add_goal(fuse_mended(obj_f1))
    problem.add_goal(fuse_mended(obj_f2))
    problem.add_goal(fuse_mended(obj_f3))

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

    def dispatch_callback(action):
        # TODO: Remove once integrated with dispatcher
        """Dispatch callback function."""
        parameters = action[1]["parameters"]
        preconditions = action[1]["preconditions"]
        post_conditions = action[1]["post_conditions"]
        # Preconditions
        for _, conditions in preconditions.items():
            for condition in conditions:
                eval(compile(condition, filename="<ast>", mode="eval"))  # pylint: disable=eval-used
            print(f"Tested preconditions: {len(conditions)}")

        action[1]["executor"](**parameters)

        for _, conditions in post_conditions.items():
            for condition, _ in conditions:
                eval(compile(condition, filename="<ast>", mode="eval"))  # pylint: disable=eval-used
            print(f"Tested postconditions: {len(conditions)}")

    graph_executor = bridge.get_executable_graph(plan)
    dispatcher.set_dispatch_callback(dispatch_callback)
    dispatcher.execute_plan(graph_executor)

    # draw graph
    plt.figure(figsize=(10, 10))

    labels = {}
    for node in graph_executor.nodes(data=True):
        labels[node[0]] = node[1]["node_name"]

    pos = nx.nx_pydot.pydot_layout(graph_executor, prog="dot")
    nx.draw(
        graph_executor,
        pos,
        with_labels=True,
        labels=labels,
        node_size=1000,
        node_color="skyblue",
        font_size=20,
    )
    plt.show()


if __name__ == "__main__":
    main()
