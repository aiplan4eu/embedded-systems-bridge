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
"""Task Manager for the execution of tasks."""
from threading import Condition, Lock
from typing import List, Optional

import networkx as nx
from unified_planning.plans import Plan

from up_esb.execution import ActionExecutor


class TaskTracker:
    """Track the amount of tasks that is being executed."""

    def __init__(self):
        self._lock = Lock()
        self._condition = Condition(self._lock)
        self._tasks = 0

    def __enter__(self):
        with self._lock:
            self._tasks += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            self._tasks -= 1
            self._condition.notify()

    def wait(self):
        """Wait until all tasks are finished."""
        with self._lock:
            while self._tasks > 0:
                self._condition.wait()


class TaskContainer:
    """Task container for enveloping one or more actions."""

    def __init__(self, graph: nx.DiGraph):
        self._container_lock = Lock()
        self._condition = Condition(self._container_lock)
        self._tasks: List[nx.DiGraph] = []
        self._task_tracker = None
        self._graph = graph
        self._executor: Optional[ActionExecutor] = None

    def __enter__(self):
        with self._container_lock:
            self._task_tracker = TaskTracker()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._container_lock:
            self._task_tracker.wait()
            self._task_tracker = None
            self._condition.notify()

    def add_task(self, task_id: int) -> bool:
        """Add a task to the execution queue."""
        if task_id not in self._graph.nodes:
            return False

        self._tasks.append(task_id)
        return True

    def execute_task(self):
        """Execute the task."""
        with self._container_lock:
            if len(self._tasks) == 1:
                self._execute_task(self._tasks[0])
            else:
                self._execute_tasks(self._tasks)

    def set_executor(self, executor: ActionExecutor):
        """Set the executor for the task container."""
        self._executor = executor

    def _execute_task(self, task):
        """Execute a single task."""
        self._executor.execute(task)

    def _execute_tasks(self, task_ids: List[int]):
        """Execute multiple tasks."""
        # TODO: Implement parallel execution of tasks
        raise NotImplementedError


class TaskManager:
    """Task Manager for the execution of tasks."""

    def __init__(self, plan: Plan, graph: nx.DiGraph, **options):
        self._graph = graph
        self._options = options
        self._executor = ActionExecutor(graph, options=options).get_executor(plan)
        self._execution_queue: List[TaskContainer] = []
        self._dispatch_cb = None

    def add_task(self, task_id: int) -> bool:
        """Add a single task to the execution queue."""
        return self._add_task(task_id)

    def _add_task(self, task_id: int) -> bool:
        """Add a single task to the execution queue."""
        _container = TaskContainer(self._graph)
        _container.add_task(task_id)
        _container.set_executor(self._executor)
        if _container:
            self._execution_queue.append(_container)
            return True
        return False

    def add_tasks(self, task_ids: List[int]) -> bool:
        """Add multiple tasks on the same level to the execution queue."""
        return self._add_tasks(task_ids)

    def _add_tasks(self, task_ids: List[int]) -> bool:
        """Add multiple tasks to the execution queue."""
        _container = TaskContainer(self._graph)
        _container.set_executor(self._executor)

        for task_id in task_ids:
            _container.add_task(task_id)

            if not _container:
                return False

        self._execution_queue.append(_container)
        return True

    def remove_task(self, task_id: int) -> bool:
        """Remove a task from the execution queue."""
        return self._remove_task(task_id)

    def _remove_task(self, task_id: int) -> bool:
        """Remove a task from the execution queue."""
        raise NotImplementedError

    def remove_tasks(self, task_ids: List[int]) -> bool:
        """Remove multiple tasks on the same level from the execution queue."""
        return self._remove_tasks(task_ids)

    def _remove_tasks(self, task_ids: List[int]) -> bool:
        """Remove multiple tasks from the execution queue."""
        raise NotImplementedError

    def set_dispatch_callback(self, callback):
        """Set the callback function for dispatching tasks."""
        self._dispatch_cb = callback

    def step(self):
        """Step the execution of the task manager."""
        if not self._execution_queue:
            return

        container = self._execution_queue.pop(0)
        with container:
            container.execute_task()
