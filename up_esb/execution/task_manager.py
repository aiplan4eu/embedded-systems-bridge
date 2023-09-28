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
from typing import List, Union


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

    def __init__(self):
        self._container_lock = Lock()
        self._condition = Condition(self._container_lock)
        self._task: Union[int, List[int]] = 0
        self._task_tracker = None

    def __enter__(self):
        with self._container_lock:
            self._task_tracker = TaskTracker()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._container_lock:
            self._task_tracker.wait()
            self._task_tracker = None
            self._condition.notify()

    def add_task(self, task: Union[int, List[int]]) -> bool:
        """Add a single task to the execution queue."""
        if self._task is None:
            self._task = task
            return True
        return False

    def execute_task(self):
        """Execute the task."""
        if isinstance(self._task, int):
            self._execute_task(self._task)
        elif isinstance(self._task, list):
            self._execute_tasks(self._task)

    def _execute_task(self, task_id: int):
        """Execute a single task."""
        raise NotImplementedError

    def _execute_tasks(self, task_ids: List[int]):
        """Execute multiple tasks."""
        # TODO: Implement parallel execution of tasks
        raise NotImplementedError


class TaskManager:
    """Task Manager for the execution of tasks."""

    def __init__(self):
        self._lock = Lock()
        self._condition = Condition(self._lock)
        self._task = None
        self._thread = None
        self._execution_queue = []

    def add_task(self, task_id: int) -> bool:
        """Add a single task to the execution queue."""
        return self._add_task(task_id)

    def _add_task(self, task_id: int) -> bool:
        """Add a single task to the execution queue."""
        _container = TaskContainer()
        _container.add_task(task_id)
        if _container:
            self._execution_queue.append(_container)
            self._condition.notify()
            return True
        return False

    def add_tasks(self, task_ids: List[int]) -> bool:
        """Add multiple tasks on the same level to the execution queue."""
        return self._add_tasks(task_ids)

    def _add_tasks(self, task_ids: List[int]) -> bool:
        """Add multiple tasks to the execution queue."""
        _container = TaskContainer()
        _container.add_task(task_ids)
        if _container:
            self._execution_queue.append(_container)
            self._condition.notify()
            return True
        return False

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
