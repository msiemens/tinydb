Is TinyDB the right choice?
===========================

Why using TinyDB?
---------------------

TinyDB is:

- **tiny**: The current source code has 800 lines of code (+ 500 lines tests)
  what makes about 100 KB. For comparison: Buzhug_ has about 2000 lines of
  code (w/o tests), CodernityDB_ has about 8000 lines of code (w/o tests).

- **document oriented**: Like MongoDB_, you can store any document
  (represented as ``dict``) in TinyDB.

- **optimized for your happiness**: TinyDB is designed to be simple and
  fun to use. It's not bloated and has a simple and clean API.

- **written in pure Python**: TinyDB neither needs an external server (as
  e.g. `PyMongo <http://api.mongodb.org/python/current/>`_) nor any packages
  from PyPI. Just run ``pip install tinydb`` and you're ready to go.

- **easily extensible**: You can easily extend TinyDB by writing new
  storages or modify the behaviour of storages with Middlewares.
  TinyDB provides Middlewares for caching and concurrency handling.

- **nearly 100% covered with tests**: If you don't count that ``__repr__``
  methods and some abstract methods are not tested, TinyDB has a code
  coverage of 100%.

In short: If you need a simple database with a clean API that just works
without lots of configuration, TinyDB might be the right choice for you.

Compatibility
:::::::::::::

TinyDB has been tested with Python 2.6, 2.7, 3.2, 3.3 and pypy.


Why **not** using TinyDB?
-----------------------------

- You need **advanced features** like multiple indexes, a HTTP server,
  relationships, or similar.
- You are really concerned about **high performance** and need a high speed
  database.

To put it plainly: TinyDB is designed to be tiny and fun to use. If you
need advanced features/high performance, TinyDB is the wrong database for you
– consider using databases like Buzhug_, CodernityDB_ or MongoDB_.

.. References
.. _Buzhug: http://buzhug.sourceforge.net/
.. _CodernityDB: http://labs.codernity.com/codernitydb/
.. _MongoDB: http://mongodb.org/