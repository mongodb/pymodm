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

from bson.objectid import ObjectId

from pymodm import fields
from pymodm.base import MongoModel
from pymodm.compat import text_type
from pymodm.context_managers import no_auto_dereference

from test import ODMTestCase
from test.models import ParentModel, User


class Vacation(MongoModel):
    destination = fields.CharField()
    travel_method = fields.CharField()
    price = fields.FloatField()


class QuerySetTestCase(ODMTestCase):

    def setUp(self):
        User(fname='Garden', lname='Tomato', phone=1111111).save()
        User(fname='Rotten', lname='Tomato', phone=2222222).save()
        User(fname='Amon', lname='Amarth', phone=3333333).save()
        User(fname='Garth', lname='Amarth', phone=4444444).save()

    def test_aggregate(self):
        Vacation.objects.bulk_create([
            Vacation(destination='HAWAII', travel_method='PLANE', price=999),
            Vacation(destination='BIGGEST BALL OF TWINE', travel_method='CAR',
                     price=0.02),
            Vacation(destination='GRAND CANYON', travel_method='CAR',
                     price=123.12),
            Vacation(destination='GRAND CANYON', travel_method='CAR',
                     price=25.31)
        ])
        results = Vacation.objects.raw({'travel_method': 'CAR'}).aggregate(
            {'$group': {'_id': 'destination', 'price': {'$min': '$price'}}},
            {'$sort': {'price': -1}}
        )
        last_price = float('inf')
        for result in results:
            self.assertGreaterEqual(last_price, result['price'])
            self.assertNotEqual('HAWAII', result['_id'])
            last_price = result['price']

    def test_does_not_exist(self):
        with self.assertRaises(User.DoesNotExist) as ctx:
            User.objects.get({'fname': 'Tulip'})
        self.assertIsInstance(ctx.exception, ParentModel.DoesNotExist)
        self.assertFalse(
            issubclass(ParentModel.DoesNotExist, User.DoesNotExist))

    def test_multiple_objects_returned(self):
        with self.assertRaises(User.MultipleObjectsReturned):
            User.objects.get({'lname': 'Tomato'})

    def test_all(self):
        results = list(User.objects.all())
        self.assertEqual(4, len(results))

    def test_get(self):
        user = User.objects.get({'_id': 'Amon'})
        self.assertEqual('Amarth', user.lname)

    def test_count(self):
        self.assertEqual(2, User.objects.raw({'lname': 'Tomato'}).count())
        self.assertEqual(3, User.objects.skip(1).count())
        self.assertEqual(1, User.objects.skip(1).limit(1).count())

    def test_raw(self):
        results = User.objects.raw({'lname': 'Tomato'}).raw({'_id': 'Rotten'})
        self.assertEqual(1, results.count())

    def test_order_by(self):
        results = list(User.objects.order_by([('_id', 1)]))
        self.assertEqual('Amarth', results[0].lname)
        self.assertEqual('Tomato', results[1].lname)
        self.assertEqual('Amarth', results[2].lname)
        self.assertEqual('Tomato', results[3].lname)

    def test_order_by_validation(self):
        with self.assertRaises(TypeError):
            User.objects.order_by('not a list')
        with self.assertRaises(TypeError):
            User.objects.order_by([(1, 1)])
        with self.assertRaises(ValueError):
            User.objects.order_by([('field', 1, 'too many elements')])
        with self.assertRaises(ValueError):
            User.objects.order_by([('field', 2)])

    def test_reverse(self):
        def assert_reverses(qs):
            normal_order = list(qs)
            reversed_order = list(qs.reverse())
            double_reversed = list(qs.reverse().reverse())
            self.assertEqual(normal_order, list(reversed(reversed_order)))
            self.assertEqual(normal_order, double_reversed)

        assert_reverses(User.objects.order_by([('_id', 1)]))
        assert_reverses(User.objects.order_by(
            [('_id', 1), ('phone', -1), ('lname', 1)]))

    def test_project(self):
        results = User.objects.project({'lname': 1})
        for result in results:
            self.assertIsNotNone(result.lname)
            self.assertIsNotNone(result.pk)
            self.assertIsNone(result.phone)

    def test_only(self):
        results = User.objects.only('phone')
        for result in results:
            self.assertIsNone(result.lname)
            self.assertIsInstance(result.phone, int)
            # Primary key cannot be projected out.
            self.assertIsNotNone(result.pk)

    def test_exclude(self):
        results = User.objects.exclude('_id').exclude('phone')
        for result in results:
            self.assertIsNone(result.phone)
            self.assertIsInstance(result.lname, text_type)
            # Primary key cannot be projected out.
            self.assertIsNotNone(result.pk)

    def test_skip(self):
        results = list(User.objects.skip(1))
        self.assertEqual(3, len(results))

    def test_limit(self):
        results = list(User.objects.limit(2))
        self.assertEqual(2, len(results))

    def test_values(self):
        results = list(User.objects.values())
        for result in results:
            self.assertIsInstance(result, dict)

    def test_first(self):
        qs = User.objects.order_by([('phone', 1)])
        result = qs.first()
        self.assertEqual('Tomato', result.lname)
        # Returns the same result the second time called.
        self.assertEqual(result, qs.first())

    def test_create(self):
        result = User.objects.create(
            fname='George',
            lname='Washington')
        retrieved = User.objects.get({'lname': 'Washington'})
        self.assertEqual(result, retrieved)

    def test_bulk_create(self):
        results = User.objects.bulk_create(
            User(fname='Louis', lname='Armstrong'))
        self.assertEqual(['Louis'], results)

        results = User.objects.bulk_create([
            User(fname='Woodrow', lname='Wilson'),
            User(fname='Andrew', lname='Jackson')])
        self.assertEqual(['Woodrow', 'Andrew'], results)
        franklins = [
            User(fname='Benjamin', lname='Franklin'),
            User(fname='Aretha', lname='Franklin')
        ]
        results = User.objects.bulk_create(franklins, retrieve=True)
        for result in results:
            self.assertIn(result, franklins)

    def test_delete(self):
        self.assertEqual(
            2, User.objects.raw({'lname': 'Tomato'}).delete())
        results = list(User.objects.all())
        self.assertEqual(2, len(results))
        for obj in results:
            self.assertNotEqual(obj.lname, 'Tomato')

    def test_update(self):
        self.assertEqual(
            2, User.objects.raw({'lname': 'Tomato'}).update(
                {'$set': {'phone': 1234567}}
            ))
        results = list(User.objects.raw({'phone': 1234567}))
        self.assertEqual(2, len(results))
        for result in results:
            self.assertEqual('Tomato', result.lname)

        User.objects.raw({'phone': 7654321}).update(
            {'$set': {'lname': 'Ennis'}},
            upsert=True)
        User.objects.get({'phone': 7654321})

    def test_getitem(self):
        users = User.objects.order_by([('phone', 1)])
        self.assertEqual(1111111, users[0].phone)
        self.assertEqual(4444444, users[3].phone)

    def test_slice(self):
        users = User.objects.order_by([('phone', 1)])[2:3]
        for user in users:
            self.assertEqual('Amon', user.fname)
            self.assertEqual('Amarth', user.lname)

    def test_select_related(self):
        class Comment(MongoModel):
            body = fields.CharField()

        class Post(MongoModel):
            body = fields.CharField()
            comments = fields.ListField(fields.ReferenceField(Comment))

        # Create a few objects...
        Post(body='Nobody read this post').save()
        comments = [
            Comment(body='This is a great post').save(),
            Comment(body='Horrible read').save()
        ]
        Post(body='More popular post', comments=comments).save()

        with no_auto_dereference(Post):
            posts = list(Post.objects.all())
            self.assertEqual([], posts[0].comments)
            self.assertIsInstance(posts[1].comments[0], ObjectId)
            self.assertIsInstance(posts[1].comments[1], ObjectId)

            posts = list(Post.objects.select_related())
            self.assertEqual([], posts[0].comments)
            self.assertEqual(posts[1].comments, comments)
