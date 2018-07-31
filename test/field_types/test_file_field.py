import os
import os.path
import shutil

from test import DB
from test.field_types import FieldTestCase

from pymodm import MongoModel
from pymodm.errors import ValidationError
from pymodm.fields import FileField
from pymodm.files import File, Storage

from test import connect_to_test_DB


TEST_FILE_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib')
UPLOADS = os.path.join(TEST_FILE_ROOT, 'uploads')


class ModelWithFile(MongoModel):
    upload = FileField()
    secondary_upload = FileField(required=False)


class ModelWithFileNoConnection(MongoModel):
    upload = FileField()
    secondary_upload = FileField(required=False)

    class Meta:
        connection_alias = 'test-field-file-no-connection'


# Test another Storage type.
class LocalFileSystemStorage(Storage):
    """A Storage implementation that saves to a local folder.

    This is for test use only!
    """
    def __init__(self, upload_to):
        self.upload_to = upload_to

    def _path(self, name):
        _, name = os.path.split(name)
        return os.path.join(self.upload_to, name)

    def open(self, name, mode='rb'):
        return File(open(self._path(name), mode))

    def save(self, name, content, metadata=None):
        name = self._path(name)
        # Create directories up to given filename.
        if not os.path.exists(self.upload_to):
            os.makedirs(self.upload_to)
        dest = None
        try:
            for chunk in content.chunks():
                if dest is None:
                    mode = 'wb' if isinstance(chunk, bytes) else 'wt'
                    dest = open(name, mode)
                dest.write(chunk)
            # Create an empty file.
            if dest is None:
                dest = open(name, 'wb')
        finally:
            dest.close()
        return name

    def delete(self, name):
        os.remove(self._path(name))

    def exists(self, name):
        return os.path.exists(self._path(name))


class ModelWithLocalFile(MongoModel):
    upload = FileField(storage=LocalFileSystemStorage(UPLOADS))
    secondary_upload = FileField(storage=LocalFileSystemStorage(UPLOADS),
                                 required=False)


class FileFieldTestMixin(object):

    testfile = os.path.join(TEST_FILE_ROOT, 'testfile.txt')
    tempfile = os.path.join(TEST_FILE_ROOT, 'tempfile.txt')

    def test_set_file(self):
        # Create directly with builtin 'open'.
        with open(self.testfile) as this_file:
            mwf = self.model(this_file).save()
        mwf.refresh_from_db()
        self.assertEqual('testfile.txt', os.path.basename(mwf.upload.name))
        self.assertIn(b'Hello from testfile!', mwf.upload.read())

    def test_set_file_object(self):
        # Create with File object.
        with open(self.testfile) as this_file:
            # Set a name explicitly ("uploaded").
            wrapped_with_name = File(
                this_file, 'uploaded', metadata=self.file_metadata)
            # Name set from underlying file.
            wrapped = File(this_file, metadata=self.file_metadata)
            mwf = self.model(wrapped_with_name, wrapped).save()
        mwf.refresh_from_db()
        self.assertEqual('uploaded', os.path.basename(mwf.upload.name))
        self.assertEqual('testfile.txt',
                         os.path.basename(mwf.secondary_upload.name))
        self.assertIn(b'Hello from testfile!', mwf.upload.read())
        if self.file_metadata is not None:
            self.assertEqual(self.file_metadata['contentType'],
                             mwf.upload.metadata['contentType'])

    def test_delete_file(self):
        # Create a file to delete.
        open(self.tempfile, 'w').close()
        with open(self.tempfile) as tempfile:
            mwf = self.model(tempfile).save()
        mwf.upload.delete()
        self.assertIsNone(mwf.upload)
        self.assertIsNone(DB.fs.files.find_one())

    def test_seek(self):
        with open(self.testfile) as this_file:
            mwf = self.model(this_file).save()
        self.assertEqual(0, mwf.upload.tell())
        with open(self.testfile, 'rb') as compare:
            self.assertEqual(compare.read(), mwf.upload.read())
            compare.seek(7)
            mwf.upload.seek(7)
            self.assertEqual(compare.read(10), mwf.upload.read(10))
            self.assertEqual(compare.tell(), mwf.upload.tell())
            self.assertEqual(compare.read(), mwf.upload.read())
            self.assertEqual(compare.tell(), mwf.upload.tell())

    def test_multiple_references_to_same_file(self):
        with open(self.testfile) as testfile:
            mwf = self.model(testfile).save()
        # Try to copy the file from its current location to a new field.
        mwf.secondary_upload = mwf.upload
        mwf.save()
        self.assertEqual(mwf.upload, mwf.secondary_upload)
        self.assertIs(mwf.upload, mwf.secondary_upload)

    def test_exists(self):
        storage = self.model.upload.storage
        self.assertFalse(storage.exists(self.testfile))
        with open(self.testfile) as this_file:
            instance = self.model(this_file).save()
        self.assertTrue(storage.exists(instance.upload.file_id))

    def test_file_modes(self):
        text_file = open(self.testfile, 'rt')
        binary_file = open(self.testfile, 'rb')
        instance = self.model(text_file, binary_file).save()
        text_file.close()
        binary_file.close()
        upload_content = instance.upload.read()
        self.assertIsInstance(upload_content, bytes)
        self.assertEqual(
            instance.secondary_upload.read(),
            upload_content)


class FileFieldGridFSTestCase(FieldTestCase, FileFieldTestMixin):
    model = ModelWithFile
    file_metadata = {'contentType': 'text/python'}


class FileFieldAlternateStorageTestCase(FieldTestCase, FileFieldTestMixin):
    model = ModelWithLocalFile
    file_metadata = None

    def tearDown(self):
        # Remove uploads directory.
        try:
            shutil.rmtree(UPLOADS)
        except OSError:
            pass


class FileFieldGridFSNoConnectionTestCase(FieldTestCase):
    testfile = os.path.join(TEST_FILE_ROOT, 'testfile.txt')
    file_metadata = {'contentType': 'text/python'}
    model = ModelWithFileNoConnection

    def test_lazy_storage_initialization(self):
        connection_alias = self.model.Meta.connection_alias
        with open(self.testfile) as this_file:
            model = self.model(
                File(this_file, 'new', metadata=self.file_metadata),
                File(this_file, 'old', metadata=self.file_metadata)
            )

            # With no connection, an exception should be thrown.
            with self.assertRaisesRegex(
                    ValidationError, "No such alias {!r}".format(
                        connection_alias)):
                model.save()

            # Should succeed once connection is created.
            connect_to_test_DB(connection_alias)
            model.save()
