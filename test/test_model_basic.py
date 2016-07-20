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

from test import ODMTestCase, DB
from test.models import User


class BasicModelTestCase(ODMTestCase):

    def test_instantiation(self):
        msg = 'Got 5 arguments for only 4 fields'
        with self.assertRaisesRegex(ValueError, msg):
            User('Gary', 1234567, '12 Apple Street', 42, 'cucumber')
        msg = 'Unrecognized field name'
        with self.assertRaisesRegex(ValueError, msg):
            User(last_name='Gygax')
        msg = 'name specified more than once in constructor for User'
        with self.assertRaisesRegex(ValueError, msg):
            User('Gary', fname='Gygax')

    def test_save(self):
        User('Gary').save()
        self.assertEqual('Gary', DB.some_collection.find_one()['_id'])

    def test_delete(self):
        gary = User('Gary').save()
        self.assertTrue(DB.some_collection.find_one())
        gary.delete()
        self.assertIsNone(DB.some_collection.find_one())

    def test_refresh_from_db(self):
        gary = User('Gary').save()
        DB.some_collection.update_one(
            {'_id': 'Gary'},
            {'$set': {'phone': 1234567}})
        gary.refresh_from_db()
        self.assertEqual(1234567, gary.phone)
