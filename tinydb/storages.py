"""
Contains the :class:`base class <tinydb.storages.Storage>` for storages and
implementations.
"""

from abc import ABCMeta, abstractmethod
import os

from tinydb.utils import with_metaclass


try:
    import ujson as json
except ImportError:
    import json


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


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
        Raise ``ValueError`` here to indicate that the storage is empty.

        :rtype: dict
        """

        raise NotImplementedError('To be overriden!')

    @abstractmethod
    def write(self, data):
        """
        Write the current state of the database to the storage.

        Any kind of serialization should go here.

        :param data: The current state of the database.
        :type data: dict
        """

        raise NotImplementedError('To be overriden!')

    def close(self):
        """
        Optional: Close open file handles, etc.
        """

        pass


class JSONStorage(Storage):
    """
    Store the data in a JSON file.
    """

    def __init__(self, path, **kwargs):
        """
        Create a new instance.

        Also creates the storage file, if it doesn't exist.

        :param path: Where to store the JSON data.
        :type path: str
        """

        super(JSONStorage, self).__init__()
        touch(path)  # Create file if not exists
        self.path = path
        self.kwargs = kwargs
        self._handle = open(path, 'r+')

    def close(self):
        self._handle.close()

    def __del__(self):
        self.close()

    def read(self):
        self._handle.seek(0)
        return json.load(self._handle)

    def write(self, data):
        self._handle.seek(0)
        json.dump(data, self._handle, **self.kwargs)
        self._handle.flush()
        self._handle.truncate()


class MemoryStorage(Storage):
    """
    Store the data as JSON in memory.
    """

    memory = None

    def __init__(self):
        """
        Create a new instance.
        """

        super(MemoryStorage, self).__init__()

    def read(self):
        if self.memory is None:
            raise ValueError
        return self.memory

    def write(self, data):
        self.memory = data
