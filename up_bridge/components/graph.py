"""Module to convert UP Plan to Dependency Graph and execute it."""
from typing import Union
import networkx as nx
from unified_planning.engines.results import PlanGenerationResultStatus
import unified_planning as up
from unified_planning.plans.sequential_plan import SequentialPlan
from unified_planning.plans.time_triggered_plan import TimeTriggeredPlan
import asyncio


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
    for action in plan.actions:
        child = action.action.name
        dependency_graph.add_node(child)
        dependency_graph.add_edge(edge, child)
        edge = child
        # for precondition in action.preconditions:
        #     dependency_graph.add_edge(precondition, action.name)

    dependency_graph.add_node("end")
    dependency_graph.add_edge(edge, "end")
    return dependency_graph


def _time_triggered_plan_to_dependency_graph(plan: TimeTriggeredPlan) -> nx.DiGraph:
    """Convert UP Plan to Dependency Graph."""
    dependency_graph = nx.DiGraph()
    dependency_graph.add_node("start")
    edge = "start"

    # TODO: Add duration to the graph
    for _, action, _ in plan.timed_actions:
        child = f"{action.action.name}_{action.actual_parameters}"
        dependency_graph.add_node(child)

        # Add edges with parent actions
        dependency_graph.add_edge(edge, child)
        edge = child

    dependency_graph.add_node("end")
    dependency_graph.add_edge(edge, "end")
    return dependency_graph
