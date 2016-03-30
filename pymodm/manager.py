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

import functools
import inspect

from pymodm.common import _import
from pymodm.compat import PY3
from pymodm.queryset import QuerySet


class BaseManager(object):
    # Creation counter to keep track of order within a Model.
    __creation_counter = 0

    def __init__(self):
        self.__counter = BaseManager.__creation_counter
        BaseManager.__creation_counter += 1

    def __get__(self, instance, cls):
        """Only let Manager be accessible from Model classes."""
        MongoModel = _import('pymodm.base.models.MongoModel')
        if isinstance(instance, MongoModel):
            raise AttributeError(
                "Manager isn't accessible via %s instances." % (cls.__name__,))
        return self

    def get_queryset(self):
        """Get a QuerySet instance."""
        return self._queryset_class(self.model)

    @property
    def creation_order(self):
        return self.__counter

    @classmethod
    def _get_queryset_methods(cls, queryset_class):
        def create_method(name, queryset_method):
            @functools.wraps(queryset_method)
            def manager_method(self, *args, **kwargs):
                return getattr(self.get_queryset(), name)(*args, **kwargs)
            return manager_method

        predicate = inspect.isfunction if PY3 else inspect.ismethod
        queryset_methods = inspect.getmembers(queryset_class, predicate)
        method_dict = {
            name: create_method(name, method)
            for name, method in queryset_methods
            # Don't shadow existing Manager methods.
            if not hasattr(cls, name)}
        return method_dict

    @classmethod
    def from_queryset(cls, queryset_class, class_name=None):
        """Create a Manager that delegates methods to the given QuerySet class.

        The type of the Manager is a subclass of this Manager.

        :parameters:
          - `queryset_class` The QuerySet class to be instantiated by the
            Manager.
          - `class_name` The name of the Manager class. If one is not provided,
            the name of the Manager will be XXXFromYYY, where XXX is the name
            of this Manager class, and YYY is the name of the QuerySet class.
        """
        if class_name is None:
            class_name = '%sFrom%s' % (cls.__name__, queryset_class.__name__)
        class_dict = dict(
            cls._get_queryset_methods(queryset_class),
            _queryset_class=queryset_class)
        return type(class_name, (cls,), class_dict)

    def contribute_to_class(self, cls, name):
        self.model = cls
        setattr(cls, name, self)


class Manager(BaseManager.from_queryset(QuerySet)):
    pass
