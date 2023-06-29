"""Executor for executing tasks."""
from threading import Condition, Lock, Thread
from typing import NamedTuple

import networkx as nx
from unified_planning.shortcuts import EndTiming, StartTiming, TimeInterval

from up_esb.status import ActionNodeStatus, ConditionStatus

# Action Result
ActionResult = NamedTuple(
    "ActionResult",
    [
        ("precondition_status", ConditionStatus),
        ("action_status", ActionNodeStatus),
        ("postcondition_status", ConditionStatus),
        ("result", object),
    ],
)


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


class ActionExecutor:
    """Base class for action executors."""

    def __init__(self, dependency_graph: nx.DiGraph, options: dict):
        self._dependency_graph = dependency_graph
        # Options
        self._options = options
        self._dry_run = options.get("dry_run", False)
        self._verbose = options.get("verbose", False)
        self._context = None
        self._action = None
        self._node_name = None
        self._parameters = None

    def execute_action(self, task_id):
        """Execute the given task."""
        self._context = self._dependency_graph.nodes[task_id]["context"]
        self._action = self._dependency_graph.nodes[task_id]["action"]
        self._node_name = self._dependency_graph.nodes[task_id]["node_name"]
        self._parameters = self._dependency_graph.nodes[task_id]["parameters"]

        precondition_status = action_status = postcondition_status = None

        # Check preconditions
        result = self._check_preconditions(task_id)
        if isinstance(result, Exception):
            precondition_status = ConditionStatus.FAILED, result
            action_status = ActionNodeStatus.FAILED, result
            return ActionResult(precondition_status, action_status, postcondition_status, result)
        elif result:
            precondition_status = ConditionStatus.SUCCEEDED, None

        # Execute action
        action_status = self._execute_action(task_id)

        if isinstance(action_status, Exception):
            result = RuntimeError(f"Action {self._action} failed with error: {action_status}")
            return ActionResult(precondition_status, action_status, postcondition_status, result)
        elif action_status:
            action_status = ActionNodeStatus.SUCCEEDED, None

        # Check postconditions
        result = self._check_postconditions(task_id)
        if isinstance(result, Exception):
            postcondition_status = ConditionStatus.FAILED, result
            action_status = ActionNodeStatus.FAILED, result
            return ActionResult(precondition_status, action_status, postcondition_status, result)
        elif result:
            postcondition_status = ConditionStatus.SUCCEEDED, None

        return ActionResult(precondition_status, action_status, postcondition_status, result)

    def _check_preconditions(self, task_id):
        raise NotImplementedError

    def _check_postconditions(self, task_id):
        raise NotImplementedError

    def _execute_action(self, task_id):
        """Execute the given task."""
        executor = self._context[self._action]

        # TODO: Proper setup of task tracker
        result = executor(**self._parameters)

        if result is None:
            return ActionNodeStatus.UNKNOWN
        elif result:
            return ActionNodeStatus.SUCCEEDED
        elif result is False:
            return ActionNodeStatus.FAILED


class InstantaneousTaskExecutor(ActionExecutor):
    """Task executor that executes tasks Instantaneous Task."""

    def __init__(self, dependency_graph: nx.DiGraph, options: dict):
        super().__init__(dependency_graph=dependency_graph, options=options)

    def _check_preconditions(self, task_id):
        """Check preconditions of the given task."""
        conditions = self._dependency_graph.nodes[task_id]["preconditions"]["start"]

        for i, condition in enumerate(conditions):
            result = eval(  # pylint: disable=eval-used
                compile(condition, filename="<ast>", mode="eval"), self._context
            )

            # Check if all preconditions return boolean True
            if not result and not self._dry_run:
                return RuntimeError(
                    f"Precondition {i+1} for action {self._node_name}{tuple(self._parameters.values())} failed!"
                )

        if self._verbose:
            print(f"Evaluated {len(conditions)} preconditions ...")

    def _check_postconditions(self, task_id):
        """Check postconditions of the given task."""
        post_conditions = self._dependency_graph.nodes[task_id]["postconditions"]

        for i, (_, conditions) in enumerate(post_conditions.items()):
            for condition, value in conditions:
                actual = eval(  # pylint: disable=eval-used
                    compile(condition, filename="<ast>", mode="eval"), self._context
                )
                expected = eval(  # pylint: disable=eval-used
                    compile(value, filename="<ast>", mode="eval"), self._context
                )

                if actual != expected and not self._dry_run:
                    return RuntimeError(
                        f"Postcondition {i+1} for action {self._node_name}{tuple(self._parameters.values())} failed!"
                    )
            if self._verbose:
                print(f"Evaluated {len(conditions)} postconditions ...")


# TODO: Make preconditions and post conditions perform things in parallel since sharing same time interval
class TemporalTaskExecutor(ActionExecutor):
    """Task executor that executes tasks Temporal Task."""

    def __init__(self, dependency_graph: nx.DiGraph, options: dict):
        super().__init__(dependency_graph=dependency_graph, options=options)

    def _check_preconditions(self, task_id):
        """Check preconditions of the given task."""
        conditions = self._dependency_graph.nodes[task_id]["preconditions"]

        start, end = StartTiming(), EndTiming()
        start_interval, end_interval = TimeInterval(start, start), TimeInterval(end, end)
        overall_interval = TimeInterval(start, end)
        intervals = list(conditions.keys())
        start_conditions = conditions[start_interval] if start_interval in intervals else []
        overall_conditions = conditions[overall_interval] if overall_interval in intervals else []
        end_conditions = conditions[end_interval] if end_interval in intervals else []

        # Check start conditions
        for i, condition in enumerate(start_conditions):
            result = self._check_precondition(condition)

            if not result:
                return RuntimeError(
                    f"Precondition (i+1) for action {self._node_name}{tuple(self._parameters.values())} failed!"
                )

        # Check overall conditions
        # Add threads for each overall condition
        # TODO: Add failure handling for threads
        for i, condition in enumerate(overall_conditions):
            thread = Thread(
                target=self._check_precondition,
                args=(condition,),
                name=f"overall_condition_{i+1}",
                daemon=True,
            )
            thread.start()

        # Check end conditions
        for i, condition in enumerate(end_conditions):
            result = self._check_precondition(condition)

            if not result:
                return RuntimeError(
                    f"Precondition (i+1) for action {self._node_name}{tuple(self._parameters.values())} failed!"
                )

    def _check_postconditions(self, task_id):
        conditions = self._dependency_graph.nodes[task_id]["postconditions"]

        start, end = StartTiming(), EndTiming()
        start_interval, end_interval = TimeInterval(start, start), TimeInterval(end, end)
        overall_interval = TimeInterval(start, end)
        intervals = list(conditions.keys())
        start_conditions = conditions[start_interval] if start_interval in intervals else []
        overall_conditions = conditions[overall_interval] if overall_interval in intervals else []
        end_conditions = conditions[end_interval] if end_interval in intervals else []

        # Check start conditions
        for i, (condition, value) in enumerate(start_conditions):
            result = self._check_postcondition(condition, value)

            if not result:
                return RuntimeError(
                    f"Postcondition {i+1} for action {self._node_name}{tuple(self._parameters.values())} failed!"
                )

        # Check overall conditions
        for i, (condition, value) in enumerate(overall_conditions):
            thread = Thread(
                target=self._check_postcondition,
                args=(condition, value),
                name=f"overall_condition_{i+1}",
                daemon=True,
            )
            thread.start()

        # Check end conditions
        for i, (condition, value) in enumerate(end_conditions):
            result = self._check_postcondition(condition, value)

            if not result:
                return RuntimeError(
                    f"Postcondition {i+1} for action {self._node_name}{tuple(self._parameters.values())} failed!"
                )

    def _check_precondition(self, condition):
        result = eval(  # pylint: disable=eval-used
            compile(condition, filename="<ast>", mode="eval"), self._context
        )

        return result

    def _check_postcondition(self, condition, value):
        """Check postconditions of the given task."""
        actual = eval(  # pylint: disable=eval-used
            compile(condition, filename="<ast>", mode="eval"), self._context
        )
        expected = eval(  # pylint: disable=eval-used
            compile(value, filename="<ast>", mode="eval"), self._context
        )

        return actual == expected
