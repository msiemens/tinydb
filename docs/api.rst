API Documentation
=================

``tinydb.database``
-------------------

.. autoclass:: tinydb.database.TinyDB
    :members:
    :special-members:
    :exclude-members: __dict__, __weakref__
    :member-order: bysource

.. _table_api:

.. autoclass:: tinydb.database.Table
    :members:
    :special-members:
    :exclude-members: __dict__, __weakref__
    :member-order: bysource

.. autoclass:: tinydb.database.Document
    :members:
    :special-members:
    :exclude-members: __dict__, __weakref__
    :member-order: bysource

    .. py:attribute:: doc_id

        The document's id

.. autoclass:: tinydb.database.Element

``tinydb.queries``
------------------

.. autoclass:: tinydb.queries.Query
    :members:
    :special-members:
    :exclude-members: __weakref__
    :member-order: bysource

``tinydb.storage``
------------------

.. automodule:: tinydb.storages
    :members: JSONStorage, MemoryStorage
    :special-members:
    :exclude-members: __weakref__

    .. class:: Storage

        The abstract base class for all Storages.

        A Storage (de)serializes the current state of the database and stores
        it in some place (memory, file on disk, ...).

        .. method:: read()

            Read the last stored state.

        .. method:: write(data)

            Write the current state of the database to the storage.

        .. method:: close()

            Optional: Close open file handles, etc.

``tinydb.middlewares``
----------------------

.. automodule:: tinydb.middlewares
    :members: CachingMiddleware
    :special-members:
    :exclude-members: __weakref__

    .. class:: Middleware

        The base class for all Middlewares.

        Middlewares hook into the read/write process of TinyDB allowing you to
        extend the behaviour by adding caching, logging, ...

        If ``read()`` or ``write()`` are not overloaded, they will be forwarded
        directly to the storage instance.

        .. attribute:: storage

            :type: :class:`.Storage`

            Access to the underlying storage instance.

        .. method:: read()

            Read the last stored state.

        .. method:: write(data)

            Write the current state of the database to the storage.

        .. method:: close()

            Optional: Close open file handles, etc.
