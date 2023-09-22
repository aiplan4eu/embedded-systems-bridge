# Copyright 2022, 2023 DFKI GmbH
# Copyright 2023 LAAS-CNRS
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
#
# Authors:
# - Sebastian Stock, DFKI
# - Marc Vinci, DFKI
# - Selvakumar H S, LAAS-CNRS
"""Dispatcher for executing plans."""
import networkx as nx
from unified_planning.plans import Plan

from up_esb.exceptions import UPESBException, UPESBWarning
from up_esb.execution import ActionExecutor, ActionResult
from up_esb.logger import Logger
from up_esb.status import ActionNodeStatus, ConditionStatus, DispatcherStatus, MonitorStatus

from .monitor import PlanMonitor


class PlanDispatcher:
    """Dispatches the actions of the executable graph."""

    def __init__(self):
        self._graph = None
        self._status = DispatcherStatus.IDLE
        self._dispatch_cb = self._default_dispatch_cb
        self._replan_cb = None
        self._options = None
        self._executor = None
        self._plan = None
        self._rules = {}
        self._monitor = None
        self._node_data = None
        self._logger = Logger(__name__)

    @property
    def monitor(self) -> PlanMonitor:
        """Plan monitor."""
        return self._monitor

    @property
    def monitor_status(self) -> MonitorStatus:
        """Plan monitor status."""
        return self._monitor.status

    @property
    def monitor_graph(self) -> nx.DiGraph:
        """Plan monitor graph."""
        return self._monitor.graph

    @property
    def execution_graph(self) -> nx.DiGraph:
        """Plan execution graph."""
        return self._graph

    def execute_plan(self, plan: Plan, graph: nx.DiGraph, **options):
        """Execute the plan."""
        self._status = DispatcherStatus.STARTED
        self._graph = graph
        self._options = options
        self._plan = plan

        self._executor = ActionExecutor(graph, options=options)
        self._executor = self._executor.get_executor(plan)

        # Setup Monitor
        self._setup_monitor(self._graph)

        while self._status != DispatcherStatus.REPLANNING or not self._node_data:
            # Get the next node to be executed
            node_id, node = self._node_data.pop(0) if len(self._node_data) > 0 else (None, None)
            if node_id is None:
                break
            if self._status == DispatcherStatus.REPLANNING:
                self._setup_monitor(self._graph)
                self._status = DispatcherStatus.IN_PROGRESS

            self._monitor.status = MonitorStatus.IN_PROGRESS

            predecessors = list(self.monitor_graph.predecessors(node_id))

            # Start and end nodes
            if node["action"] == "start":
                assert len(predecessors) == 0, "Start node cannot have predecessors"
                self._monitor.update_action_status(node_id, ActionNodeStatus.SUCCEEDED)
                continue
            elif node["action"] == "end":
                # Check if all the predecessors are succeeded
                predecessors_status = self._check_node_status(
                    predecessors, ActionNodeStatus.SUCCEEDED
                )
                if predecessors_status is False:
                    self._monitor.update_action_status(node_id, ActionNodeStatus.FAILED)
                    self._monitor.status = MonitorStatus.FAILED
                    continue

                self._monitor.update_action_status(node_id, ActionNodeStatus.SUCCEEDED)
                continue

            # Check if all the predecessors are succeeded
            predecessors_status = self._check_node_status(predecessors, ActionNodeStatus.SUCCEEDED)
            if predecessors_status is False:
                self._monitor.update_action_status(node_id, ActionNodeStatus.NOT_STARTED)
                self._status = DispatcherStatus.FAILED

                message = f"Predecessors for action {node['node_name']} are not succeeded. Cannot execute the action. Exiting..."
                if options.get("dry_run", False):
                    self._logger.warning(message)
                    exit(1)
                raise UPESBWarning(message)

            # Execute the action
            # TODO: Add parallel execution with Task Trackers
            result = self._executor.execute_action(node_id)
            self._monitor.update_action_status(node_id, result.action_status)

            # Process the result
            if result.result is None:
                self._monitor.update_action_status(node_id, result.action_status)
            else:
                self._monitor.status = MonitorStatus.FAILED
                self._monitor.process_action_result(result, dry_run=options.get("dry_run", True))

            if self._check_result(result) is False:
                self._status = DispatcherStatus.FAILED

                # Replan if replan callback is provided
                if self._replan_cb is not None:
                    self._status = DispatcherStatus.REPLANNING
                    self._plan, self._graph = self._replan_cb(self._plan, self._rules)
                    continue
            else:
                self._monitor.status = MonitorStatus.IN_PROGRESS
                self._status = DispatcherStatus.IN_PROGRESS

        if self._status == DispatcherStatus.FAILED and self._replan_cb is not None:
            return False

        self._status = DispatcherStatus.FINISHED
        self._monitor.status = MonitorStatus.FINISHED

        return True

    def _check_node_status(self, nodes: list, status: ActionNodeStatus):
        """Check node status from monitoring graph."""
        for node_id in nodes:
            if self.monitor_graph.nodes[node_id]["status"] != status:
                return False

        return True

    def _check_result(self, result: ActionResult):
        if (
            result.precondition_status != ConditionStatus.SUCCEEDED
            or result.action_status != ActionNodeStatus.SUCCEEDED
            or result.postcondition_status != ConditionStatus.SUCCEEDED
        ):
            return False

        return True

    def _setup_monitor(self, graph: nx.DiGraph):
        """Setup monitor for monitoring the execution."""
        self._monitor = PlanMonitor(graph)
        self._monitor.status = MonitorStatus.STARTED

        self._node_data = [(node_id, node) for node_id, node in graph.nodes(data=True)]

    def set_dispatch_callback(self, callback):
        """Set callback function for executing actions.
        For now, that function is expected to be blocking and
        to return True if the action has been executed successfully
        and False in case of failure.
        """
        self._dispatch_cb = callback

    @property
    def status(self) -> str:
        """Return the current status of the dispatcher."""
        return self._status

    def set_replan_callback(self, callback, **args):
        """Set callback function that triggers replanning"""

        if args.get("rules", None) is not None:
            if not isinstance(self._rules, dict):
                raise UPESBException(
                    "Rules argument should be a dictionary with rule name as key and rule as value"
                )
            self._rules = args.get("rules")
        else:
            self._rules = {}

        if args.get("plan", None) is not None:
            self._plan = args.get("plan")
        else:
            raise UPESBException("Plan argument is not provided for replanning callback")

        # TODO: Check if return type of callback is Plan and Graph
        self._replan_cb = callback

    def _default_dispatch_cb(self, node_id: str):
        # TODO: Involve with monitoring and logging
        raise NotImplementedError

    def _default_replan_cb(self):
        # TODO: Involve with monitoring and logging
        raise NotImplementedError
