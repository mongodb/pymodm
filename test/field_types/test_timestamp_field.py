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

import datetime

from bson.timestamp import Timestamp

from pymodm.errors import ValidationError
from pymodm.fields import TimestampField

from test.field_types import FieldTestCase
from test.field_types.test_datetime_field import DATETIME_CASES


class TimestampFieldTestCase(FieldTestCase):

    field = TimestampField()

    def test_conversion(self):
        for dt_expected, to_convert in DATETIME_CASES:
            self.assertConversion(
                self.field,
                Timestamp(dt_expected, 0), to_convert)

    def test_validate(self):
        msg = 'cannot be converted to a Timestamp'
        with self.assertRaisesRegex(ValidationError, msg):
            # Inconvertible type.
            self.field.validate(42)
        with self.assertRaisesRegex(ValidationError, msg):
            # Unacceptable format for date string.
            self.field.validate("2006-7-2T01:03:04.123456-03000")
        self.field.validate(datetime.datetime.now())
        self.field.validate('2006-7-2T01:03:04.123456-0300')
        self.field.validate(Timestamp(0, 0))
