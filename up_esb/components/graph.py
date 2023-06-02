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
from typing import Optional, Set, Tuple, Union

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

    # Prepare Node IDs
    nodes = set()
    node_map = {}
    for action, successors in plan.get_adjacency_list.items():
        nodes.add(action)
        for succ in successors:
            nodes.add(succ)
    nodes.add("start")
    nodes.add("end")

    for i, node in enumerate(nodes):
        node_map[node] = i

    dependency_graph.add_node(node_map["end"], node_name="end", action="end", parameters=())
    for action, successors in plan.get_adjacency_list.items():
        dependency_graph.add_node(
            node_map[action],
            node_name=str(action),
            action=action.action.name,
            parameters=action.actual_parameters,
        )
        # add edges to successors
        for succ in successors:
            dependency_graph.add_edge(node_map[action], node_map[succ])
        # add end node and edges from nodes without successors
        if len(successors) == 0:
            dependency_graph.add_edge(node_map[action], node_map["end"])

    # add start node and edges to nodes without predecessors
    start_nodes = [node for node, in_degree in dependency_graph.in_degree() if in_degree == 0]
    dependency_graph.add_node(node_map["start"], node_name="start", action="start", parameters=())
    for node in start_nodes:
        dependency_graph.add_edge(node_map["start"], node)

    return dependency_graph


def _sequential_plan_to_dependency_graph(plan: SequentialPlan) -> nx.DiGraph:
    """Convert UP Sequential Plan to Dependency Graph."""
    dependency_graph = nx.DiGraph()
    parent_id = 0
    dependency_graph.add_node(parent_id, node_name="start", action="start", parameters=())
    for i, action in enumerate(plan.actions):
        child_id = i + 1
        dependency_graph.add_node(
            child_id,
            node_name=str(action),
            action=action.action.name,
            parameters=action.actual_parameters,
        )
        dependency_graph.add_edge(parent_id, child_id)
        parent_id = child_id

    child_id = parent_id + 1  # End node
    dependency_graph.add_node(child_id, node_name="end", action="end", parameters=())
    dependency_graph.add_edge(parent_id, child_id)
    return dependency_graph


def _time_triggered_plan_to_dependency_graph(plan: TimeTriggeredPlan) -> nx.DiGraph:
    """Convert UP Time Triggered Plan to Dependency Graph."""
    dependency_graph = nx.DiGraph()
    parent_id = 0
    next_parents: Set[Tuple[int, Fraction, ActionInstance, Optional[Fraction]]] = set()

    # Add all nodes
    dependency_graph.add_node(parent_id, node_name="start", action="start", parameters=())
    for i, (start, action, duration) in enumerate(plan.timed_actions):
        child_id = i + 1
        duration = float(duration.numerator) / float(duration.denominator)
        dependency_graph.add_node(
            child_id,
            node_name=f"{str(action)}({duration})",
            action=action.action.name,
            parameters=action.actual_parameters,
        )

    dependency_graph.add_node(
        len(plan.timed_actions) + 1, node_name="end", action="end", parameters=()
    )

    # Add all edges and durations
    for i, (start, action, duration) in enumerate(plan.timed_actions):
        child_id = i + 1
        dependency_graph.add_edge(parent_id, child_id)
        if i + 1 < len(plan.timed_actions):
            next_start, next_action, next_duration = plan.timed_actions[i + 1]
            next_duration = float(next_duration.numerator) / float(next_duration.denominator)
            if start != next_start:
                parent_id = child_id
                for next_parent in next_parents:
                    next_child_name = f"{str(next_action)}({next_duration}s)"

                    next_parent_id = next_parent[0]
                    next_child_id = _get_node_id(dependency_graph, next_child_name)
                    if next_child_id is None:
                        next_child_id = child_id + 1
                        dependency_graph.add_node(
                            next_child_id,
                            node_name=next_child_name,
                            action=next_action.action.name,
                            parameters=next_action.actual_parameters,
                        )
                    dependency_graph.add_edge(next_parent_id, next_child_id)
                next_parents = set()
            else:
                next_parents.add((child_id, start, action, duration))

    # Link last nodes to end node
    # TODO: this is a hack, because the last node is not linked to the end node
    # May create a problem if there are multiple nodes at the same time
    dependency_graph.add_edge(len(plan.timed_actions), len(plan.timed_actions) + 1)
    return dependency_graph


def _get_node_id(dependency_graph: nx.DiGraph, name: str) -> Optional[int]:
    """Get the UUID for the node"""
    for node in dependency_graph.nodes(data=True):
        if node[1]["node_name"] == name:
            return node[0]

    return None
