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
from pymodm.fields import GenericIPAddressField

from test.field_types import FieldTestCase


class GenericIPAddressFieldTestCase(FieldTestCase):

    field_ipv4 = GenericIPAddressField(protocol=GenericIPAddressField.IPV4)
    field_ipv6 = GenericIPAddressField(protocol=GenericIPAddressField.IPV6)
    field_both = GenericIPAddressField(protocol=GenericIPAddressField.BOTH)

    def test_conversion(self):
        self.assertConversion(self.field_ipv4, '192.168.1.100', '192.168.1.100')
        self.assertConversion(self.field_ipv6,
                              'fe80::6203:8ff:fe89', 'fe80::6203:8ff:fe89')
        self.assertConversion(self.field_both, '192.168.1.100', '192.168.1.100')
        self.assertConversion(self.field_both,
                              'fe80::6203:8ff:fe89', 'fe80::6203:8ff:fe89')

    def test_validate(self):
        with self.assertRaisesRegex(ValidationError, 'not a valid IP address'):
            self.field_ipv4.validate('fe80::6203:8ff:fe89')
        with self.assertRaisesRegex(ValidationError, 'not a valid IP address'):
            self.field_ipv6.validate('192.168.1.100')
        with self.assertRaisesRegex(ValidationError, 'not a valid IP address'):
            self.field_both.validate('hello')
        with self.assertRaisesRegex(ValidationError, 'not a valid IP address'):
            self.field_both.validate('192.168.1.100 ')  # Trailing space
        self.field_ipv4.validate('192.168.1.100')
        self.field_ipv6.validate('fe80::6203:8ff:fe89')
        self.field_both.validate('192.168.1.100')
        self.field_both.validate('fe80::6203:8ff:fe89')
