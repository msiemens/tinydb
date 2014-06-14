How to Extend TinyDB
====================


Storages
--------

To write a custom storage, subclass :class:`~tinydb.storages.Storage`:

.. autoclass:: tinydb.storages.Storage
    :members:

To use your custom storage, use:

.. code-block:: python

    db = TinyDB(storage=YourStorageClass)

.. hint::

    TinyDB will pass all arguments and keyword arguments (except for
    ``storage``) to your storage's ``__init__``.

For example implementations, check out the source of
:class:`~tinydb.storages.JSONStorage` or
:class:`~tinydb.storages.MemoryStorage`.

Middlewares
-----------

To write a custom storage, subclass :class:`~tinydb.middlewares.Middleware`:

.. autoclass:: tinydb.middlewares.Middleware

    .. attribute:: storage

        This will contain the underlying :class:`~tinydb.storages.Storage`

    .. function:: read(self)

        Modify the way TinyDB reads data.

        To access the underlying storage's
        read method, use
        :func:`self.storage.read <tinydb.storages.Storage.read>`.

    .. function:: write(self, data)

        Modify the way TinyDB writes data.

        To access the underlying storage's
        read method, use
        :func:`self.storage.read <tinydb.storages.Storage.write>`.

To use your middleware, use:

.. code-block:: python

    db = TinyDB(storage=YourMiddleware(SomeStorageClass))

For example implementations, check out the source of
:class:`~tinydb.middlewares.CachingMiddleware` or
:class:`~tinydb.middlewares.ConcurrencyMiddleware`.
