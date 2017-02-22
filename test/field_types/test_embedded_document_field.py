# Copyright 2016 MongoDB, Inc.
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
from bson import SON

from pymodm import EmbeddedMongoModel
from pymodm.fields import EmbeddedDocumentField, CharField

from test.field_types import FieldTestCase


class EmbeddedDocument(EmbeddedMongoModel):
    name = CharField()

    class Meta:
        final = True


class EmbeddedDocumentFieldTestCase(FieldTestCase):

    field = EmbeddedDocumentField(EmbeddedDocument)

    def test_to_python(self):
        value = self.field.to_python({'name': 'Bob'})
        self.assertIsInstance(value, EmbeddedDocument)

        doc = EmbeddedDocument(name='Bob')
        value = self.field.to_python(doc)
        self.assertIsInstance(value, EmbeddedDocument)
        self.assertEqual(value, doc)

    def test_to_mongo(self):
        doc = EmbeddedDocument(name='Bob')
        value = self.field.to_mongo(doc)
        self.assertIsInstance(value, SON)
        self.assertEqual(value, SON({'name': 'Bob'}))

        son = value
        value = self.field.to_mongo(son)
        self.assertIsInstance(value, SON)
        self.assertEqual(value, SON({'name': 'Bob'}))

        value = self.field.to_mongo({'name': 'Bob'})

        self.assertIsInstance(value, SON)
        self.assertEqual(value, SON({'name': 'Bob'}))
