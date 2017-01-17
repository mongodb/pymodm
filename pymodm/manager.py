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
    """Abstract base class for all Managers.

    `BaseManager` has no underlying :class:`~pymodm.queryset.QuerySet`
    implementation. To extend this class into a concrete class, a `QuerySet`
    implementation must be provided by calling :meth:`~from_queryset`::

        class MyQuerySet(QuerySet):
            ...

        MyManager = BaseManager.from_queryset(MyQuerySet)

    Extending this class by calling `from_queryset` creates a new Manager class
    that wraps only the methods from the given `QuerySet` type (and not from the
    default `QuerySet` implementation).

    .. seealso:: The default :class:`~pymodm.manager.Manager`.

    """
    # Creation counter to keep track of order within a Model.
    __creation_counter = 0

    def __init__(self):
        self.__counter = BaseManager.__creation_counter
        BaseManager.__creation_counter += 1

    def __get__(self, instance, cls):
        """Only let Manager be accessible from Model classes."""
        TopLevelMongoModel = _import('pymodm.base.models.TopLevelMongoModel')
        if isinstance(instance, TopLevelMongoModel):
            raise AttributeError(
                "Manager isn't accessible via %s instances." % (cls.__name__,))
        return self

    def get_queryset(self):
        """Get a QuerySet instance."""
        return self._queryset_class(self.model)

    @property
    def creation_order(self):
        """The order in which this Manager instance was created."""
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
        """Create a Manager that delegates methods to the given
        :class:`~pymodm.queryset.QuerySet` class.

        The Manager class returned is a subclass of this Manager class.

        :parameters:
          - `queryset_class`: The QuerySet class to be instantiated by the
            Manager.
          - `class_name`: The name of the Manager class. If one is not provided,
            the name of the Manager will be `XXXFromYYY`, where `XXX`
            is the name of this Manager class, and YYY is the name of the
            QuerySet class.

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
    """The default manager used for :class:`~pymodm.MongoModel` instances.

    This implementation of :class:`~pymodm.manager.BaseManager` uses
    :class:`~pymodm.queryset.QuerySet` as its QuerySet class.

    This Manager class (accessed via the ``objects`` attribute on a
    :class:`~pymodm.MongoModel`) is used by default for all MongoModel classes,
    unless another Manager instance is supplied as an attribute within the
    MongoModel definition.

    Managers have two primary functions:

    1. Construct :class:`~pymodm.queryset.QuerySet` instances for use when
       querying or working with :class:`~pymodm.MongoModel` instances in bulk.
    2. Define collection-level functionality that can be reused across different
       MongoModel types.

    If you created a custom QuerySet that makes certain queries easier, for
    example, you will need to create a custom Manager type that returns this
    queryset using the :meth:`~pymodm.manager.BaseManager.from_queryset`
    method::

        class UserQuerySet(QuerySet):
            def active(self):
                '''Return only active users.'''
                return self.raw({"active": True})

        class User(MongoModel):
            active = fields.BooleanField()
            # Add our custom Manager.
            users = Manager.from_queryset(UserQuerySet)

    In the above example, we added a `users` attribute on `User` so that we can
    use the `active` method on our new QuerySet type::

        active_users = User.users.active()

    If we wanted every method on the QuerySet to examine active users *only*, we
    can do that by customizing the Manager itself::

        class UserManager(Manager):
            def get_queryset(self):
                # Override get_queryset, so that every QuerySet created will
                # have this filter applied.
                return super(UserManager, self).get_queryset().raw(
                    {"active": True})

        class User(MongoModel):
            active = fields.BooleanField()
            users = UserManager()

        active_users = User.users.all()

    """
    pass
