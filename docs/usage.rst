:tocdepth: 3

How to Use TinyDB
=================


Basic Usage
-----------


Initializing
::::::::::::

By default, TinyDB stores data as JSON files, so you have to specify the file
path:

>>> from tinydb import TinyDB, where
>>> db = TinyDB('/path/to/db.json')

You also can use in-memory JSON to store data:

>>> from tinydb.storages import MemoryStorage
>>> db = TinyDB(storage=MemoryStorage)


Inserting
:::::::::

As a document-oriented database, TinyDB uses ``dict``\ s to store data:

>>> db.insert({'int': 1, 'char': 'a'})
>>> db.insert({'int': 1, 'char': 'b'})
>>> db.insert({'int': 1, 'value': 5.0})


Getting Data
::::::::::::

.. hint::

    Throughout this section, the return values are stripped of the ``_id``
    key for clarity reasons. So::

        [{'int': 1, 'value': 5.0}]

    would actually be some something like::

        [{'int': 1, 'value': 5.0, '_id': 3}]


Getting all data stored:

>>> db.all()
[{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}, {'int': 1, 'value': 5.0}]


Getting the database size (number of elements stored):

>>> len(db)
3


Search for all elements, that have the ``value`` key defined:

>>> db.search(where('value'))
[{'int': 1, 'value': 5.0}]


Search for a specific value:

>>> db.search(where('int') == 1)
[{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]

Other comparison operators you can use:

- ``where('int') != 1``
- ``where('int') < 2`` and ``<=``
- ``where('int') > 0`` and ``>=``


Combine two queries with logical and:

>>> db.search((where('int') == 1) & (where('char') == 'b'))
[{'int': 1, 'char': 'b'}]


Combine two queries with logical or:

>>> db.search((where('char') == 'a') | (where('char') == 'b'))
[{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]

When using ``&`` or ``|``, make sure you wrap the conditions on both sides
with parentheses or Python will mess up the comparison.

More advanced queries
.....................

Check against a regex:

>>> db.search(where('char').matches('[aZ]*'))
[{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]


Use a custom test function:

>>> test_func = lambda c: c == 'a'
>>> db.search(where('char').test(test_func))


Also, if you want to get only one element, you can use:

>>> db.get(where('value'))

.. caution::

    If multiple elements match the query, only one of them will
    be returned!


In addition, TinyDB provides an alternative query syntax to be used in
if-clauses:

>>> if where('value') == 0.5 in db: print 'Found!'
Found!


Removing
::::::::

You can remove all elements matching a query:

>>> db.remove(where('int') == 1)
>>> len(db)
0

You also can purge all entries:

>>> db.purge()
>>> len(db)
0

Advanced Usage
--------------


Tables
::::::

You can use TinyDB with multiple tables. They behave exactly as descibred
above:

>>> table = db.table('name')
>>> table.insert({'value': True})
>>> table.all()
[{'value': True}]


In addition, you can remove all tables by using:

>>> db.purge_tables()


above:

>>> table = db.table('name')
>>> table.insert({'value': True})
>>> table.all()
[{'value': True}]


In addition, you can remove all tables by using:

>>> db.purge_all()

.. hint::

    When using the operations described above using ``db``,
    TinyDB actually uses a table named ``_default``.


.. _middlewares:

Middlewares
:::::::::::

Middlewares wrap around existing storages allowing you to customize their
behaviour.

>>> from tinydb.storages import JSONStorage
>>> from tinydb.middlewares import CachingMiddleware
>>> db = TinyDB('/path/to/db.json', storage=CachingMiddleware(JSONStorage))

TinyDB ships with these middlewares:

- **CachingMiddleware**: Improves speed by reducing disk I/O. It caches all
  read operations and writes data to disk every
  ``CachingMiddleware.WRITE_CACHE_SIZE`` write operations.
- **ConcurrencyMiddleware**: Allows you to use TinyDB in multithreaded
  environments by using a lock on read and write operations making
  them virtually atomic.

.. hint::

    You can nest middlewares:

    >>> from tinydb.middlewares import CachingMiddleware, ConcurrencyMiddleware
    >>> db = TinyDB('/path/to/db.json', storage=ConcurrencyMiddleware(CachingMiddleware(JSONStorage)))