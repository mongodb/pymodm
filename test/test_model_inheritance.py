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

from pymongo.operations import IndexModel

from pymodm import fields, MongoModel
from pymodm.errors import InvalidModel

from test import ODMTestCase, DB
from test.models import ParentModel, User


class AnotherUser(ParentModel):
    class Meta:
        collection_name = 'bulbasaur'


class MultipleInheritanceModel(User, AnotherUser):
    phone = fields.CharField()  # Shadow phone field from ParentModel.


class FinalModel(MongoModel):
    class Meta:
        final = True


class ModelInheritanceTest(ODMTestCase):

    def test_simple_inheritance(self):
        child = User(fname='Gary', phone=1234567)
        self.assertIsInstance(child, User)
        self.assertIsInstance(child, ParentModel)
        # 'name' is primary key from parent.
        self.assertEqualsModel(
            SON([('_id', 'Gary'), ('phone', 1234567)]), child)
        child.save()
        # We use the correct collection name.
        result = User.objects.first()
        self.assertEqual(child, result)

    def test_no_field_shadow(self):
        self.assertIsInstance(
            MultipleInheritanceModel.phone, fields.CharField)

    def test_multiple_inheritance(self):
        mim = MultipleInheritanceModel(
            fname='Ash', phone='123', address='24 Pallet Town Ave.')
        self.assertIsInstance(mim, User)
        self.assertIsInstance(mim, AnotherUser)
        self.assertEqualsModel(
            SON([('_id', 'Ash'), ('address', '24 Pallet Town Ave.'),
                 ('phone', '123')]),
            mim)
        mim.save()
        result = MultipleInheritanceModel.objects.first()
        self.assertEqual(mim, result)
        # Use the correct collection name.
        self.assertEqual(
            'bulbasaur', MultipleInheritanceModel._mongometa.collection_name)
        self.assertEqual(
            MultipleInheritanceModel.from_document(DB.bulbasaur.find_one()),
            result)

    def test_inheritance_collocation(self):
        parent = ParentModel('Oak', phone=9876432).save()
        user = User('Blane', phone=3456789, address='72 Cinnabar').save()
        results = list(ParentModel.objects.order_by([('phone', 1)]))
        self.assertEqual([user, parent], results)
        self.assertEqual([user], list(User.objects.all()))

    def test_final(self):
        msg = 'Cannot extend class .* because it has been declared final'
        with self.assertRaisesRegex(InvalidModel, msg):
            class ExtendsFinalModel(FinalModel):
                pass

    def test_final_metadata_storage(self):
        FinalModel().save()
        self.assertNotIn('_cls', DB.final_model.find_one())

    def test_indexes(self):
        class ModelWithIndexes(MongoModel):
            product_id = fields.UUIDField()
            name = fields.CharField()

            class Meta:
                indexes = [
                    IndexModel([('product_id', 1), ('name', 1)], unique=True)
                ]

        # No Exception.
        class ChildModel(ModelWithIndexes):
            pass

        index_info = DB.model_with_indexes.index_information()
        self.assertTrue(index_info['product_id_1_name_1']['unique'])
