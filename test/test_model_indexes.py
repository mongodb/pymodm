from pymodm import fields, MongoModel, connect
from pymodm.context_managers import switch_collection, switch_connection
from pymongo import IndexModel, ASCENDING

from test import ODMTestCase, DB, MONGO_URI, CLIENT


class ModelIndexesTestCase(ODMTestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_name = 'alternate-db'
        connect(MONGO_URI + '/' + cls.db_name, 'backups')
        cls.db = CLIENT[cls.db_name]

    @classmethod
    def tearDownClass(cls):
        CLIENT.drop_database(cls.db_name)

    def test_indexes_with_auto_create_indexes_option_on(self):
        class ModelWithAutoIndexes(MongoModel):
            product_id = fields.UUIDField()
            name = fields.CharField()

            class Meta:
                auto_create_indexes = True
                indexes = [
                    IndexModel([('product_id', 1), ('name', 1)],
                               unique=True, name='product_name')
                ]

        index_info = DB.model_with_auto_indexes.index_information()
        self.assertTrue(index_info['product_name']['unique'])

    def test_indexes_with_auto_create_indexes_option_off(self):
        class ModelWithIndexes(MongoModel):
            product_id = fields.UUIDField()
            name = fields.CharField()

            class Meta:
                auto_create_indexes = False
                indexes = [
                    IndexModel([('product_id', 1), ('name', 1)],
                               unique=True, name='product_name')
                ]

        # ensure collection is created
        ModelWithIndexes().save()

        index_info = DB.model_with_indexes.index_information()
        self.assertNotIn('product_name', index_info)

        # create indexes explicitly
        ModelWithIndexes.objects.create_indexes()
        index_info = DB.model_with_indexes.index_information()
        self.assertTrue(index_info['product_name']['unique'])

    def test_indexes_with_default_auto_create_indexes_option(self):
        class ModelWithAutoIndexes(MongoModel):
            product_id = fields.UUIDField()
            name = fields.CharField()

            class Meta:
                indexes = [
                    IndexModel([('product_id', 1), ('name', 1)],
                               unique=True, name='product_name')
                ]

        # by default auto_create_indexes option should be True
        index_info = DB.model_with_auto_indexes.index_information()
        self.assertTrue(index_info['product_name']['unique'])

    def test_create_indexes_with_no_indexes_defined(self):
        class ModelWithoutIndexes(MongoModel):
            name = fields.CharField()

        # should not raise any error
        ModelWithoutIndexes.objects.create_indexes()

    def test_create_indexes_with_switch_collection_context_manager(self):
        class User(MongoModel):
            fname = fields.CharField()

            class Meta:
                auto_create_indexes = False
                indexes = [
                    IndexModel([('fname', ASCENDING)], name="fname_index")
                ]

        # ensure collection exists
        User(fname='Bob').save()

        with switch_collection(User, 'copied_user') as CopiedUser:
            CopiedUser.objects.create_indexes()

        index_info = DB.copied_user.index_information()
        self.assertIn('fname_index', index_info)

        index_info = DB.user.index_information()
        self.assertNotIn('fname_index', index_info)

    def test_create_indexes_with_switch_connection_context_manager(self):
        class User(MongoModel):
            fname = fields.CharField()

            class Meta:
                auto_create_indexes = False
                indexes = [
                    IndexModel([('fname', ASCENDING)], name="fname_index")
                ]

        # ensure collection exists
        User(fname='Bob').save()

        with switch_connection(User, 'backups') as BackupUser:
            BackupUser.objects.create_indexes()

        index_info = self.db.user.index_information()
        self.assertIn('fname_index', index_info)

        index_info = DB.user.index_information()
        self.assertNotIn('fname_index', index_info)
