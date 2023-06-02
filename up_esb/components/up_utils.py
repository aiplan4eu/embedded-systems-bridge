"""Utility functions for Unified Planning."""
from typing import Union

from unified_planning.model import FNode


def map_effect_value(value: FNode) -> Union[int, float, bool]:
    """Map effect value to UP value."""
    if value.is_constant():
        return value.constant_value()
    if value.is_bool_constant():
        return value.boolean_value()
    if value.is_int_constant():
        return value.int_value()

    raise NotImplementedError("Effect value not supported")
