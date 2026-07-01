.. _api_docs:

API Documentation
=================

Architecture Overview
---------------------

TinyDB is organized in three layers: the **core API** you interact with in
application code, a **persistence layer** that serializes database state, and
**supporting components** used internally for caching, updates, and query
hashing.

At the center is :class:`~tinydb.database.TinyDB`, which owns a
:class:`~tinydb.storages.Storage` instance and manages one or more
:class:`~tinydb.table.Table` objects. Each table stores documents as
:class:`~tinydb.table.Document` instances (dict-like objects that also expose
``doc_id``) and executes queries built from :class:`~tinydb.queries.Query` and
:class:`~tinydb.queries.QueryInstance`.

Persistence is handled by subclasses of :class:`~tinydb.storages.Storage` such
as :class:`~tinydb.storages.JSONStorage` and
:class:`~tinydb.storages.MemoryStorage`. You can wrap a storage with
:class:`~tinydb.middlewares.Middleware` implementations like
:class:`~tinydb.middlewares.CachingMiddleware` to change how reads and writes
are processed.

The diagram below summarizes how these pieces relate:

.. image:: /_static/architecture.svg
   :alt: TinyDB class diagram showing relationships between TinyDB, Table, Document, Query, Storage, and supporting components
   :align: center

**Typical data flow**

1. You call methods on :class:`~tinydb.database.TinyDB` (for example
   ``insert`` or ``search``). Unless you opened a named table explicitly,
   these calls are forwarded to the default table.
2. The :class:`~tinydb.table.Table` evaluates a :class:`~tinydb.queries.QueryInstance`
   against its documents. Results may be served from the table's
   :class:`~tinydb.utils.LRUCache` query cache.
3. When the table changes, it reads and writes the full database state through
   its :class:`~tinydb.storages.Storage` instance.
4. For partial document updates, :mod:`tinydb.operations` provides helper
   callables that can be passed to :meth:`~tinydb.table.Table.update`.

If you plan to extend TinyDB, start with :doc:`extend` for custom storages and
middlewares, then use the class reference sections below for method-level
details.

``tinydb.database``
-------------------

.. autoclass:: tinydb.database.TinyDB
    :members:
    :private-members:
    :member-order: bysource

.. _table_api:

``tinydb.table``
----------------

.. autoclass:: tinydb.table.Table
    :members:
    :special-members:
    :exclude-members: __dict__, __weakref__
    :member-order: bysource

.. autoclass:: tinydb.table.Document
    :members:
    :special-members:
    :exclude-members: __dict__, __weakref__
    :member-order: bysource

    .. py:attribute:: doc_id

        The document's id

``tinydb.queries``
------------------

.. autoclass:: tinydb.queries.Query
    :members:
    :special-members:
    :exclude-members: __weakref__
    :member-order: bysource

.. autoclass:: tinydb.queries.QueryInstance
    :members:
    :special-members:
    :exclude-members: __weakref__
    :member-order: bysource

``tinydb.operations``
---------------------

.. automodule:: tinydb.operations
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

``tinydb.utils``
----------------

.. autoclass:: tinydb.utils.LRUCache
    :members:
    :special-members:
