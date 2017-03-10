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

from collections import OrderedDict

from pymodm.errors import ValidationError
from pymodm.fields import OrderedDictField

from test import INVALID_MONGO_NAMES, VALID_MONGO_NAMES
from test.field_types import FieldTestCase


class OrderedDictFieldTestCase(FieldTestCase):

    field = OrderedDictField()

    def test_conversion(self):
        data = OrderedDict({'one': 1, 'two': 2})
        self.assertConversion(self.field, data, data)
        self.assertConversion(self.field, data, {'one': 1, 'two': 2})

    def test_validate(self):
        msg = 'Dictionary keys must be a string type, not a int'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({42: 'forty-two'})

        for invalid_mongo_name in INVALID_MONGO_NAMES:
            msg = "Dictionary keys cannot .*"
            with self.assertRaisesRegex(ValidationError, msg):
                self.field.validate({invalid_mongo_name: 42})
            # Invalid name in a sub dict.
            with self.assertRaisesRegex(ValidationError, msg):
                self.field.validate({'foo': {invalid_mongo_name: 42}})
            # Invalid name in a sub dict inside an array.
            with self.assertRaisesRegex(ValidationError, msg):
                self.field.validate({'foo': [[{invalid_mongo_name: 42}]]})

        for valid_mongo_name in VALID_MONGO_NAMES:
            self.field.validate({valid_mongo_name: 42})
            self.field.validate({valid_mongo_name: [{valid_mongo_name: 42}]})
