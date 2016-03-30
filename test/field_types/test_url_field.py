from pymodm.errors import ValidationError
from pymodm.fields import URLField

from test.field_types import FieldTestCase


class URLFieldTestCase(FieldTestCase):

    field = URLField()

    def test_conversion(self):
        self.assertConversion(self.field,
                              'http://192.168.1.100/admin',
                              'http://192.168.1.100/admin')

    def test_validate(self):
        with self.assertRaisesRegex(ValidationError, 'Unrecognized scheme'):
            # Bad scheme.
            self.field.validate('afp://192.168.1.100')
        with self.assertRaisesRegex(ValidationError, 'Invalid URL'):
            # Bad domain.
            self.field.validate('http://??????????')
        with self.assertRaisesRegex(ValidationError, 'Invalid URL'):
            # Bad port.
            self.field.validate('http://foo.com:bar')
        with self.assertRaisesRegex(ValidationError, 'Invalid path'):
            # Bad path.
            self.field.validate('http://foo.com/ index.html')
        self.field.validate('http://foo.com:8080/index.html')
        self.field.validate('ftps://fe80::6203:8ff:fe89:b6b0:1234/foo/bar')
