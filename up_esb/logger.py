# Copyright 2023, Selvakumar H S, LAAS-CNRS
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
import logging


class Logger:
    """Logger module for UP-ESB"""

    LEVEL = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARN": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }

    def __init__(self, _module_name: str = "up-esb", _level=LEVEL["INFO"]) -> None:
        self.logger = logging.getLogger(_module_name)

        if not self.logger.handlers:
            console = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)-8s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            console.setFormatter(formatter)
            self.logger.addHandler(console)
            self.logger.setLevel(_level)
            self.logger.propagate = False

    def info(self, _message: str) -> None:
        """Information that need to be logged

        Args:
            _message (str): Message to be logged
        """
        # Green
        _message = f"\033[92m{_message}\033[0m"
        self.logger.info(_message)

    def debug(self, _message: str) -> None:
        """Debugging messages that need to be logged

        Args:
            _message (str): Message to be logged
        """
        # Blue
        _message = f"\033[94m{_message}\033[0m"
        self.logger.debug(_message)

    def warning(self, _message: str) -> None:
        """Warning messages that need to be logged

        Args:
            _message (str): Message to be logged
        """
        # Yellow
        _message = f"\033[93m{_message}\033[0m"
        self.logger.warning(_message)

    def error(self, _message: str, traceback: bool = False) -> None:
        """Error messages that need to be logged

        Args:
            _message (str): Message to be logged
        """
        # Red
        _message = f"\033[91m{_message}\033[0m"
        self.logger.error(_message, exc_info=traceback)

    def critical(self, _message: str, traceback: bool = False) -> None:
        """Critical error messages that need to be logged

        Args:
            _message (str): Message to be logged
        """
        # Red with background
        _message = f"\033[41m{_message}\033[0m"
        self.logger.critical(_message, exc_info=traceback)
