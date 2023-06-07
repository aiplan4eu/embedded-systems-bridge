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
from unified_planning.plans.sequential_plan import SequentialPlan


class SequentialPlanDispatcher:
    """Dispatches the actions of a sequential plan."""

    def __init__(self):
        self._plan = None
        self._status = "idle"
        self._dispatch_cb = None
        self._replan_cb = None
        self._dispatched_position = 0

    def execute_plan(self, plan: SequentialPlan):
        """Execute the plan."""
        self._status = "executing"
        self._plan = plan
        self._dispatched_position = 0
        replanned = False
        last_failed_action = None
        while self._dispatched_position < len(self._plan.actions) and self._status != "failure":
            current_action = self._plan.actions[self._dispatched_position]
            action_result = self._dispatch_cb(current_action)
            if not action_result:
                # TODO Move error handling into separate method
                if last_failed_action != current_action:
                    last_failed_action = current_action
                    if not replanned and self._replan_cb:
                        # replan once if an action fails for each action
                        # TODO make replannig more flexible (dependent on the action) and generic
                        print("Action failed: Replanning once!")
                        new_plan = self._replan_cb()
                        if new_plan is not None:
                            self._plan = new_plan
                            self._dispatched_position = 0
                            replanned = True
                            continue
                self._status = "failure"
            else:
                replanned = False
                if last_failed_action == current_action:
                    last_failed_action = None
                if self._plan.actions[self._dispatched_position].action.name == "!replan":
                    self._dispatched_position = 0
                else:
                    self._dispatched_position += 1
        if self._status != "failure":
            self._status = "finished"
            return True

        return False

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


class PlanDispatcher:
    """Dispatches the actions of the executable graph."""

    def __init__(self):
        self._graph = None
        self._status = "idle"
        self._dispatch_cb = self._default_dispatch_cb
        self._replan_cb = None
        self._dispatched_position = 0
        self._options = None

    def execute_plan(self, graph: nx.DiGraph, **options):
        """Execute the plan."""
        self._status = "executing"
        self._graph = graph
        self._dispatched_position = 0
        self._options = options
        replanned = False
        last_failed_action = None
        for node in self._graph.nodes(data=True):
            if node[1]["node_name"] in ["start", "end"]:
                continue  # skip start and end node
            successors = list(self._graph.successors(node[0]))
            if len(successors) > 1 and self._status != "failure":  # Assume as single action
                # TODO: Handle multiple successors
                print(f"Node {node[0]} has {len(successors)} successors: {successors}. Exiting!")
                self._status = "failure"
                return False
            current_action = node
            action_result = self._dispatch_cb(current_action)
            if not action_result:
                # TODO Move error handling into separate method
                if last_failed_action != current_action:
                    last_failed_action = current_action
                    if not replanned and self._replan_cb:
                        # replan once if an action fails for each action
                        # TODO make replannig more flexible
                        # (dependent on the action) and generic
                        print("Action failed: Replanning once!")
                        new_plan = self._replan_cb()
                        if new_plan is not None:
                            self._graph = new_plan
                            self._dispatched_position = 0
                            replanned = True
                            continue
                self._status = "failure"
            else:
                replanned = False
                if last_failed_action == current_action:
                    last_failed_action = None
                # TODO:Check the below condition
                if node[0] == "!replan":
                    self._dispatched_position = 0
                else:
                    self._dispatched_position += 1

        if self._status != "failure":
            self._status = "finished"
            return True

        return False

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
