# Copyright 2018 MongoDB, Inc.
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

from pymodm import MongoModel
from pymodm.fields import ReferenceField, IntegerField, CharField

from test.field_types import FieldTestCase


class DummyReferenceModel(MongoModel):
    data = CharField()


class ReferenceFieldTestCase(FieldTestCase):
    def test_validation_on_initialization(self):
        # Initializing ReferenceField with a model instance raises exception.
        dummy = DummyReferenceModel(data='hello')
        with self.assertRaisesRegex(
                ValueError,
                "model must be a Model class or a string"):
            _ = ReferenceField(dummy)

        # Initializing ReferenceField with a model class is OK.
        _ = ReferenceField(DummyReferenceModel)
