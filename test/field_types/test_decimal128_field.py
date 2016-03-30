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

import decimal

from unittest import SkipTest

from pymodm.errors import ValidationError
from pymodm.fields import Decimal128Field

HAS_DECIMAL128 = True
try:
    from bson.decimal128 import Decimal128, create_decimal128_context
except ImportError:
    HAS_DECIMAL128 = False

from test import DB
from test.field_types import FieldTestCase


class Decimal128FieldTestCase(FieldTestCase):

    @classmethod
    def setUpClass(cls):
        if not HAS_DECIMAL128:
            raise SkipTest(
                'Need PyMongo >= 3.4 in order to test Decimal128Field.')
        buildinfo = DB.command('buildinfo')
        version = tuple(buildinfo['versionArray'][:3])
        if version < (3, 3, 6):
            raise SkipTest('Must have MongoDB >= 3.4 to test Decimal128Field.')
        cls.field = Decimal128Field(min_value=0, max_value=100)

    def test_conversion(self):
        with decimal.localcontext(create_decimal128_context()) as ctx:
            expected = Decimal128(ctx.create_decimal('42'))
        self.assertConversion(self.field, expected, 42)
        self.assertConversion(self.field, expected, '42')
        self.assertConversion(self.field, expected, decimal.Decimal('42'))

    def test_validate(self):
        with self.assertRaisesRegex(ValidationError, 'greater than maximum'):
            self.field.validate(101)
        with self.assertRaisesRegex(ValidationError, 'less than minimum'):
            self.field.validate(-1)
        msg = 'Cannot convert value .* InvalidOperation'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate('hello')
        # No Exception.
        self.field.validate(42)
        self.field.validate(decimal.Decimal('42.111'))
        self.field.validate('42.111')
