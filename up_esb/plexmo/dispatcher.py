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

from up_esb.execution.executor import ActionResult, InstantaneousTaskExecutor
from up_esb.status import ActionNodeStatus, ConditionStatus, DispatcherStatus


class PlanDispatcher:
    """Dispatches the actions of the executable graph."""

    def __init__(self):
        self._graph = None
        self._status = DispatcherStatus.IDLE
        self._dispatch_cb = self._default_dispatch_cb
        self._replan_cb = None
        self._dispatched_position = 0
        self._options = None
        self._executor = None

    def execute_plan(self, graph: nx.DiGraph, **options):
        """Execute the plan."""
        self._status = DispatcherStatus.STARTED
        self._graph = graph
        self._dispatched_position = 0
        self._options = options

        self._executor = InstantaneousTaskExecutor(dependency_graph=graph)
        for node_id, node in self._graph.nodes(data=True):
            if node["action"] in ["start", "end"]:
                continue
            result = self._executor.execute_action(node_id)

            if self._check_result(result) is False:
                self._status = DispatcherStatus.FAILED

        if self._status != DispatcherStatus.FAILED:
            self._status = DispatcherStatus.FINISHED
            return True

        return False

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

    def status(self) -> str:
        """Return the current status of the dispatcher."""
        return self._status

    def set_replan_callback(self, callback):
        """Set callback function that triggers replanning"""
        self._replan_cb = callback

    def _default_dispatch_cb(self, action):
        """Dispatch callback function."""
        # TODO: Add verification of preconditions
        parameters = action[1]["parameters"]
        preconditions = action[1]["preconditions"]
        post_conditions = action[1]["postconditions"]
        context = action[1]["context"]
        executor = context[action[1]["action"]]

        # Execution options
        dry_run = self._options.get("dry_run", False)
        verbose = self._options.get("verbose", False)

        # Preconditions
        for i, (_, conditions) in enumerate(preconditions.items()):
            for condition in conditions:
                result = eval(  # pylint: disable=eval-used
                    compile(condition, filename="<ast>", mode="eval"), context
                )

                # Check if all preconditions return boolean True
                if not result and not dry_run:
                    raise RuntimeError(
                        f"Precondition {i+1} for action {action[1]['action']}{tuple(parameters.values())} failed!"
                    )
            if verbose:
                print(f"Evaluated {len(conditions)} preconditions ...")

        # Execute action
        executor(**parameters)

        for i, (_, conditions) in enumerate(post_conditions.items()):
            for condition, value in conditions:
                actual = eval(  # pylint: disable=eval-used
                    compile(condition, filename="<ast>", mode="eval"), context
                )
                expected = eval(  # pylint: disable=eval-used
                    compile(value, filename="<ast>", mode="eval"), context
                )

                if actual != expected and not dry_run:
                    raise RuntimeError(
                        f"Postcondition {i+1} for action {action[1]['action']}{tuple(parameters.values())} failed!"
                    )
            if verbose:
                print(f"Evaluated {len(conditions)} postconditions ...")
