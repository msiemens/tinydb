How to Extend TinyDB
====================

There are three main ways to extend TinyDB and modify its behaviour:

1. custom storages,
2. custom middlewares,
3. use hooks and overrides, and
4. subclassing ``TinyDB`` and ``Table``.

Let's look at them in this order.

Write a Custom Storage
----------------------

First, we have support for custom storages. By default TinyDB comes with an
in-memory storage and a JSON file storage. But of course you can add your own.
Let's look how you could add a `YAML <http://yaml.org/>`_ storage using
`PyYAML <http://pyyaml.org/wiki/PyYAML>`_:

.. code-block:: python

    import yaml

    class YAMLStorage(Storage):
        def __init__(self, filename):  # (1)
            self.filename = filename

        def read(self):
            with open(self.filename) as handle:
                try:
                    data = yaml.safe_load(handle.read())  # (2)
                    return data
                except yaml.YAMLError:
                    return None  # (3)

        def write(self, data):
            with open(self.filename, 'w+') as handle:
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
3. If the storage is uninitialized, TinyDB expects the storage to return
   ``None`` so it can do any internal initialization that is necessary.
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


Write Custom Middleware
-------------------------

Sometimes you don't want to write a new storage module but rather modify the
behaviour of an existing one. As an example we'll build middleware that filters
out empty items.

Because middleware acts as a wrapper around a storage, they needs a ``read()``
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
        def __init__(self, storage_cls):
            # Any middleware *has* to call the super constructor
            # with storage_cls
            super().__init__(storage_cls)  # (1)

        def read(self):
            data = self.storage.read()

            for table_name in data:
                table_data = data[table_name]

                for doc_id in table_data:
                    item = table_data[doc_id]

                    if item == {}:
                        del table_data[doc_id]

            return data

        def write(self, data):
            for table_name in data:
                table_data = data[table_name]

                for doc_id in table:
                    item = table_data[doc_id]

                    if item == {}:
                        del table_data[doc_id]

            self.storage.write(data)

        def close(self):
            self.storage.close()


Note that the constructor calls the middleware constructor (1) and passes
the storage class to the middleware constructor.

To wrap storage with this new middleware, we use it like this:

.. code-block:: python

    db = TinyDB(storage=RemoveEmptyItemsMiddleware(SomeStorageClass))

Here ``SomeStorageClass`` should be replaced with the storage you want to use.
If you leave it empty, the default storage will be used (which is the ``JSONStorage``).

Use hooks and overrides
-----------------------

.. _extend_hooks:

There are cases when neither creating a custom storage nor using a custom
middlware will allow you to adapt TinyDB in the way you need. In this case
you can modify TinyDB's behavior by using predefined hooks and override points.
For example you can configure the name of the default table by setting
``TinyDB.default_table_name``:

.. code-block:: python

    TinyDB.default_table_name = 'my_table_name'

Both :class:`~tinydb.database.TinyDB` and the :class:`~tinydb.table.Table`
classes allow modifying their behavior using hooks and overrides. To use
``Table``'s overrides, you can access the class using ``TinyDB.table_class``:

.. code-block:: python

    TinyDB.table_class.default_query_cache_capacity = 100

Read the :ref:`api_docs` for more details on the available hooks and override
points.

Subclassing ``TinyDB`` and ``Table``
------------------------------------

Finally, there's the last option to modify TinyDB's behavior. That way you
can change how TinyDB itself works more deeply than using the other extension
mechanisms.

When creating a subclass you can use it by using hooks and overrides to override
the default classes that TinyDB uses:

.. code-block:: python

    class MyTable(Table):
        # Add your method overrides
        ...

    TinyDB.table_class = MyTable

    # Continue using TinyDB as usual

TinyDB's source code is documented with extensions in mind, explaining how
everything works even for internal methods and classes. Feel free to dig into
the source and adapt everything you need for your projects.
