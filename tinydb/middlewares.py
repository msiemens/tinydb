"""
Contains the :class:`base class <tinydb.middlewares.Middleware>` for
middlewares and implementations.
"""
from tinydb import TinyDB
from tinydb.storages import JSONStorage


class Middleware(object):
    """
    The base class for all Middlewares.

    Middlewares hook into the read/write process of TinyDB allowing you to
    extend the behaviour by adding caching, logging, ...

    Your middleware's ``__init__`` method has to accept exactly one
    argument which is the class of the "real" storage. It has to be stored as
    ``_storage_cls`` (see :class:`~tinydb.middlewares.CachingMiddleware` for an
    example).
    """

    def __init__(self, storage_cls=TinyDB.DEFAULT_STORAGE):
        self._storage_cls = storage_cls
        self.storage = None

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
    the last DB state every :attr:`WRITE_CACHE_SIZE` time and reading always
    from cache.
    """

    #: The number of write operations to cache before writing to disc
    WRITE_CACHE_SIZE = 1000

    def __init__(self, storage_cls=TinyDB.DEFAULT_STORAGE):
        super(CachingMiddleware, self).__init__(storage_cls)

        self.cache = None
        self._cache_modified_count = 0

    def __del__(self):
        self.flush()  # Flush potentially unwritten data

    def read(self):
        if self.cache is None:
            self.cache = self.storage.read()
        return self.cache

    def write(self, data):
        self.cache = data
        self._cache_modified_count += 1

        if self._cache_modified_count >= self.WRITE_CACHE_SIZE:
            self.flush()

    def flush(self):
        """
        Flush all unwritten data to disk.
        """
        if self._cache_modified_count > 0:
            self.storage.write(self.cache)
            self._cache_modified_count = 0

    def close(self):
        self.flush()
        self.storage.close()


class SerializationMiddleware(Middleware):
    """
    Provide custom serialization for TinyDB.

    This middleware allows users of TinyDB to register custom serializations.
    The serialized data will be passed to the wrapped storage and data that
    is read from the storage will be deserialized.
    """

    def __init__(self, storage_cls=TinyDB.DEFAULT_STORAGE):
        super(SerializationMiddleware, self).__init__(storage_cls)

        self._serializers = {}

    def register_serializer(self, serializer, name):
        """
        Register a new Serializer.

        When reading from/writing to the underlying storage, TinyDB
        will run all objects through the list of registered serializers
        allowing each one to handle objects it recognizes.

        .. note:: The name has to be unique among this database instance.
                  Re-using the same name will overwrite the old serializer.
                  Also, registering a serializer will be reflected in all
                  tables when reading/writing them.

        :param serializer: an instance of the serializer
        :type serializer: tinydb.serialize.Serializer
        """
        self._serializers[name] = serializer

    def read(self):
        data = self.storage.read()

        for serializer_name in self._serializers:
            serializer = self._serializers[serializer_name]
            tag = '{{{0}}}:'.format(serializer_name)  # E.g: '{TinyDate}:'

            for table_name in data:
                table = data[table_name]

                for eid in table:
                    item = data[table_name][eid]

                    for field in item:
                        try:
                            if item[field].startswith(tag):
                                encoded = item[field][len(tag):]
                                item[field] = serializer.decode(encoded)
                        except AttributeError:
                            pass  # Not a string

        return data

    def write(self, data):
        for serializer_name in self._serializers:
            # If no serializers are registered, this code will just look up
            # the serializer list and continue. But if there are serializers,
            # the inner loop will run very often.
            # For that reason, the lookup of the serialized class is pulled
            # out into the outer loop:

            serializer = self._serializers[serializer_name]
            serializer_class = serializer.OBJ_CLASS

            for table_name in data:
                table = data[table_name]

                for eid in table:
                    item = data[table_name][eid]

                    for field in item:
                        if isinstance(item[field], serializer_class):
                            encoded = serializer.encode(item[field])
                            tagged = '{{{0}}}:{1}'.format(serializer_name,
                                                          encoded)

                            item[field] = tagged

        self.storage.write(data)
