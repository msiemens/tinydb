.. image:: artwork/logo.png
    :scale: 100%
    :height: 150px

|Build Status| |Coverage| |Version|

TinyDB is a tiny, document oriented database optimized for your happiness :)
It's written in pure Python and has no external requirements. The target are
small apps that would be blown away by a SQL-DB or an external database server.

TinyDB is:

- **tiny:** The current source code has 1200 lines of code (with about 40% documentation) and 600 lines tests.
  For comparison: Buzhug_ has about 2000 lines of
  code (w/o tests), CodernityDB_ has about 8000 lines of code (w/o tests).

- **document oriented:** Like MongoDB_, you can store any document
  (represented as ``dict``) in TinyDB.

- **optimized for your happiness:** TinyDB is designed to be simple and
  fun to use by providing a simple and clean API.

- **written in pure Python:** TinyDB neither needs an external server (as
  e.g. `PyMongo <http://api.mongodb.org/python/current/>`_) nor any dependencies
  from PyPI.

- **works on Python 2.6 – 3.4 and PyPy:** TinyDB works on all
  modern versions of Python and PyPy.

- **easily extensible:** You can easily extend TinyDB by writing new
  storages or modify the behaviour of storages with Middlewares.

- **nearly 100% test coverage:** If you don't count that ``__repr__``
  methods and some abstract methods are not tested, TinyDB has a test
  coverage of 100%.


Example Code
************

.. code-block:: python

    >>> from tinydb import TinyDB, where
    >>> db = TinyDB('/path/to/db.json')
    >>> db.insert({'int': 1, 'char': 'a'})
    >>> db.insert({'int': 1, 'char': 'b'})

Query Language
==============

.. code-block:: python

    >>> # Search for a field value
    >>> db.search(where('int') == 1)
    [{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]

    >>> # Combine two queries with logical and
    >>> db.search((where('int') == 1) & (where('char') == 'b'))
    [{'int': 1, 'char': 'b'}]

    >>> # Combine two queries with logical or
    >>> db.search((where('char') == 'a') | (where('char') == 'b'))
    [{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]

    >>> # More possible comparisons:  !=  <  >  <=  >=
    >>> # More possible checks: where(...).matches(regex), where(...).test(your_test_func)

Tables
======

.. code-block:: python

    >>> table = db.table('name')
    >>> table.insert({'value': True})
    >>> table.all()
    [{'value': True}]

Using Middlewares
=================

.. code-block:: python

    >>> from tinydb.storages import JSONStorage
    >>> from tinydb.middlewares import CachingMiddleware
    >>> db = TinyDB('/path/to/db.json', storage=CachingMiddleware(JSONStorage))


Documentation
*************

The documentation for TinyDB is hosted at ``Read the Docs``: https://tinydb.readthedocs.org/


Supported Python Versions
*************************

TinyDB has been tested with Python 2.6, 2.7, 3.2, 3.3, 3.4 and pypy.


Extensions
**********

| **Name:**        ``tinyrecord``
| **Repo:**        https://github.com/eugene-eeo/tinyrecord
| **Status:**      *experimental*
| **Description:** Tinyrecord is a library which implements experimental atomic
                   transaction support for the TinyDB NoSQL database. It uses a
                   record-first then execute architecture which allows us to
                   minimize the time that we are within a thread lock.
|

| **Name:**        ``tinyindex``
| **Repo:**        https://github.com/eugene-eeo/tinyindex
| **Status:**      *experimental*
| **Description:** Document indexing for TinyDB. Basically ensures deterministic
                   (as long as there aren't any changes to the table) yielding
                   of documents.
|


Contributing
************

Whether reporting bugs, discussing improvements and new ideas or writing
extensions: Contributions to TinyDB are welcome! Here's how to get started:

1. Check for open issues or open a fresh issue to start a discussion around
   a feature idea or a bug
2. Fork `the repository <https://github.com/msiemens/tinydb/>`_ on Github,
   create a new branch off the `master` branch and start making your changes
   (known as `GitHub Flow <https://guides.github.com/introduction/flow/index.html>`_)
3. Write a test which shows that the bug was fixed or that the feature works
   as expected
4. Send a pull request and bug the maintainer until it gets merged and
   published ☺


Changelog
*********

**v2.1.0** (2014-10-14)
=======================

- Added ``where(...).contains(regex)`` (see `issue #32 <https://github.com/msiemens/tinydb/issues/32>`_)
- Fixed a bug that corrupted data after reopening a database (see `issue #34 <https://github.com/msiemens/tinydb/issues/34>`_)

**v2.0.1** (2014-09-22)
=======================

- Fixed handling of unicode data in Python 2 (see `issue #28 <https://github.com/msiemens/tinydb/issues/28>`_).

**v2.0.0** (2014-09-05)
=======================

`Upgrade Notes <http://tinydb.readthedocs.org/en/v2.0/upgrade.html#upgrade-v2-0>`_

**Warning:** TinyDB changed the way data is stored. You may need to migrate
your databases to the new scheme. Check out the `Upgrade Notes <http://tinydb.readthedocs.org/en/v2.0/upgrade.html#upgrade-v2-0>`_
for details.

- The syntax ``query in db`` has been removed, use ``db.contains`` instead.
- The ``ConcurrencyMiddleware`` has been removed due to a insecure implementation
  (see `Issue #18 <https://github.com/msiemens/tinydb/issues/18>`_).  Consider
  `tinyrecord <http://tinydb.readthedocs.org/en/v2.0/extensions.html#tinyrecord>`_ instead.

- Better support for working with `Element IDs <http://tinydb.readthedocs.org/en/v2.0.0/usage.html#using-element-ids>`_.
- Added support for `nested comparisons <http://tinydb.readthedocs.org/en/v2.0.0/usage.html#nested-queries>`_.
- Added ``all`` and ``any`` `comparisons on lists <http://tinydb.readthedocs.org/en/v2.0.0/usage.html#nested-queries>`_.
- Added optional `smart query caching <http://tinydb.readthedocs.org/en/v2.0.0/usage.html#smart-query-cache>`_.
- The query cache is now a `fixed size lru cache <http://tinydb.readthedocs.org/en/v2.0.0/usage.html#query-caching>`_.

**v1.4.0** (2014-07-22)
=======================

- Added ``insert_multiple`` function (see `issue #8 <https://github.com/msiemens/tinydb/issues/8>`_).

**v1.3.0** (2014-07-02)
=======================

- Fixed `bug #7 <https://github.com/msiemens/tinydb/issues/7>`_: IDs not unique.
- Extended the API: ``db.count(where(...))`` and ``db.contains(where(...))``
- The syntax ``query in db`` is now **deprecated** and replaced
  by ``db.contains``.

**v1.2.0** (2014-06-19)
=======================

- Added ``update`` method (see `Issue #6 <https://github.com/msiemens/tinydb/issues/6>`_).

**v1.1.1** (2014-06-14)
=======================

- Merged `PR #5 <https://github.com/msiemens/tinydb/pull/5>`_: Fix minor
  documentation typos and style issues.

**v1.1.0** (2014-05-06)
=======================

- Improved the docs and fixed some typos.
- Refactored some internal code.
- Fixed a bug with multiple ``TinyDB`` instances.

**v1.0.1** (2014-04-26)
=======================

- Fixed a bug in ``JSONStorage`` that broke the database when removing entries.

**v1.0.0** (2013-07-20)
=======================

- First official release – consider TinyDB stable now.



.. |Build Status| image:: http://img.shields.io/travis/msiemens/tinydb.svg?style=flat-square
   :target: https://travis-ci.org/msiemens/tinydb
.. |Coverage| image:: http://img.shields.io/coveralls/msiemens/tinydb.svg?style=flat-square
   :target: https://coveralls.io/r/msiemens/tinydb
.. |Version| image:: http://img.shields.io/pypi/v/tinydb.svg?style=flat-square
   :target: https://pypi.python.org/pypi/tinydb/
.. _Buzhug: http://buzhug.sourceforge.net/
.. _CodernityDB: http://labs.codernity.com/codernitydb/
.. _MongoDB: http://mongodb.org/
