from pymodm.errors import ValidationError
from pymodm.fields import PolygonField

from test.field_types import FieldTestCase


class PolygonFieldTestCase(FieldTestCase):

    field = PolygonField()
    coordinates = [
        [
            [1, 2], [3, 4], [1, 2]
        ],
        [
            [-1, -2]
        ]
    ]
    geojson = {'type': 'Polygon', 'coordinates': coordinates}

    def test_conversion(self):
        self.assertConversion(self.field, self.geojson, self.coordinates)
        self.assertConversion(self.field, self.geojson, self.geojson)

    def test_validate(self):
        msg = 'Value must be a dict'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(42)
        msg = "GeoJSON type must be 'Polygon'"
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Point', 'coordinates': [[]]})
        msg = 'Coordinates must be one of .*list.*tuple'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Polygon', 'coordinates': 42})
        msg = 'must contain at least one LineString'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Polygon', 'coordinates': [42]})
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Polygon', 'coordinates': [[]]})
        msg = 'must start and end at the same Point'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Polygon', 'coordinates': [
                [[1, 2], [3, 4]]
            ]})
