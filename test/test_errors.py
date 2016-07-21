import re
import unittest

from pymodm.base import MongoModel
from pymodm.errors import ValidationError
from pymodm.fields import CharField, IntegerField


def must_be_all_caps(value):
    if re.search(r'[^A-Z]', value):
        raise ValidationError('field must be all uppercase.')


def must_be_three_letters(value):
    if len(value) != 3:
        raise ValidationError('field must be exactly three characters.')


class Document(MongoModel):
    region_code = CharField(
        validators=[must_be_all_caps, must_be_three_letters])
    number = IntegerField(min_value=0, max_value=100)
    title = CharField(required=True)


class ErrorTestCase(unittest.TestCase):

    def test_validation_error(self):
        messed_up_document = Document(region_code='asdf', number=12345)

        with self.assertRaises(ValidationError) as cm:
            messed_up_document.full_clean()

        message = cm.exception.message
        self.assertIsInstance(message, dict)
        self.assertIn('region_code', message)
        self.assertIn('number', message)

        self.assertIsInstance(message['region_code'], list)
        self.assertIn('field must be all uppercase.',
                      message['region_code'])
        self.assertIn('field must be exactly three characters.',
                      message['region_code'])

        self.assertIsInstance(message['number'], list)
        self.assertIn('12345 is greater than maximum value of 100.',
                      message['number'])

        self.assertEqual(['field is required.'], message['title'])
