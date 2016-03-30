from pymodm.errors import ValidationError
from pymodm.fields import MultiLineStringField

from test import ODMTestCase


class MultiLineStringFieldTestCase(ODMTestCase):

    field = MultiLineStringField()
    geojson = {'type': 'MultiLineString', 'coordinates': [[[1, 2], [3, 4]]]}

    def test_to_python(self):
        self.assertEqual(self.geojson, self.field.to_python([[[1, 2], [3, 4]]]))
        self.assertEqual(self.geojson, self.field.to_python(self.geojson))

    def test_to_mongo(self):
        self.assertEqual(self.geojson, self.field.to_mongo([[[1, 2], [3, 4]]]))
        self.assertEqual(self.geojson, self.field.to_mongo(self.geojson))

    def test_validate(self):
        msg = 'Value must be a dict'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(42)
        msg = "GeoJSON type must be 'MultiLineString'"
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Polygon', 'coordinates': []})
        msg = 'Coordinates must be one of .*list.*tuple'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'MultiLineString', 'coordinates': 42})
        msg = 'must contain at least one LineString'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'MultiLineString', 'coordinates': []})
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(
                {'type': 'MultiLineString', 'coordinates': [[]]})
