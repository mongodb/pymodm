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

from pymodm.errors import ValidationError
from pymodm.fields import CharField

from test.field_types import FieldTestCase


class CharFieldTestCase(FieldTestCase):

    field = CharField(min_length=2, max_length=5)

    def test_conversion(self):
        self.assertConversion(self.field, 'hello', 'hello')
        self.assertConversion(self.field, '42', 42)

    def test_validate(self):
        msg = 'exceeds the maximum length of 5'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate('onomatopoeia')
        msg = 'is under the minimum length of 2'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate('a')
        self.field.validate('hello')
