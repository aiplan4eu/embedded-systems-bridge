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
import uuid
from typing import Union

import networkx as nx
from unified_planning.plans import (
    ActionInstance,
    PartialOrderPlan,
    SequentialPlan,
    TimeTriggeredPlan,
)
from unified_planning.shortcuts import Fraction


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
    parent_id = uuid.uuid1()
    dependency_graph.add_node(parent_id, node_name="start", action="start", parameters=())
    for action in plan.actions:
        child_id = uuid.uuid1()
        child = action.action.name
        child_name = f"{child}{action.actual_parameters}"
        dependency_graph.add_node(
            child_id,
            node_name=child_name,
            action=child,
            parameters=action.actual_parameters,
        )
        dependency_graph.add_edge(parent_id, child_id)
        parent_id = child_id

    child_id = uuid.uuid1()
    dependency_graph.add_node(child_id, node_name="end", action="end", parameters=())
    dependency_graph.add_edge(parent_id, child_id)
    return dependency_graph


def _time_triggered_plan_to_dependency_graph(plan: TimeTriggeredPlan) -> nx.DiGraph:
    """Convert UP Plan to Dependency Graph."""
    dependency_graph = nx.DiGraph()
    parent_id = uuid.uuid1()
    dependency_graph.add_node(parent_id, node_name="start", action="start", parameters=())

    next_parents: Set[Tuple[Fraction, ActionInstance, Optional[Fraction]]] = set()
    for i, (start, action, duration) in enumerate(plan.timed_actions):
        child = action.action.name
        duration = float(duration.numerator) / float(duration.denominator)
        child_name = f"{child}{action.actual_parameters}({duration}s)"
        child_id = uuid.uuid1()
        dependency_graph.add_node(
            child_id, node_name=child_name, action=child, parameters=action.actual_parameters
        )
        dependency_graph.add_edge(parent_id, child_id, weight=duration)
        if i + 1 < len(plan.timed_actions):
            next_start, next_action, next_duration = plan.timed_actions[i + 1]
            next_duration = float(next_duration.numerator) / float(next_duration.denominator)
            if start != next_start:
                parent_id = child_id
                for next_parent in next_parents:
                    next_parent_name = f"{next_parent[1].action.name}{next_parent[1].actual_parameters}({next_parent[2]}s)"
                    next_child_name = f"{next_action.action.name}{next_action.actual_parameters}({next_duration}s)"

                    next_parent_id = get_node_id(dependency_graph, next_parent_name)
                    next_child_id = get_node_id(dependency_graph, next_child_name)

                    if next_child_id is None:
                        next_child_id = uuid.uuid1()
                        dependency_graph.add_node(
                            next_child_id,
                            node_name=next_child_name,
                            action=next_action.action.name,
                            parameters=next_action.actual_parameters,
                        )
                    dependency_graph.add_edge(next_parent_id, next_child_id, weight=next_duration)
                next_parents = set()
            else:
                next_parents.add((start, action, duration))

    # FIXME: End Node is conflicting with parent node
    # dependency_graph.add_node("end", action="end", parameters=())
    # dependency_graph.add_edge(parent, "end")
    return dependency_graph


def get_node_id(dependency_graph: nx.DiGraph, name: str) -> str:
    """Get the UUID for the node"""
    for node in dependency_graph.nodes(data=True):
        if node[1]["node_name"] == name:
            return node[0]
