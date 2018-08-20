How to Extend TinyDB
====================

There are three main ways to extend TinyDB and modify its behaviour:

1. custom storage,
2. custom middleware, and
3. custom table classes.

Let's look at them in this order.

Write Custom Storage
----------------------

First, we have support for custom storage. By default TinyDB comes with an
in-memory storage mechanism and a JSON file storage mechanism. But of course you can add your own.
Let's look how you could add a `YAML <http://yaml.org/>`_ storage using
`PyYAML <http://pyyaml.org/wiki/PyYAML>`_:

.. code-block:: python

    import yaml

    def represent_doc(dumper, data):
        # Represent `Document` objects as their dict's string representation
        # which PyYAML understands
        return dumper.represent_data(dict(data))

    yaml.add_representer(Document, represent_doc)

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

Sometimes you don't want to write a new storage module but rather modify the behaviour
of an existing one. As an example we'll build middleware that filters out
any empty items.

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
        def __init__(self, storage_cls=TinyDB.DEFAULT_STORAGE):
            # Any middleware *has* to call the super constructor
            # with storage_cls
            super(CustomMiddleware, self).__init__(storage_cls)

        def read(self):
            data = self.storage.read()

            for table_name in data:
                table = data[table_name]

                for doc_id in table:
                    item = table[doc_id]

                    if item == {}:
                        del table[doc_id]

            return data

        def write(self, data):
            for table_name in data:
                table = data[table_name]

                for doc_id in table:
                    item = table[doc_id]

                    if item == {}:
                        del table[doc_id]

            self.storage.write(data)

        def close(self):
            self.storage.close()


Two remarks:

1. You have to use the ``super(...)`` call as shown in the example. To run your
   own initialization, add it below the ``super(...)`` call.
2. This is an example for middleware, not an example for clean code. Don't
   use it as shown here without at least refactoring the loops into a separate
   method.

To wrap storage with this new middleware, we use it like this:

.. code-block:: python

    db = TinyDB(storage=RemoveEmptyItemsMiddleware(SomeStorageClass))

Here ``SomeStorageClass`` should be replaced with the storage you want to use.
If you leave it empty, the default storage will be used (which is the ``JSONStorage``).

Creating a Custom Table Classes
-------------------------------

Custom storage and middleware are useful if you want to modify the way
TinyDB stores its data. But there are cases where you want to modify how
TinyDB itself behaves. For that use case TinyDB supports custom table classes.
Internally TinyDB creates a ``Table`` instance for every table that is used.
You can overwrite which class is used by setting ``TinyDB.table_class``
before creating a ``TinyDB`` instance. This class has to support the
:ref:`Table API <table_api>`. The best way to accomplish that is to subclass
it:

.. code-block:: python

    from tinydb import TinyDB
    from tinydb.database import Table

    class YourTableClass(Table):
        pass  # Modify original methods as needed

    TinyDB.table_class = YourTableClass

For an more advanced example, see the source of the
`tinydb-smartcache <https://github.com/msiemens/tinydb-smartcache>`_ extension.

Creating a Custom Storage Proxy Classes
---------------------------------------

.. warning::
    This extension requires knowledge of TinyDB internals. Use it if
    you understand how TinyDB works in detail.

Another way to modify TinyDB's behavior is to create a custom storage
proxy class. Internally, TinyDB uses a proxy class to allow tables to
access a storage object. The proxy makes sure the table only accesses
its own table data and doesn't accidentally modify other table's data.

In this class you can modify how a table can read and write from a
storage instance. Also, the proxy class has a method called
``_new_document`` which creates a new document object. If you want
to replace it with a different document class, you can do it right
here.

.. code-block:: python

    from tinydb import TinyDB
    from tinydb.database import Table, StorageProxy, Document
    from tinydb.storages import MemoryStorage

    class YourStorageProxy(StorageProxy):
        def _new_document(self, key, val):
            # Modify document object creation
            doc_id = int(key)
            return Document(val, doc_id)

        def read(self):
            return {}  # Modify reading

       def write(self, data):
            pass  # Modify writing

    TinyDB.storage_proxy_class = YourStorageProxy
    # Or:
    TinyDB(storage=..., storage_proxy_class=YourStorageProxy)