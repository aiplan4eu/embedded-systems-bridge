# Copyright 2023 Selvakumar H S, LAAS-CNRS
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
from up_esb import Bridge
from up_esb.execution.task_manager import TaskManager

# pylint: disable=protected-access


class TestTaskManager:
    """Test the execution of instantaneous tasks."""

    def setup_manager(self, plan):
        """Setup the task manager for the given plan."""
        bridge = Bridge()
        ContextManager.plan = plan
        bridge._api_actions = ContextManager.get_actions_context(returns=True)
        bridge._api_objects = ContextManager.get_objects_context()
        bridge._fluent_functions = ContextManager.get_fluents_context()
        graph = bridge.get_executable_graph(plan)

        manager = TaskManager(plan, graph)

        has_multiple_successors = {}
        for node_id in graph.nodes():
            successors = list(graph.successors(node_id))
            if len(successors) > 1:
                has_multiple_successors[node_id] = True
            else:
                has_multiple_successors[node_id] = False

        for node_id in graph.nodes():
            if has_multiple_successors[node_id] is False:
                manager.add_task(node_id)
                continue

            manager.add_tasks(list(graph.successors(node_id)))

        return manager, graph

    @pytest.mark.parametrize("plan_name, plan", get_example_plans().items())
    def test_setup_task_manager(self, plan_name, plan):
        """Test setup of task manager for sequential execution."""

        print(f"Task manager test for plan: {plan_name}")

        manager, graph = self.setup_manager(plan)

        assert manager._graph == graph
        assert len(manager._execution_queue) == len(graph.nodes())

    @pytest.mark.parametrize("plan_name, plan", get_example_plans().items())
    def test_check_task_container(self, plan_name, plan):
        """Test the task container for sequential execution."""

        print(f"Task container test for plan: {plan_name}")

        manager, _ = self.setup_manager(plan)

        for container in manager._execution_queue:
            with container:
                assert len(container._tasks) == 1
