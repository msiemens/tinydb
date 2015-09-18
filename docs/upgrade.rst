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

For migration from v1 to v2, check out the `v2.0 documentation <http://tinydb.readthedocs.org/en/v2.0/upgrade.html#upgrade-v2-0>`_
