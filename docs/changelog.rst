Changelog
=========

Version Numbering
^^^^^^^^^^^^^^^^^

TinyDB follows the SemVer versioning guidelines. For more information,
see `semver.org <http://semver.org/>`_

**v2.0.0** (2014-XX-XX)
^^^^^^^^^^^^^^^^^^^^^^^

- `search`, `get` and friends now returns an `Element` object that contain the value
  and the element's id.
- Added ``get_by_id``.
- Added optional smart query caching (see :ref:`Usage <smart_cache>`).
- Added support for nested comparisons.
- Added `all` and `any` comparisons on lists.
- Query cache is now a fixed size lru cache.

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
