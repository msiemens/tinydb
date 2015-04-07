:tocdepth: 3

.. toctree::
   :maxdepth: 2

Advanced Usage
==============

Remarks on Storages
-------------------

Before we dive deeper into the usage of TinyDB, we should stop for a moment
and discuss how TinyDB stores data.

To convert your data to a format that is writable to disk TinyDB uses the
`Python JSON <http://docs.python.org/2/library/json.html>`_ module by default.
It's great when only simple data types are involved but it cannot handle more
complex data types like custom classes. On Python 2 it also converts strings to
unicode strings upon reading
(described `here <http://stackoverflow.com/q/956867/997063>`_).

If that causes problems, you can write
:doc:`your own storage <extend>`, that uses a more powerful (but also slower)
library like `pickle  <http://docs.python.org/library/pickle.html>`_ or
`PyYAML  <http://pyyaml.org/>`_.

Alternative JSON libary
.......................

As already mentioned, the default storage relies upon Python's
JSON module. To improve performance, you can install
`ujson <http://pypi.python.org/pypi/ujson>`_ , an extremely fast JSON
implementation. TinyDB will auto-detect and use it if possible.

Handling Data
-------------

With that out of the way, let's start with inserting, updating and retrieving
data from your database.

Inserting data
..............

As already described you can insert an element using ``db.insert(...)``.
In case you want to insert multiple elements, you can use ``db.insert_multiple(...)``:

>>> db.insert_multiple([{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}])
>>> db.insert_multiple({'int': 1, 'value': i} for i in range(2))

Updating data
.............

``db.update(fields, query)`` only allows you to update an element by adding
or overwriting it's values. But sometimes you may need to e.g. remove one field
or increment it's value. In that case you can pass a function instead of
``fields``:

>>> from tinydb.operations import delete
>>> db.update(delete('key1'), where('key') == 'value')

This will remove the key ``key1`` from all matching elements. TinyDB comes
with these operations:

- ``delete(key)``: delete a key from the element
- ``increment(key)``: incremenet the value of a key
- ``decrement(key)``: decremenet the value of a key

Of course you also can write your own operations:

>>> def your_operation(your_arguments):
...     def transform(element):
...         # do something with the element
...         # ...
...     return transform
...
>>> db.update(your_operation(arguments), query)

Retrieving data
...............

There are several ways to retrieve data from your database. For instance you
can get the number of stored elements:

>>> len(db)
3

Then of course you can use ``db.search(...)`` as described in the :doc:`getting-started`
section. But sometimes you want to get only one matching element. Instead of using

>>> try:
...     result = db.search(where('value') == 1)[0]
... except IndexError:
...     pass


you can use ``db.get(...)``:

>>> db.get(where('value') == 1)
{'int': 1, 'value': 1}
>>> db.get(where('value') == 100)
None

.. caution::

    If multiple elements match the query, propably a random one of them will
    be returned!

Often you don't want to search for elements but only know whether they are
stored in the database. In this case ``db.contains(...)`` is your friend:

>>> db.contains(where('char') == 'a')

In a similar manner you can look up the number of elements matching a query:

>>> db.count(where('int') == 1)
3

Recap
^^^^^

Let's summarize the ways to handle data:

+-------------------------------+---------------------------------------------------------------+
| **Inserting data**                                                                            |
+-------------------------------+---------------------------------------------------------------+
| ``db.insert_multiple(...)``   | Insert multiple elements                                      |
+-------------------------------+---------------------------------------------------------------+
| **Updatingg data**                                                                            |
+-------------------------------+---------------------------------------------------------------+
| ``db.update(operation, ...)`` | Update all matching elements with a special operation         |
+-------------------------------+---------------------------------------------------------------+
| **Retrieving data**                                                                           |
+-------------------------------+---------------------------------------------------------------+
| ``len(db)``                   | Get the number of elements in the database                    |
+-------------------------------+---------------------------------------------------------------+
| ``db.get(query)``             | Get one element matching the query                            |
+-------------------------------+---------------------------------------------------------------+
| ``db.contains(query)``        | Check if the database contains a matching element             |
+-------------------------------+---------------------------------------------------------------+
| ``db.count(query)``           | Get the number of matching elements                           |
+-------------------------------+---------------------------------------------------------------+


.. _element_ids:

Using Element IDs
-----------------

Internally TinyDB associates an ID with every element you insert. It's returned
after inserting an element:

>>> db.insert({'value': 1})
3
>>> db.insert_multiple([{...}, {...}, {...}])
[4, 5, 6]

In addition you can get the ID of already inserted elements using
``element.eid``:

>>> el = db.get(where('value') == 1)
>>> el.eid
3

Different TinyDB methods also work with IDs, namely: ``update``, ``remove``,
``contains`` and ``get``.

>>> db.update({'value': 2}, eids=[1, 2])
>>> db.contains(eids=[1])
True
>>> db.remove(eids=[1, 2])
>>> db.get(eid=3)
{...}

Recap
.....

Let's sum up the way TinyDB supports working with IDs:

+----------------------------------+---------------------------------------------------------------+
| **Getting an element's ID**                                                                      |
+----------------------------------+---------------------------------------------------------------+
| ``db.insert(...)``               | Returns the inserted element's ID                             |
+----------------------------------+---------------------------------------------------------------+
| ``db.insert_multiple(...)``      | Returns the inserted elements' ID                             |
+----------------------------------+---------------------------------------------------------------+
| ``element.eid``                  | Get the ID of an element fetched from the db                  |
+----------------------------------+---------------------------------------------------------------+
| **Working with IDs**                                                                             |
+----------------------------------+---------------------------------------------------------------+
| ``db.get(eid=...)``              | Get the elemtent with the given ID                            |
+----------------------------------+---------------------------------------------------------------+
| ``db.contains(eids=[...])``      | Check if the db contains elements with one of the given IDs   |
+----------------------------------+---------------------------------------------------------------+
| ``db.update({...}, eids=[...])`` | Update all elements with the given IDs                        |
+----------------------------------+---------------------------------------------------------------+
| ``db.remove(eids=[...])``        | Remove all elements with the given IDs                        |
+----------------------------------+---------------------------------------------------------------+


Queries
-------

TinyDB lets you use a rich set of queries. In the :doc:`getting-started` you've
learned about the basic comparisons (``==``, ``<``, ``>``, ...). In addition
to that TinyDB enables you run logical operations on queries.

>>> # Negate a query:
>>> db.search(~ where('int') == 1)

>>> # Logical AND:
>>> db.search((where('int') == 1) & (where('char') == 'b'))
[{'int': 1, 'char': 'b'}]

>>> # Logical OR:
>>> db.search((where('char') == 'a') | (where('char') == 'b'))
[{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]

.. note::

    When using ``&`` or ``|``, make sure you wrap the conditions on both sides
    with parentheses or Python will mess up the comparison.

You also can search for elements where a specific key exists:

>>> db.search(where('char'))
[{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]

Advanced queries
................

In addition to these checks TinyDB supports checking against
a regex or a custom test function:

>>> # Regex:
>>> db.search(where('char').matches('[aZ]*'))
[{'int': 1, 'char': 'abc'}, {'int': 1, 'char': 'def'}]
>>> db.search(where('char').contains('b+'))
[{'int': 1, 'char': 'abbc'}, {'int': 1, 'char': 'bb'}]

>>> # Custom test:
>>> test_func = lambda c: c == 'a'
>>> db.search(where('char').test(test_func))
[{'char': 'a', 'int': 1}]

.. _nested_queries:

Nested Queries
..............

You can insert nested elements into your database:

>>> db.insert({'field': {'name': {'first_name': 'John', 'last_name': 'Doe'}}})

To search for a nested field, use ``where('field').has(...)``. You can apply
any queries you already know to this selector:

>>> db.search(where('field').has('name'))
[{'field': ...}]
>>> db.search(where('field').has('name').has('last_name') == 'Doe')
[{'field': ...}]

You also can use lists inside of elements:

>>> db.insert({'field': [{'val': 1}, {'val': 2}, {'val': 3}])

Using ``where('field').any(...)`` and ``where('field').all(...)`` you can
specify checks for the list's items using either a nested query or a sequence
such as a list. They behave similarly to Python's `any` and `all`:

>>> # Nested Query:
>>> db.search(where('field').any(where('val') == 1))
True
>>> db.search(where('field').all(where('val') > 0))
True

>>> # List:
>>> db.search(where('field').any([{'val': 1}, {'val': 4}]))
True
>>> db.search(where('field').all([{'val': 1}, {'val': 4}]))
False
>>> db.search(where('field').all([{'val': 1}, {'val': 3}]))
True

Recap
.....

Again, let's recapitulate the query operations:

+-----------------------------------+-----------------------------------------------------------+
| **Queries**                                                                                   |
+-----------------------------------+-----------------------------------------------------------+
| ``where('field').matches(regex)`` | Match any element matching the regular expression         |
+-----------------------------------+-----------------------------------------------------------+
| ``where('field').contains(regex)``| Match any element with a matching substring               |
+-----------------------------------+-----------------------------------------------------------+
| ``where('field').test(func)``     | Matches any element for which the function returns        |
|                                   | ``True``                                                  |
+-----------------------------------+-----------------------------------------------------------+
| **Combining Queries**                                                                         |
+-----------------------------------+-----------------------------------------------------------+
| ``~ query``                       | Match elements that don't match the query                 |
+-----------------------------------+-----------------------------------------------------------+
| ``(query1) & (query2)``           | Match elements that match both queries                    |
+-----------------------------------+-----------------------------------------------------------+
| ``(query1) | (query2)``           | Match elements that match one of the queries              |
+-----------------------------------+-----------------------------------------------------------+
| **Nested Queries**                |                                                           |
+-----------------------------------+-----------------------------------------------------------+
| ``where('field').has('field')``   | Match any element that has the specified item. Perform    |
|                                   | more queries on this selector as needed                   |
+-----------------------------------+-----------------------------------------------------------+
| ``where('field').any(query)``     | Match any element where 'field' is a list where one of    |
|                                   | the items matches the subquery                            |
+-----------------------------------+-----------------------------------------------------------+
| ``where('field').all(query)``     | Match any element where 'field' is a list where all items |
|                                   | match the subquery                                        |
+-----------------------------------+-----------------------------------------------------------+


Tables
------

TinyDB supports working with multiple tables. They behave just the same as
the ``TinyDB`` class. To create and use a table, use ``db.table(name)``.

>>> table = db.table('table_name')
>>> table.insert({'value': True})
>>> table.all()
[{'value': True}]

To remove all tables from a database, use:

>>> db.purge_tables()

.. note::

    TinyDB uses a table named ``_default`` as default table. All operations
    on the database object (like ``db.insert(...)``) operate on this table.

.. _query_caching:

You can get a list with the names of all tables in your database:

>>> db.tables()
{'_default', 'table_name'}

Query Caching
.............

TinyDB caches query result for performance. You can optimize the query cache
size by passing the ``cache_size`` to the ``table(...)`` function:

>>> table = db.table('table_name', cache_size=30)

.. hint:: You can set ``cache_size`` to ``None`` to make the cache unlimited in
   size.

.. _smart_cache:

Smart Query Cache
^^^^^^^^^^^^^^^^^

If you perform lots of queries while the data changes only little, you may
enable a smarter query cache. It updates the query cache when
inserting/removing/updating elements so the cache doesn't get invalidated.

>>> table = db.table('table_name', smart_cache=True)

Storages & Middlewares
----------------------

Storage Types
.............

TinyDB comes with two storage types: JSON and in-memory. By
default TinyDB stores its data in JSON files so you have to specify the path
where to store it:

>>> from tinydb import TinyDB, where
>>> db = TinyDB('path/to/db.json')

To use the in-memory storage, use:

>>> from tinydb.storages import MemoryStorage
>>> db = TinyDB(storage=MemoryStorage)

Middlewares
...........

Middlewares wrap around existing storages allowing you to customize their
behaviour.

>>> from tinydb.storages import JSONStorage
>>> from tinydb.middlewares import CachingMiddleware
>>> db = TinyDB('/path/to/db.json', storage=CachingMiddleware(JSONStorage))

.. hint::

    You can nest middlewares:

    >>> db = TinyDB('/path/to/db.json', storage=FirstMiddleware(SecondMiddleware(JSONStorage)))

CachingMiddleware
^^^^^^^^^^^^^^^^^

The ``CachingMiddleware`` improves speed by reducing disk I/O. It caches all
read operations and writes data to disk after a configured number of
write operations.

To make sure that all data is safely written when closing the table, use one
of these ways:

.. code-block:: python

    # Using a context manager:
    with database as db:
        # Your operations

.. code-block:: python

    # Using the close function
    db.close()

What's next
-----------

Congratulations, you've made through the user guide! Now go and build something
awesome or dive deeper into TinyDB with these ressources:

- Want to learn how to customize TinyDB (custom serializers, storages,
  middlewares) and what extensions exist? Check out :doc:`extend` and
  :doc:`extensions`.
- Want to study the API in detail? Read :doc:`api`.
- Interested in contributing to the TinyDB development guide? Go on to the
  :doc:`contribute`.
