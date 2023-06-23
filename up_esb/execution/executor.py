"""Executor for executing tasks."""
from threading import Condition, Lock, Thread


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


class TaskExecutor:
    """Base class for task executors."""

    def __init__(self):
        self._lock = Lock()
        self._condition = Condition(self._lock)
        self._task = None
        self._thread = None
        self._task_tracker = None


class SequentialTaskExecutor(TaskExecutor):
    """Task executor that executes tasks sequentially."""

    def __init__(self):
        super().__init__()
