# -*- encoding: utf-8 -*-

import unittest

from pymongo.collation import Collation, CollationStrength
from pymodm import fields, MongoModel

from test import ODMTestCase, MONGO_VERSION


class ModelForCollations(MongoModel):
    name = fields.CharField()

    class Meta:
        # Default collation: American English, differentiate base characters.
        collation = Collation('en_US', strength=CollationStrength.PRIMARY)


class CollationTestCase(ODMTestCase):

    @classmethod
    @unittest.skipIf(MONGO_VERSION < (3, 4), 'Requires MongoDB >= 3.4')
    def setUpClass(cls):
        super(CollationTestCase, cls).setUpClass()

    def setUp(self):
        # Initial data.
        ModelForCollations._mongometa.collection.drop()
        ModelForCollations.objects.bulk_create([
            ModelForCollations(u'Aargren'),
            ModelForCollations(u'Åårgren'),
        ])

    def test_collation(self):
        # Use a different collation (not default) for this QuerySet.
        qs = ModelForCollations.objects.collation(
            Collation('en_US', strength=CollationStrength.TERTIARY))
        self.assertEqual(1, qs.raw({'name': 'Aargren'}).count())

    def test_count(self):
        self.assertEqual(
            2, ModelForCollations.objects.raw({'name': 'Aargren'}).count())

    def test_aggregate(self):
        self.assertEqual(
            [{'name': u'Aargren'}, {'name': u'Åårgren'}],
            list(ModelForCollations.objects.aggregate(
                {'$match': {'name': 'Aargren'}},
                {'$project': {'name': 1, '_id': 0}}
            ))
        )
        # Override with keyword argument.
        alternate_collation = Collation(
            'en_US', strength=CollationStrength.TERTIARY)
        self.assertEqual(
            [{'name': u'Aargren'}],
            list(ModelForCollations.objects.aggregate(
                {'$match': {'name': 'Aargren'}},
                {'$project': {'name': 1, '_id': 0}},
                collation=alternate_collation)))

    def test_delete(self):
        self.assertEqual(2, ModelForCollations.objects.delete())

    def test_update(self):
        self.assertEqual(2, ModelForCollations.objects.raw(
            {'name': 'Aargren'}).update({'$set': {'touched': 1}}))
        # Override with keyword argument.
        alternate_collation = Collation(
            'en_US', strength=CollationStrength.TERTIARY)
        self.assertEqual(
            1, ModelForCollations.objects.raw({'name': 'Aargren'}).update(
                {'$set': {'touched': 2}},
                collation=alternate_collation))

    def test_query(self):
        qs = ModelForCollations.objects.raw({'name': 'Aargren'})
        # Iterate the QuerySet.
        self.assertEqual(2, sum(1 for _ in qs))
