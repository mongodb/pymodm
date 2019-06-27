from collections import defaultdict
from pymodm import connection
from pymodm.connection import connect, _get_connection
from pymodm import MongoModel, CharField
from pymongo import IndexModel
from pymongo.monitoring import CommandListener, ServerHeartbeatListener

from test import ODMTestCase


class HeartbeatStartedListener(ServerHeartbeatListener):
    def __init__(self):
        self.results = []

    def started(self, event):
        self.results.append(event)

    def succeeded(self, event):
        pass

    def failed(self, event):
        pass


class WhiteListEventListener(CommandListener):
    def __init__(self, *commands):
        self.commands = set(commands)
        self.results = defaultdict(list)

    def started(self, event):
        if event.command_name in self.commands:
            self.results['started'].append(event)

    def succeeded(self, event):
        if event.command_name in self.commands:
            self.results['succeeded'].append(event)

    def failed(self, event):
        if event.command_name in self.commands:
            self.results['failed'].append(event)


class MockMongoClient(object):
    """Intercept and record calls to MongoClient."""
    def __init__(self):
        self.args = None
        self.kwargs = None

    def enable(self):
        self._original = connection.MongoClient

        def _mock_mongoclient(*args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            return self._original(*args, **kwargs)

        connection.MongoClient = _mock_mongoclient

    def disable(self):
        connection.MongoClient = self._original

    def __enter__(self):
        self.enable()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disable()


class ConnectionTestCase(ODMTestCase):
    def test_connect_with_kwargs(self):
        connect('mongodb://localhost:27017/foo?maxPoolSize=42',
                'foo-connection',
                minpoolsize=10)
        client = _get_connection('foo-connection').database.client
        self.assertEqual(42, client.max_pool_size)
        self.assertEqual(10, client.min_pool_size)

    def test_handshake(self):
        from pymodm.connection import DriverInfo
        from pymodm import version
        if DriverInfo is None:
            self.skipTest("Underlying PyMongo version does not implement the "
                          "handshake specification.")

        # PyMODM should implicitly pass along DriverInfo.
        with MockMongoClient() as mock:
            connect('mongodb://localhost:27017/foo')
        self.assertEqual(DriverInfo('PyMODM', version), mock.kwargs['driver'])

        # PyMODM should not override user-provided DriverInfo.
        driver_info = DriverInfo('bar', 'baz')
        with MockMongoClient() as mock:
            connect('mongodb://localhost:27017/foo', driver=driver_info)
        self.assertEqual(driver_info, mock.kwargs['driver'])

    def test_connect_lazily(self):
        heartbeat_listener = HeartbeatStartedListener()
        connect('mongodb://localhost:27017/foo',
                'foo-connection',
                connect=False,
                event_listeners=[heartbeat_listener])

        class Article(MongoModel):
            title = CharField()
            class Meta:
                connection_alias = 'foo-connection'

        # Creating the class didn't create a connection.
        self.assertEqual(len(heartbeat_listener.results), 0)

        # The connection is created on the first query.
        self.assertEqual(Article.objects.count(), 0)
        self.assertGreaterEqual(len(heartbeat_listener.results), 1)

    def test_connect_lazily_with_index(self):
        heartbeat_listener = HeartbeatStartedListener()
        create_indexes_listener = WhiteListEventListener('createIndexes')
        connect('mongodb://localhost:27017/foo',
                'foo-connection',
                connect=False,
                event_listeners=[heartbeat_listener, create_indexes_listener])

        class Article(MongoModel):
            title = CharField()
            class Meta:
                connection_alias = 'foo-connection'
                indexes = [
                    IndexModel([('title', 1)])
                ]

        # Creating the class didn't create a connection, or any indexes.
        self.assertEqual(len(heartbeat_listener.results), 0)
        self.assertEqual(len(create_indexes_listener.results['started']), 0)

        # The connection and indexes are created on the first query.
        self.assertEqual(Article.objects.count(), 0)
        self.assertGreaterEqual(len(heartbeat_listener.results), 1)
        self.assertGreaterEqual(
            len(create_indexes_listener.results['started']), 1)
