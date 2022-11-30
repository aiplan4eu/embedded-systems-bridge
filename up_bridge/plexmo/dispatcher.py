# Copyright 2022 Sebastian Stock, Marc Vinci, DFKI
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

from unified_planning.plans.sequential_plan import SequentialPlan


class SequentialPlanDispatcher:
    """Dispatches the actions of a sequential plan."""

    def __init__(self):
        self._plan = None
        self._status = "idle"
        self._dispatch_cb = None
        self._replan_cb = None

    def execute_plan(self, plan: SequentialPlan):
        self._status = "executing"
        self._plan = plan
        self._dispatched_position = 0
        replanned = False
        last_failed_action = None
        while (
            self._dispatched_position < len(self._plan.actions)
            and self._status != "failure"
        ):
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
                if (
                    self._plan.actions[self._dispatched_position].action.name
                    == "!replan"
                ):
                    self._dispatched_position = 0
                else:
                    self._dispatched_position += 1
        if self._status != "failure":
            self._status = "finished"
            return True
        else:
            return False

    def set_dispatch_callback(self, callback):
        """Set callback function for executing actions.
        For now, that function is expected to be blocking and
        to return True if the action has been executed successfully
        and False in case of failure.
        """
        self._dispatch_cb = callback

    def status(self) -> str:
        return self._status

    def set_replan_callback(self, callback):
        """Set callback function that triggers replanning"""
        self._replan_cb = callback
