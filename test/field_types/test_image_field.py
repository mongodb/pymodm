import os
import os.path

from unittest import SkipTest

from test import DB
from test.field_types import FieldTestCase

from pymodm import MongoModel
from pymodm.errors import ConfigurationError
from pymodm.fields import ImageField
from pymodm.files import File


class ImageFieldTestCase(FieldTestCase):

    image_src = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'lib', 'augustus.png')
    image_width = 589
    image_height = 387
    image_format = 'PNG'

    @classmethod
    def setUpClass(cls):
        try:
            # Define class here so tests don't fail with an error if PIL is not
            # installed.
            class ModelWithImage(MongoModel):
                image = ImageField()
            cls.ModelWithImage = ModelWithImage
        except ConfigurationError:
            raise SkipTest('Cannot test ImageField without PIL installed.')

    def test_set_file(self):
        # Create directly with builtin 'open'.
        with open(self.image_src, 'rb') as image_src:
            mwi = self.ModelWithImage(image_src).save()
        mwi.refresh_from_db()
        # Uploaded!
        self.assertEqual(self.image_src, mwi.image.name)
        self.assertTrue(DB.fs.files.find_one().get('length'))

    def test_set_file_object(self):
        # Create with File object.
        with open(self.image_src, 'rb') as image_src:
            wrapped = File(image_src, metadata={'contentType': 'image/png'})
            mwi = self.ModelWithImage(wrapped).save()
        mwi.refresh_from_db()
        self.assertEqual(self.image_src, mwi.image.name)
        self.assertTrue(DB.fs.files.find_one().get('length'))
        self.assertEqual('image/png', mwi.image.metadata.get('contentType'))

    def test_image_field_file_properties(self):
        with open(self.image_src, 'rb') as image_src:
            mwi = self.ModelWithImage(image_src).save()
        self.assertEqual(self.image_width, mwi.image.width)
        self.assertEqual(self.image_height, mwi.image.height)
        self.assertEqual(self.image_format, mwi.image.format)
