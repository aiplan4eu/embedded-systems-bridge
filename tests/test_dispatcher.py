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

import unittest

from unified_planning.plans.plan import ActionInstance
from unified_planning.plans.sequential_plan import SequentialPlan
from unified_planning.test.examples import get_example_problems

from up_esb.plexmo.dispatcher import SequentialPlanDispatcher

# pylint: disable=all


def get_example_plan() -> SequentialPlan:
    example_problems = get_example_problems()
    return example_problems["basic"].plan


class TestDispatcher(unittest.TestCase):
    def suceeding_execute_cb(self, action: ActionInstance) -> bool:
        print("In callback. Action: %s" % action.action.name)
        self._dispatched_action = action
        return True

    def failing_execute_cb(self, action: ActionInstance) -> bool:
        print("In callback. Action: %s" % action.action.name)
        self._dispatched_action = action
        return False

    def test_callback(self):
        dispatcher = SequentialPlanDispatcher()
        dispatcher.set_dispatch_callback(self.suceeding_execute_cb)
        assert dispatcher._dispatch_cb == self.suceeding_execute_cb

    def test_successfull_execution(self):
        plan = get_example_plan()
        dispatcher = SequentialPlanDispatcher()
        dispatcher.set_dispatch_callback(self.suceeding_execute_cb)
        dispatcher.execute_plan(plan)
        assert dispatcher.status() == "finished"

    def test_failing_execution(self):
        plan = get_example_plan()
        dispatcher = SequentialPlanDispatcher()
        dispatcher.set_dispatch_callback(self.failing_execute_cb)
        dispatcher.execute_plan(plan)
        assert dispatcher.status() == "failure"


if __name__ == "__main__":
    td = TestDispatcher()
    td.test_successfull_execution()
