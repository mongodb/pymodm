from bson.objectid import ObjectId

from pymongo.errors import DuplicateKeyError
from pymongo.write_concern import WriteConcern

from pymodm import MongoModel, EmbeddedMongoModel, fields
from pymodm.connection import connect
from pymodm.context_managers import (
    switch_connection, switch_collection, no_auto_dereference,
    collection_options)

from test import ODMTestCase, MONGO_URI, CLIENT, DB


class Game(MongoModel):
    title = fields.CharField()


class Badge(EmbeddedMongoModel):
    name = fields.CharField()
    game = fields.ReferenceField(Game)


class User(MongoModel):
    fname = fields.CharField()
    friend = fields.ReferenceField('test.test_context_managers.User')
    badges = fields.EmbeddedDocumentListField(Badge)


class ContextManagersTestCase(ODMTestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_name = 'alternate-db'
        connect(MONGO_URI + '/' + cls.db_name, 'backups')
        cls.db = CLIENT[cls.db_name]

    @classmethod
    def tearDownClass(cls):
        CLIENT.drop_database(cls.db_name)

    def test_switch_connection(self):
        with switch_connection(User, 'backups') as BackupUser:
            BackupUser('Bert').save()
        User('Ernie').save()

        self.assertEqual('Ernie', DB.user.find_one()['fname'])
        self.assertEqual('Bert', self.db.user.find_one()['fname'])

    def test_switch_collection(self):
        with switch_collection(User, 'copies') as CopiedUser:
            CopiedUser('Bert').save()
        User('Ernie').save()

        self.assertEqual('Ernie', DB.user.find_one()['fname'])
        self.assertEqual('Bert', DB.copies.find_one()['fname'])

    def test_no_auto_dereference(self):
        game = Game('Civilization').save()
        badge = Badge(name='World Domination', game=game)
        ernie = User(fname='Ernie').save()
        bert = User(fname='Bert', badges=[badge], friend=ernie).save()

        bert.refresh_from_db()

        with no_auto_dereference(User):
            self.assertIsInstance(bert.friend, ObjectId)
            self.assertIsInstance(bert.badges[0].game, ObjectId)
        self.assertIsInstance(bert.friend, User)
        self.assertIsInstance(bert.badges[0].game, Game)

    def test_collection_options(self):
        user_id = ObjectId()
        User(_id=user_id).save()
        wc = WriteConcern(w=0)
        with collection_options(User, write_concern=wc):
            User(_id=user_id).save(force_insert=True)
        with self.assertRaises(DuplicateKeyError):
            User(_id=user_id).save(force_insert=True)
