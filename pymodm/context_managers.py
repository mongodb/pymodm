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


class switch_connection(object):
    """Change the active connection for a Model."""

    def __init__(self, model, connection_alias):
        self.model = model
        self.original_connection_alias = self.model._mongometa.connection_alias
        self.target_connection_alias = connection_alias

    def __enter__(self):
        self.model._mongometa.connection_alias = self.target_connection_alias
        return self.model

    def __exit__(self, typ, val, tb):
        self.model._mongometa.connection_alias = self.original_connection_alias


class switch_collection(object):
    """Change the active collection for a Model."""

    def __init__(self, model, collection_name):
        self.model = model
        self.original_collection_name = self.model._mongometa.collection_name
        self.target_collection_name = collection_name

    def __enter__(self):
        self.model._mongometa.collection_name = self.target_collection_name
        return self.model

    def __exit__(self, typ, val, tb):
        self.model._mongometa.collection_name = self.original_collection_name


class collection_options(object):
    """Change collections options for a Model."""

    def __init__(self, model, codec_options=None, read_preference=None,
                 write_concern=None, read_concern=None):
        self.model = model
        meta = self.model._mongometa
        self.orig_read_preference = meta.read_preference
        self.orig_read_concern = meta.read_concern
        self.orig_write_concern = meta.write_concern
        self.orig_codec_options = meta.codec_options

        self.read_preference = read_preference
        self.read_concern = read_concern
        self.write_concern = write_concern
        self.codec_options = codec_options

    def __enter__(self):
        meta = self.model._mongometa
        meta.read_preference = self.read_preference
        meta.read_concern = self.read_concern
        meta.write_concern = self.write_concern
        meta.codec_options = self.codec_options
        # Clear cached reference to Collection.
        self.model._mongometa._collection = None
        return self.model

    def __exit__(self, typ, val, tb):
        meta = self.model._mongometa
        meta.read_preference = self.orig_read_preference
        meta.read_concern = self.orig_read_concern
        meta.write_concern = self.orig_write_concern
        meta.codec_options = self.orig_codec_options

        self.model._mongometa._collection = None


class no_auto_dereference(object):
    """Turn off automatic dereferencing for a model class."""

    def __init__(self, klass):
        self.klass = klass
        self.orig_auto_deref = self.klass._mongometa.auto_dereference

    def __enter__(self):
        self.klass._mongometa.auto_dereference = False

    def __exit__(self, typ, val, tb):
        self.klass._mongometa.auto_dereference = self.orig_auto_deref
