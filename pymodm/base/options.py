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

from bisect import bisect

from bson.codec_options import CodecOptions

from pymodm.connection import _get_db, DEFAULT_CONNECTION_ALIAS
from pymodm.errors import InvalidModel
from pymodm.fields import EmbeddedDocumentField, EmbeddedDocumentListField

# Attributes that can be user-specified in MongoOptions.
DEFAULT_NAMES = (
    'connection_alias', 'collection_name', 'codec_options', 'final',
    'cascade', 'read_preference', 'read_concern', 'write_concern',
    'indexes', 'collation', 'ignore_unknown_fields')


class MongoOptions(object):
    """Base class for metadata stored in Model classes."""

    def __init__(self, meta=None):
        self.meta = meta
        self.connection_alias = DEFAULT_CONNECTION_ALIAS
        self.collection_name = None
        self.codec_options = CodecOptions()
        self.fields_dict = {}
        self.fields_attname_dict = {}
        self.fields_ordered = []
        self.implicit_id = False
        self.delete_rules = {}
        self.final = False
        self.cascade = False
        self.pk = None
        self.codec_options = None
        self.object_name = None
        self.model = None
        self.read_preference = None
        self.read_concern = None
        self.write_concern = None
        self.indexes = []
        self.collation = None
        self.ignore_unknown_fields = False
        self._auto_dereference = True
        self._indexes_created = False

    @property
    def collection(self):
        coll = _get_db(self.connection_alias).get_collection(
            self.collection_name,
            read_preference=self.read_preference,
            read_concern=self.read_concern,
            write_concern=self.write_concern,
            codec_options=self.codec_options)
        if self.indexes and not self._indexes_created:
            coll.create_indexes(self.indexes)
            self._indexes_created = True
        return coll

    @property
    def auto_dereference(self):
        return self._auto_dereference

    @auto_dereference.setter
    def auto_dereference(self, auto_dereference):
        """Turn automatic dereferencing on or off."""
        for field in self.get_fields():
            if isinstance(field, (EmbeddedDocumentField,
                                  EmbeddedDocumentListField)):
                embedded_options = field.related_model._mongometa
                embedded_options.auto_dereference = auto_dereference
        self._auto_dereference = auto_dereference

    def get_field(self, field_name):
        """Retrieve a Field instance with the given MongoDB name."""
        return self.fields_dict.get(field_name)

    def get_field_from_attname(self, attname):
        """Retrieve a Fields instance with the given attribute name."""
        return self.fields_attname_dict.get(attname)

    def add_field(self, field_inst):
        """Add or replace a given Field."""
        try:
            orig_field = self.get_field(field_inst.mongo_name)
        except Exception:
            # FieldDoesNotExist, etc. may be raised by subclasses.
            orig_field = None
        if orig_field is None:
            try:
                orig_field = self.get_field_from_attname(field_inst.attname)
            except Exception:
                pass

        if orig_field:
            if field_inst.attname != orig_field.attname:
                raise InvalidModel('%r cannot have the same mongo_name of '
                                   'existing field %r' % (field_inst.attname,
                                                          orig_field.attname))
            # Remove the field as it may have a different MongoDB name.
            del self.fields_dict[orig_field.mongo_name]
            self.fields_ordered.remove(orig_field)

        self.fields_dict[field_inst.mongo_name] = field_inst
        self.fields_attname_dict[field_inst.attname] = field_inst
        index = bisect(self.fields_ordered, field_inst)
        self.fields_ordered.insert(index, field_inst)

        # Set the primary key if we don't have one yet, or it if is implicit.
        if field_inst.primary_key and self.pk is None or self.implicit_id:
            self.pk = field_inst

    def get_fields(self, include_parents=True, include_hidden=False):
        """Get a list of all fields on the Model."""
        return self.fields_ordered

    def contribute_to_class(self, cls, name):
        """Callback executed when added to a Model class definition."""
        self.model = cls
        # Name used to look up this class with get_document().
        self.object_name = '%s.%s' % (cls.__module__, cls.__name__)
        setattr(cls, name, self)

        # Metadata was defined by user.
        if self.meta:
            for attr in DEFAULT_NAMES:
                if attr in self.meta.__dict__:
                    setattr(self, attr, getattr(self.meta, attr))
