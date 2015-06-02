How to Extend TinyDB
====================

Write a Serializer
------------------

TinyDB's default JSON storage is fairly limited when it comes to supported data
types. If you need more flexibility, you can implement a Serializer. This allows
TinyDB to handle classes it couldn't serialize otherwise. Let's see how a
Serializer for ``datetime`` objects could look like:

.. code-block:: python

    from datetime import datetime

    class DateTimeSerializer(Serializer):
        OBJ_CLASS = datetime  # The class this serializer handles

        def encode(self, obj):
            return obj.strftime('%Y-%m-%dT%H:%M:%S')

        def decode(self, s):
            return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')

To use the new serializer, we need to use the serialization middleware:

.. code-block:: python

    >>> from tinydb.storages import JSONStorage
    >>> from tinydb.middlewares import SerializationMiddleware
    >>>
    >>> serialization = SerializationMiddleware()
    >>> serialization.register_serializer(DateTimeSerializer(), 'TinyDate')
    >>>
    >>> db = TinyDB('db.json', storage=serialization)
    >>> db.insert({'date': datetime(2000, 1, 1, 12, 0, 0)})
    >>> db.all()
    [{'date': datetime.datetime(2000, 1, 1, 12, 0)}]

Write a custom Storage
----------------------

By default TinyDB comes with a in-memory storage and a JSON file storage. But
of course you can add your own. Let's look how you could add a
`YAML <http://yaml.org/>`_ storage using `PyYAML <http://pyyaml.org/wiki/PyYAML>`_:

.. code-block:: python

    import yaml

    class YAMLStorage(Storage):
        def __init__(self, filename):  # (1)
            self.filename = filename

        def read(self):
            with open(self.filename) as handle:
                data = yaml.safe_load(handle.read())  # (2)

            if data is None:  # (3)
                raise ValueError

        def write(self, data):
            with open(self.filename, 'w') as handle:
                yaml.dump(data, handle)

        def close(self):  # (4)
            pass

There are some things we should look closer at:

1. The constructor will receive all arguments passed to TinyDB when creating
   the database instance (except ``storage`` which TinyDB itself consumes).
   In other words calling ``TinyDB('something', storage=YAMLStorage)`` will
   pass ``'something'`` as an argument to ``YAMLStorage``.
2. We use ``yaml.safe_load`` as recommended by the
   `PyYAML documentation <http://pyyaml.org/wiki/PyYAMLDocumentation#LoadingYAML>`_
   when processing data from a potentially untrusted source.
3. If the storage is uninitialized, TinyDB expects the storage to throw a
   ``ValueError`` so it can do any internal initialization that is necessary.
4. If your storage needs any cleanup (like closing file handles) before an
   instance is destroyed, you can put it in the ``close()`` method. To run
   these, you'll either have to run ``db.close()`` on your ``TinyDB`` instance
   or use it as a context manager, like this:

   .. code-block:: python

        with TinyDB('db.yml', storage=YAMLStorage) as db:
            # ...

Finally, using the YAML storage is very straight-forward:

.. code-block:: python

    db = TinyDB('db.yml', storage=YAMLStorage)
    # ...


Write a custom Middleware
-------------------------

Sometimes you don't want to write a new storage but rather modify the behaviour
of an existing one. As an example we'll build a middleware that filters out
any empty items.

Because middlewares act as a wrapper around a storage, they needs a ``read()``
and a ``write(data)`` method. In addition, they can access the underlying storage
via ``self.storage``. Before we start implementing we should look at the structure
of the data that the middleware receives. Here's what the data that goes through
the middleware looks like:

.. code-block:: python

    {
        '_default': {
            1: {'key': 'value'},
            2: {'key': 'value'},
            # other items
        },
        # other tables
    }

Thus, we'll need two nested loops:

1. Process every table
2. Process every item

Now let's implement that:

.. code-block:: python

    class RemoveEmptyItemsMiddleware(Middleware):
        def __init__(self, storage_cls=TinyDB.DEFAULT_STORAGE):
            # Any middleware *has* to call the super constructor
            # with storage_cls
            super(CustomMiddleware, self).__init__(storage_cls)

        def read(self):
            data = self.storage.read()

            for table_name in data:
                table = data[table_name]

                for element_id in table:
                    item = table[element_id]

                    if item == {}:
                        del table[element_id]

            return data

        def write(self, data):
            for table_name in data:
                table = data[table_name]

                for element_id in table:
                    item = table[element_id]

                    if item == {}:
                        del table[element_id]

            self.storage.write(data)

        def close(self):
            self.storage.close()


Two remarks:

1. You have to use the ``super(...)`` call as shown in the example. To run your
   own initialization, add it below the ``super(...)`` call.
2. This is an example for a middleware, not an example for clean code. Don't
   use it as shown here without at least refactoring the loops into a separate
   method.

To wrap a storage with this new middleware, we use it like this:

.. code-block:: python

    db = TinyDB(storage=RemoveEmptyItemsMiddleware(SomeStorageClass))

Here ``SomeStorageClass`` should be replaced with the storage you want to use.
If you leave it empty, the default storage will be used (which is the ``JSONStorage``).
