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

from pymodm import MongoModel
from pymodm.errors import ValidationError
from pymodm.fields import ListField, IntegerField, CharField

from test import DB
from test.field_types import FieldTestCase


class ListFieldTestCase(FieldTestCase):

    field = ListField(IntegerField(min_value=0))

    class Article(MongoModel):
        tags = ListField(CharField())

    def test_conversion(self):
        self.assertConversion(self.field, [1, 2, 3], [1, 2, 3])
        self.assertConversion(self.field, [1, 2, 3], ['1', '2', '3'])

    def test_validate(self):
        with self.assertRaisesRegex(ValidationError, 'less than minimum'):
            self.field.validate([-1, 3, 4])
        self.field.validate([1, 2, 3])

    def test_get_default(self):
        self.assertEqual([], self.field.get_default())

    def test_mutable_default(self):
        article = self.Article()
        self.assertIs(article.tags, article.tags)

        article.tags.append('foo')
        article.tags.append('bar')
        self.assertEqual(article.tags, ['foo', 'bar'])

        # Ensure tags is saved to the database.
        article.save()
        self.assertEqual(article.tags, self.Article.objects.first().tags)
        self.assertEqual(article.tags, ['foo', 'bar'])

        # Ensure that deleting a field restores the default value.
        del article.tags
        self.assertEqual(article.tags, [])

        # Ensure the deleted field is removed from the database.
        article.save()
        self.assertNotIn('tags', DB.article.find_one())
