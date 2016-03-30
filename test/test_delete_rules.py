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

from test import ODMTestCase

from pymodm.base import MongoModel
from pymodm.errors import OperationError
from pymodm import fields


class ReferencedModel(MongoModel):
    pass


class ReferencingModel(MongoModel):
    ref = fields.ReferenceField(ReferencedModel)


# Model classes that both reference each other.
class A(MongoModel):
    ref = fields.ReferenceField('B')


class B(MongoModel):
    ref = fields.ReferenceField(A)


class DeleteRulesTestCase(ODMTestCase):

    def tearDown(self):
        super(DeleteRulesTestCase, self).tearDown()
        # Remove all delete rules.
        for model_class in (ReferencedModel, ReferencingModel, A, B):
            model_class._mongometa.delete_rules.clear()

    def test_nullify(self):
        ReferencedModel.register_delete_rule(
            ReferencingModel, 'ref', fields.ReferenceField.NULLIFY)
        reffed = ReferencedModel().save()
        reffing = ReferencingModel(reffed).save()
        reffed.delete()
        reffing.refresh_from_db()
        self.assertIsNone(reffing.ref)

    # Test the on_delete attribute for one rule.
    def test_nullify_on_delete_attribute(self):
        class ReferencingModelWithAttribute(MongoModel):
            ref = fields.ReferenceField(
                ReferencedModel,
                on_delete=fields.ReferenceField.NULLIFY)
        reffed = ReferencedModel().save()
        reffing = ReferencingModelWithAttribute(reffed).save()
        reffed.delete()
        reffing.refresh_from_db()
        self.assertIsNone(reffing.ref)

    def test_bidirectional_on_delete_attribute(self):
        msg = 'Cannot specify on_delete without providing a Model class'
        with self.assertRaisesRegex(ValueError, msg):
            class ReferencingModelWithAttribute(MongoModel):
                ref = fields.ReferenceField(
                    # Cannot specify class a string.
                    'ReferencedModel',
                    on_delete=fields.ReferenceField.NULLIFY)

    def test_cascade(self):
        ReferencedModel.register_delete_rule(
            ReferencingModel, 'ref', fields.ReferenceField.CASCADE)
        reffed = ReferencedModel().save()
        ReferencingModel(reffed).save()
        reffed.delete()
        self.assertEqual(0, ReferencingModel.objects.count())

    def test_infinite_cascade(self):
        A.register_delete_rule(B, 'ref', fields.ReferenceField.CASCADE)
        B.register_delete_rule(A, 'ref', fields.ReferenceField.CASCADE)
        a = A().save()
        b = B().save()
        a.ref = b
        b.ref = a
        a.save()
        b.save()
        # No SystemError due to infinite recursion.
        a.delete()
        self.assertFalse(A.objects.count())
        self.assertFalse(B.objects.count())

    def test_deny(self):
        ReferencedModel.register_delete_rule(
            ReferencingModel, 'ref', fields.ReferenceField.DENY)
        reffed = ReferencedModel().save()
        ReferencingModel(reffed).save()
        with self.assertRaises(OperationError):
            ReferencedModel.objects.delete()
        with self.assertRaises(OperationError):
            reffed.delete()

    def test_pull(self):
        class MultiReferencingModel(MongoModel):
            refs = fields.ListField(fields.ReferenceField(ReferencedModel))
        ReferencedModel.register_delete_rule(
            MultiReferencingModel, 'refs', fields.ReferenceField.PULL)

        refs = [ReferencedModel().save() for i in range(3)]
        multi_reffing = MultiReferencingModel(refs).save()

        refs[0].delete()
        multi_reffing.refresh_from_db()
        self.assertEqual(2, len(multi_reffing.refs))

    def test_bidirectional(self):
        A.register_delete_rule(B, 'ref', fields.ReferenceField.DENY)
        B.register_delete_rule(A, 'ref', fields.ReferenceField.NULLIFY)

        a = A().save()
        b = B(a).save()
        a.ref = b
        a.save()

        with self.assertRaises(OperationError):
            a.delete()
        b.delete()
        a.refresh_from_db()
        self.assertIsNone(a.ref)

    def test_bidirectional_order(self):
        A.register_delete_rule(B, 'ref', fields.ReferenceField.DENY)
        B.register_delete_rule(A, 'ref', fields.ReferenceField.CASCADE)

        a = A().save()
        b = B(a).save()
        a.ref = b
        a.save()

        # Cannot delete A while referenced by a B.
        with self.assertRaises(OperationError):
            a.delete()
        # OK to delete a B, and doing so deletes all referencing A objects.
        b.delete()
        self.assertFalse(A.objects.count())
        self.assertFalse(B.objects.count())
