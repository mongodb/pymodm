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

import re

from bson.regex import Regex

from pymodm.fields import RegularExpressionField

from test.field_types import FieldTestCase


class RegularExpressionFieldTestCase(FieldTestCase):

    field = RegularExpressionField()
    pattern = re.compile('hello', re.UNICODE)
    regex = Regex.from_native(pattern)

    def assertPatternEquals(self, reg1, reg2):
        """Assert two compiled regular expression pattern objects are equal."""
        self.assertEqual(reg1.pattern, reg2.pattern)
        self.assertEqual(reg1.flags, reg2.flags)

    def test_to_python(self):
        self.assertPatternEquals(
            self.pattern, self.field.to_python(self.pattern))
        self.assertPatternEquals(
            self.pattern, self.field.to_python(self.regex))

    def test_to_mongo(self):
        self.assertEqual(self.regex, self.field.to_mongo(self.regex))
