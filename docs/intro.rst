Introduction
============

Great that you've taken time to check out the TinyDB docs! Before we begin
looking at TinyDB itself, let's take some time to see whether you should use
TinyDB.

Why Use TinyDB?
-----------------

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

- **works on Python 2.6 – 3.5 and PyPy:** TinyDB works on all modern versions
  of Python and PyPy.

- **powerfully extensible:** You can easily extend TinyDB by writing new
  storages or modify the behaviour of storages with Middlewares.

- **100% test coverage:** No explanation needed.

In short: If you need a simple database with a clean API that just works
without lots of configuration, TinyDB might be the right choice for you.


Why **Not** Use TinyDB?
-------------------------

- You need **advanced features** like access from multiple processes, indexes,
  a HTTP server, relationships or similar.
- You are really concerned about **performance** and need a high speed
  database.

To put it plainly: If you need advanced features or high performance, TinyDB
is the wrong database for you – consider using databases like Buzhug_, CodernityDB_ or MongoDB_.

.. References
.. _Buzhug: http://buzhug.sourceforge.net/
.. _CodernityDB: http://labs.codernity.com/codernitydb/
.. _MongoDB: http://mongodb.org/
