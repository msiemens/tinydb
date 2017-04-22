Changelog
=========

Version Numbering
^^^^^^^^^^^^^^^^^

TinyDB follows the SemVer versioning guidelines. For more information,
see `semver.org <http://semver.org/>`_

**v3.2.3** (2017-04-22)
^^^^^^^^^^^^^^^^^^^^^^^

- Fix bug with accidental modifications to the query cache when modifying
  the list of search results (see `issue #132 <https://github.com/msiemens/tinydb/issues/132>`_).

**v3.2.2** (2017-01-16)
^^^^^^^^^^^^^^^^^^^^^^^

- Fix the ``Query`` constructor to prevent wrong usage
  (see `issue #117 <https://github.com/msiemens/tinydb/issues/117>`_).

**v3.2.1** (2016-06-29)
^^^^^^^^^^^^^^^^^^^^^^^

- Fix a bug with queries on elements that have a ``path`` key
  (see `pull request #107 <https://github.com/msiemens/tinydb/pull/107>`_).
- Don't write to the database file needlessly when opening the database
  (see `pull request #104 <https://github.com/msiemens/tinydb/pull/104>`_).

**v3.2.0** (2016-04-25)
^^^^^^^^^^^^^^^^^^^^^^^

- Add a way to specify the default table name via :ref:`default_table <default_table>`
  (see `pull request #98 <https://github.com/msiemens/tinydb/pull/98>`_).
- Add ``db.purge_table(name)`` to remove a single table
  (see `pull request #100 <https://github.com/msiemens/tinydb/pull/100>`_).

  - Along the way: celebrating 100 issues and pull requests! Thanks everyone for every single contribution!

- Extend API documentation (see `issue #96 <https://github.com/msiemens/tinydb/issues/96>`_).

**v3.1.3** (2016-02-14)
^^^^^^^^^^^^^^^^^^^^^^^

- Fix a bug when using unhashable elements (lists, dicts) with
  ``Query.any`` or ``Query.all`` queries
  (see `a forum post by karibul <https://forum.m-siemens.de/d/4-error-with-any-and-all-queries>`_).

**v3.1.2** (2016-01-30)
^^^^^^^^^^^^^^^^^^^^^^^

- Fix a bug when using unhashable elements (lists, dicts) with
  ``Query.any`` or ``Query.all`` queries
  (see `a forum post by karibul <https://forum.m-siemens.de/d/4-error-with-any-and-all-queries>`_).

**v3.1.1** (2016-01-23)
^^^^^^^^^^^^^^^^^^^^^^^

- Inserting a dictionary with data that is not JSON serializable doesn't
  lead to corrupt files anymore (see `issue #89 <https://github.com/msiemens/tinydb/issues/89>`_).
- Fix a bug in the LRU cache that may lead to an invalid query cache
  (see `issue #87 <https://github.com/msiemens/tinydb/issues/87>`_).

**v3.1.0** (2015-12-31)
^^^^^^^^^^^^^^^^^^^^^^^

- ``db.update(...)`` and ``db.remove(...)`` now return affected element IDs
  (see `issue #83 <https://github.com/msiemens/tinydb/issues/83>`_).
- Inserting an invalid element (i.e. not a ``dict``) now raises an error
  instead of corrupting the database (see
  `issue #74 <https://github.com/msiemens/tinydb/issues/74>`_).

**v3.0.0** (2015-11-13)
^^^^^^^^^^^^^^^^^^^^^^^

-  Overhauled Query model:

   -  ``where('...').contains('...')`` has been renamed to
      ``where('...').search('...')``.
   -  Support for ORM-like usage:
      ``User = Query(); db.search(User.name == 'John')``.
   -  ``where('foo')`` is an alias for ``Query().foo``.
   -  ``where('foo').has('bar')`` is replaced by either
      ``where('foo').bar`` or ``Query().foo.bar``.

      -  In case the key is not a valid Python identifier, array
         notation can be used: ``where('a.b.c')`` is now
         ``Query()['a.b.c']``.

   -  Checking for the existence of a key has to be done explicitely:
      ``where('foo').exists()``.

-  Migrations from v1 to v2 have been removed.
-  ``SmartCacheTable`` has been moved to `msiemens/tinydb-smartcache`_.
-  Serialization has been moved to `msiemens/tinydb-serialization`_.
- Empty storages are now expected to return ``None`` instead of raising ``ValueError``.
  (see `issue #67 <https://github.com/msiemens/tinydb/issues/67>`_.

.. _msiemens/tinydb-smartcache: https://github.com/msiemens/tinydb-smartcache
.. _msiemens/tinydb-serialization: https://github.com/msiemens/tinydb-serialization

**v2.4.0** (2015-08-14)
^^^^^^^^^^^^^^^^^^^^^^^

- Allow custom parameters for custom test functions
  (see `issue #63 <https://github.com/msiemens/tinydb/issues/63>`_ and
  `pull request #64 <https://github.com/msiemens/tinydb/pull/64>`_).

**v2.3.2** (2015-05-20)
^^^^^^^^^^^^^^^^^^^^^^^

- Fix a forgotten debug output in the ``SerializationMiddleware``
  (see `issue #55 <https://github.com/msiemens/tinydb/issues/55>`_).
- Fix an "ignored exception" warning when using the ``CachingMiddleware``
  (see `pull request #54 <https://github.com/msiemens/tinydb/pull/54>`_)
- Fix a problem with symlinks when checking out TinyDB on OSX Yosemite
  (see `issue #52 <https://github.com/msiemens/tinydb/issues/52>`_).

**v2.3.1** (2015-04-30)
^^^^^^^^^^^^^^^^^^^^^^^

- Hopefully fix a problem with using TinyDB as a dependency in a ``setup.py`` script
  (see `issue #51 <https://github.com/msiemens/tinydb/issues/51>`_).

**v2.3.0** (2015-04-08)
^^^^^^^^^^^^^^^^^^^^^^^

- Added support for custom serialization. That way, you can teach TinyDB
  to store ``datetime`` objects in a JSON file :)
  (see `issue #48 <https://github.com/msiemens/tinydb/issues/48>`_ and
  `pull request #50 <https://github.com/msiemens/tinydb/pull/50>`_)
- Fixed a performance regression when searching became slower with every search
  (see `issue #49 <https://github.com/msiemens/tinydb/issues/49>`_)
- Internal code has been cleaned up

**v2.2.2** (2015-02-12)
^^^^^^^^^^^^^^^^^^^^^^^

- Fixed a data loss when using ``CachingMiddleware`` together with ``JSONStorage``
  (see `issue #47 <https://github.com/msiemens/tinydb/issues/47>`_)

**v2.2.1** (2015-01-09)
^^^^^^^^^^^^^^^^^^^^^^^

- Fixed handling of IDs with the JSON backend that converted integers
  to strings (see `issue #45 <https://github.com/msiemens/tinydb/issues/45>`_)

**v2.2.0** (2014-11-10)
^^^^^^^^^^^^^^^^^^^^^^^

- Extended ``any`` and ``all`` queries to take lists as conditions
  (see `pull request #38 <https://github.com/msiemens/tinydb/pull/38>`_)
- Fixed an ``decode error`` when installing TinyDB in a non-UTF-8 environment
  (see `pull request #37 <https://github.com/msiemens/tinydb/pull/37>`_)
- Fixed some issues with ``CachingMiddleware`` in combination with
  ``JSONStorage`` (see `pull request #39 <https://github.com/msiemens/tinydb/pull/39>`_)

**v2.1.0** (2014-10-14)
^^^^^^^^^^^^^^^^^^^^^^^

- Added ``where(...).contains(regex)``
  (see `issue #32 <https://github.com/msiemens/tinydb/issues/32>`_)
- Fixed a bug that corrupted data after reopening a database
  (see `issue #34 <https://github.com/msiemens/tinydb/issues/34>`_)

**v2.0.1** (2014-09-22)
^^^^^^^^^^^^^^^^^^^^^^^

- Fixed handling of Unicode data in Python 2
  (see `issue #28 <https://github.com/msiemens/tinydb/issues/28>`_).

**v2.0.0** (2014-09-05)
^^^^^^^^^^^^^^^^^^^^^^^

:ref:`Upgrade Notes <upgrade_v2_0>`

.. warning:: TinyDB changed the way data is stored. You may need to migrate
             your databases to the new scheme. Check out the
             :ref:`Upgrade Notes <upgrade_v2_0>` for details.

- The syntax ``query in db`` has been removed, use ``db.contains`` instead.
- The ``ConcurrencyMiddleware`` has been removed due to a insecure implementation
  (see `issue #18 <https://github.com/msiemens/tinydb/issues/18>`_).  Consider
  :ref:`tinyrecord` instead.

- Better support for working with :ref:`Element IDs <element_ids>`.
- Added support for `nested comparisons <http://tinydb.readthedocs.io/en/v2.0.0/usage.html#nested-queries>`_.
- Added ``all`` and ``any`` `comparisons on lists <http://tinydb.readthedocs.io/en/v2.0.0/usage.html#nested-queries>`_.
- Added optional :<http://tinydb.readthedocs.io/en/v2.0.0/usage.html#smart-query-cache>`_.
- The query cache is now a :ref:`fixed size LRU cache <query_caching>`.

**v1.4.0** (2014-07-22)
^^^^^^^^^^^^^^^^^^^^^^^

- Added ``insert_multiple`` function
  (see `issue #8 <https://github.com/msiemens/tinydb/issues/8>`_).

**v1.3.0** (2014-07-02)
^^^^^^^^^^^^^^^^^^^^^^^

- Fixed `bug #7 <https://github.com/msiemens/tinydb/issues/7>`_: IDs not unique.
- Extended the API: ``db.count(where(...))`` and ``db.contains(where(...))``.
- The syntax ``query in db`` is now **deprecated** and replaced
  by ``db.contains``.

**v1.2.0** (2014-06-19)
^^^^^^^^^^^^^^^^^^^^^^^

- Added ``update`` method
  (see `issue #6 <https://github.com/msiemens/tinydb/issues/6>`_).

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
