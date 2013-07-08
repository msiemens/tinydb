from abc import ABCMeta, abstractmethod

from tinydb.storages import Storage


class Middleware(Storage):
    """
    This is the base class for all Middlewares.

    Middlewares allow you to customize the way TinyDB writes and reads data.
    This may include caching/compression or a totally custom storage format.

    To use Middlewares, your ``__init__`` method has to accept exactly one
    argument which is the class of the "real" storage. In addition,
    you need a ``__call__(*args, **kwargs)`` that passes ``args`` and
    ``kwargs`` to the storage's ``__init__``.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, *args, **kwargs):
        """
        This method has to return a reference to ``self`` and construct the
        storage from the given arguments.
        """
        pass


class CachingMiddleware(Middleware):
    """
    Add some caching to TinyDB.

    This Middleware aims to improve the performance of TinyDB by writing only
    the last DB state every ``WRITE_CACHE_SIZE`` time and reading always from
    cache.
    """

    WRITE_CACHE_SIZE = 1000

    def __init__(self, storage_cls):
        self.cache = None
        self._cache_modified_count = 0
        self._storage_cls = storage_cls

    def __del__(self):
        """
        There may still be some data in the cache. Clear it.
        """
        if self._cache_modified_count:
            self.storage.write(self.cache)

    def __call__(self, *args, **kwargs):
        self.storage = self._storage_cls(*args, **kwargs)
        return self

    def write(self, data):
        self.cache = data
        self._cache_modified_count += 1

        if self._cache_modified_count >= self.WRITE_CACHE_SIZE:
            self.storage.write(data)
            self._cache_modified_count = 0

    def read(self):
        if self.cache is None:
            self.cache = self.storage.read()

        return self.cache
