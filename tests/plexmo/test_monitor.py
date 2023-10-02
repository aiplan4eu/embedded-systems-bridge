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

import pytest

from tests import ContextManager, get_example_plans
from up_esb.components.graph import plan_to_dependency_graph
from up_esb.plexmo import PlanMonitor

# pylint: disable=all


class TestMonitor:
    """Test the PlanMonitor class."""

    @pytest.mark.parametrize("plan", list(get_example_plans().values()))
    def test_plan_monitor_setup(self, plan):
        graph = plan_to_dependency_graph(plan)
        monitor = PlanMonitor(graph)

        assert list(monitor._graph.nodes) == list(graph.nodes)
        assert list(monitor._graph.edges) == list(graph.edges)

        for _, node in monitor._graph.nodes(data=True):
            assert list(node.keys()) == [
                "processed",
                "action",
                "status",
                "node_name",
                "result",
                "predecessors",
                "successors",
            ]
