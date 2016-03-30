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
from pymodm.fields import DictField

from test.field_types import FieldTestCase


class DictFieldTestCase(FieldTestCase):

    field = DictField()

    def test_conversion(self):
        self.assertConversion(self.field,
                              {'one': 1, 'two': 2}, {'one': 1, 'two': 2})

    def test_validate(self):
        msg = 'All dictionary keys must be strings'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({42: 'forty-two'})
        msg = 'Dictionary keys must not contain "\$" or "\."'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'foo.bar': 42})
        self.field.validate({'forty-two': 42})
