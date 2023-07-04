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
# - Sebastian Stock, DFKI
# - Selvakumar H S, LAAS-CNRS
import pytest
from unified_planning.plans.plan import ActionInstance

from tests import ContextManager, get_example_plans
from up_esb.bridge import Bridge
from up_esb.plexmo.dispatcher import PlanDispatcher
from up_esb.status import ActionNodeStatus, DispatcherStatus, MonitorStatus

# pylint: disable=all


class TestDispatcher:
    def suceeding_execute_cb(self, action: ActionInstance) -> bool:
        print("In callback. Action: %s" % action.action.name)
        self._dispatched_action = action
        return True

    def test_callback(self):
        dispatcher = PlanDispatcher()
        dispatcher.set_dispatch_callback(self.suceeding_execute_cb)
        assert dispatcher._dispatch_cb == self.suceeding_execute_cb

    @pytest.mark.parametrize("plan_name, plan", get_example_plans().items())
    def test_successfull_execution(self, plan_name, plan):
        bridge = Bridge()
        ContextManager.plan = plan
        bridge._api_actions = ContextManager.get_actions_context(returns=True)
        bridge._api_objects = ContextManager.get_objects_context()
        bridge._fluent_functions = ContextManager.get_fluents_context()
        graph = bridge.get_executable_graph(plan)

        dispatcher = PlanDispatcher()
        dispatcher.execute_plan(plan, graph, verbose=True, dry_run=True)
        assert dispatcher.status == DispatcherStatus.FINISHED
        assert dispatcher.monitor_status == MonitorStatus.FINISHED

        for _, node in dispatcher.monitor_graph.nodes(data=True):
            assert node["processed"] == True
            assert node["status"] == ActionNodeStatus.SUCCEEDED
