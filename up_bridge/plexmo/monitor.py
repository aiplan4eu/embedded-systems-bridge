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

from typing import List, Tuple

from unified_planning.engines import SequentialSimulator
from unified_planning.model.fnode import FNode
from unified_planning.model.problem import Problem
from unified_planning.model.state import ROState
from unified_planning.plans.plan import ActionInstance


class SequentialPlanMonitor:
    """Monitors a SequentialPlan"""

    def __init__(self, problem: Problem):
        self._simulator = SequentialSimulator(problem)

    def check_preconditions(
        self, instance: ActionInstance, state: ROState
    ) -> Tuple[bool, List[FNode]]:
        """
        Returns result of checking preconditions of a given `ActionInstance` in the `ROState`
        and a list of the precondtions that are not fulfilled.
        """
        events = self._simulator.get_events(instance.action, instance.actual_parameters)
        assert len(events) == 1
        self._simulator.is_applicable(events[0], state)
        unsatisfied = self._simulator.get_unsatisfied_conditions(
            events[0], state, early_termination=False
        )
        return (len(unsatisfied) == 0, unsatisfied)
