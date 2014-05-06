"""
Contains the :class:`base class <tinydb.middlewares.Middleware>` for
middlewares and two implementations.
"""

from threading import RLock

from tinydb.storages import Storage


class Middleware(Storage):
    """
    The base class for all Middlewares.

    Middlewares hook into the read/write process of TinyDB allowing you to
    extend the behaviour by adding caching, logging, ...

    Your middleware's ``__init__`` method has to accept exactly one
    argument which is the class of the "real" storage. It has to be stored as
    ``_storage_cls`` (see :class:`~tinydb.middlewares.CachingMiddleware` for an
    example).
    """

    def __call__(self, *args, **kwargs):
        """
        Create the storage instance and store it as self.storage.

        Usually a user creates a new TinyDB instance like this::

            TinyDB(storage=StorageClass)

        The storage kwarg is used by TinyDB this way::

            self._storage = storage(*args, **kwargs)

        As we can see, ``storage(...)`` runs the constructor and returns the
        new storage instance.


        Using Middlewares, the user will call::

                                       The 'real' storage class
                                       v
            TinyDB(storage=Middleware(StorageClass))
                           ^
                           Already an instance!

        So, when running ``self._storage = storage(*args, **kwargs)`` Python
        now will call ``__call__`` and TinyDB will expect the return value to
        be the storage (or Middleware) instance. Returning the instance is
        simple, but we also got the underlying (*real*) StorageClass as an
        __init__ argument that still is not an instance.
        So, we initialize it in __call__ forwarding any arguments we recieve
        from TinyDB (``TinyDB(arg1, kwarg1=value, storage=...)``).

        In case of nested Middlewares, calling the instance as if it was an
        class results in calling ``__call__`` what initializes the next
        nested Middleware that itself will initialize the next Middleware and
        so on.
        """
        self.storage = self._storage_cls(*args, **kwargs)

        return self

    def __getattr__(self, name):
        """
        Forward all unknown attribute calls to the underlying storage so we
        remain as transparent as possible.
        """
        return getattr(self.__dict__['storage'], name)


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
        self.flush()  # Flush potentially unwritten data

    def write(self, data):
        self.cache = data
        self._cache_modified_count += 1

        if self._cache_modified_count >= self.WRITE_CACHE_SIZE:
            self.flush()

    def read(self):
        if self.cache is None:
            raise ValueError
        return self.cache

    def flush(self):
        """
        Flush all unwritten data to disk.
        """
        self.storage.write(self.cache)
        self._cache_modified_count = 0


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
