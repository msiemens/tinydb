API Documentation
=================

``tinydb.database``
-------------------

.. autoclass:: tinydb.database.TinyDB
    :members:
    :special-members:
    :exclude-members: __dict__, __weakref__
    :member-order: bysource

.. autoclass:: tinydb.database.Table
    :members:
    :special-members:
    :exclude-members: __dict__, __weakref__
    :member-order: bysource

.. autoclass:: tinydb.database.SmartCacheTable
    :members:
    :special-members:
    :exclude-members: __dict__, __weakref__
    :member-order: bysource

.. autoclass:: tinydb.database.Element
    :members:
    :special-members:
    :exclude-members: __dict__, __weakref__
    :member-order: bysource

    .. py:attribute:: eid

        The element's id

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

``tinydb.middlewares``
----------------------

.. automodule:: tinydb.middlewares
    :members: CachingMiddleware
    :special-members:
