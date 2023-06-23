"""Status Enum for up_esb"""
from enum import Enum, auto


class ActionNodeStatus(Enum):
    """ActionNode Enum"""

    NOT_STARTED = auto()
    STARTED = auto()
    IN_PROGRESS = auto()
    DONE = auto()
    FAILED = auto()
    SKIPPED = auto()


class ConditionStatus(Enum):
    """ConditionStatus Enum"""

    NOT_STARTED = auto()
    STARTED = auto()
    IN_PROGRESS = auto()
    DONE = auto()
    FAILED = auto()
    SKIPPED = auto()
    TIMEOUT = auto()


class DispatcherStatus(Enum):
    """DispatcherStatus Enum"""

    NOT_STARTED = auto()
    STARTED = auto()
    IN_PROGRESS = auto()
    FAILED = auto()
    FINISHED = auto()
