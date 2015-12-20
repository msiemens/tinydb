"""
Contains the :class:`base class <tinydb.storages.Storage>` for storages and
implementations.
"""

from abc import ABCMeta, abstractmethod
import os
import pickletools

from tinydb.utils import with_metaclass


try:
    import ujson as json
except ImportError:
    import json

try:
    import cPickle as pickle
except ImportError:
    import pickle


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

    def __init__(self, path, **kwargs):
        """
        Create a new instance.

        Also creates the storage file, if it doesn't exist.

        :param path: Where to store the JSON data.
        :type path: str
        """

        super(JSONStorage, self).__init__()
        touch(path)  # Create file if not exists
        self.kwargs = kwargs
        self._handle = open(path, 'r+')

    def close(self):
        self._handle.close()

    def read(self):
        # Get the file size
        self._handle.seek(0, 2)
        size = self._handle.tell()

        if not size:
            # File is empty
            return None
        else:
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


class PickleStorage(Storage):
    """
    Store the data in a pickle file.
    """

    def __init__(self, path, **kwargs):
        """
        Create a new instance.

        Also creates the storage file, if it doesn't exist.

        :param path: Where to store the pickle data.
        :type path: str
        """

        super(PickleStorage, self).__init__()
        touch(path)  # Create file if not exists
        self.kwargs = kwargs
        self._handle = open(path, 'rb+')

    def close(self):
        self._handle.close()

    def read(self):
        # Get the file size
        self._handle.seek(0, 2)
        size = self._handle.tell()

        if not size:
            # File is empty
            return None
        else:
            self._handle.seek(0)
            return pickle.load(self._handle)

    def write(self, data):
        self._handle.seek(0)
        pickle_data = pickletools.optimize(pickle.dumps(data))
        self._handle.write(pickle_data, **self.kwargs)
        self._handle.flush()
        self._handle.truncate()
