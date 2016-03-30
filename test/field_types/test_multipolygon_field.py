from pymodm.errors import ValidationError
from pymodm.fields import MultiPolygonField

from test import ODMTestCase


class MultiPolygonFieldTestCase(ODMTestCase):

    field = MultiPolygonField()
    coordinates = [[
        [
            [1, 2], [3, 4], [1, 2]
        ],
        [
            [-1, -2]
        ]
    ]]
    geojson = {'type': 'MultiPolygon', 'coordinates': coordinates}

    def test_to_python(self):
        self.assertEqual(self.geojson, self.field.to_python(self.coordinates))
        self.assertEqual(self.geojson, self.field.to_python(self.geojson))

    def test_to_mongo(self):
        self.assertEqual(self.geojson, self.field.to_mongo(self.coordinates))
        self.assertEqual(self.geojson, self.field.to_mongo(self.geojson))

    def test_validate(self):
        msg = 'Value must be a dict'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(42)
        msg = "GeoJSON type must be 'MultiPolygon'"
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Polygon', 'coordinates': []})
        msg = 'Coordinates must be one of .*list.*tuple'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'MultiPolygon', 'coordinates': 42})
        msg = 'must contain at least one Polygon'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'MultiPolygon', 'coordinates': [42]})
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(
                {'type': 'MultiPolygon', 'coordinates': [[[]]]})
