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

from up_esb.execution import ActionExecutor, ActionResult
from up_esb.status import ActionNodeStatus, ConditionStatus, DispatcherStatus, MonitorStatus

from .monitor import PlanMonitor


class PlanDispatcher:
    """Dispatches the actions of the executable graph."""

    def __init__(self):
        self._graph = None
        self._status = DispatcherStatus.IDLE
        self._dispatch_cb = self._default_dispatch_cb
        self._replan_cb = self._default_replan_cb
        self._dispatched_position = 0
        self._options = None
        self._executor = None
        # TODO: Use the plan for plan repair, replanning, etc.
        self._plan = None
        self._monitor = None

    def execute_plan(self, plan: Plan, graph: nx.DiGraph, **options):
        """Execute the plan."""
        self._status = DispatcherStatus.STARTED
        self._graph = graph
        self._dispatched_position = 0
        self._options = options
        self._plan = plan
        self._monitor = PlanMonitor(graph)
        self._monitor.status = MonitorStatus.STARTED

        self._executor = ActionExecutor(graph, options=options)
        self._executor = self._executor.get_executor(plan)

        # TODO: Dispatch actions based on predecessors and successors.
        for node_id, node in self._graph.nodes(data=True):
            self._monitor.status = MonitorStatus.IN_PROGRESS

            if node["action"] in ["start", "end"]:
                self._monitor.update_action_status(node_id, ActionNodeStatus.SUCCEEDED)
                continue
            result = self._executor.execute_action(node_id)
            self._monitor.update_action_status(node_id, result.action_status)

            if result.result is None:
                self._monitor.update_action_status(node_id, result.action_status)
            else:
                self._monitor.status = MonitorStatus.FAILED
                self._monitor.process_action_result(node_id, result)

            if self._check_result(result) is False:
                # TODO: Replan
                self._status = DispatcherStatus.FAILED
            else:
                self._monitor.status = MonitorStatus.IN_PROGRESS
                self._status = DispatcherStatus.IN_PROGRESS

        if self._status == DispatcherStatus.FAILED and self._replan_cb is not None:
            return False

        self._status = DispatcherStatus.FINISHED
        self._monitor.status = MonitorStatus.FINISHED

        return True

    def _check_result(self, result: ActionResult):
        if (
            result.precondition_status != ConditionStatus.SUCCEEDED
            or result.action_status != ActionNodeStatus.SUCCEEDED
            or result.postcondition_status != ConditionStatus.SUCCEEDED
        ):
            return False

        return True

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

    def set_replan_callback(self, callback):
        """Set callback function that triggers replanning"""
        self._replan_cb = callback

    def _default_dispatch_cb(self, node_id: str):
        # TODO: Involve with monitoring and logging
        raise NotImplementedError

    def _default_replan_cb(self):
        # TODO: Involve with monitoring and logging
        raise NotImplementedError
