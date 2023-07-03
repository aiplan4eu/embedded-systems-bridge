# Copyright 2022 Sebastian Stock, DFKI
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
"""Monitoring of a SequentialPlan."""
import networkx as nx

from up_esb.execution import ActionResult
from up_esb.status import ActionNodeStatus, MonitorStatus


class PlanMonitor:
    """Monitors the expecution of a UP-ESB plan graph."""

    def __init__(self, executable_graph: nx.DiGraph):
        self._graph = executable_graph
        self._status = MonitorStatus.IDLE
        self._action_status = ActionNodeStatus.NOT_STARTED

        # Preprocess the graph to remove the executable elements.
        self._preprocess_graph()

    @property
    def status(self) -> MonitorStatus:
        """Current status of the monitor."""
        return self._status

    @status.setter
    def status(self, status: MonitorStatus) -> None:
        """Set the status of the monitor."""
        self._status = status

    def _preprocess_graph(self) -> None:
        """Preprocess graph to remove the executable elements."""

        new_graph = nx.DiGraph()

        for node_id, node in self._graph.nodes(data=True):
            # Add the node.
            new_graph.add_node(node_id)
            new_graph.nodes[node_id]["processed"] = False
            new_graph.nodes[node_id]["action"] = node["action"]
            new_graph.nodes[node_id]["status"] = ActionNodeStatus.NOT_STARTED
            new_graph.nodes[node_id]["node_name"] = node["node_name"]
            new_graph.nodes[node_id]["result"] = ""

            # Add the edges.
            new_graph.add_edges_from(self._graph.edges(node_id))

            # Predecessors and successors.
            new_graph.nodes[node_id]["predecessors"] = list(self._graph.predecessors(node_id))
            new_graph.nodes[node_id]["successors"] = list(self._graph.successors(node_id))

        self._graph = new_graph

    def get_status(self) -> MonitorStatus:
        """Return the current status of the monitor."""
        return self._status

    def get_action_status(self, action_name: str) -> ActionNodeStatus:
        """Return the status of the given action."""
        self._action_status = self._get_action_status(action_name)

        return self._action_status

    def _get_action_status(self, action_name: str) -> ActionNodeStatus:
        """Return the status of the given action."""
        for _, node in self._graph.nodes(data=True):
            if node["node_name"] == action_name:
                return node["status"]
        return ActionNodeStatus.UNKNOWN

    def update_action_status(self, node_id: int, status: ActionNodeStatus) -> None:
        """Update the status of the given action."""
        self._graph.nodes[node_id]["status"] = status

    def process_action_result(self, node_id: int, result: ActionResult) -> None:
        """Process the result of an action."""


class ProcessActionResult:
    """Process ActionResult from the executor."""

    def __init__(self, graph: nx.DiGraph):
        self._graph = graph

    def is_action_succeeded(self, node_id: int):
        """Check if the action result is already processed."""
        return self._graph.nodes[node_id]["status"] == ActionNodeStatus.SUCCEEDED

    def is_action_failed(self, node_id: int):
        """Check if the action result is already processed."""
        return self._graph.nodes[node_id]["status"] == ActionNodeStatus.FAILED

    def is_action_unknown(self, node_id: int):
        """Check if the action result is already processed."""
        return self._graph.nodes[node_id]["status"] == ActionNodeStatus.UNKNOWN

    def is_action_not_started(self, node_id: int):
        """Check if the action result is already processed."""
        return self._graph.nodes[node_id]["status"] == ActionNodeStatus.NOT_STARTED

    def is_action_started(self, node_id: int):
        """Check if the action result is already processed."""
        return self._graph.nodes[node_id]["status"] == ActionNodeStatus.STARTED

    def process_result(self, result: ActionResult, node_id: int) -> None:
        """Process the result of an action."""
