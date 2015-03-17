How to Extend TinyDB
====================

Write a Serializer
------------------

TinyDB's default storage is fairly limited when it comes to supported data types.
If you need more flexibility, you can implement a Serializer. This allows TinyDB
to handle classes it otherwise couldn't serialize. Let's see how a Serializer
for ``datetime`` objects could look like:

.. code-block:: python

    from datetime import datetime

    class DateTimeSerializer(Serializer):
        NAME = 'TinyDate'  # A unique name
        OBJ_CLASS = datetime  # The class this serializer handles

        def encode(self, obj):
            return obj.strftime('%Y-%m-%dT%H:%M:%S')

        def decode(self, s):
            return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')

We can use this Serializer like this:

.. code-block:: python

    >>> db = TinyDB('db.json')
    >>> db.register_serializer(DateTimeSerializer())
    >>> db.insert({'date': datetime(2000, 1, 1, 12, 0, 0)})
    >>> db.all()
    [{'date': datetime.datetime(2000, 1, 1, 12, 0)}]

Write a custom Storage
----------------------

You can write a custom storage by subclassing :class:`~tinydb.storages.Storage`:

.. code-block:: python

    class CustomStorage(Storage):
        def __init__(self, arg1):
            pass

        def read(self):
            # your implementation

        def write(self, data):
            # your implementation

        def close(self):
            # optional: close open file handles, etc.

To indicate that your storage is empty, raise an ``ValueError`` in
``read(self)``. TinyDB will create the data for a new database and ask your
storage to write it.

When creating a new instance of :class:`.TinyDB`, the instance will pass
all arguments and keyword arguments (except ``storage``) to your storage class:

.. code-block:: python

    db = TinyDB(arg1, storage=CustomStorage)


Write a custom Middleware
-------------------------

You can modify the behaviour of existing storages by writing a custom
middleware. To do so, subclass :class:`~tinydb.middlewares.Middleware`:

.. code-block:: python

    class CustomMiddleware(Middleware):
        def __init__(self, storage_cls):
            # Any middleware *has* to call the super constructor
            # with storage_cls
            super(CustomMiddleware, self).__init__(storage_cls)

        def read(self):
            # your implementation
            self.storage.read()  # access the storage's read function

        def write(self, data):
            # your implementation
            self.storage.write(data)  # access the storage's write function

        def close(self):
            # optional: close open file handles, etc.
            self.storage.close()  # access the storage's close function

Remember to call the super constructor in your ``__init__`` as shown in the
example.

To wrap a storage with your new middleware, use

.. code-block:: python

    db = TinyDB(storage=CustomMiddleware(SomeStorageClass))
