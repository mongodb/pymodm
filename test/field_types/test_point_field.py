from pymodm.errors import ValidationError
from pymodm.fields import PointField

from test.field_types import FieldTestCase


class PointFieldTestCase(FieldTestCase):

    field = PointField()
    geojson = {'type': 'Point', 'coordinates': [1, 2]}

    def test_conversion(self):
        self.assertConversion(self.field, self.geojson, [1, 2])
        self.assertConversion(self.field, self.geojson, self.geojson)

    def test_validate(self):
        msg = 'Value must be a dict'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(42)
        msg = "GeoJSON type must be 'Point'"
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'banana', 'coordinates': [1, 2]})
        msg = 'Coordinates must be one of .*list.*tuple'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Point', 'coordinates': 42})
        msg = 'Point is not a pair'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Point', 'coordinates': [42]})
