Changelog
=========

Version Numbering
^^^^^^^^^^^^^^^^^

TinyDB follows the SemVer versioning guidelines. For more information,
see `semver.org <http://semver.org/>`_

**v2.0.1** (2014-09-22)
=======================

- Fixed handling of unicode data in Python 2 (see `issue #28 <https://github.com/msiemens/tinydb/issues/28>`_).

**v2.0.0** (2014-09-05)
^^^^^^^^^^^^^^^^^^^^^^^

:ref:`Upgrade Notes <upgrade_v2_0>`

.. warning:: TinyDB changed the way data is stored. You may need to migrate
             your databases to the new scheme. Check out the
             :ref:`Upgrade Notes <upgrade_v2_0>` for details.

- The syntax ``query in db`` has been removed, use ``db.contains`` instead.
- The ``ConcurrencyMiddleware`` has been removed due to a insecure implementation
  (see `Issue #18 <https://github.com/msiemens/tinydb/issues/18>`_).  Consider
  :ref:`tinyrecord` instead.

- Better support for working with :ref:`Element IDs <element_ids>`.
- Added support for :ref:`nested comparisons <nested_queries>`.
- Added ``all`` and ``any`` :ref:`comparisons on lists <nested_queries>`.
- Added optional :ref:`smart query caching <smart_cache>`.
- The query cache is now a :ref:`fixed size lru cache <query_caching>`.

**v1.4.0** (2014-07-22)
^^^^^^^^^^^^^^^^^^^^^^^

- Added ``insert_multiple`` function (see `issue #8 <https://github.com/msiemens/tinydb/issues/8>`_).

**v1.3.0** (2014-07-02)
^^^^^^^^^^^^^^^^^^^^^^^

- Fixed `bug #7 <https://github.com/msiemens/tinydb/issues/7>`_: IDs not unique.
- Extended the API: ``db.count(where(...))`` and ``db.contains(where(...))``.
- The syntax ``query in db`` is now **deprecated** and replaced
  by ``db.contains``.

**v1.2.0** (2014-06-19)
^^^^^^^^^^^^^^^^^^^^^^^

- Added ``update`` method (see `Issue #6 <https://github.com/msiemens/tinydb/issues/6>`_).

**v1.1.1** (2014-06-14)
^^^^^^^^^^^^^^^^^^^^^^^

- Merged `PR #5 <https://github.com/msiemens/tinydb/pull/5>`_: Fix minor
  documentation typos and style issues.

**v1.1.0** (2014-05-06)
^^^^^^^^^^^^^^^^^^^^^^^

- Improved the docs and fixed some typos.
- Refactored some internal code.
- Fixed a bug with multiple ``TinyDB?`` instances.

**v1.0.1** (2014-04-26)
^^^^^^^^^^^^^^^^^^^^^^^

- Fixed a bug in ``JSONStorage`` that broke the database when removing entries.


**v1.0.0** (2013-07-20)
^^^^^^^^^^^^^^^^^^^^^^^

- First official release – consider TinyDB stable now.
