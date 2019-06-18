"""
Contains the :class:`base class <tinydb.storages.Storage>` for storages and
implementations.
"""
from abc import ABCMeta, abstractmethod
import codecs
import os
import warnings

from .utils import with_metaclass


try:
    import ujson as json

    warnings.warn(
        'Support for `ujson` is reprecated and will be replaced in '
        'a future version. '
        'See https://github.com/msiemens/tinydb/issues/263 for '
        'details.',
        DeprecationWarning
    )
except ImportError:
    import json


def touch(fname, create_dirs):
    if create_dirs:
        base_dir = os.path.dirname(fname)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

    if not os.path.exists(fname):
        with open(fname, 'a'):
            os.utime(fname, None)


class Storage(with_metaclass(ABCMeta, object)):
    """
    The abstract base class for all Storages.

    A Storage (de)serializes the current state of the database and stores it in
    some place (memory, file on disk, ...).
    """

    # Using ABCMeta as metaclass allows instantiating only storages that have
    # implemented read and write

    @abstractmethod
    def read(self):
        """
        Read the last stored state.

        Any kind of deserialization should go here.
        Return ``None`` here to indicate that the storage is empty.

        :rtype: dict
        """

        raise NotImplementedError('To be overridden!')

    @abstractmethod
    def write(self, data):
        """
        Write the current state of the database to the storage.

        Any kind of serialization should go here.

        :param data: The current state of the database.
        :type data: dict
        """

        raise NotImplementedError('To be overridden!')

    def close(self):
        """
        Optional: Close open file handles, etc.
        """

        pass


class JSONStorage(Storage):
    """
    Store the data in a JSON file.
    """

    def __init__(self, path, create_dirs=False, encoding=None, **kwargs):
        """
        Create a new instance.

        Also creates the storage file, if it doesn't exist.

        :param path: Where to store the JSON data.
        :type path: str
        """

        super(JSONStorage, self).__init__()
        touch(path, create_dirs=create_dirs)  # Create file if not exists
        self.kwargs = kwargs
        self._handle = codecs.open(path, 'r+', encoding=encoding)

    def close(self):
        self._handle.close()

    def read(self):
        # Get the file size
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()

        if not size:
            # File is empty
            return None
        else:
            self._handle.seek(0)
            return json.load(self._handle)

    def write(self, data):
        self._handle.seek(0)
        serialized = json.dumps(data, **self.kwargs)
        self._handle.write(serialized)
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.truncate()


class MemoryStorage(Storage):
    """
    Store the data as JSON in memory.
    """

    def __init__(self):
        """
        Create a new instance.
        """

        super(MemoryStorage, self).__init__()
        self.memory = None

    def read(self):
        return self.memory

    def write(self, data):
        self.memory = data
