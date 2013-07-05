from abc import ABCMeta, abstractmethod

import os

try:
    import ujson as json
except ImportError:
    import json


def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)


class Storage(object):
    """
    A generic storage for TinyDB.

    TODO: Better docs!
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def write(self, data):
        raise NotImplementedError('To be overriden!')

    @abstractmethod
    def read(self):
        raise NotImplementedError('To be overriden!')


class JSONStorage(Storage):
    """
    Store the data in a JSON file.
    """

    def __init__(self, path):
        super(JSONStorage, self).__init__()
        touch(path)  # Create file if not exists
        self.path = path
        self._handle = open(path, 'r+')

    def __del__(self):
        self._handle.close()

    def write(self, data):
        self._handle.seek(0)
        json.dump(data, self._handle)
        self._handle.flush()

    def read(self):
        self._handle.seek(0)
        return json.load(self._handle)


class MemoryStorage(Storage):
    """
    Store the data as JSON in memory.
    """

    def __init__(self, path=None):
        super(MemoryStorage, self).__init__()
        self.memory = None

    def write(self, data):
        self.memory = data

    def read(self):
        if self.memory is None:
            raise ValueError
        return self.memory
