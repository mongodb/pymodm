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

"""Tools for managing connections in MongoModels."""
import sys

from pymongo import uri_parser, MongoClient

from pymodm.compat import reraise


__all__ = ['connect']


class ConnectionInfo:
    """Stores the information of each connection alias
    """
    __slots__ = ('parsed_uri', 'conn_string', 'database')

    def __init__(self, parsed_uri, conn_string, database):
        """Initializes the ConnectionInfo Object

        :parameters:
          - `parsed_uri` (dict): A dict of the form:

            {
                'nodelist': <list of (host, port) tuples>,
                'username': <username> or None,
                'password': <password> or None,
                'database': <database name> or None,
                'collection': <collection name> or None,
                'options': <dict of MongoDB URI options>
            }

          - `connection_str` (str): expects a `mongodb_uri`, a MongoDB connection
            of the general form:

                'mongodb://localhost:27017/<db_name>'

            Any options may be passed within the string that are supported by PyMongo.
            `mongodb_uri` must specify a database, which will be used by any
            :class:`~pymodm.MongoModel` that uses this connection.

          - `database` (pymongo.database.Database): of the general form:

                Database(
                    MongoClient(
                        host=['localhost:27017'],
                        document_class=dict,
                        tz_aware=False,
                        connect=False,
                        event_listeners=[]
                    ),
                    'foo'
                )
        """
        self.parsed_uri = parsed_uri
        self.conn_string = conn_string
        self.database = database


DEFAULT_CONNECTION_ALIAS = 'default'


_CONNECTIONS = dict()


def connect(mongodb_uri, alias=DEFAULT_CONNECTION_ALIAS, **kwargs):
    """Register a connection to MongoDB, optionally providing a name for it.

    Note: :func:`connect` must be called with before any
    :class:`~pymodm.MongoModel` is used with the given `alias`.

    :parameters:
      - `mongodb_uri`: A MongoDB connection string. Any options may be passed
        within the string that are supported by PyMongo. `mongodb_uri` must
        specify a database, which will be used by any
        :class:`~pymodm.MongoModel` that uses this connection.
      - `alias`: An optional name for this connection, backed by a
        :class:`~pymongo.mongo_client.MongoClient` instance that is cached under
        this name. You can specify what connection a MongoModel uses by
        specifying the connection's alias via the `connection_alias` attribute
        inside their `Meta` class.  Switching connections is also possible using
        the :class:`~pymodm.context_managers.switch_connection` context
        manager.  Note that calling `connect()` multiple times with the same
        alias will replace any previous connections.
      - `kwargs`: Additional keyword arguments to pass to the underlying
        :class:`~pymongo.mongo_client.MongoClient`.

    """
    # Make sure the database is provided.
    parsed_uri = uri_parser.parse_uri(mongodb_uri)
    if not parsed_uri.get('database'):
        raise ValueError('Connection must specify a database.')
    _CONNECTIONS[alias] = ConnectionInfo(
        parsed_uri=parsed_uri,
        conn_string=mongodb_uri,
        database=MongoClient(mongodb_uri, **kwargs)[parsed_uri['database']])


def _get_connection(alias=DEFAULT_CONNECTION_ALIAS):
    """Return a `ConnectionInfo` by connection alias."""
    try:
        return _CONNECTIONS[alias]
    except KeyError:
        _, _, tb = sys.exc_info()
        reraise(ValueError,
                "No such alias '%s'. Did you forget to call connect()?" % alias,
                tb)


def _get_db(alias=DEFAULT_CONNECTION_ALIAS):
    """Return the `pymongo.database.Database` instance for the given alias."""
    return _get_connection(alias).database
