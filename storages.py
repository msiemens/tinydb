from abc import ABCMeta, abstractmethod

import os

import yaml


def touch(fname, times=None):
    with file(fname, 'a'):
        os.utime(fname, times)


class Storage(object):
    """
    A generic storage for TinyDB.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def write(self, data):
        raise NotImplementedError('To be overriden!')

    @abstractmethod
    def read(self):
        raise NotImplementedError('To be overriden!')


class YAMLStorage(Storage):
    """
    Store the data in a YAML file.
    """
    # TODO: Add caching

    def __init__(self, path):
        super(YAMLStorage, self).__init__()
        touch(path)  # Create file if not exists
        self._handle = open(path, 'r+')

    def write(self, data):
        self._handle.seek(0)
        yaml.dump(data, self._handle)
        self._handle.flush()

    def read(self):
        self._handle.seek(0)
        return yaml.load(self._handle)


class MemoryStorage(Storage):
    """
    Store the data as YAML in memory.
    """

    def __init__(self, path=None):
        super(MemoryStorage, self).__init__()
        self.memory = ''

    def write(self, data):
        self.memory = yaml.dump(data)

    def read(self):
        return yaml.load(self.memory)
