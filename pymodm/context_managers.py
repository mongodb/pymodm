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
    """Context manager that changes the active connection for a Model.

    Example::

        connect('mongodb://.../mainDatabase', alias='main-app')
        connect('mongodb://.../backupDatabase', alias='backup')

        # 'MyModel' normally writes to 'mainDatabase'. Let's change that.
        with switch_connection(MyModel, 'backup'):
            # This goes to 'backupDatabase'.
            MyModel(name='Bilbo').save()

    """

    def __init__(self, model, connection_alias):
        """
        :parameters:
          - `model`: A :class:`~pymodm.MongoModel` class.
          - `connection_alias`: A connection alias that was set up earlier via
            a call to :func:`~pymodm.connection.connect`.

        """
        self.model = model
        self.original_connection_alias = self.model._mongometa.connection_alias
        self.target_connection_alias = connection_alias

    def __enter__(self):
        self.model._mongometa.connection_alias = self.target_connection_alias
        return self.model

    def __exit__(self, typ, val, tb):
        self.model._mongometa.connection_alias = self.original_connection_alias


class switch_collection(object):
    """Context manager that changes the active collection for a Model.

    Example::

        with switch_collection(MyModel, "other_collection"):
            ...

    """

    def __init__(self, model, collection_name):
        """
        :parameters:
          - `model`:  A :class:`~pymodm.MongoModel` class.
          - `collection_name`: The name of the new collection to use.

        """
        self.model = model
        self.original_collection_name = self.model._mongometa.collection_name
        self.target_collection_name = collection_name

    def __enter__(self):
        self.model._mongometa.collection_name = self.target_collection_name
        return self.model

    def __exit__(self, typ, val, tb):
        self.model._mongometa.collection_name = self.original_collection_name


class collection_options(object):
    """Context manager that changes the collections options for a Model.

    Example::

        with collection_options(
                MyModel,
                read_preference=ReadPreference.SECONDARY):
            # Read objects off of a secondary.
            MyModel.objects.raw(...)

    """

    def __init__(self, model, codec_options=None, read_preference=None,
                 write_concern=None, read_concern=None):
        """
        :parameters:
          - `model`: A :class:`~pymodm.MongoModel` class.
          - `codec_options`: An instance of
            :class:`~bson.codec_options.CodecOptions`.
          - `read_preference`: A read preference from the
            :mod:`~pymongo.read_preferences` module.
          - `write_concern`: An instance of
            :class:`~pymongo.write_concern.WriteConcern`.
          - `read_concern`: An instance of
            :class:`~pymongo.read_concern.ReadConcern`.

        """
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
    """Context manager that turns off automatic dereferencing.

    Example::

        >>> some_profile = UserProfile.objects.first()
        >>> with no_auto_dereference(UserProfile):
        ...     some_profile.user
        ObjectId('5786cf1d6e32ab419952fce4')
        >>> some_profile.user
        User(name='Sammy', points=123)

    """

    def __init__(self, model):
        """
        :parameters:
          - `model`:  A :class:`~pymodm.MongoModel` class.

        """
        self.model = model
        self.orig_auto_deref = self.model._mongometa.auto_dereference

    def __enter__(self):
        self.model._mongometa.auto_dereference = False

    def __exit__(self, typ, val, tb):
        self.model._mongometa.auto_dereference = self.orig_auto_deref
