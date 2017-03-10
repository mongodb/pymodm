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

import pymongo

from pymodm import errors
from pymodm.common import (
    _import, validate_boolean, validate_list_or_tuple, validate_mapping,
    validate_ordering)


class QuerySet(object):
    """The default QuerySet type.

    QuerySets handle queries and allow working with documents in bulk.
    """

    def __init__(self, model=None, query=None):
        """
        :parameters:
          - `model`: The :class:`~pymodm.MongoModel` class to be produced
            by the QuerySet.
          - `query`: The MongoDB query that filters the QuerySet.
        """
        self._model = model
        self._query = query or {}
        self._order_by = None
        self._limit = 0
        self._skip = 0
        self._projection = None
        self._return_raw = False
        self._select_related_fields = None
        self._collation = self._model._mongometa.collation
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
            '_select_related_fields', '_collation')

        clone = type(self)(model=model or self._model,
                           query=query or self._query)

        for prop in clone_properties:
            setattr(clone, prop, copy.copy(getattr(self, prop)))

        return clone

    def get(self, raw_query):
        """Retrieve the object matching the given criteria.

        Raises `DoesNotExist` if no object was found.
        Raises `MultipleObjectsReturned` if multiple objects were found.

        Note that these exception types are specific to the model class itself,
        so that it's possible to differentiate exceptions on the model type::

            try:
                user = User.objects.get({'_id': user_id})
                profile = UserProfile.objects.get({'user': user.email})
            except User.DoesNotExist:
                # Handle User not existing.
                return redirect_to_registration(user_id)
            except UserProfile.DoesNotExist:
                # User has not set up their profile.
                return setup_user_profile(user_id)

        These model-specific exceptions all inherit from exceptions of the same
        name defined in the :mod:`~pymodm.errors` module, so you can catch them
        all::

            try:
                user = User.objects.get({'_id': user_id})
                profile = UserProfile.objects.get({'user': user.email})
            except errors.DoesNotExist:
                # Either the User or UserProfile does not exist.
                return redirect_to_404(user_id)

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
            self.raw_query, skip=self._skip, limit=self._limit,
            collation=self._collation)

    def first(self):
        """Return the first object from this QuerySet."""
        try:
            return next(iter(self.limit(-1)))
        except StopIteration:
            raise self._model.DoesNotExist()

    def aggregate(self, *pipeline, **kwargs):
        """Perform a MongoDB aggregation.

        Any query, projection, sort, skip, and limit applied to this QuerySet
        will become aggregation pipeline stages in that order *before* any
        additional stages given in `pipeline`.

        :parameters:
          - `pipeline`: Additional aggregation pipeline stages.
          - `kwargs`: Keyword arguments to pass down to PyMongo's
            :meth:`~pymongo.collection.Collection.aggregate` method.

        :returns: A :class:`~pymongo.command_cursor.CommandCursor` over the
          result set.

        example::

            >>> # Apply a filter before aggregation.
            >>> qs = Vacation.objects.raw({'travel_method': 'CAR'})
            >>> # Run aggregation pipeline.
            >>> cursor = qs.aggregate(
            ...     {'$group': {'_id': '$destination',
            ...                 'price': {'$min': '$price'}}},
            ...     {'$sort': {'price': pymongo.DESCENDING}},
            ...     allowDiskUse=True)
            >>> list(cursor)
            [{'_id': 'GRAND CANYON', 'price': 123.12},
             {'_id': 'MUIR WOODS', 'price': '25.31'},
             {'_id': 'BIGGEST BALL OF TWINE', 'price': '0.25'}]

        """
        before_pipeline = []
        raw_query = self.raw_query
        if raw_query:
            before_pipeline.append({'$match': raw_query})
        if self._projection:
            before_pipeline.append({'$project': self._projection})
        if self._order_by:
            before_pipeline.append({'$sort': self._order_by})
        if self._skip:
            before_pipeline.append({'$skip': self._skip})
        if self._limit:
            before_pipeline.append({'$limit': self._limit})

        kwargs.setdefault('collation', self._collation)

        return self._collection.aggregate(
            before_pipeline + list(pipeline), **kwargs)

    #
    # QuerySet methods returning new QuerySets.
    #

    def all(self):
        """Return a QuerySet over all the objects in this QuerySet."""
        return self._clone()

    def select_related(self, *fields):
        """Allow this QuerySet to pre-fetch objects related to the Model.

        :parameters:
          - `fields`: Names of related fields on this model that should be
            fetched.

        """
        clone = self._clone()
        clone._select_related_fields = set(fields)
        return clone

    def raw(self, raw_query):
        """Filter using a raw MongoDB query.

        :parameters:
          - `raw_query`: A raw MongoDB query.

        example::

            >>> list(Vacation.objects.raw({"travel_method": "CAR"}))
            [Vacation(destination='NAPA', travel_method='CAR'),
             Vacation(destination='GRAND CANYON', travel_method='CAR')]

        """
        query = self._query
        if query:
            return self._clone(
                query={'$and': [raw_query, query]})
        return self._clone(query=raw_query)

    def order_by(self, ordering):
        """Set an ordering for this QuerySet.

        :parameters:
          - `ordering`: The sort criteria. This should be a list of 2-tuples
            consisting of [(field_name, direction)], where "direction" can
            be one of :data:`~pymongo.ASCENDING` or :data:`~pymongo.DESCENDING`.
        """
        ordering = validate_ordering('ordering', ordering)
        clone = self._clone()
        clone._order_by = ordering
        return clone

    def reverse(self):
        """Reverse the ordering for this QuerySet.

        If :meth:`~pymodm.queryset.QuerySet.order_by` has not been called,
        reverse() has no effect.
        """
        clone = self._clone()
        if clone._order_by:
            reversed_order_by = []
            for field, order in clone._order_by:
                if order == pymongo.ASCENDING:
                    reversed_order = pymongo.DESCENDING
                else:
                    reversed_order = pymongo.ASCENDING
                reversed_order_by.append((field, reversed_order))
            clone._order_by = reversed_order_by
        return clone

    def project(self, projection):
        """Specify a raw MongoDB projection to use in QuerySet results.

        This method overrides any previous projections on this QuerySet,
        including those created with :meth:`~pymodm.queryset.QuerySet.only` and
        :meth:`~pymodm.queryset.QuerySet.exclude`. Unlike these methods,
        `project` allows projecting out the primary key. However, note that
        objects that do not have their primary key cannot be re-saved to the
        database.

        :parameters:
          - `projection`: A MongoDB projection document.

        example::

            >>> Vacation.objects.project({
            ...     'destination': 1,
            ...     'flights': {'$elemMatch': {'available': True}}}).first()
            Vacation(destination='HAWAII',
                     flights=[{'available': True, 'from': 'SFO'}])

        """
        projection = validate_mapping('projection', projection)
        clone = self._clone()
        clone._projection = projection
        return clone

    def only(self, *fields):
        """Include only specified fields in QuerySet results.

        This method is chainable and performs a union of the given fields.

        :parameters:
          - `fields`: MongoDB names of fields to be included.

        example::

            >>> list(Vacation.objects.all())
            [Vacation(destination='HAWAII', travel_method='BOAT'),
             Vacation(destination='NAPA', travel_method='CAR')]
            >>> list(Vacation.objects.only('travel_method'))
            [Vacation(travel_method='BOAT'), Vacation(travel_method='CAR')]

        """
        clone = self._clone()
        clone._projection = clone._projection or {}
        for field in fields:
            clone._projection[field] = 1
        return clone

    def exclude(self, *fields):
        """Exclude specified fields in QuerySet results.

        :parameters:
          - `fields`: MongoDB names of fields to be excluded.

        example::

            >>> list(Vacation.objects.all())
            [Vacation(destination='HAWAII', travel_method='BOAT'),
             Vacation(destination='NAPA', travel_method='CAR')]
            >>> list(Vacation.objects.exclude('travel_method'))
            [Vacation(destination='HAWAII'), Vacation(destination='NAPA')]

        """
        clone = self._clone()
        clone._projection = clone._projection or {}
        for field in fields:
            # Primary key cannot be excluded.
            if field not in (self._model._mongometa.pk.attname, '_id'):
                clone._projection[field] = 0
        return clone

    def limit(self, limit):
        """Limit the number of objects in this QuerySet.

        :parameters:
          - `limit`: The maximum number of documents to return.

        """
        clone = self._clone()
        clone._limit = limit
        return clone

    def skip(self, skip):
        """Skip over the first number of objects in this QuerySet.

        :parameters:
          - `skip`: The number of documents to skip.

        """
        clone = self._clone()
        clone._skip = skip
        return clone

    def values(self):
        """Return Python ``dict`` instances instead of Model instances."""
        clone = self._clone()
        clone._return_raw = True
        return clone

    def collation(self, collation):
        """Specify a collation to use for string comparisons.

        This will override the default collation of the collection.

        :parameters:
          - `collation`: An instance of `~pymongo.collation.Collation` or a
            ``dict`` specifying the collation.

        """
        clone = self._clone()
        clone._collation = collation
        return clone

    #
    # Object-manipulation methods.
    #

    def create(self, **kwargs):
        """Save an instance of this QuerySet's Model.

        :parameters:
          - `kwargs`: Keyword arguments specifying the field values for the
            :class:`~pymodm.MongoModel` instance to be created.

        :returns: The :class:`~pymodm.MongoModel` instance, after it has been
                  saved.

        example::

            >>> vacation = Vacation.objects.create(
            ...     destination="ROME",
            ...     travel_method="PLANE")
            >>> print(vacation)
            Vacation(destination='ROME', travel_method='PLANE')
            >>> print(vacation.pk)
            ObjectId('578925ed6e32ab1d6a8dc717')

        """
        return self._model(**kwargs).save()

    def bulk_create(self, object_or_objects, retrieve=False, full_clean=False):
        """Save Model instances in bulk.

        :parameters:
          - `object_or_objects`: A list of MongoModel instances or a single
            instance.
          - `retrieve`: Whether to return the saved MongoModel
            instances. If ``False`` (the default), only the ids will be
            returned.
          - `full_clean`: Whether to validate each object by calling
            the :meth:`~pymodm.MongoModel.full_clean` method before saving.
            This isn't done by default.

        :returns: A list of ids for the documents saved, or of the
                  :class:`~pymodm.MongoModel` instances themselves if `retrieve`
                  is ``True``.

        example::

            >>> vacation_ids = Vacation.objects.bulk_create([
            ...     Vacation(destination='TOKYO', travel_method='PLANE'),
            ...     Vacation(destination='ALGIERS', travel_method='PLANE')])
            >>> print(vacation_ids)
            [ObjectId('578926716e32ab1d6a8dc718'),
             ObjectId('578926716e32ab1d6a8dc719')]

        """
        retrieve = validate_boolean('retrieve', retrieve)
        full_clean = validate_boolean('full_clean', full_clean)
        TopLevelMongoModel = _import('pymodm.base.models.TopLevelMongoModel')
        if isinstance(object_or_objects, TopLevelMongoModel):
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
        """Delete objects matched by this QuerySet.

        :returns: The number of documents deleted.

        """
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
                    related_qs = related_model._mongometa.default_manager.raw(
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
            result = self._collection.delete_many(
                self._query, collation=self._collation).deleted_count

            # Apply the rest of the delete rules.
            for rule_entry in self._model._mongometa.delete_rules:
                related_model, related_field = rule_entry
                rule = self._model._mongometa.delete_rules[rule_entry]
                if ReferenceField.DO_NOTHING == rule:
                    continue
                related_qs = (related_model._mongometa.default_manager
                              .raw({related_field: {'$in': refs}})
                              .values())
                if ReferenceField.NULLIFY == rule:
                    related_qs.update({'$unset': {related_field: None}})
                elif ReferenceField.CASCADE == rule:
                    related_qs.delete()
                elif ReferenceField.PULL == rule:
                    related_qs.update({'$pull': {related_field: {'$in': refs}}})

            return result

        return self._collection.delete_many(
            self._query, collation=self._collation).deleted_count

    def update(self, update, **kwargs):
        """Update the objects in this QuerySet and return the number updated.

        :parameters:
          - `update`: The modifications to apply.
          - `kwargs`: (optional) keyword arguments to pass down to
            :meth:`~pymongo.collection.Collection.update_many`.

        example::

            Subscription.objects.raw({"year": 1995}).update(
                {"$set": {"expired": True}},
                upsert=True)

        """
        # If we're doing an upsert on a non-final class, we need to add '_cls'
        # manually, since it won't be saved with upsert alone.
        if kwargs.get('upsert') and not self._model._mongometa.final:
            dollar_set = update.setdefault('$set', {})
            dollar_set['_cls'] = self._model._mongometa.object_name
        kwargs.setdefault('collation', self._collation)
        return self._collection.update_many(
            self.raw_query, update, **kwargs).modified_count

    #
    # Helper methods
    #

    @property
    def raw_query(self):
        """The raw query that will be executed by this QuerySet."""
        if self._types_query and self._query:
            return {'$and': [self._query, self._types_query]}
        return self._query or self._types_query

    def _get_raw_cursor(self):
        return self._collection.find(
            self.raw_query,
            sort=self._order_by,
            limit=self._limit,
            skip=self._skip,
            projection=self._projection,
            collation=self._collation)

    def __iter__(self):
        if self._return_raw:
            return self._get_raw_cursor()
        to_instance = self._model.from_document
        if self._select_related_fields is not None:
            dereference = _import('pymodm.dereference.dereference')
            to_instance = lambda doc: dereference(
                self._model.from_document(doc), self._select_related_fields)
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
