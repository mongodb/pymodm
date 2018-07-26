# Copyright 2018-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import copy
import unittest

from itertools import chain

from bson.decimal128 import Decimal128

from pymodm.base.models import _LazyDecoder


PYTHON_DATA = {
    "python": "helloworld"
}


MONGO_DATA = {
    "mongo": Decimal128("1.23")
}


class TestLazyDecoder(unittest.TestCase):
    def setUp(self):
        self.ld = _LazyDecoder()
        self.populate_lazy_decoder(self.ld)

    def tearDown(self):
        del self.ld

    def populate_lazy_decoder(self, ld):
        for key in PYTHON_DATA:
            ld.set_python_value(key, PYTHON_DATA[key])
        for key in MONGO_DATA:
            ld.set_mongo_value(key, MONGO_DATA[key])

    def test_clear(self):
        self.ld.clear()

        self.assertEqual(self.ld, _LazyDecoder())
        self.assertEqual(sum(1 for _ in self.ld), 0)

    def test_iter(self):
        all_members = set(iter(self.ld))
        expected_members = set(
            iter(chain(self.ld._mongo_data, self.ld._python_data))
        )

        self.assertGreater(len(expected_members), 0)
        self.assertEqual(all_members, expected_members)
        for item in self.ld:
            self.assertIn(item, expected_members)

    def test_eq(self):
        ld2 = _LazyDecoder()
        self.populate_lazy_decoder(ld2)
        self.assertEqual(self.ld, ld2)

        self.ld.set_python_value('python2', 'hellonewworld')
        self.assertNotEqual(self.ld, ld2)

    def test_remove(self):
        def _generate_keyset(*iterables):
            return set([k for k in iter(chain(*iterables))])

        all_keys = _generate_keyset(MONGO_DATA, PYTHON_DATA)
        expected_keyset = copy.copy(all_keys)
        for key in all_keys:
            self.ld.remove(key)
            expected_keyset.discard(key)
            data_keyset = _generate_keyset(
                self.ld._python_data, self.ld._mongo_data)
            iter_keyset = _generate_keyset(self.ld)

            # For each check the data, iter, and contains.
            self.assertEqual(data_keyset, expected_keyset)
            self.assertEqual(iter_keyset, expected_keyset)
            for candidate_key in expected_keyset:
                self.assertTrue(candidate_key in self.ld)

    def test_get_mongo_data_as_mongo_value(self):
        ldcopy = copy.deepcopy(self.ld)
        key = next(iter(self.ld._mongo_data))
        def _to_mongo(value):
            _to_mongo.call_count += 1
            return str.upper(value)
        _to_mongo.call_count = 0
        value = self.ld.get_mongo_value(key, _to_mongo)

        self.assertEqual(_to_mongo.call_count, 0)
        self.assertEqual(value, self.ld._mongo_data[key])
        self.assertEqual(self.ld, ldcopy)

    def test_get_python_data_as_mongo_value(self):
        ldcopy = copy.deepcopy(self.ld)
        key = next(iter(self.ld._python_data))
        def _to_python(value):
            _to_python.call_count +=1
            return str.upper(value)
        _to_python.call_count = 0
        value = self.ld.get_mongo_value(key, _to_python)

        self.assertEqual(_to_python.call_count, 1)
        self.assertEqual(value, _to_python(self.ld._python_data[key]))
        self.assertEqual(self.ld, ldcopy)

    def test_get_mongo_data_as_python_value(self):
        ldcopy = copy.deepcopy(self.ld)
        key = next(iter(self.ld._mongo_data))
        def _to_python(value):
            _to_python.call_count += 1
            return value.to_decimal()
        _to_python.call_count = 0
        mongo_value = self.ld.get_mongo_value(key, lambda x: None)
        value = self.ld.get_python_value(key, _to_python)

        # We expect the data to be converted to python and cached.
        self.assertEqual(_to_python.call_count, 1)
        self.assertEqual(value, _to_python(mongo_value))
        self.assertIn(key, self.ld._python_data)
        self.assertNotIn(key, self.ld._mongo_data)
        self.assertNotEqual(self.ld, ldcopy)
        self.assertEqual(set(iter(self.ld)), set(iter(ldcopy)))

        # Second access should not call conversion again.
        _to_python.call_count = 0
        _ = self.ld.get_python_value(key, _to_python)
        self.assertEqual(_to_python.call_count, 0)

    def test_get_python_data_as_python_value(self):
        ldcopy = copy.deepcopy(self.ld)
        key = next(iter(self.ld._python_data))
        def _to_python(value):
            _to_python.call_count += 1
            return str.upper(value)
        _to_python.call_count = 0
        value = self.ld.get_python_value(key, _to_python)

        self.assertEqual(_to_python.call_count, 0)
        self.assertEqual(value, self.ld._python_data[key])
        self.assertEqual(self.ld, ldcopy)
