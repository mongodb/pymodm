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

from pymongo import IndexModel

from pymodm import MongoModel, fields


class ParentModel(MongoModel):
    fname = fields.CharField("Customer first name", primary_key=True)
    lname = fields.CharField()
    phone = fields.IntegerField("Phone #",
                                min_value=1000000, max_value=9999999)
    foo = 'bar'  # Not counted among fields.

    class Meta:
        collection_name = 'some_collection'


class UserOtherCollection(ParentModel):
    class Meta:
        collection_name = 'other_collection'


class User(ParentModel):
    address = fields.CharField()


class Fruit(MongoModel):
    name = fields.CharField()
    color = fields.CharField()

    class Meta:
        collection_name = 'test_fruit'
        indexes = [IndexModel([('name', 1), ('color', 1)], unique=True)]
