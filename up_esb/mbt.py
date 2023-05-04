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
A generic behavior tree implementation which executes one action (of type T) per call.
 Type T can be an abstract representation because each action is passed to the
 get_executable_action() method first before its executable representation is called.
 The behavior tree itself is mutable since you can modify it between calls, e.g.,
 to refine further actions at runtime depending on previous results.
"""


from typing import Callable, Generic, List, Tuple, TypeVar

T = TypeVar("T")


class Node(Generic[T]):
    def __init__(
        self,
        tree: "MutableBehaviorTree",
        actions: List[T],
        action_success_function: Callable[..., bool],
        action_continuation_function: Callable[..., bool],
    ) -> None:
        self.tree = tree
        self.actions = list(actions)
        self.action_success_function = action_success_function
        self.action_continuation_function = action_continuation_function
        self.subnodes: List[Node] = []

    def get_next_action(self) -> T:
        """Return the next action from this node's subnodes or itself."""
        if self.subnodes:
            return self.subnodes[0].get_next_action()

        if self.actions:
            return self.actions[0]

        raise RuntimeError("Cannot determine next action.")

    def execute_action(self) -> bool:
        """Execute the next of this node's actions."""
        # Get next executable action and parameters from tree.
        executable_action, parameters = self.tree.get_executable_action(self.actions.pop(0))
        # Execute action and store its result.
        result = executable_action(*parameters)
        self.tree.action_result = result
        # Determine the action's success based on the action_success_function, and return this.
        is_success = self.action_success_function(result)
        if not self.action_continuation_function(result):
            self.subnodes.clear()
            self.actions.clear()
        return is_success

    def execute(self) -> bool:
        """
        Execute the next action from this node's subnodes or itself.
        Return whether it was sucessful, determined by the action_success_function.
        """
        if self.subnodes:
            node = self.subnodes[0]
            is_success = node.execute()
            if not node.actions and not node.subnodes:
                self.subnodes.pop(0)
            return is_success

        if self.actions:
            return self.execute_action()

        return True


class MutableBehaviorTree(Generic[T]):
    def __init__(self) -> None:
        self.root = Node[T](self, [], lambda: False, lambda: False)
        self.active = True
        self.total_failure_count = 0
        self._action_result: object = None

    @property
    def action_result(self) -> object:
        return self._action_result

    @action_result.setter
    def action_result(self, value: object) -> None:
        self._action_result = value

    def set_actions(
        self,
        actions: List[T],
        action_success_function: Callable[..., bool] = lambda result: bool(result),
        action_continuation_function: Callable[..., bool] = lambda result: bool(result),
    ) -> None:
        """
        Set this behavior tree to execute actions, one per execute() call.
         Whether an action is considered successful, is determined by the action_success_function.
         Whether it should continue with the following actions, is determined by the
         action_continuation_function.
        """
        self.root.subnodes.clear()
        self.append_actions(actions, action_success_function, action_continuation_function)

    def prepend_actions(
        self,
        actions: List[T],
        action_success_function: Callable[..., bool] = lambda result: bool(result),
        action_continuation_function: Callable[..., bool] = lambda result: bool(result),
    ) -> None:
        """
        Prepend execution of actions before all other of this behavior tree, one per execute() call.
         Whether an action is considered successful, is determined by the action_success_function.
         Whether it should continue with the following actions, is determined by the
         action_continuation_function.
        """
        node = self.root
        while node.subnodes:
            node = node.subnodes[0]
        node.subnodes.append(
            Node[T](self, actions, action_success_function, action_continuation_function)
        )
        self.active = True

    def append_actions(
        self,
        actions: List[T],
        action_success_function: Callable[..., bool] = lambda result: bool(result),
        action_continuation_function: Callable[..., bool] = lambda result: bool(result),
    ) -> None:
        """
        Append execution of actions after all other of this behavior tree, one per execute() call.
         Whether an action is considered successful, is determined by the action_success_function.
         Whether it should continue with the following actions, is determined by the
         action_continuation_function.
        """
        self.root.subnodes.append(
            Node[T](self, actions, action_success_function, action_continuation_function)
        )
        self.active = True

    def has_next_action(self) -> bool:
        """Return whether this behavior tree has a next action."""
        return bool(self.root.subnodes)

    def get_next_action(self) -> T:
        """Return the next action of this behavior tree."""
        return self.root.get_next_action()

    def execute(self) -> bool:
        """
        Execute the next action of this behavior tree.
         Afterwards, remove completed and obsolete actions.
        """
        is_success = self.root.execute()
        # Count failures.
        if not is_success:
            self.total_failure_count += 1
        # Determine whether this tree's actions were successfully completed.
        elif not self.has_next_action():
            self.active = False
        return is_success

    def get_last_action_result(self) -> object:
        """Return the result of the last action execution."""
        return self.action_result

    def get_executable_action(self, action: T) -> Tuple[Callable[..., object], List[object]]:
        """Return the executable action and its parameters corresponding to action."""
        pass
