# Copyright 2022 Sebastian Stock, DFKI
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
"""Monitoring of a SequentialPlan."""
from typing import List, Tuple

from unified_planning.engines import UPSequentialSimulator
from unified_planning.model.fnode import FNode
from unified_planning.model.problem import Problem
from unified_planning.model.state import State
from unified_planning.plans.plan import ActionInstance


class SequentialPlanMonitor:
    """Monitors a SequentialPlan"""

    def __init__(self, problem: Problem):
        self._simulator = UPSequentialSimulator(problem)

    def check_preconditions(
        self, instance: ActionInstance, state: State
    ) -> Tuple[bool, List[FNode]]:
        """
        Returns result of checking preconditions of a given `ActionInstance` in the `State`
        and a list of the precondtions that are not fulfilled.
        """
        unsatisfied = self._simulator.get_unsatisfied_conditions(
            state, instance.action, instance.actual_parameters, early_termination=False
        )
        return (len(unsatisfied) == 0, unsatisfied)
