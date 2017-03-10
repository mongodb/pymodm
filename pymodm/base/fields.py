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
import bson

from pymodm import validators
from pymodm.common import (
    _import, get_document,
    validate_string_or_none, validate_boolean, validate_list_tuple_or_none,
    validate_mongo_field_name_or_none)
from pymodm.compat import string_types
from pymodm.errors import ValidationError


class MongoBaseField(object):
    """Base class for all MongoDB Model Field types."""
    # Creation counter used to keep track of field ordering within Models.
    __creation_counter = 0

    empty_values = [[], (), {}, None, '', b'', set()]

    def __init__(self, verbose_name=None, mongo_name=None, primary_key=False,
                 blank=False, required=False, default=None, choices=None,
                 validators=None):
        """Create a new Field instance.

        :parameters:
          - `verbose_name`: A human-readable name for the Field.
          - `mongo_name`: The name of this field when stored in MongoDB.
          - `primary_key`: If ``True``, this Field will be used for the ``_id``
            field when stored in MongoDB. Note that the `mongo_name` of the
            primary key field cannot be changed from ``_id``.
          - `blank`: If ``True``, allow this field to have an empty value.
          - `required`: If ``True``, do not allow this field to be unspecified.
          - `default`: The default value to use for this field if no other value
            has been given. If ``default`` is callable, then the return value of
            ``default()`` will be used as the default value.
          - `choices`: A list of possible values for the field. This can be a
            flat list, or a list of 2-tuples consisting of an allowed field
            value and a human-readable version of that value.
          - `validators`: A list of callables used to validate this Field's
            value.
        """
        self._verbose_name = validate_string_or_none(
            'verbose_name', verbose_name)
        self.primary_key = validate_boolean('primary_key', primary_key)
        self.mongo_name = self._validate_mongo_name(mongo_name)
        self.blank = validate_boolean('blank', blank)
        self.required = validate_boolean('required', required)
        self.choices = validate_list_tuple_or_none('choices', choices)
        self.validators = validate_list_tuple_or_none(
            'validators', validators or [])
        self.default = default
        # "attname" is the attribute name of this field on the Model.
        # We may be assigned a different name by the Model's metaclass later on.
        self.attname = self.mongo_name
        self.__counter = MongoBaseField.__creation_counter
        MongoBaseField.__creation_counter += 1

    def _validate_mongo_name(self, mongo_name, attname=None):
        if not self.primary_key and mongo_name == '_id':
            field_msg = ' of field %s' % (attname,) if attname else ''
            raise ValueError(
                'mongo_name%s is "_id", but primary_key is False.'
                % (field_msg,))
        if self.primary_key:
            if mongo_name not in (None, '_id'):
                raise ValueError(
                    'The mongo_name of a primary key must be "_id".')
            return '_id'
        return validate_mongo_field_name_or_none('mongo_name', mongo_name)

    def __get__(self, inst, owner):
        MongoModelBase = _import('pymodm.base.models.MongoModelBase')
        if inst is not None and isinstance(inst, MongoModelBase):
            raw_value = inst._data.get(self.attname, self.get_default())
            if self.is_blank(raw_value):
                return raw_value
            # Cache pythonized value.
            python_value = self.to_python(raw_value)
            self.__set__(inst, python_value)
            return python_value
        # Access from outside a Model instance.
        return self

    def __set__(self, inst, value):
        inst._data[self.attname] = value

    def __delete__(self, inst):
        inst._data.pop(self.attname, None)

    def get_default(self):
        return self.default() if callable(self.default) else self.default

    def is_blank(self, value):
        """Determine if the value is blank."""
        return value in self.empty_values

    def is_undefined(self, inst):
        """Determine if a field is undefined (has not been given any value)."""
        return self.attname not in inst._data

    @property
    def verbose_name(self):
        return self._verbose_name or self.attname or self.mongo_name

    @verbose_name.setter
    def verbose_name(self, name):
        self._verbose_name = name

    def to_python(self, value):
        """Coerce the raw value for this field to an appropriate Python type.

        Sub-classes should override this method to perform custom conversion
        when this field is accessed from a :class:`~pymodm.MongoModel`
        instance.

        """
        return value

    def to_mongo(self, value):
        """Get the value of this field as it should be stored in MongoDB.

        Sub-classes should override this method to perform custom conversion
        before the value of this field is stored in MongoDB.

        """
        return self.to_python(value)

    def _validate_choices(self, value):
        # Is self.choices a list of pairs? A flat list?
        if isinstance(self.choices[0], (list, tuple)):
            flat_choices = [pair[0] for pair in self.choices]
            if value not in flat_choices:
                raise ValidationError(
                    '%r is not a choice. Choices are %r.'
                    % (value, flat_choices))
        elif value not in self.choices:
            raise ValidationError(
                '%r is not a choice. Choices are %r.'
                % (value, self.choices))

    def validate(self, value):
        """Validate the value of this field."""
        # If the field hasn't been set, then don't validate.
        if self.is_blank(value):
            if self.blank:
                # Allowed blank fields don't need further validation.
                return
            else:
                raise ValidationError('must not be blank (was: %r)' % value)

        value = self.to_python(value)

        if self.choices:
            self._validate_choices(value)

        # Run all validators on the given value.
        error_list = []
        for v in self.validators:
            try:
                v(value)
            except Exception as e:
                error_list.append(e)
        if error_list:
            raise ValidationError(error_list)

    @property
    def creation_order(self):
        """Get the creation order of this Field."""
        return self.__counter

    def value_from_object(self, instance):
        """Get the value of this field from the given Model instance."""
        return getattr(instance, self.attname)

    def __eq__(self, other):
        if isinstance(other, MongoBaseField):
            return self.creation_order == other.creation_order
        return NotImplemented

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        # This is needed because bisect does not take a comparison function.
        if isinstance(other, MongoBaseField):
            return self.creation_order < other.creation_order
        return NotImplemented

    def contribute_to_class(self, cls, name):
        """Callback executed when adding this Field to a Model."""
        self.attname = name
        # The empty string is a valid MongoDB field name.
        if self.mongo_name is None:
            self.mongo_name = self._validate_mongo_name(name, attname=name)
        self.model = cls
        if self.primary_key and not cls._mongometa.implicit_id:
            self.required = True
        cls._mongometa.add_field(self)
        setattr(cls, name, self)


class RelatedModelFieldsBase(MongoBaseField):
    """Base class for Field types that reference another Model type."""

    def __init__(self, model, verbose_name=None, mongo_name=None, **kwargs):
        super(RelatedModelFieldsBase, self).__init__(verbose_name=verbose_name,
                                                     mongo_name=mongo_name,
                                                     **kwargs)
        self.__model = model
        self.__related_model = None

        MongoModelBase = _import('pymodm.base.models.MongoModelBase')
        if not (isinstance(model, string_types) or
                (isinstance(model, type) and
                 issubclass(model, MongoModelBase))):
            raise ValueError('model must be a Model class or a string, not %s'
                             % model.__class__.__name__)

    @property
    def related_model(self):
        if not self.__related_model:
            MongoModelBase = _import('pymodm.base.models.MongoModelBase')
            if isinstance(self.__model, string_types):
                self.__related_model = get_document(self.__model)
            # 'issubclass' complains if first argument is not a class.
            elif (isinstance(self.__model, type) and
                  issubclass(self.__model, MongoModelBase)):
                self.__related_model = self.__model
        return self.__related_model

    def _model_to_document(self, value):
        if isinstance(value, bson.SON):
            # value has been already converted
            return value

        if isinstance(value, self.related_model):
            return value.to_son()

        if isinstance(value, dict):
            # if value is a dict convert in to model
            # so we can properly generate SON
            return self.related_model.from_document(value).to_son()

        # we could not convert value to SON
        raise ValidationError(
            '%s is not a valid %s' % (value, self.related_model.__name__))


class GeoJSONField(MongoBaseField):
    """Base class for GeoJSON fields."""

    def __init__(self, verbose_name=None, mongo_name=None, **kwargs):
        """
        :parameters:
          - `verbose_name`: A human-readable name for the Field.
          - `mongo_name`: The name of this field when stored in MongoDB.

        .. seealso:: constructor for
                     :class:`~pymodm.base.fields.MongoBaseField`
        """
        super(GeoJSONField, self).__init__(verbose_name=verbose_name,
                                           mongo_name=mongo_name,
                                           **kwargs)

        self.validators.append(self.validate_geojson)

    @classmethod
    def validate_geojson(cls, value):
        validators.validator_for_type(dict)(value)
        validators.validator_for_geojson_type(
            cls._geojson_name)(value)
        coordinates = value.get('coordinates')
        validators.validator_for_type(
            (list, tuple), 'Coordinates')(coordinates)
        cls.validate_coordinates(coordinates)

    def to_python(self, value):
        if isinstance(value, list):
            return {'type': self._geojson_name, 'coordinates': value}
        return value
