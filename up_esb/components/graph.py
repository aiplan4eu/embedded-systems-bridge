# Copyright 2022, 2023 LAAS-CNRS
# Copyright 2023 DFKI
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
# Authors:
# - Selvakumar H S, LAAS-CNRS
# - Sebastian Stock, DFKI

"""Module to convert UP Plan to Dependency Graph and execute it."""
from typing import Set, Union

import networkx as nx
from unified_planning.plans.partial_order_plan import PartialOrderPlan
from unified_planning.plans.sequential_plan import SequentialPlan
from unified_planning.plans.time_triggered_plan import TimeTriggeredPlan


def plan_to_dependency_graph(
    plan: Union[SequentialPlan, TimeTriggeredPlan, PartialOrderPlan]
) -> nx.DiGraph:
    """Convert UP Plan to Dependency Graph."""
    if isinstance(plan, SequentialPlan):
        return _sequential_plan_to_dependency_graph(plan)
    if isinstance(plan, TimeTriggeredPlan):
        return _time_triggered_plan_to_dependency_graph(plan)
    if isinstance(plan, PartialOrderPlan):
        return _partial_order_plan_to_dependency_graph(plan)
    raise NotImplementedError("Plan type not supported")


def _partial_order_plan_to_dependency_graph(plan: PartialOrderPlan) -> nx.DiGraph:
    """Convert UP Partial Order Plan to Dependency Graph."""
    dependency_graph = nx.DiGraph()
    dependency_graph.add_node("end", action="end", parameters=())
    for action, successors in plan.get_adjacency_list.items():
        action_name = action.action.name
        params = action.actual_parameters
        node_name = f"{action_name}{params}"
        dependency_graph.add_node(node_name, action=action_name, parameters=params)
        # add edges to successors
        for succ in successors:
            succ_node_name = f"{succ.action.name}{succ.actual_parameters}"
            dependency_graph.add_edge(node_name, succ_node_name)
        # add end node and edges from nodes without successors
        if len(successors) == 0:
            dependency_graph.add_edge(node_name, "end")

    # add start node and edges to nodes without predecessors
    start_nodes = [node for node, in_degree in dependency_graph.in_degree() if in_degree == 0]
    dependency_graph.add_node("start", action="start", parameters=())
    for node in start_nodes:
        dependency_graph.add_edge("start", node)
    return dependency_graph


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

    next_parents: Set[tuple] = set()
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
                    next_parent_name = f"{next_parent[1].action.name}{next_parent[1].actual_parameters}({next_parent[2]}s)"  # pylint: disable=line-too-long
                    next_child_name = f"{next_action.action.name}{next_action.actual_parameters}({next_duration}s)"  # pylint: disable=line-too-long
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
