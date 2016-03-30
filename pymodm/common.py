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

import re

from collections import Mapping
from importlib import import_module

from pymodm.errors import ModelDoesNotExist

from pymodm.compat import string_types


# Mapping of class names to class objects.
# Used for fields that nest or reference other Model classes.
_DOCUMENT_REGISTRY = {}

# Mapping of fully-qualified names to their imported objects.
_IMPORT_CACHE = {}

CTS1 = re.compile('(.)([A-Z][a-z]+)')
CTS2 = re.compile('([a-z0-9])([A-Z])')


def snake_case(camel_case):
    snake = re.sub(CTS1, r'\1_\2', camel_case)
    snake = re.sub(CTS2, r'\1_\2', snake)
    return snake.lower()


def _import(full_name):
    """Avoid circular imports without re-importing each time."""
    if full_name in _IMPORT_CACHE:
        return _IMPORT_CACHE[full_name]

    module_name, class_name = full_name.rsplit('.', 1)
    module = import_module(module_name)

    _IMPORT_CACHE[full_name] = getattr(module, class_name)
    return _IMPORT_CACHE[full_name]


def register_document(document):
    key = '%s.%s' % (document.__module__, document.__name__)
    _DOCUMENT_REGISTRY[key] = document


def get_document(name):
    """Retrieve the definition for a class by name."""
    if name in _DOCUMENT_REGISTRY:
        return _DOCUMENT_REGISTRY[name]

    possible_matches = []
    for key in _DOCUMENT_REGISTRY:
        parts = key.split('.')
        if name == parts[-1]:
            possible_matches.append(key)
    if len(possible_matches) == 1:
        return _DOCUMENT_REGISTRY[possible_matches[0]]
    raise ModelDoesNotExist('No document type by the name %r.' % (name,))


#
# Type validation.
#

def validate_string(option, value):
    if not isinstance(value, string_types):
        raise TypeError('%s must be a string type, not a %s'
                        % (option, value.__class__.__name__))
    return value


def validate_string_or_none(option, value):
    if value is None:
        return value
    return validate_string(option, value)


def validate_boolean(option, value):
    if not isinstance(value, bool):
        raise TypeError('%s must be a boolean, not a %s'
                        % (option, value.__class__.__name__))
    return value


def validate_boolean_or_none(option, value):
    if value is None:
        return value
    return validate_boolean(option, value)


def validate_list_or_tuple(option, value):
    if not isinstance(value, (list, tuple)):
        raise TypeError('%s must be a list or a tuple, not a %s'
                        % (option, value.__class__.__name__))
    return value


def validate_list_tuple_or_none(option, value):
    if value is None:
        return value
    return validate_list_or_tuple(option, value)


def validate_mapping(option, value):
    if not isinstance(value, Mapping):
        raise TypeError('%s must be a Mapping, not a %s'
                        % (option, value.__class__.__name__))
    return value
