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

"""Simple executor for UP Bridge. Currently no await is supported."""

import asyncio

import networkx as nx


# TODO: Move to dispatcher
class Executor:
    """Add simple executor for UP Bridge. Currently no await is supported.

    - Handles sequential, time-triggered and parallel actions
    """

    def __init__(self):
        pass

    def execute(self, graph: nx.DiGraph):
        """Execute the graph."""
        result = None
        for node in graph.nodes(data=True):
            if node[1]["node_name"] in ["start", "end"]:
                continue
            successors = list(graph.successors(node[0]))
            if len(successors) > 1:
                # Assume all successors are parallel actions

                # Fetch complete node data
                for s in successors:
                    successors[successors.index(s)] = (s, graph.nodes[s])
                self._execute_coroutines(successors)
            else:
                parameters = node[1]["parameters"]
                executor = node[1]["context"][node[1]["action"]]
                result = executor(**parameters)

        return result

    async def _execute_concurrent_action(self, action):
        # TODO: Better implementation
        # FIXME: Duplicate execution of actions
        parameters = action[1]["parameters"]
        executor = action[1]["context"][action[1]["action"]]
        result = executor(**parameters)

        return result

    async def _run_concurrent_tasks(self, tasks):
        # TODO: add await on parallel actions
        await asyncio.gather(*tasks)

    def _execute_coroutines(self, actions):
        tasks = [self._execute_concurrent_action(a) for a in actions]
        asyncio.run(self._run_concurrent_tasks(tasks))
