.. image:: https://raw.githubusercontent.com/msiemens/tinydb/master/artwork/logo.png
    :scale: 100%
    :height: 150px

|Build Status| |Coverage| |Version|

Quick Links
***********

- `Example Code`_
- `Supported Python Versions`_
- `Documentation <http://tinydb.readthedocs.org/>`_
- `Changelog <https://tinydb.readthedocs.io/en/latest/changelog.html>`_
- `Extensions <https://tinydb.readthedocs.io/en/latest/extensions.html>`_
- `Contributing`_

Introduction
************

TinyDB is a lightweight document oriented database optimized for your happiness :)
It's written in pure Python and has no external dependencies. The target are
small apps that would be blown away by a SQL-DB or an external database server.

TinyDB is:

- **tiny:** The current source code has 1200 lines of code (with about 40%
  documentation) and 1000 lines tests. For comparison: Buzhug_ has about 2500
  lines of code (w/o tests), CodernityDB_ has about 7000 lines of code
  (w/o tests).

- **document oriented:** Like MongoDB_, you can store any document
  (represented as ``dict``) in TinyDB.

- **optimized for your happiness:** TinyDB is designed to be simple and
  fun to use by providing a simple and clean API.

- **written in pure Python:** TinyDB neither needs an external server (as
  e.g. `PyMongo <http://api.mongodb.org/python/current/>`_) nor any dependencies
  from PyPI.

- **works on Python 2.7 and 3.3 – 3.6 and PyPy:** TinyDB works on all modern
  versions of Python and PyPy.

- **powerfully extensible:** You can easily extend TinyDB by writing new
  storages or modify the behaviour of storages with Middlewares.

- **100% test coverage:** No explanation needed.

To dive straight into all the details, head over to the `TinyDB docs
<https://tinydb.readthedocs.io/>`_. You can also discuss everything related
to TinyDB like general development, extensions or showcase your TinyDB-based
projects on the `discussion forum <http://forum.m-siemens.de/.>`_.

Supported Python Versions
*************************

TinyDB has been tested with Python 2.7, 3.3 - 3.6 and PyPy.

Example Code
************

.. code-block:: python

    >>> from tinydb import TinyDB, Query
    >>> db = TinyDB('/path/to/db.json')
    >>> db.insert({'int': 1, 'char': 'a'})
    >>> db.insert({'int': 1, 'char': 'b'})

Query Language
==============

.. code-block:: python

    >>> User = Query()
    >>> # Search for a field value
    >>> db.search(User.name == 'John')
    [{'name': 'John', 'age': 22}, {'name': 'John', 'age': 37}]

    >>> # Combine two queries with logical and
    >>> db.search((User.name == 'John') & (User.age <= 30))
    [{'name': 'John', 'age': 22}]

    >>> # Combine two queries with logical or
    >>> db.search((User.name == 'John') | (User.name == 'Bob'))
    [{'name': 'John', 'age': 22}, {'name': 'John', 'age': 37}, {'name': 'Bob', 'age': 42}]

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

.. |Build Status| image:: http://img.shields.io/travis/msiemens/tinydb.svg?style=flat-square
   :target: https://travis-ci.org/msiemens/tinydb
.. |Coverage| image:: http://img.shields.io/coveralls/msiemens/tinydb.svg?style=flat-square
   :target: https://coveralls.io/r/msiemens/tinydb
.. |Version| image:: http://img.shields.io/pypi/v/tinydb.svg?style=flat-square
   :target: https://pypi.python.org/pypi/tinydb/
.. _Buzhug: http://buzhug.sourceforge.net/
.. _CodernityDB: http://labs.codernity.com/codernitydb/
.. _MongoDB: http://mongodb.org/
