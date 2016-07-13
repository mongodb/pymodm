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

from collections import defaultdict, deque

from bson.dbref import DBRef

from pymodm.base.models import MongoModelBase
from pymodm.connection import _get_db
from pymodm.context_managers import no_auto_dereference
from pymodm.fields import ReferenceField


class _ObjectMap(dict):
    def __init__(self):
        self.hashed = {}
        self.nohash = []

    def __getitem__(self, item):
        try:
            return self.hashed[item]
        except TypeError:
            # Unhashable type
            for key, value in self.nohash:
                if key == item:
                    return value
            raise KeyError(item)

    def __setitem__(self, key, value):
        try:
            self.hashed[key] = value
        except TypeError:
            # Unhashable type.
            self.nohash.append((key, value))

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False


def _find_references_in_object(object, field, reference_map, fields=None):
    if isinstance(object, DBRef):
        reference_map[object.collection].append(object.id)
    elif isinstance(field, ReferenceField) and not field._is_instance:
        collection_name = field.related_model._mongometa.collection_name
        reference_map[collection_name].append(
            field.related_model._mongometa.pk.to_mongo(object))
    elif isinstance(object, list):
        if hasattr(field, '_field'):
            field = field._field
        for item in object:
            _find_references_in_object(item, field, reference_map, fields)
    elif isinstance(object, MongoModelBase):
        _find_references(object, reference_map, fields)
    # else:  doesn't matter...


def _find_references(model_instance, reference_map, fields=None):
    # Gather the names of the fields we're looking for at this level.
    field_names_map = {}
    if fields:
        for idx, field in enumerate(fields):
            if field:
                field_names_map[idx] = field.popleft()
        field_names = set(field_names_map.values())

    for field in model_instance._mongometa.get_fields():
        # Skip any fields we don't care about.
        if fields and field.attname not in field_names:
            continue
        field_value = getattr(model_instance, field.attname)
        _find_references_in_object(field_value, field, reference_map, fields)

    # Restore parts of field names that we took off while scanning.
    for field_idx, field_name in field_names_map.items():
        fields[field_idx].appendleft(field_name)


def _resolve_references(database, reference_map):
    document_map = _ObjectMap()
    for collection_name in reference_map:
        collection = database[collection_name]
        query = {'_id': {'$in': reference_map[collection_name]}}
        documents = collection.find(query)
        for document in documents:
            document_map[document['_id']] = document
    return document_map


def _get_value(container, key):
    if hasattr(container, '__getitem__'):
        return container[key]
    return getattr(container, key)


def _set_value(container, key, value):
    if hasattr(container, '__setitem__'):
        container[key] = value
    else:
        setattr(container, key, value)


def _set_or_recurse(object, document_map, path, key, value):
    if not path:
        if isinstance(value, DBRef) and value.id in document_map:
            _set_value(object, key, document_map[value.id])
        # elif isinstance(value, ObjectId) and value in document_map:
        elif value in document_map:
            _set_value(object, key, document_map[value])
        else:
            # path is empty, but value could be a list.
            _attach_objects_in_path(value, document_map, path)
    else:
        _attach_objects_in_path(value, document_map, path)


def _attach_objects_in_path(container, document_map, path=None):
    # Paths can't name indexes in a list, so just recurse on the list.
    if isinstance(container, list):
        for index, item in enumerate(container):
            _set_or_recurse(container, document_map, path, index, item)
    # Retrieve and recurse on the next field, if we have a path.
    elif path:
        part = path.popleft()
        value = _get_value(container, part)
        _set_or_recurse(container, document_map, path, part, value)
    # Recurse on every field, if there's no path given.
    elif hasattr(container, 'items'):
        # Container is a dict or a MongoModel of some kind.
        # Both iterate their keys.
        for key in container:
            value = _get_value(container, key)
            _set_or_recurse(container, document_map, path, key, value)


def _attach_objects(container, document_map, fields=None):
    if fields:
        for field in fields:
            _attach_objects_in_path(container, document_map, field)
    else:
        _attach_objects_in_path(container, document_map)


def dereference(model_instance, fields=None):
    """Dereference ReferenceFields on a MongoModel instance.
    This function is handy for dereferencing many fields at once and is more
    efficient than dereferencing one field at a time.

    :parameters:
      - `model_instance`: The MongoModel instance.
      - `fields`: An iterable of field names in "dot" notation that
        should be dereferenced. If left blank, all fields will be dereferenced.
    """
    # Map of collection name --> list of ids to retrieve from the collection.
    reference_map = defaultdict(list)

    # Fields may be nested (dot-notation). Split each field into its parts.
    if fields:
        fields = [deque(field.split('.')) for field in fields]

    # Tell ReferenceFields not to look up their value while we scan the object.
    with no_auto_dereference(model_instance):
        _find_references(model_instance, reference_map, fields)

        db = _get_db(model_instance._mongometa.connection_alias)
        # Resolve all references, one collection at a time.
        # This will give us a mapping of id --> resolved object.
        document_map = _resolve_references(db, reference_map)

        # Traverse the object and attach resolved references where needed.
        _attach_objects(model_instance._data, document_map, fields)

    return model_instance


def dereference_id(model_class, model_id):
    """Dereference a single object by id.

    :parameters:
      - `model_class`: The class of a model to be dereferenced.
      - `model_id`: The id of the model to be dereferenced.
    """
    collection = model_class._mongometa.collection
    return model_class.from_document(collection.find_one(model_id))
