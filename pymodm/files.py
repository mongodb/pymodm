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

"""Tools for working with GridFS."""
from io import UnsupportedOperation

try:
    from PIL import Image
except ImportError:
    Image = None

from pymodm.compat import PY3
from pymodm.errors import ValidationError, ConfigurationError

from gridfs.errors import NoFile
from gridfs.grid_file import GridIn, DEFAULT_CHUNK_SIZE


class Storage(object):
    """Abstract class that defines the API for managing files."""
    def open(self, file_id, mode='rb'):
        """Open a file.

        :parameters:
          - `file_id`: The id of the file.
          - `mode`: The file mode. Defaults to ``rb``. Not all Storage
            implementations may support different modes.

        :returns: The :class:`~pymodm.files.FieldFile` with the given `file_id`.

        """
        raise NotImplementedError

    def save(name, content, metadata=None):
        """Save `content` in a file named `name`.

        :parameters:
          - `name`: The name of the file.
          - `content`: A file-like object, string, or bytes.
          - `metadata`: Metadata dictionary to be saved with the file.

        :returns: The id of the saved file.

        """
        raise NotImplementedError

    def delete(self, file_id):
        """Delete the file with the given `file_id`."""
        raise NotImplementedError

    def exists(self, file_id):
        """Returns ``True`` if the file with the given `file_id` exists."""
        raise NotImplementedError


class GridFSStorage(Storage):
    """:class:`~pymodm.files.Storage` class that uses GridFS to store files.

    This is the default Storage implementation for
    :class:`~pymodm.files.FileField`.

    """

    def __init__(self, gridfs_bucket):
        self.gridfs = gridfs_bucket

    def open(self, file_id, mode='rb'):
        """Open a file.

        :parameters:
          - `file_id`: The id of the file.
          - `mode`: The file mode. Defaults to ``rb``. Not all Storage
            implementations may support different modes.

        :returns: The :class:`~pymodm.files.GridFSFile` with the given
                  `file_id`.

        .. note:: Files from GridFS can only be opened in ``rb`` mode.

        """
        if mode != 'rb':
            raise ValueError('GridFS files must be opened in "rb" mode.')
        return GridFSFile(file_id, self.gridfs)

    def save(self, name, content, metadata=None):
        """Save `content` in a file named `name`.

        :parameters:
          - `name`: The name of the file.
          - `content`: A file-like object, string, or bytes.
          - `metadata`: Metadata dictionary to be saved with the file.

        :returns: The id of the saved file.

        """
        gridin_opts = {'filename': name, 'encoding': 'utf8'}
        if metadata is not None:
            gridin_opts['metadata'] = metadata
        gridin = GridIn(self.gridfs._collection, **gridin_opts)

        try:
            content.seek(0)
        except (AttributeError, UnsupportedOperation):
            pass

        if PY3 and hasattr(content, 'mode') and 'b' not in content.mode:
            # File opened in text mode.
            gridin.writelines(content)
        else:
            # File in binary mode, bytes, or text.
            gridin.write(content)

        # Finish writing the file.
        gridin.close()
        return gridin._id

    def delete(self, file_id):
        """Delete the file with the given `file_id`."""
        try:
            self.gridfs.delete(file_id)
        except NoFile:
            pass

    def exists(self, file_id):
        """Returns ``True`` if the file with the given `file_id` exists."""
        try:
            self.gridfs.open_download_stream(file_id)
        except NoFile:
            return False
        return True


class _FileProxyMixin(object):
    """Proxy methods from an underlying file."""
    def __getattr__(self, attr):
        try:
            return getattr(self.file, attr)
        except AttributeError:
            raise AttributeError(
                '%s object has no attribute "%s".' % (
                    self.__class__.__name__, attr))

    def __iter__(self):
        return iter(self.file)


class File(_FileProxyMixin):
    """Wrapper around a Python `file`.

    This class may be assigned directly to a :class:`~pymodm.fields.FileField`.

    You can use this class with Python's builtin `file` implementation::

        >>> my_file = File(open('some/path.txt'))
        >>> my_object.filefield = my_file
        >>> my_object.save()

    """
    def __init__(self, file, name=None, metadata=None):
        self.file = file
        self.file_id = name or file.name
        self.metadata = metadata

    def open(self, mode='rb'):
        """Open this file or seek to the beginning if already open."""
        if self.closed:
            self.file = open(self.file.name, mode)
        else:
            self.file.seek(0)

    def close(self):
        """Close the this file."""
        self.file.close()

    def chunks(self, chunk_size=DEFAULT_CHUNK_SIZE):
        """Read the file and yield chunks of ``chunk_size`` bytes.

        The default chunk size is the same as the default for GridFS.

        This method is useful for streaming large files without loading the
        entire file into memory.

        """
        try:
            self.seek(0)
        except (AttributeError, UnsupportedOperation):
            pass

        while True:
            data = self.read(chunk_size)
            if not data:
                break
            yield data


class FieldFile(_FileProxyMixin):
    """Type returned when accessing a :class:`~pymodm.fields.FileField`.

    This type is just a thin wrapper around a :class:`~pymodm.files.File` and
    can be treated as a file-like object in most places where a `file` is
    expected.

    """

    def __init__(self, instance, field, file_id):
        self.instance = instance
        self.field = field
        self.file_id = file_id
        self.storage = field.storage
        self._file = None
        self._committed = True

    @property
    def file(self):
        """The underlying :class:`~pymodm.files.File` object.

        This will open the file if necessary.

        """
        if self._file is None:
            self.open()
        return self._file

    @file.setter
    def file(self, file):
        self._file = file

    def save(self, name, content):
        """Save this file.

        :parameters:
          - `name`: The name of the file.
          - `content`: The file's contents. This can be a file-like object,
            string, or bytes.

        """
        self.file_id = self.storage.save(name, content, self.metadata)
        setattr(self.instance, self.field.attname, self.file_id)
        self._committed = True

    def delete(self):
        """Delete this file."""
        self.storage.delete(self.file_id)
        delattr(self.instance, self.field.attname)
        self._committed = False

    def open(self, mode='rb'):
        """Open this file with the specified `mode`."""
        self.close()
        self._file = self.storage.open(self.file_id, mode)
        self._committed = True

    def close(self):
        """Close this file."""
        if self._file is not None:
            self._file.close()

    def __eq__(self, other):
        if isinstance(other, File):
            return self.file_id == other.file_id
        return NotImplemented

    def __ne__(self, other):
        return not self == other


class ImageFieldFile(FieldFile):
    """Type returned when accessing a :class:`~pymodm.fields.ImageField`.

    This type is very similar to :class:`~pymodm.files.FieldFile`, except that
    it provides a few convenience properties for the underlying image.
    """

    @property
    def image(self):
        """The underlying image."""
        if Image is None:
            raise ConfigurationError(
                'PIL or Pillow must be installed to access the "image" '
                'property on an ImageFieldFile.')
        if not hasattr(self, '_image') or self._image is None:
            self._image = Image.open(self.file)
        return self._image

    @property
    def width(self):
        """The width of the image in pixels."""
        return self.image.width

    @property
    def height(self):
        """The height of the image in pixels."""
        return self.image.height

    @property
    def format(self):
        """The format of the image as a string."""
        return self.image.format


class GridFSFile(File):
    """Representation of a file stored on GridFS.

    Note that GridFS files are read-only. To change a file on GridFS, you can
    replace the file with a new version::

        >>> my_object(upload=File(open('somefile.txt'))).save()
        >>> my_object.upload.delete()  # Delete the old version.
        >>> my_object.upload = File(open('new_version.txt'))
        >>> my_object.save()  # Old file is replaced with the new one.
    """

    def __init__(self, file_id, gridfs_bucket, file=None):
        super(GridFSFile, self).__init__(file, file_id, None)
        self.gridfs = gridfs_bucket
        self._file = file

    @property
    def file(self):
        """The underlying :class:`~gridfs.GridOut` object.

        This will open the file if necessary.

        """
        if self._file is None:
            try:
                self.file = self.gridfs.open_download_stream(self.file_id)
            except NoFile:
                raise ValidationError('No file with id: %s' % self.file_id)
        return self._file

    @file.setter
    def file(self, file):
        self._file = file
        if self._file:
            self.metadata = self._file.metadata

    def delete(self):
        """Delete this file from GridFS."""
        self.gridfs.delete(self.file_id)
