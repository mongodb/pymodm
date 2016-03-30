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
from pymodm.fields import FloatField

from test.field_types import FieldTestCase


class FloatFieldTestCase(FieldTestCase):

    field = FloatField(min_value=0, max_value=100)

    def test_conversion(self):
        self.assertConversion(self.field, 42.0, '42')
        self.assertConversion(self.field, 42.0, 42)

    def test_validate(self):
        with self.assertRaisesRegex(ValidationError, 'greater than maximum'):
            self.field.validate(101)
        with self.assertRaisesRegex(ValidationError, 'less than minimum'):
            self.field.validate(-1)
        # No Exception.
        self.field.validate(42.123)
