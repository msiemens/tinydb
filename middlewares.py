from threading import RLock

from tinydb.storages import Storage


class Middleware(Storage):
    """
    This is the base class for all Middlewares.

    Middlewares allow you to customize the way TinyDB writes and reads data.
    This may include caching/compression or a totally custom storage format.

    To use Middlewares, your ``__init__`` method has to accept exactly one
    argument which is the class of the "real" storage. It has to be stored as
     self._storage_cls (see implementations below).
    """

    def __call__(self, *args, **kwargs):
        self.storage = self._storage_cls(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.storage, name)


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

    def write(self, data):
        self.cache = data
        self._cache_modified_count += 1

        if self._cache_modified_count >= self.WRITE_CACHE_SIZE:
            self.storage.write(data)
            self._cache_modified_count = 0

    def read(self):
        return self.cache


class ConcurrencyMiddleware(Middleware):
    """
    Makes TinyDB working with multithreading.

    Uses a lock so write/read operations are virtually atomic.
    """

    def __init__(self, storage_cls):
        self.lock = RLock()
        self._storage_cls = storage_cls

    def write(self, data):
        with self.lock:
            self.storage.write(data)

    def read(self):
        with self.lock:
            return self.storage.read()
