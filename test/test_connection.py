from pymodm.connection import connect, _get_connection
from pymodm import MongoModel, CharField
from pymongo import IndexModel

from test import ODMTestCase


class ConnectionTestCase(ODMTestCase):
    def test_connect_with_kwargs(self):
        connect('mongodb://localhost:27017/foo?maxPoolSize=42',
                'foo-connection',
                minpoolsize=10)
        client = _get_connection('foo-connection').database.client
        self.assertEqual(42, client.max_pool_size)
        self.assertEqual(10, client.min_pool_size)

    def test_connect_lazily(self):
        connect('mongodb://localhost:27017/foo',
                'foo-connection',
                connect=False)
        client = _get_connection('foo-connection').database.client

        class Article(MongoModel):
            title = CharField()
            class Meta:
                connection_alias = 'foo-connection'
        self.assertFalse(client._topology._opened)

        self.assertEqual(Article.objects.count(), 0)
        self.assertTrue(client._topology._opened)

    def test_connect_lazily_with_index(self):
        connect('mongodb://localhost:27017/foo',
                'foo-connection',
                connect=False)
        client = _get_connection('foo-connection').database.client

        class Article(MongoModel):
            title = CharField()
            class Meta:
                connection_alias = 'foo-connection'
                indexes = [
                    IndexModel([('title', 1)])
                ]
        self.assertFalse(client._topology._opened)

        self.assertEqual(Article.objects.count(), 0)
        self.assertTrue(client._topology._opened)
