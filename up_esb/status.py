"""Status Enum for up_esb"""
from enum import Enum, auto


class ActionNodeStatus(Enum):
    """ActionNode Enum"""

    NOT_STARTED = auto()
    STARTED = auto()
    IN_PROGRESS = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    SKIPPED = auto()
    UNKNOWN = auto()


class ConditionStatus(Enum):
    """ConditionStatus Enum"""

    NOT_STARTED = auto()
    STARTED = auto()
    IN_PROGRESS = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    SKIPPED = auto()
    TIMEOUT = auto()


class DispatcherStatus(Enum):
    """DispatcherStatus Enum"""

    IDLE = auto()
    STARTED = auto()
    IN_PROGRESS = auto()
    FAILED = auto()
    FINISHED = auto()


class MonitorStatus(Enum):
    """MonitorStatus Enum"""

    IDLE = auto()
    STARTED = auto()
    IN_PROGRESS = auto()
    FAILED = auto()
    FINISHED = auto()
    TIMEOUT = auto()
