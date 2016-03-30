from pymodm.errors import ValidationError
from pymodm.fields import MultiPointField

from test import ODMTestCase


class MultiPointFieldTestCase(ODMTestCase):

    field = MultiPointField()
    geojson = {'type': 'MultiPoint', 'coordinates': [[1, 2], [3, 4]]}

    def test_to_python(self):
        self.assertEqual(self.geojson, self.field.to_python([[1, 2], [3, 4]]))
        self.assertEqual(self.geojson, self.field.to_python(self.geojson))

    def test_to_mongo(self):
        self.assertEqual(self.geojson, self.field.to_mongo([[1, 2], [3, 4]]))
        self.assertEqual(self.geojson, self.field.to_mongo(self.geojson))

    def test_validate(self):
        msg = 'Value must be a dict'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(42)
        msg = "GeoJSON type must be 'MultiPoint'"
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Polygon', 'coordinates': []})
        msg = 'Coordinates must be one of .*list.*tuple'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'MultiPoint', 'coordinates': 42})
        msg = 'must contain at least one Point'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'MultiPoint', 'coordinates': []})
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'MultiPoint', 'coordinates': [[]]})
