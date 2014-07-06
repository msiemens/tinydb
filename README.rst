TinyDB
======

|Build Status| |Coverage| |Version|

TinyDB is a tiny, document oriented database optimized for your happiness :)
It's written in pure Python and has no external requirements. The target are
small apps that would be blown away by a SQL-DB or an external database server.

TinyDB is:

- **tiny**: The current source code has 800 lines of code (+ 500 lines tests)
  what makes about 100 KB. For comparison: Buzhug_ has about 2000 lines of code
  (w/o tests), CodernityDB_ has about 8000 lines of code (w/o tests).

- **document oriented**: Like `MongoDB <http://mongodb.org/>`_, you can store
  any document (represented as ``dict``) in TinyDB.

- **optimized for your happiness**: TinyDB is designed to be simple and fun to
  use. It's not bloated and has a simple and clean API.

- **written in pure Python**: TinyDB neither needs an external server (as e.g.
  `PyMongo <http://api.mongodb.org/python/current/>`_) nor any packages from
  PyPI. Just install TinyDB and you're ready to go.

- **easily extensible**: You can easily extend TinyDB by writing new storages
  or modify the behaviour of storages with Middlewares. TinyDB provides
  Middlewares for caching and concurrency handling.

- **nearly 100% code coverage**: If you don't count that ``__repr__`` methods
  and some abstract methods are not tested, TinyDB has a code coverage of 100%.


Example Code
------------

.. code-block:: python

    >>> from tinydb import TinyDB, where
    >>> db = TinyDB('/path/to/db.json')
    >>> db.insert({'int': 1, 'char': 'a'})
    >>> db.insert({'int': 1, 'char': 'b'})

Query Language
^^^^^^^^^^^^^^

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
^^^^^^

.. code-block:: python

    >>> table = db.table('name')
    >>> table.insert({'value': True})
    >>> table.all()
    [{'value': True}]

Using Middlewares
^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> from tinydb.storages import JSONStorage
    >>> from tinydb.middlewares import CachingMiddleware
    >>> db = TinyDB('/path/to/db.json', storage=CachingMiddleware(JSONStorage))


Documentation
-------------

The documentation for TinyDB is hosted at ``Read the Docs``: https://tinydb.readthedocs.org/en/latest/


Supported Python Versions
-------------------------

TinyDB has been tested with Python 2.6, 2.7, 3.2, 3.3 and pypy.


Limitations
-----------

JSON Serialization
^^^^^^^^^^^^^^^^^^

TinyDB serializes all data using the
`Python JSON <http://docs.python.org/2/library/json.html>`_ module by default.
It serializes most basic Python data types very well, but fails serializing
classes. If you need a better serializer, you can write your own storage,
that e.g. uses the more powerfull (but also slower)
`pickle  <http://docs.python.org/library/pickle.html>`_
or `PyYAML  <http://pyyaml.org/>`_.

Performance
^^^^^^^^^^^

TinyDB is NOT designed to be used in environments, where performance might be
an issue. Altough you can improve the TinyDB performance as described below,
you should consider using a DB that is optimized for speed like Buzhug_ or
CodernityDB_.

How to Improve TinyDB Performance
`````````````````````````````````

The default storage serializes the data using JSON. To improve performance,
you can install `ujson <http://pypi.python.org/pypi/ujson>`_ , an extremely
fast JSON implementation. TinyDB will auto-detect and use it if possible.

In addition, you can wrap the storage with the ``CachingMiddleware`` which
reduces disk I/O (see `Using Middlewares`_)


.. image:: http://i.imgur.com/if4JI70.png
   :width: 800 px
   :align: center


Version Numbering
-----------------

TinyDB follows the SemVer versioning guidelines. For more information,
see `semver.org <http://semver.org/>`_


Changelog
---------

**v1.3.0** (2014-07-02)
^^^^^^^^^^^^^^^^^^^^^^^

- Fixed `bug #7 <https://github.com/msiemens/tinydb/issues/7>`_: IDs not unique.
- Extended the API: ``db.count(where(...))`` and ``db.contains(where(...))``
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
- Fixed a bug with multiple ``TinyDB`` instances.

**v1.0.1** (2014-04-26)
^^^^^^^^^^^^^^^^^^^^^^^

- Fixed a bug in ``JSONStorage`` that broke the database when removing entries.

**v1.0.0** (2013-07-20)
^^^^^^^^^^^^^^^^^^^^^^^

- First official release – consider TinyDB stable now.



.. |Build Status| image:: http://img.shields.io/travis/msiemens/tinydb.svg?style=flat
   :target: https://travis-ci.org/msiemens/TinyDB
.. |Coverage| image:: http://img.shields.io/coveralls/msiemens/tinydb.svg?style=flat
   :target: https://coveralls.io/r/msiemens/tinydb
.. |Version| image:: http://img.shields.io/pypi/v/tinydb.svg?style=flat
   :target: https://crate.io/packages/tinydb
.. _Buzhug: http://buzhug.sourceforge.net/
.. _CodernityDB: http://labs.codernity.com/codernitydb/
