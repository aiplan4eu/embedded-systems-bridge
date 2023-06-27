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

from up_esb.status import ActionNodeStatus, MonitorStatus


class PlanMonitor:
    """Monitors the expecution of a UP-ESB plan graph."""

    def __init__(self, executable_graph: nx.DiGraph):
        self._graph = executable_graph
        self._status = MonitorStatus.IDLE
        self._action_status = ActionNodeStatus.NOT_STARTED

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
