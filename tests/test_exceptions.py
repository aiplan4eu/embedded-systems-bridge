# Copyright 2023 Selvakumar H S, LAAS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from up_esb.exceptions import *  # pylint: disable=unused-wildcard-import
from up_esb.execution import ActionResult
from up_esb.status import ActionNodeStatus, ConditionStatus

expected_precondition_exceptions = [
    (ActionResult(ConditionStatus.FAILED, None, None, "Test exception"), PreconditionsNotMet),
    (ActionResult(ConditionStatus.TIMEOUT, None, None, "Test exception"), PreconditionsTimeout),
    (ActionResult(ConditionStatus.SKIPPED, None, None, "Test exception"), PreconditionWarn),
    (
        ActionResult(
            ConditionStatus.NOT_STARTED, ActionNodeStatus.NOT_STARTED, None, "Test exception"
        ),
        PreconditionError,
    ),
    (ActionResult(ConditionStatus.SUCCEEDED, None, None, "Test exception"), AssertionError),
]

expected_action_exceptions = [
    (ActionResult(None, ActionNodeStatus.FAILED, None, "Test exception"), AssertionError),
    (
        ActionResult(ConditionStatus.SUCCEEDED, ActionNodeStatus.TIMEOUT, None, "Test exception"),
        ActionTimeout,
    ),
    (
        ActionResult(ConditionStatus.SUCCEEDED, ActionNodeStatus.SKIPPED, None, "Test exception"),
        ActionWarn,
    ),
    (
        ActionResult(ConditionStatus.FAILED, ActionNodeStatus.NOT_STARTED, None, "Test exception"),
        PreconditionsNotMet,
    ),
]

expected_postcondition_exceptions = [
    (
        ActionResult(ConditionStatus.SUCCEEDED, ActionNodeStatus.SUCCEEDED, None, "Test exception"),
        AssertionError,
    ),
    (
        ActionResult(
            ConditionStatus.SUCCEEDED,
            ActionNodeStatus.SUCCEEDED,
            ConditionStatus.FAILED,
            "Test exception",
        ),
        PostconditionNotMet,
    ),
    (
        ActionResult(
            ConditionStatus.SUCCEEDED,
            ActionNodeStatus.SUCCEEDED,
            ConditionStatus.SKIPPED,
            "Test exception",
        ),
        PostconditionWarn,
    ),
    (
        ActionResult(
            ConditionStatus.SUCCEEDED,
            ActionNodeStatus.SUCCEEDED,
            ConditionStatus.TIMEOUT,
            "Test exception",
        ),
        PostconditionTimeout,
    ),
    (
        ActionResult(
            ConditionStatus.FAILED,
            ActionNodeStatus.SUCCEEDED,
            ConditionStatus.SUCCEEDED,
            "Test exception",
        ),
        PreconditionsNotMet,
    ),
]


class TestException:
    """Test exception classes."""

    @pytest.mark.parametrize("result, exception", expected_precondition_exceptions)
    def test_precondition_exceptions(self, result: ActionResult, exception: Exception):
        """Test precondition exceptions."""
        with pytest.raises(expected_exception=exception):
            raise process_action_result(result)

    @pytest.mark.parametrize("result, exception", expected_action_exceptions)
    def test_action_exceptions(self, result: ActionResult, exception: Exception):
        """Test action exceptions."""
        with pytest.raises(expected_exception=exception):
            raise process_action_result(result)

    @pytest.mark.parametrize("result, exception", expected_postcondition_exceptions)
    def test_postcondition_exceptions(self, result: ActionResult, exception: Exception):
        """Test postcondition exceptions."""
        with pytest.raises(expected_exception=exception):
            raise process_action_result(result)
