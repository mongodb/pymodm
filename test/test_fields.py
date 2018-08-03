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

import datetime
import re

from decimal import Decimal

import bson

from pymodm import fields, MongoModel
from pymodm.errors import ValidationError

from test import ODMTestCase, DB, INVALID_MONGO_NAMES, VALID_MONGO_NAMES


def name_must_be_capitalized(name):
    """Custom validator for Fields representing people's names."""
    if not re.match('[A-Z][a-z]*', name):
        raise ValidationError('name must be capitalized.')


class Person(MongoModel):
    email = fields.CharField(primary_key=True)
    first_name = fields.CharField(mongo_name='firstName',
                                  validators=[name_must_be_capitalized],
                                  required=True)
    last_name = fields.CharField(mongo_name='lastName',
                                 validators=[name_must_be_capitalized])
    ssn = fields.IntegerField(min_value=100000000, max_value=999999999)


class Student(Person):
    year = fields.CharField(
        choices=('freshman', 'sophomore', 'junior', 'senior')
    )


class Simple(MongoModel):
    name = fields.CharField(blank=True)


class Student2d(Person):
    FRESHMAN = 'FR'
    SOPHOMORE = 'SO'
    JUNIOR = 'JR'
    SENIOR = 'SR'

    year = fields.CharField(
        choices=(
            (FRESHMAN, 'freshman'),
            (SOPHOMORE, 'sophomore'),
            (JUNIOR, 'junior'),
            (SENIOR, 'senior')
        )
    )


class FloatDecimal(fields.FloatField):
    """ Toy class to test field encoding/decoding behavior."""
    def __init__(self, *args, **kwargs):
        self.to_python_call_count = 0
        self.to_mongo_call_count = 0
        super(FloatDecimal, self).__init__(*args, **kwargs)

    def to_python(self, value):
        self.to_python_call_count += 1
        return Decimal(value)

    def to_mongo(self, value):
        self.to_mongo_call_count += 1
        return float(value)

    def reset_counters(self):
        self.to_python_call_count = 0
        self.to_mongo_call_count = 0


class Simple2(MongoModel):
    qty = FloatDecimal()


class FieldsTestCase(ODMTestCase):

    def test_auto_generate_primary_key(self):
        class AutoGeneratePrimaryKeyDefaultCallable(MongoModel):
            identifier = fields.ObjectIdField(
                primary_key=True, default=bson.ObjectId)
            data = fields.CharField()
        model = AutoGeneratePrimaryKeyDefaultCallable(data="some data")
        model.save()

    def test_commit_required_field_with_default(self):
        class RequiredFieldWithDefault(MongoModel):
            age = fields.IntegerField(default=10, required=True)
        model = RequiredFieldWithDefault()
        model.save()

    def test_field_encoding_decoding(self):
        def _refresh_and_reset(model_instance):
            model_instance.refresh_from_db()
            type(model_instance).qty.reset_counters()

        # Test reads from SON.
        model_instance = Simple2(qty=Decimal("1.23")).save()
        _refresh_and_reset(model_instance)
        num_tries = 5
        for _ in range(num_tries):
            _ = model_instance.qty
        self.assertEqual(Simple2.qty.to_python_call_count, 1)

        # Test conversion to SON.
        _refresh_and_reset(model_instance)
        num_tries = 5
        for _acc in range(num_tries):
            _ = model_instance.to_son()
        self.assertEqual(Simple2.qty.to_mongo_call_count, num_tries)

    def test_field_dbname(self):
        self.assertEqual('firstName', Person.first_name.mongo_name)
        Person(email='han@site.com', first_name='Han').save()
        self.assertEqual(
            'Han',
            DB.person.find_one().get('firstName'))

    def test_rename_primary_key(self):
        msg = 'The mongo_name of a primary key must be "_id".'
        with self.assertRaisesRegex(ValueError, msg):
            class RenamedPrimaryKey(MongoModel):
                renamed_pk = fields.CharField(mongo_name='foo',
                                              primary_key=True)

    def test_non_primary_key_named_id(self):
        msg = 'mongo_name is "_id", but primary_key is False.'
        with self.assertRaisesRegex(ValueError, msg):
            class NonPrimaryKeyNamedId(MongoModel):
                not_primary_key = fields.CharField(mongo_name='_id')
        msg = 'mongo_name of field _id is "_id", but primary_key is False.'
        with self.assertRaisesRegex(ValueError, msg):
            class NonPrimaryKeyNamedIdImplicitly(MongoModel):
                _id = fields.CharField()

    def test_validate_mongo_name(self):
        for invalid_mongo_name in INVALID_MONGO_NAMES:
            with self.assertRaisesRegex(ValueError, 'mongo_name cannot .*'):
                class InvalidMongoName(MongoModel):
                    field = fields.CharField(mongo_name=invalid_mongo_name)

        for valid_mongo_name in VALID_MONGO_NAMES:
            class ValidMongoName(MongoModel):
                field = fields.CharField(mongo_name=valid_mongo_name)
            self.assertEqual(ValidMongoName.field.mongo_name,
                             valid_mongo_name)
            self.assertEqual(ValidMongoName.field.attname, 'field')

    def test_pk_alias(self):
        Person('han.solo+wookie@milleniumfalcon.net', 'Han', 'Solo').save()
        retrieved = DB.person.find_one()
        self.assertEqual('han.solo+wookie@milleniumfalcon.net',
                         retrieved['_id'])

    def test_empty_fields(self):
        partial_info = Person(
            email='stranger@whatever.com',
            first_name='Stranger').save()
        retrieved = DB.person.find_one(projection={'_cls': 0})
        self.assertEqual(
            {'_id': partial_info.email, 'firstName': partial_info.first_name},
            retrieved)

    def test_model_validation(self):
        person = Person(email='luke@site.com', first_name='Luke', ssn='nan')
        with self.assertRaises(ValidationError):
            # SSN cannot be turned into an int.
            person.full_clean()

        person = Person(email='luke@site.com', first_name='Luke', ssn=42)
        with self.assertRaises(ValidationError):
            # SSN is out of range.
            person.full_clean()

    def test_custom_validators(self):
        person = Person(email='leia@site.com', first_name='leia')
        with self.assertRaises(ValidationError):
            # Names have to be capitalized.
            person.full_clean()

    def test_implicit_id(self):
        class NoExplicitId(MongoModel):
            first_name = fields.CharField()

        noid = NoExplicitId('hello')
        self.assertFalse(noid._id)
        self.assertNotIn('_id', noid.to_son())
        noid.save()
        self.assertIn('_id', noid.to_son())
        self.assertIsInstance(noid._id, bson.objectid.ObjectId)

    def test_field_choices(self):
        # Ok.
        Student(
            email='joe@site.com',
            first_name='Joe',
            year='freshman').full_clean()
        # Not a choice.
        with self.assertRaisesRegex(ValidationError, 'not a choice'):
            Student(year='sixth-year').full_clean()

    def test_field_choices_2d(self):
        # Ok.
        Student2d(
            email='bernard@site.com',
            first_name='Bernard',
            year=Student2d.FRESHMAN).full_clean()
        # Not a choice.
        with self.assertRaisesRegex(ValidationError, 'not a choice'):
            Student2d(year='freshman').full_clean()

    def test_required(self):
        # Positive cases tested in other tests.
        with self.assertRaisesRegex(ValidationError, 'field is required'):
            Student2d(
                email="bob@site.com", year=Student2d.FRESHMAN).full_clean()

    def test_set_empty(self):
        inst = Simple('a string with more than zero characters').save()
        self.assertEqual('a string with more than zero characters',
                         DB.simple.find_one()['name'])
        del inst.name
        inst.save()
        self.assertNotIn('name', DB.simple.find_one())

    def test_set_blank(self):
        class NoBlank(MongoModel):
            name = fields.CharField()

        inst = NoBlank('Gorgon')

        # Blank values.
        inst.name = ''
        with self.assertRaisesRegex(ValidationError, 'must not be blank'):
            inst.full_clean()
        inst.name = None
        with self.assertRaisesRegex(ValidationError, 'must not be blank'):
            inst.full_clean()

        # No value for the field is ok.
        del inst.name
        inst.full_clean()

    def test_save_blank_value(self):
        inst = Simple('a string with more than zero characters').save()
        inst.name = ''
        inst.save()
        self.assertEqual('', DB.simple.find_one()['name'])

        inst.name = None
        inst.save()
        self.assertIsNone(DB.simple.find_one()['name'])
        inst.refresh_from_db()
        self.assertIsNone(inst.name)

    def test_simple_required(self):
        class SimpleRequired(MongoModel):
            name = fields.CharField(required=True, blank=True)

        simple = SimpleRequired()
        with self.assertRaises(ValidationError):
            simple.full_clean()

        # No ValidationError.
        simple.name = ''
        simple.full_clean()

        del simple.name
        with self.assertRaises(ValidationError):
            simple.full_clean()

    def test_default(self):
        class SimpleDefault(MongoModel):
            name = fields.CharField(default='Bozo')

        inst = SimpleDefault()
        self.assertEqual('Bozo', inst.name)
        inst.name = 'Harold'
        self.assertEqual('Harold', inst.name)
        del inst.name
        self.assertEqual('Bozo', inst.name)

    def test_callable_default(self):
        now = datetime.datetime.now()

        class CallableDefault(MongoModel):
            date = fields.DateTimeField(default=lambda: now)

        inst = CallableDefault()
        self.assertEqual(now, inst.date)
        earlier = datetime.datetime(year=1999, month=10, day=4)
        inst.date = earlier
        self.assertEqual(earlier, inst.date)
        del inst.date
        self.assertEqual(now, inst.date)

        inst = CallableDefault().save()
        self.assertEqual(now, inst.date)

        # Default that is an empty value.
        class CallableEmptyValue(MongoModel):
            list_of_things = fields.ListField()

        inst = CallableEmptyValue().save()
        self.assertNotIn('list_of_things', DB.callable_empty_value.find_one())

    def test_mutable_default(self):
        class Article(MongoModel):
            tags = fields.ListField(fields.CharField())

        article = Article()
        self.assertIs(article.tags, article.tags)

        article.tags.append('foo')
        self.assertEqual(article.tags, ['foo'])
        article.tags.append('bar')
        self.assertEqual(article.tags, ['foo', 'bar'])

        # Ensure tags is saved to the database.
        article.save()
        self.assertEqual(article.tags, Article.objects.first().tags)
        self.assertEqual(article.tags, ['foo', 'bar'])

        # Ensure that deleting a field restores the default value.
        del article.tags
        self.assertEqual(article.tags, [])

        # Ensure the deleted field is removed from the database.
        article.save()
        self.assertNotIn('tags', DB.article.find_one())

        # Ensure that a refresh restores the default value.
        article.tags.append('foo')
        self.assertEqual(article.tags, ['foo'])
        article.refresh_from_db()
        self.assertEqual(article.tags, [])
