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

"""Module to convert UP Plan to Dependency Graph and execute it."""
from typing import Union

import networkx as nx
from unified_planning.plans.sequential_plan import SequentialPlan
from unified_planning.plans.time_triggered_plan import TimeTriggeredPlan


def plan_to_dependency_graph(plan: Union[SequentialPlan, TimeTriggeredPlan]) -> nx.DiGraph:
    """Convert UP Plan to Dependency Graph."""
    if isinstance(plan, SequentialPlan):
        return _sequential_plan_to_dependency_graph(plan)
    if isinstance(plan, TimeTriggeredPlan):
        return _time_triggered_plan_to_dependency_graph(plan)
    raise NotImplementedError("Plan type not supported")


def _sequential_plan_to_dependency_graph(plan: SequentialPlan) -> nx.DiGraph:
    """Convert UP Plan to Dependency Graph."""
    dependency_graph = nx.DiGraph()
    edge = "start"
    dependency_graph.add_node(edge, action="start", parameters=())
    for action in plan.actions:
        child = action.action.name
        child_name = f"{child}{action.actual_parameters}"
        dependency_graph.add_node(child_name, action=child, parameters=action.actual_parameters)
        dependency_graph.add_edge(edge, child_name)
        edge = child_name

    dependency_graph.add_node("end", action="end", parameters=())
    dependency_graph.add_edge(edge, "end")
    return dependency_graph


def _time_triggered_plan_to_dependency_graph(plan: TimeTriggeredPlan) -> nx.DiGraph:
    """Convert UP Plan to Dependency Graph."""
    dependency_graph = nx.DiGraph()
    parent = "start"
    dependency_graph.add_node(parent, action="start", parameters=())

    next_parents = set()
    for i, (start, action, duration) in enumerate(plan.timed_actions):
        child = action.action.name
        duration = float(duration.numerator) / float(duration.denominator)
        child_name = f"{child}{action.actual_parameters}({duration}s)"
        dependency_graph.add_node(child_name, action=child, parameters=action.actual_parameters)
        dependency_graph.add_edge(parent, child_name, weight=duration)
        if i + 1 < len(plan.timed_actions):
            next_start, next_action, next_duration = plan.timed_actions[i + 1]
            next_duration = float(next_duration.numerator) / float(next_duration.denominator)
            if start != next_start:
                parent = child_name
                for next_parent in next_parents:
                    next_parent_name = f"{next_parent[1].action.name}{next_parent[1].actual_parameters}({next_parent[2]}s)"
                    next_child_name = f"{next_action.action.name}{next_action.actual_parameters}({next_duration}s)"
                    dependency_graph.add_edge(
                        next_parent_name, next_child_name, weight=next_duration
                    )
                next_parents = set()
            else:
                next_parents.add((start, action, duration))

    # FIXME: End Node is conflicting with parent node
    # dependency_graph.add_node("end", action="end", parameters=())
    # dependency_graph.add_edge(parent, "end")
    return dependency_graph
