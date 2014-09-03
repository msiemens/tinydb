Upgrading to Newer Releases
===========================

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


Migration
^^^^^^^^^

To improve the handling of IDs TinyDB changed the way it stores data
(see `Issue #13`_ for details). Opening an database from v1.4 or prior will
most likely result in an exception:

.. code-block:: pytb

    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "tinydb\database.py", line 49, in __init__
        self._table = self.table('_default')
      File "tinydb\database.py", line 69, in table
        table = table_class(name, self, **options)
      File "tinydb\database.py", line 171, in __init__
        self._last_id = int(sorted(self._read().keys())[-1])
      File "tinydb\database.py", line 212, in _read
        data[eid] = Element(data[eid], eid)
    TypeError: list indices must be integers, not dict

In this case you need to migrate the database to the recent scheme. TinyDB
provides a migration script for the default JSON storage:

.. code-block:: console

    $ python -m tinydb.migrate db1.json db2.json
    Processing db1.json ... Done
    Processing db2.json ... Done

Migration with a custom storage
...............................

If you have database files that have been written using a custom storage class,
you can write your own migration script that calls ``tinydb.migrate.migrate``:

.. automodule:: tinydb.migrate
    :members: migrate

.. _Issue #13: https://github.com/msiemens/tinydb/issues/13
