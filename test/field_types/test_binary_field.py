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

from bson.binary import OLD_BINARY_SUBTYPE, Binary

from pymodm.fields import BinaryField

from test.field_types import FieldTestCase


class BinaryFieldTestCase(FieldTestCase):

    field = BinaryField(subtype=OLD_BINARY_SUBTYPE)
    binary = Binary(b'\x01\x02\x03\x04', OLD_BINARY_SUBTYPE)

    def test_conversion(self):
        self.assertConversion(self.field, self.binary, self.binary)
        self.assertConversion(self.field, self.binary, b'\x01\x02\x03\x04')
