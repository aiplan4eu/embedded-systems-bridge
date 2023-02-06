"""Simple executor for UP Bridge. Currently no await is supported."""

import asyncio

import networkx as nx


class Executor:
    """Add simple executor for UP Bridge. Currently no await is supported.

    - Handles sequential, time-triggered and parallel actions
    """

    def __init__(self):
        pass

    def execute(self, graph: nx.DiGraph = None):
        for node in graph.nodes(data=True):
            if node[0] in ["start", "end"]:
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
                result = node[1]["executor"]()(*parameters)

    async def _execute_concurrent_action(self, action):
        # TODO: Better implementation
        # FIXME: Duplicate execution of actions
        parameters = action[1]["parameters"]
        result = action[1]["executor"]()(*parameters)

    async def _run_concurrent_tasks(self, tasks):
        # TODO: add await on parallel actions
        await asyncio.gather(*tasks)

    def _execute_coroutines(self, actions):
        tasks = [self._execute_concurrent_action(a) for a in actions]
        asyncio.run(self._run_concurrent_tasks(tasks))