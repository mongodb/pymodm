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

import copy

from pymodm import errors
from pymodm.common import (
    _import, validate_boolean, validate_list_or_tuple)


class QuerySet(object):

    def __init__(self, model=None, query=None):
        """Create a new QuerySet instance.

        :parameters:
          - `model` The MongoModel class to be produced by the QuerySet.
          - `query` The MongoDB query that filters the QuerySet.
        """
        self._model = model
        self._query = query or {}
        self._order_by = None
        self._limit = 0
        self._skip = 0
        self._projection = None
        self._return_raw = False
        self._select_related_fields = None
        # Select all subclasses of the given Model.
        self._types_query = {}
        if not self._model._mongometa.final:
            if len(self._model._subclasses) > 1:
                self._types_query = {
                    '_cls': {'$in': list(self._model._subclasses)}}
            elif self._model._subclasses:
                self._types_query = {'_cls': self._model._mongometa.object_name}

    @property
    def _collection(self):
        return self._model._mongometa.collection

    def _clone(self, model=None, query=None):
        """Return an identical copy of this QuerySet."""
        clone_properties = (
            '_order_by', '_limit', '_skip', '_projection', '_return_raw',
            '_select_related_fields')

        clone = QuerySet(model=model or self._model, query=query or self._query)

        for prop in clone_properties:
            setattr(clone, prop, copy.copy(getattr(self, prop)))

        return clone

    def get(self, raw_query):
        """Retrieve the object matching the given criteria.

        Raises `DoesNotExist` if no object was found.
        Raises `MultipleObjectsReturned` if multiple objects were found.
        """
        results = iter(self.raw(raw_query))
        try:
            first = next(results)
        except StopIteration:
            raise self._model.DoesNotExist()
        try:
            next(results)
        except StopIteration:
            pass
        else:
            raise self._model.MultipleObjectsReturned()
        return first

    def count(self):
        """Return the number of objects in this QuerySet."""
        return self._collection.count(
            self.raw_query, skip=self._skip, limit=self._limit)

    def first(self):
        """Return the first object from this QuerySet."""
        try:
            return next(iter(self.limit(-1)))
        except StopIteration:
            raise self._model.DoesNotExist()

    #
    # QuerySet methods returning new QuerySets.
    #

    def all(self):
        """Return a QuerySet over all the objects in this QuerySet."""
        return self._clone()

    def select_related(self, *fields):
        """Allow this QuerySet to pre-fetch objects related to the Model."""
        clone = self._clone()
        clone._select_related_fields = set(fields)
        return clone

    def raw(self, raw_query):
        """Filter using a raw MongoDB query."""
        query = self._query
        if query:
            return self._clone(
                query={'$and': [raw_query, query]})
        return self._clone(query=raw_query)

    def order_by(self, ordering):
        """Set an ordering for this QuerySet.

        :parameters:
          - `ordering` The sort criteria. This should be a list of 2-tuples
            consisting of [(field_name, direction)], where "direction" can
            be one of `pymongo.ASCENDING` or `pymongo.DESCENDING`.
        """
        clone = self._clone()
        clone._order_by = ordering
        return clone

    def only(self, *fields):
        """Include only specified fields in QuerySet results.

        This method is chainable and performs a union of the given fields.
        """
        clone = self._clone()
        clone._projection = clone._projection or {}
        for field in fields:
            clone._projection[field] = 1
        return clone

    def exclude(self, *fields):
        """Exclude specified fields in QuerySet results."""
        clone = self._clone()
        clone._projection = clone._projection or {}
        for field in fields:
            # Primary key cannot be excluded.
            if field != self._model._mongometa.pk.attname:
                clone._projection[field] = 0
        return clone

    def limit(self, limit):
        """Limit the number of objects in this QuerySet."""
        clone = self._clone()
        clone._limit = limit
        return clone

    def skip(self, skip):
        """Skip over the first number of objects in this QuerySet.
        """
        clone = self._clone()
        clone._skip = skip
        return clone

    def values(self):
        """Return Python ``dict`` instances instead of Model instances."""
        clone = self._clone()
        clone._return_raw = True
        return clone

    #
    # Object-manipulation methods.
    #

    def create(self, **kwargs):
        """Save an instance of this QuerySet's Model."""
        return self._model(**kwargs).save()

    def bulk_create(self, object_or_objects, retrieve=False, full_clean=False):
        """Save Model instances in bulk.

        :parameters:
          - `object_or_objects` - A list of MongoModel instances or a single
            instance.
          - `retrieve` (optional) - Whether to return the saved MongoModel
            instances. If ``False`` (the default), only the ids will be
            returned.
          - `full_clean` (optional) - Whether to validate each object by calling
            the :meth:`~pymodm.MongoModel.full_clean` method before saving.
            This isn't done by default.
        """
        retrieve = validate_boolean('retrieve', retrieve)
        full_clean = validate_boolean('full_clean', full_clean)
        MongoModel = _import('pymodm.base.models.MongoModel')
        if isinstance(object_or_objects, MongoModel):
            object_or_objects = [object_or_objects]
        object_or_objects = validate_list_or_tuple(
            'object_or_objects', object_or_objects)
        if full_clean:
            for object in object_or_objects:
                object.full_clean()
        docs = (obj.to_son() for obj in object_or_objects)
        ids = self._collection.insert_many(docs).inserted_ids
        if retrieve:
            return list(self.raw({'_id': {'$in': ids}}))
        return ids

    def delete(self):
        """Delete objects in this QuerySet and return the number deleted."""
        ReferenceField = _import('pymodm.fields.ReferenceField')
        if self._model._mongometa.delete_rules:
            # Don't apply any delete rules if no documents match.
            if not self.count():
                return 0

            # Use values() to avoid overhead converting to Model instances.
            refs = [doc['_id'] for doc in self.values()]

            # Check for DENY rules before anything else.
            for rule_entry in self._model._mongometa.delete_rules:
                related_model, related_field = rule_entry
                rule = self._model._mongometa.delete_rules[rule_entry]
                if ReferenceField.DENY == rule:
                    related_qs = related_model._default_manager.raw(
                        {related_field: {'$in': refs}}).values()
                    if related_qs.count() > 0:
                        raise errors.OperationError(
                            'Cannot delete a %s object while a %s object '
                            'refers to it through its "%s" field.'
                            % (self._model._mongometa.object_name,
                               related_model._mongometa.object_name,
                               related_field))

            # If we've made it this far, it's ok to delete the objects in this
            # QuerySet.
            result = self._collection.delete_many(self._query).deleted_count

            # Apply the rest of the delete rules.
            for rule_entry in self._model._mongometa.delete_rules:
                related_model, related_field = rule_entry
                rule = self._model._mongometa.delete_rules[rule_entry]
                if ReferenceField.DO_NOTHING == rule:
                    continue
                related_qs = (related_model._default_manager
                              .raw({related_field: {'$in': refs}})
                              .values())
                if ReferenceField.NULLIFY == rule:
                    related_qs.update({'$unset': {related_field: None}})
                elif ReferenceField.CASCADE == rule:
                    related_qs.delete()
                elif ReferenceField.PULL == rule:
                    related_qs.update({'$pull': {related_field: {'$in': refs}}})

            return result

        return self._collection.delete_many(self._query).deleted_count

    def update(self, update):
        """Update the objects in this QuerySet and return the number updated."""
        return self._collection.update_many(
            self.raw_query, update).modified_count

    #
    # Helper methods
    #

    @property
    def raw_query(self):
        if self._types_query and self._query:
            return {'$and': [self._query, self._types_query]}
        return self._query or self._types_query

    def _get_raw_cursor(self):
        return self._collection.find(
            self.raw_query,
            sort=self._order_by,
            limit=self._limit,
            skip=self._skip,
            projection=self._projection)

    def __iter__(self):
        if self._return_raw:
            return self._get_raw_cursor()
        to_instance = self._model.from_dict
        if self._select_related_fields is not None:
            dereference = _import('pymodm.dereference.dereference')
            to_instance = lambda doc: dereference(
                self._model.from_dict(doc), self._select_related_fields)
        return (to_instance(doc) for doc in self._get_raw_cursor())

    def __next__(self):
        return next(iter(self))

    next = __next__

    def __getitem__(self, key):
        clone = self._clone()

        if isinstance(key, slice):
            # PyMongo will later raise an Exception if the slice is invalid.
            if key.start is not None:
                clone._skip = key.start
                if key.stop is not None:
                    clone._limit = key.stop - key.start
            elif key.stop is not None:
                clone._limit = key.stop
            return clone
        else:
            return clone.skip(key).first()
