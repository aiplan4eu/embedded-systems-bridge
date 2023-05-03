# Software License Agreement (BSD License)
#
#  Copyright (c) 2023, DFKI GmbH
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.
#   * Neither the name of Willow Garage nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.

"""
A generic behavior tree implementation which executes one action per call.
 Basically you can modify the tree between calls, e.g., to refine an action at runtime.
"""


from typing import Callable, Generic, List, Optional, Tuple, TypeVar

T = TypeVar("T")


class Node(Generic[T]):
    def __init__(
        self,
        tree: "MutableBehaviorTree",
        action_success_function: Callable[..., bool],
        is_done_on_success: bool,
    ) -> None:
        self.tree = tree
        self.action_success_function = action_success_function
        self.is_done_on_success = is_done_on_success
        self.subnodes: List[Node] = []
        self.actions: List[T] = []

    def get_next_action(self) -> T:
        """Return the next action from this node or its subnodes."""
        if self.actions:
            return self.actions[0]

        if self.subnodes:
            return self.subnodes[0].get_next_action()

        raise RuntimeError("Cannot determine next action.")

    def execute_action(self) -> bool:
        """Execute the next of this node's actions."""
        # Get next executable action and parameters from bridge.
        executable_action, parameters = self.tree.get_executable_action(self.actions.pop(0))
        # Execute action and store its result.
        result = executable_action(*parameters)
        self.tree.action_result = result
        # Determine the action's success based on the action_success_function, and return this.
        is_success = self.action_success_function(result)
        if is_success and self.is_done_on_success:
            self.subnodes.clear()
            self.actions.clear()
        return is_success

    def execute(self) -> bool:
        """
        Execute the next action from this node or its subnodes.
        Return whether it was sucessful, determined by the action_success_function.
        """
        if self.actions:
            return self.execute_action()

        if self.subnodes:
            node = self.subnodes[0]
            is_success = node.execute()
            if not node.actions and not node.subnodes:
                self.subnodes.pop(0)
            return is_success

        return False


class MutableBehaviorTree(Generic[T]):
    def __init__(self) -> None:
        self.root: Optional[Node[T]] = None
        self.active = True
        self.total_failure_count = 0
        self._action_result: object = None

    @property
    def action_result(self) -> object:
        return self._action_result

    @action_result.setter
    def action_result(self, value: object) -> None:
        self._action_result = value

    def set_action_sequence(
        self,
        actions: List[T],
        action_success_function: Callable[..., bool] = lambda result: bool(result),
    ) -> None:
        """
        Update this behavior tree by a sequence of actions. Whether an action is
         considered successful, is determined by the action_success_function.
        """
        self.root = Node[T](self, action_success_function, False)
        self.root.actions = list(actions)
        self.active = True

    def has_next_action(self) -> bool:
        """Return whether this behavior tree has a next action."""
        return self.root and (self.root.actions or self.root.subnodes)

    def get_next_action(self) -> T:
        """Return the next action of this behavior tree."""
        assert self.root, "Behavior Tree has no actions."
        return self.root.get_next_action()

    def execute(self) -> bool:
        """
        Execute the next action of this behavior tree.
        Afterwards, remove completed and obsolete actions.
        """
        is_success = self.root.execute()
        # Update whether there is at least one more action after the current one.
        self.active = self.has_next_action()
        # Count failures.
        if not is_success:
            self.total_failure_count += 1
        return is_success

    def get_last_action_result(self) -> object:
        """Return the result of the last action execution."""
        return self.action_result

    def get_executable_action(self, action: T) -> Tuple[Callable[..., object], List[object]]:
        """Return the executable action and its parameters corresponding to action."""
        pass
