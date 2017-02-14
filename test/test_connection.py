from pymodm.connection import connect, _get_connection

from test import ODMTestCase


class ConnectionTestCase(ODMTestCase):
    def test_connect_with_kwargs(self):
        connect('mongodb://localhost:27017/foo?maxPoolSize=42',
                'foo-connection',
                minpoolsize=10)
        client = _get_connection('foo-connection').database.client
        self.assertEqual(42, client.max_pool_size)
        self.assertEqual(10, client.min_pool_size)
