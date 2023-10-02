"""Exceptions for the execution module"""
from up_esb.execution import ActionResult
from up_esb.status import ActionNodeStatus, ConditionStatus


class UPESBException(Exception):
    """Raised when an exception occurs"""


class UPESBWarning(Warning):
    """Raised when a warning occurs"""


class ConditionNotMet(Exception):
    """Raised when a condition is not met"""


class ConditionTimeout(Exception):
    """Raised when a condition is not met within a certain time"""


class PreconditionsNotMet(Exception):
    """Raised when preconditions are not met"""


class PreconditionsTimeout(Exception):
    """Raised when preconditions are not met within a certain time"""


class PreconditionError(Exception):
    """Raised when a precondition is not met"""


class PreconditionWarn(Warning):
    """Raised when a precondition is not met"""


class PostconditionNotMet(Exception):
    """Raised when postconditions are not met"""


class PostconditionTimeout(Exception):
    """Raised when postconditions are not met within a certain time"""


class PostconditionError(Exception):
    """Raised when a postcondition is not met"""


class PostconditionWarn(Warning):
    """Raised when a postcondition is not met"""


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


class ActionError(Exception):
    """Raised when an action is not executed"""


class ActionWarn(Warning):
    """Raised when an action is not executed"""


def process_action_result(result: ActionResult) -> Exception:
    """Process the result of an action."""
    if result.precondition_status == ConditionStatus.FAILED:
        return PreconditionsNotMet(result.result)
    elif result.precondition_status == ConditionStatus.SKIPPED:
        return PreconditionWarn(result.result)
    elif result.precondition_status == ConditionStatus.NOT_STARTED:
        return PreconditionError(result.result)
    elif result.precondition_status == ConditionStatus.TIMEOUT:
        return PreconditionsTimeout(result.result)

    assert result.precondition_status == ConditionStatus.SUCCEEDED
    assert result.action_status is not None

    if result.action_status == ActionNodeStatus.FAILED:
        return ActionNotFinished(result.result)
    elif result.action_status == ActionNodeStatus.SKIPPED:
        return ActionWarn(result.result)
    elif result.action_status == ActionNodeStatus.NOT_STARTED:
        return ActionNotExecuted(result.result)
    elif result.action_status == ActionNodeStatus.TIMEOUT:
        return ActionTimeout(result.result)

    assert result.action_status == ActionNodeStatus.SUCCEEDED
    assert result.postcondition_status is not None

    if result.postcondition_status == ConditionStatus.FAILED:
        return PostconditionNotMet(result.result)
    if result.postcondition_status == ConditionStatus.SKIPPED:
        return PostconditionWarn(result.result)
    if result.postcondition_status == ConditionStatus.NOT_STARTED:
        return PostconditionError(result.result)
    if result.postcondition_status == ConditionStatus.TIMEOUT:
        return PostconditionTimeout(result.result)

    return UPESBException(result.result)
