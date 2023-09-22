# Copyright 2022 DFKI
# Copyright 2023 LAAS
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
# Sebastian Stock, DFKI
# Selvakumar H S, LAAS-CNRS

"""Monitoring of a SequentialPlan."""
import networkx as nx

from up_esb.exceptions import process_action_result
from up_esb.execution import ActionResult
from up_esb.logger import Logger
from up_esb.status import ActionNodeStatus, MonitorStatus


class PlanMonitor:
    """Monitors the expecution of a UP-ESB plan graph."""

    def __init__(self, executable_graph: nx.DiGraph):
        self._graph = executable_graph
        self._status = MonitorStatus.IDLE
        self._action_status = ActionNodeStatus.NOT_STARTED
        self._logger = Logger(__name__)

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

    @property
    def graph(self) -> nx.DiGraph:
        """Monitor graph."""
        return self._graph

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
        self._graph.nodes[node_id]["processed"] = True

    def process_action_result(self, result: ActionResult, dry_run: bool = False) -> None:
        """Process the result of an action."""
        if not dry_run:
            raise process_action_result(result)
        else:
            # Reraise as warning
            exception = process_action_result(result)
            self._logger.warning(str(exception))
