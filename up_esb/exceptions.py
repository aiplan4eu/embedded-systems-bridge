"""Exceptions for the execution module"""


class ConditionNotMet(Exception):
    """Raised when a condition is not met"""


class ConditionTimeout(Exception):
    """Raised when a condition is not met within a certain time"""


class PreconditionsNotMet(Exception):
    """Raised when preconditions are not met"""


class PreconditionsTimeout(Exception):
    """Raised when preconditions are not met within a certain time"""


class PostconditionsNotMet(Exception):
    """Raised when postconditions are not met"""


class PostconditionsTimeout(Exception):
    """Raised when postconditions are not met within a certain time"""


class ExecutionTimeout(Exception):
    """Raised when execution is not finished within a certain time"""


class ActionTimeout(Exception):
    """Raised when an action is not finished within a certain time"""


class ActionNotFinished(Exception):
    """Raised when an action is not finished"""


class ActionNotStarted(Exception):
    """Raised when an action is not started"""


class ActionNotExecuted(Exception):
    """Raised when an action is not executed"""
