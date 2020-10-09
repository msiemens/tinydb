Upgrading to Newer Releases
===========================

Version 4.0
-----------

.. _upgrade_v4_0:

- API changes:
    - Replace ``TinyDB.purge_tables(...)`` with ``TinyDB.drop_tables(...)``
    - Replace ``TinyDB.purge_table(...)`` with ``TinyDB.drop_table(...)``
    - Replace ``Table.purge()`` with ``Table.trunacte()``
    - Replace ``TinyDB(default_table='name')`` with ``TinyDB.default_table_name = 'name'``
    - Replace ``TinyDB(table_class=Class)`` with ``TinyDB.table_class = Class``
    - If you were using ``TinyDB.DEFAULT_TABLE``, ``TinyDB.DEFAULT_TABLE_KWARGS``,
      or ``TinyDB.DEFAULT_STORAGE``: Use the new methods for customizing TinyDB
      described in :ref:`How to Extend TinyDB <extend_hooks>`

Version 3.0
-----------

.. _upgrade_v3_0:

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

-  Querying (see `Issue #62 <https://github.com/msiemens/tinydb/issues/62>`_):

   -  ``where('...').contains('...')`` has been renamed to
      ``where('...').search('...')``.
   -  ``where('foo').has('bar')`` is replaced by either
      ``where('foo').bar`` or ``Query().foo.bar``.

      -  In case the key is not a valid Python identifier, array
         notation can be used: ``where('a.b.c')`` is now
         ``Query()['a.b.c']``.

  -  Checking for the existence of a key has to be done explicitely:
     ``where('foo').exists()``.

-  ``SmartCacheTable`` has been moved to `msiemens/tinydb-smartcache`_.
-  Serialization has been moved to `msiemens/tinydb-serialization`_.
-  Empty storages are now expected to return ``None`` instead of raising
   ``ValueError`` (see `Issue #67 <https://github.com/msiemens/tinydb/issues/67>`_).

.. _msiemens/tinydb-smartcache: https://github.com/msiemens/tinydb-smartcache
.. _msiemens/tinydb-serialization: https://github.com/msiemens/tinydb-serialization

.. _upgrade_v2_0:

Version 2.0
-----------

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- The syntax ``query in db`` is not supported any more. Use ``db.contains(...)``
  instead.
- The ``ConcurrencyMiddleware`` has been removed due to a insecure implementation
  (see `Issue #18 <https://github.com/msiemens/tinydb/issues/18>`_).  Consider
  :ref:`tinyrecord` instead.

Apart from that the API remains compatible to v1.4 and prior.

For migration from v1 to v2, check out the `v2.0 documentation <http://tinydb.readthedocs.io/en/v2.0/upgrade.html#upgrade-v2-0>`_
