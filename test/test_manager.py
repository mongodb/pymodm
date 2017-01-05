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

from pymodm import fields, MongoModel
from pymodm.manager import Manager
from pymodm.queryset import QuerySet

from test import ODMTestCase


class CustomQuerySet(QuerySet):
    def authors(self):
        """Return a QuerySet over documents representing authors."""
        return self.raw({'role': 'A'})

    def editors(self):
        """Return a QuerySet over documents representing editors."""
        return self.raw({'role': 'E'})


CustomManager = Manager.from_queryset(CustomQuerySet)


class BookCredit(MongoModel):
    first_name = fields.CharField()
    last_name = fields.CharField()
    role = fields.CharField(choices=[('A', 'author'), ('E', 'editor')])
    contributors = CustomManager()
    more_contributors = CustomManager()


class ManagerTestCase(ODMTestCase):

    def test_default_manager(self):
        # No auto-created Manager, since we defined our own.
        self.assertFalse(hasattr(BookCredit, 'objects'))
        # Check that our custom Manager was installed.
        self.assertIsInstance(BookCredit.contributors, CustomManager)
        # Contributors should be the default manager, not more_contributors.
        self.assertIs(BookCredit.contributors,
                      BookCredit._mongometa.default_manager)

    def test_get_queryset(self):
        self.assertIsInstance(
            BookCredit.contributors.get_queryset(), CustomQuerySet)

    def test_access(self):
        credit = BookCredit(first_name='Frank', last_name='Herbert', role='A')
        msg = "Manager isn't accessible via BookCredit instances"
        with self.assertRaisesRegex(AttributeError, msg):
            credit.contributors

    def test_wrappers(self):
        manager = BookCredit.contributors
        self.assertTrue(hasattr(manager, 'editors'))
        self.assertTrue(hasattr(manager, 'authors'))
        self.assertEqual(
            CustomQuerySet.editors.__doc__, manager.editors.__doc__)
        self.assertEqual(
            CustomQuerySet.authors.__doc__, manager.authors.__doc__)
