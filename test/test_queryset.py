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


class User(MongoModel):
    fname = fields.CharField()
    lname = fields.CharField()
    creds = fields.IntegerField()


class QuerySetTestCase(ODMTestCase):

    def setUp(self):
        User(fname='Joe', lname='Biden', creds=0).save()
        User(fname='Joe', lname='Tomato', creds=1).save()
        User(fname='Amon', lname='Amarth', creds=2).save()
        User(fname='Amon', lname='Tomato', creds=3).save()

    def test_all(self):
        results = list(User.objects.all())
        self.assertEqual(4, len(results))

    def test_get(self):
        user = User.objects.get({'lname': 'Amarth'})
        self.assertEqual('Amon', user.fname)

    def test_count(self):
        self.assertEqual(2, User.objects.raw({'lname': 'Tomato'}).count())
        self.assertEqual(3, User.objects.skip(1).count())
        self.assertEqual(1, User.objects.skip(1).limit(1).count())

    def test_raw(self):
        results = User.objects.raw({'fname': 'Joe'}).raw({'lname': 'Tomato'})
        self.assertEqual(1, len(list(results)))

    def test_order_by(self):
        results = list(User.objects.order_by([('fname', 1)]))
        self.assertEqual('Amon', results[0].fname)
        self.assertEqual('Amon', results[1].fname)
        self.assertEqual('Joe', results[2].fname)
        self.assertEqual('Joe', results[3].fname)

    def test_only(self):
        results = User.objects.only('fname').only('creds')
        for result in results:
            self.assertIsNone(result.lname)
            self.assertIsInstance(result.creds, int)
            # Primary key cannot be projected out.
            self.assertIsInstance(result.pk, ObjectId)

    def test_exclude(self):
        results = User.objects.exclude('fname').exclude('creds')
        for result in results:
            self.assertIsNone(result.fname)
            self.assertIsNone(result.creds)
            self.assertIsInstance(result.lname, text_type)
            # Primary key cannot be projected out.
            self.assertIsInstance(result.pk, ObjectId)

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
        qs = User.objects.order_by([('creds', 1)])
        result = qs.first()
        self.assertEqual('Biden', result.lname)
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
        self.assertEqual(1, len(results))
        self.assertIsInstance(results[0], ObjectId)

        results = User.objects.bulk_create([
            User(fname='Woodrow', lname='Wilson'),
            User(fname='Andrew', lname='Jackson')])
        self.assertEqual(2, len(results))
        for result in results:
            self.assertIsInstance(result, ObjectId)

        results = User.objects.bulk_create(
            [
                User(fname='Benjamin', lname='Franklin'),
                User(fname='Benjamin', lname='Button')
            ],
            retrieve=True)
        self.assertEqual(2, len(results))
        for result in results:
            self.assertIsInstance(result, MongoModel)
            self.assertEqual('Benjamin', result.fname)

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
                {'$set': {'fname': 'Banana'}}
            ))
        results = list(User.objects.raw({'fname': 'Banana'}))
        self.assertEqual(2, len(results))
        for result in results:
            self.assertEqual('Tomato', result.lname)

    def test_getitem(self):
        users = User.objects.order_by([('creds', 1)])
        self.assertEqual(0, users[0].creds)
        self.assertEqual(3, users[3].creds)

    def test_slice(self):
        users = User.objects.order_by([('creds', 1)])[2:3]
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
            self.assertIsNone(posts[0].comments)
            self.assertIsInstance(posts[1].comments[0], ObjectId)
            self.assertIsInstance(posts[1].comments[1], ObjectId)

            posts = list(Post.objects.select_related())
            self.assertIsNone(posts[0].comments)
            self.assertEqual(posts[1].comments, comments)
