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
from pymodm.fields import EmbeddedDocumentListField, CharField

from test.field_types import FieldTestCase


class EmbeddedDocument(EmbeddedMongoModel):
    name = CharField()

    class Meta:
        final = True


class EmbeddedDocumentFieldTestCase(FieldTestCase):

    field = EmbeddedDocumentListField(EmbeddedDocument)

    def test_to_python(self):
        # pass a raw list
        value = self.field.to_python([{'name': 'Bob'}, {'name': 'Alice'}])

        self.assertIsInstance(value, list)
        self.assertIsInstance(value[0], EmbeddedDocument)
        self.assertEqual(value[0].name, 'Bob')
        self.assertIsInstance(value[1], EmbeddedDocument)
        self.assertEqual(value[1].name, 'Alice')

        # pass a list of models
        bob = EmbeddedDocument(name='Bob')
        alice = EmbeddedDocument(name='Alice')
        value = self.field.to_python([bob, alice])

        self.assertIsInstance(value, list)
        self.assertIsInstance(value[0], EmbeddedDocument)
        self.assertEqual(value[0].name, 'Bob')
        self.assertIsInstance(value[1], EmbeddedDocument)
        self.assertEqual(value[1].name, 'Alice')

    def test_to_mongo(self):
        bob = EmbeddedDocument(name='Bob')
        alice = EmbeddedDocument(name='Alice')
        emb_list = [bob, alice]
        value = self.field.to_mongo(emb_list)
        self.assertIsInstance(value, list)
        self.assertIsInstance(value[0], SON)
        self.assertEqual(value[0], SON({'name': 'Bob'}))
        self.assertIsInstance(value[1], SON)
        self.assertEqual(value[1], SON({'name': 'Alice'}))

        son = value
        value = self.field.to_mongo(son)
        self.assertIsInstance(value, list)
        self.assertIsInstance(value[0], SON)
        self.assertEqual(value[0], SON({'name': 'Bob'}))
        self.assertIsInstance(value[1], SON)
        self.assertEqual(value[1], SON({'name': 'Alice'}))

        value = self.field.to_mongo([{'name': 'Bob'}, alice])
        self.assertIsInstance(value, list)
        self.assertIsInstance(value[0], SON)
        self.assertEqual(value[0], SON({'name': 'Bob'}))
        self.assertIsInstance(value[1], SON)
        self.assertEqual(value[1], SON({'name': 'Alice'}))

    def test_get_default(self):
        self.assertEqual([], self.field.get_default())
