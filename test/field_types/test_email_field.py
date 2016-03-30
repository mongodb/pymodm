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
from pymodm.fields import EmailField

from test.field_types import FieldTestCase


class EmailFieldTestCase(FieldTestCase):

    field = EmailField()

    def test_conversion(self):
        self.assertConversion(self.field, 'foo@bar.com', 'foo@bar.com')

    def test_validate(self):
        msg = 'not a valid email address'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate('hello')
        self.field.validate('foo@bar.com')
