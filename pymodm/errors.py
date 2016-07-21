# Copyright 2016 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tools and types for Exception handling."""
from pymodm.compat import text_type


class DoesNotExist(Exception):
    pass


class MultipleObjectsReturned(Exception):
    pass


class ConnectionError(Exception):
    pass


class ModelDoesNotExist(Exception):
    """Raised when a reference to a Model cannot be resolved."""
    pass


class InvalidModel(Exception):
    """Raised if a Model definition is invalid."""
    pass


class ValidationError(Exception):
    """Indicates an error while validating data.

    A ValidationError may contain a single error, a list of errors, or even a
    dictionary mapping field names to errors. Any of these cases are acceptable
    to pass as a "message" to the constructor for ValidationError.
    """

    def __init__(self, message, **kwargs):
        self._message = message

    def _get_message(self, message):
        if isinstance(message, ValidationError):
            return message.message
        elif isinstance(message, Exception):
            return text_type(message)
        elif isinstance(message, list):
            message_list = []
            for item in message:
                extracted = self._get_message(item)
                if isinstance(extracted, list):
                    message_list.extend(extracted)
                else:
                    message_list.append(extracted)
            return message_list
        elif isinstance(message, dict):
            return {key: self._get_message(message[key])
                    for key in message}
        return message

    @property
    def message(self):
        return self._get_message(self._message)

    def __str__(self):
        return text_type(self.message)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self)


class OperationError(Exception):
    """Raised when an operation cannot be performed."""


class ConfigurationError(Exception):
    """Raised when there is a configuration error."""
