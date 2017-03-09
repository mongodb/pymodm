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

from pymodm.base.options import MongoOptions
from pymodm.connection import DEFAULT_CONNECTION_ALIAS
from pymodm import fields

from test import ODMTestCase
from test.models import ParentModel, UserOtherCollection, User


class Renamed(User):
    # Override existing field and change mongo_name
    address = fields.CharField(mongo_name='mongo_address')


class MongoOptionsTestCase(ODMTestCase):

    def test_metadata(self):
        # Defined on Model.
        self.assertEqual(
            'other_collection',
            UserOtherCollection._mongometa.collection_name)
        # Not inherited from parent.
        self.assertEqual(
            DEFAULT_CONNECTION_ALIAS,
            UserOtherCollection._mongometa.connection_alias)
        # Inherited from parent.
        self.assertEqual(
            'some_collection',
            User._mongometa.collection_name)

    def test_collection(self):
        self.assertEqual(
            'some_collection',
            ParentModel._mongometa.collection.name)
        self.assertEqual(
            'other_collection',
            UserOtherCollection._mongometa.collection.name)

    def test_get_fields(self):
        # Fields are returned in order.
        self.assertEqual(
            ['_id', 'lname', 'phone', 'address'],
            [field.mongo_name for field in User._mongometa.get_fields()])

    def test_get_field(self):
        self.assertIs(
            User.address, User._mongometa.get_field('address'))
        self.assertIs(
            Renamed.address, Renamed._mongometa.get_field('mongo_address'))
        self.assertIsNone(Renamed._mongometa.get_field('address'))

    def test_get_field_from_attname(self):
        self.assertIs(
            User.address, User._mongometa.get_field_from_attname('address'))
        self.assertIs(
            Renamed.address,
            Renamed._mongometa.get_field_from_attname('address'))
        self.assertIsNone(
            Renamed._mongometa.get_field_from_attname('mongo_address'))

    def test_add_field(self):
        options = MongoOptions()
        # Add new Fields.
        options.add_field(fields.CharField(mongo_name='fname'))
        options.add_field(fields.UUIDField(mongo_name='id'))
        self.assertEqual(
            ['fname', 'id'],
            [field.mongo_name for field in options.get_fields()])
        # Replace a Field.
        options.add_field(fields.ObjectIdField(mongo_name='id'))
        self.assertIsInstance(options.get_fields()[-1], fields.ObjectIdField)
        # Replace a field with a different mongo_name, but same attname.
        new_field = fields.ObjectIdField(mongo_name='newid')
        new_field.attname = 'id'
        options.add_field(new_field)
        self.assertEqual(len(options.get_fields()), 2)
