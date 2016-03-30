from pymodm.errors import ValidationError
from pymodm.fields import GeometryCollectionField

from test import ODMTestCase


class GeometryCollectionFieldTestCase(ODMTestCase):

    field = GeometryCollectionField()
    geometries = [
        {'type': 'Point', 'coordinates': [1, 2]},
        {'type': 'LineString', 'coordinates': [[1, 2]]}
    ]
    geojson = {'type': 'GeometryCollection', 'geometries': geometries}

    def test_to_python(self):
        self.assertEqual(self.geojson, self.field.to_python(self.geometries))
        self.assertEqual(self.geojson, self.field.to_python(self.geojson))

    def test_to_mongo(self):
        self.assertEqual(self.geojson, self.field.to_mongo(self.geometries))
        self.assertEqual(self.geojson, self.field.to_mongo(self.geojson))

    def test_validate(self):
        msg = 'Value must be a dict'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(42)
        msg = "GeoJSON type must be 'GeometryCollection'"
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'Polygon', 'coordinates': []})
        msg = 'geometries must contain at least one geometry'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate({'type': 'GeometryCollection',
                                 'geometries': []})
        msg = 'Geometries must be one of .*list.*tuple'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(
                {'type': 'GeometryCollection', 'geometries': 42})
        msg = 'LineString must start and end at the same Point'
        with self.assertRaisesRegex(ValidationError, msg):
            self.field.validate(
                {'type': 'GeometryCollection', 'geometries': [
                    {'type': 'Polygon', 'coordinates': [
                        [[1, 2], [3, 4]]
                    ]}
                ]})
