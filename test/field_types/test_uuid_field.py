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

import uuid

from bson.binary import JAVA_LEGACY
from bson.codec_options import CodecOptions

from pymodm import MongoModel
from pymodm.errors import ValidationError
from pymodm.fields import UUIDField

from test import DB
from test.field_types import FieldTestCase


class ModelWithUUID(MongoModel):
    id = UUIDField(primary_key=True)

    class Meta:
        # The UUID representation is given at the Model level instead of at the
        # field level because PyMongo's CodecOptions has collection level
        # granularity. Providing the ability to mix UUID representations will
        # make those UUIDs very difficult to read back properly.
        codec_options = CodecOptions(uuid_representation=JAVA_LEGACY)


class UUIDFieldTestCase(FieldTestCase):
    id = uuid.UUID('026fab8f-975f-4965-9fbf-85ad874c60ff')
    field = ModelWithUUID.id

    def test_conversion(self):
        self.assertConversion(self.field, self.id, self.id)
        self.assertConversion(self.field,
                              self.id, '{026fab8f-975f-4965-9fbf-85ad874c60ff}')

    def test_validate(self):
        # Error message comes from UUID.__init__.
        with self.assertRaises(ValidationError):
            self.field.validate('hello')
        self.field.validate('{026fab8f-975f-4965-9fbf-85ad874c60ff}')
        self.field.validate(self.id)

    def test_uuid_representation(self):
        ModelWithUUID(self.id).save()
        collection = DB.get_collection(
            'model_with_uuid',
            codec_options=CodecOptions(uuid_representation=JAVA_LEGACY))
        self.assertEqual(self.id, collection.find_one()['_id'])
