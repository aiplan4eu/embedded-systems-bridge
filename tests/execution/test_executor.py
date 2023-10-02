# Copyright 2022 Selvakumar H S, LAAS-CNRS
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

import pytest

from tests import ContextManager, get_example_plans
from up_esb.bridge import Bridge
from up_esb.execution import ActionExecutor
from up_esb.status import ActionNodeStatus, ConditionStatus

# pylint: disable=protected-access


class TestTaskExecutor:
    """Test the execution of instantaneous tasks."""

    @pytest.mark.parametrize("plan_name, plan", get_example_plans().items())
    def test_task_executor(self, plan_name, plan):
        """Test the execution of instantaneous tasks."""

        bridge = Bridge()
        ContextManager.plan = plan
        bridge._api_actions = ContextManager.get_actions_context(returns=True)
        bridge._api_objects = ContextManager.get_objects_context()
        bridge._fluent_functions = ContextManager.get_fluents_context()
        graph = bridge.get_executable_graph(plan)

        executor = ActionExecutor(graph, options={"verbose": True, "dry_run": True})
        executor = executor.get_executor(plan)

        if not isinstance(plan, executor.supported_plan_kind):
            pytest.skip(f"Skipping unsupported plan: {plan_name}")

        for node_id, node in graph.nodes(data=True):
            if node["action"] in ["start", "end"]:
                continue

            result = executor.execute_action(node_id)

            assert result.precondition_status == ConditionStatus.SUCCEEDED
            assert result.action_status == ActionNodeStatus.SUCCEEDED
            assert result.postcondition_status == ConditionStatus.SUCCEEDED
            assert result.result is None
