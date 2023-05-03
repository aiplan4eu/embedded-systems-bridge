from typing import Callable, List, Tuple

from unified_planning.plans.plan import ActionInstance

from up_esb.bridge import Bridge
from up_esb.mbt import MutableBehaviorTree

"""
Simple inheritance of the generic behavior tree to retrieve an executable action
 from a Unified Planning ActionInstance by querying the up_esb.brindge.
"""


class Orchestrator(MutableBehaviorTree[ActionInstance]):
    def __init__(self, bridge: Bridge) -> None:
        super().__init__()
        self.bridge = bridge

    def get_executable_action(
        self, action: ActionInstance
    ) -> Tuple[Callable[..., object], List[object]]:
        return self.bridge.get_executable_action(action)
