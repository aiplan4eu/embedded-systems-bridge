# Copyright 2022 Selvakumar H S, LAAS-CNRS
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

"""Action representation for the UP project."""
from typing import Callable


class ActionDefinition:
    """Action Definition bridge between Unified Planning and Application."""

    def __init__(self, name, **kwargs):
        self.name = name
        self.parameters = kwargs
        self.preconditions = []
        self.effects = []
        self.duration = 0
        self._execute_action: Callable = None

    def add_preconditions(self, preconditions):
        self.preconditions = preconditions

    def add_effects(self, effects):
        self.effects = effects

    def add_precondition(self, _callable: Callable, output=None, **kwargs):
        self.preconditions.append((_callable, output, kwargs))

    def add_effect(self, _callable: Callable, output=None, **kwargs):
        self.effects.append((_callable, output, kwargs))

    def set_duration(self, duration):
        self.duration = duration

    def _check_preconditions(self, preconditions=[]):
        ret = False
        for condition in preconditions:
            precondition, value, args = condition
            assert (
                precondition(expected_value=value, **args) == value
            ), f"{precondition} != {value}. Failed precondition."

            ret = True
        return ret

    def _execute_effects(self, effects=[]):
        ret = False
        for effect in effects:
            eff, value, args = effect
            result = eff(expected_value=value, **args)

            assert result == value, f"{result} != {value}. Failed effect."
            ret = True

        return ret

    def __call__(self, *args, **kwds):
        self._check_preconditions(self.preconditions)
        self._execute_effects(self.effects)
        self._execute_action(*args, **kwds)
