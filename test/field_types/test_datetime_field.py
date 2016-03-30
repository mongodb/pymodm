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

from bson.tz_util import utc, FixedOffset

from pymodm.errors import ValidationError
from pymodm.fields import DateTimeField

from test.field_types import FieldTestCase


# (expected value, value to be converted)
DATETIME_CASES = [
    (   # datetimes are given back as-is.
        datetime.datetime(2006, 7, 2, 1, 3, 4, 123456, utc),
        datetime.datetime(2006, 7, 2, 1, 3, 4, 123456, utc)
    ),
    (   # parse str() of datetime.
        datetime.datetime(2006, 7, 2, 1, 3, 4, 123456, utc),
        '2006-07-02 01:03:04.123456+00:00'
    ),
    (   # alternative format
        datetime.datetime(2006, 7, 2, 1, 3, 4, 123456, utc),
        '2006-7-2T01:03:04.123456Z'
    ),
    (   # with fixed timezone offset
        datetime.datetime(
            2006, 7, 2, 1, 3, 4, 123456, FixedOffset(270, '+04:30')),
        '2006-7-2T01:03:04.123456+04:30'
    ),
    (   # missing microseconds
        datetime.datetime(2006, 7, 2, 1, 3, 4, 0, FixedOffset(270, '+04:30')),
        '2006-7-2T01:03:04+04:30'
    ),
    (   # missing seconds
        datetime.datetime(2006, 7, 2, 1, 3, 0, 0, FixedOffset(270, '+04:30')),
        '2006-7-2T01:03+04:30'
    ),
    (  # only hour and minute
        datetime.datetime(2006, 7, 2, 0, 0, 0, 0, FixedOffset(270, '+04:30')),
        '2006-7-2+04:30'
    ),
    (   # with negative timezone offset
        datetime.datetime(2006, 7, 2, 1, 3, 4, 123456,
                          FixedOffset(-180, '-03:00')),
        '2006-7-2T01:03:04.123456-0300'
    ),
    (   # only three digits of microseconds
        datetime.datetime(2006, 7, 2, 1, 3, 4, 123000,
                          FixedOffset(-180, '-03:00')),
        '2006-7-2T01:03:04.123-0300'
    )
]


class DateTimeFieldTestCase(FieldTestCase):

    field = DateTimeField()
    date = datetime.datetime(
        year=2006, month=7, day=2, hour=1, minute=3, second=4,
        microsecond=123456, tzinfo=utc)

    def test_conversion(self):
        self.assertConversion(
            self.field,
            datetime.datetime(2006, 7, 2),
            datetime.date(2006, 7, 2))

        for expected, to_convert in DATETIME_CASES:
            self.assertConversion(self.field, expected, to_convert)

    def test_validate(self):
        msg = 'cannot be converted to a datetime object'
        with self.assertRaisesRegex(ValidationError, msg):
            # Inconvertible type.
            self.field.validate(22)
        with self.assertRaisesRegex(ValidationError, msg):
            # Microseconds without seconds.
            self.field.validate('2006-7-2T123.456')
        with self.assertRaisesRegex(ValidationError, msg):
            # Nonsense timezone.
            self.field.validate("2006-7-2T01:03:04.123456-03000")
        with self.assertRaisesRegex(ValidationError, msg):
            # Hours only.
            self.field.validate('2006-7-2T01')
