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

from pymodm.errors import ValidationError


def together(*funcs):
    """Run several validators successively on the same value."""
    def validator(value):
        for func in funcs:
            func(value)
    return validator


def validator_for_func(func):
    """Return a validator that re-raises any errors from the given function."""
    def validator(value):
        try:
            func(value)
        except Exception as exc:
            raise ValidationError(exc)
    return validator


def validator_for_type(types, value_name=None):
    """Return a validator that ensures its value is among the given `types`."""
    def validator(value):
        if not isinstance(value, types):
            if isinstance(types, tuple):  # multiple types
                type_names = tuple(t.__name__ for t in types)
                err = 'must be one of %r' % (type_names,)
            else:
                err = 'must be a %s' % types.__name__
            raise ValidationError(
                '%s %s, not %r'
                % (value_name or 'Value', err, value))
    return validator


def validator_for_geojson_type(geojson_type):
    """Return a validator that validates its value as having the given GeoJSON
    ``type``.
    """
    def validator(value):
        if value.get('type') != geojson_type:
            raise ValidationError(
                'GeoJSON type must be %r, not %r'
                % (geojson_type, value.get('type')))
    return validator


def validator_for_min_max(min, max):
    """Return a validator that validates its value against a minimum/maximum."""
    def validator(value):
        if min is not None and value < min:
            raise ValidationError(
                '%s is less than minimum value of %s.' % (value, min))
        if max is not None and value > max:
            raise ValidationError(
                '%s is greater than maximum value of %s.' % (value, max))
    return validator


def validator_for_length(min, max):
    """Return a validator that validates a given value's length."""
    def validator(value):
        len_value = len(value)
        if min is not None and len_value < min:
            raise ValidationError(
                '%s is under the minimum length of %d.' % (value, min))
        if max is not None and len_value > max:
            raise ValidationError(
                'value exceeds the maximum length of %d.' % (max,))
    return validator
