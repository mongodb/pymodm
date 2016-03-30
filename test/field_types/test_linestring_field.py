from pymodm.errors import ValidationError
from pymodm.fields import LineStringField

from test.field_types import FieldTestCase


class LineStringFieldTestCase(FieldTestCase):

    field = LineStringField()
    geojson = {'type': 'LineString', 'coordinates': [[1, 2], [3, 4]]}

    def test_conversion(self):
        self.assertConversion(self.field, self.geojson, [[1, 2], [3, 4]])
        self.assertConversion(self.field, self.geojson, self.geojson)

    def test_validate(self):
        msg = 'Value must be a dict'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(42)
        msg = "GeoJSON type must be 'LineString'"
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Polygon', 'coordinates': []})
        msg = 'Coordinates must be one of .*list.*tuple'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'LineString', 'coordinates': 42})
        msg = 'must contain at least one Point'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'LineString', 'coordinates': [42]})
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'LineString', 'coordinates': [[]]})
