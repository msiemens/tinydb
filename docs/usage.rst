:tocdepth: 3

.. toctree::
   :maxdepth: 2

Advanced Usage
==============

Remarks on Storage
------------------

Before we dive deeper into the usage of TinyDB, we should stop for a moment
and discuss how TinyDB stores data.

To convert your data to a format that is writable to disk TinyDB uses the
`Python JSON <http://docs.python.org/2/library/json.html>`_ module by default.
It's great when only simple data types are involved but it cannot handle more
complex data types like custom classes. On Python 2 it also converts strings to
Unicode strings upon reading
(described `here <http://stackoverflow.com/q/956867/997063>`_).

If that causes problems, you can write
:doc:`your own storage <extend>`, that uses a more powerful (but also slower)
library like `pickle  <http://docs.python.org/library/pickle.html>`_ or
`PyYAML  <http://pyyaml.org/>`_.

Alternative JSON library
........................

As already mentioned, the default storage relies upon Python's
JSON module. To improve performance, you can install
`ujson <http://pypi.python.org/pypi/ujson>`_ , an extremely fast JSON
implementation. TinyDB will auto-detect and use it if possible.

Queries
-------

With that out of the way, let's start with TinyDB's rich set of queries.
There are two main ways to construct queries. The first one resembles the
syntax of popular ORM tools:

>>> from tinydb import Query
>>> User = Query()
>>> db.search(User.name == 'John')

As you can see, we first create a new Query object and then use it to specify
which fields to check. Searching for nested fields is just as easy:

>>> db.search(User.birthday.year == 1990)

Not all fields can be accessed this way if the field name is not a valid Python
identifier. In this case, you can switch to array indexing notation:

>>> # This would be invalid Python syntax:
>>> db.search(User.country-code == 'foo')
>>> # Use this instead:
>>> db.search(User['country-code'] == 'foo')

The second, traditional way of constructing queries is as follows:

>>> from tinydb import where
>>> db.search(where('field') == 'value')

Using ``where('field')`` is a shorthand for the following code:

>>> db.search(Query()['field'] == 'value')

Advanced queries
................

In the :doc:`getting-started` you've learned about the basic comparisons
(``==``, ``<``, ``>``, ...). In addition to these TinyDB supports the following
queries:

>>> # Existence of a field:
>>> db.search(User.name.exists())

>>> # Regex:
>>> db.search(User.name.matches('[aZ]*'))
>>> db.search(User.name.search('b+'))

>>> # Custom test:
>>> test_func = lambda s: s == 'John'
>>> db.search(User.name.test(test_func))

>>> # Custom test with parameters:
>>> def test_func(val, m, n):
>>>     return m <= val <= n
>>> db.search(User.age.test(test_func, 0, 21))
>>> db.search(User.age.test(test_func, 21, 99))

When a field contains a list, you also can use the following methods:

>>> # Using a query:
>>> # User is member of at least one admin group
>>> db.search(User.groups.any(Group.name == 'admin'))
>>> # User is only member of admin groups
>>> db.search(User.groups.all(Group.name == 'admin'))

>>> # Using a list of values:
>>> # User is member of at least one group which is 'admin' or 'user'
>>> db.search(User.groups.any(['admin', 'user']))
>>> # User's groups are all either 'admin' or 'user'
>>> db.search(User.groups.all(['admin', 'user']))

Query modifiers
...............

TinyDB also allows you to use logical operations to modify and combine
queries:

>>> # Negate a query:
>>> db.search(~ User.name == 'John')

>>> # Logical AND:
>>> db.search((User.name == 'John') & (User.age <= 30))

>>> # Logical OR:
>>> db.search((User.name == 'John') | (User.name == 'Bob'))

.. note::

    When using ``&`` or ``|``, make sure you wrap the conditions on both sides
    with parentheses or Python will mess up the comparison.

Recap
.....

Let's review the query operations we've learned:

+-------------------------------------+-----------------------------------------------------------+
| **Queries**                                                                                     |
+-------------------------------------+-----------------------------------------------------------+
| ``Query().field.exists()``          | Match any element where a field called ``field`` exists   |
+-------------------------------------+-----------------------------------------------------------+
| ``Query().field.matches(regex)``    | Match any element matching the regular expression         |
+-------------------------------------+-----------------------------------------------------------+
| ``Query().field.search(regex)``     | Match any element with substring matching the regular     |
|                                     | expression                                                |
+-------------------------------------+-----------------------------------------------------------+
| ``Query().field.test(func, *args)`` | Matches any element for which the function returns        |
|                                     | ``True``                                                  |
+-------------------------------------+-----------------------------------------------------------+
| ``Query().field.all(query | list)`` | If given a query, matches all elements where all elements |
|                                     | in the list ``field`` match the query.                    |
|                                     | If given a list, matches all elements where all elements  |
|                                     | in the list ``field`` are a member of the given list      |
+-------------------------------------+-----------------------------------------------------------+
| ``Query().field.any(query | list)`` | If given a query, matches all elements where at least one |
|                                     | element in the list ``field`` match the query.            |
|                                     | If given a list, matches all elements where at least one  |
|                                     | elements in the list ``field`` are a member of the given  |
|                                     | list                                                      |
+-------------------------------------+-----------------------------------------------------------+
| **Logical operations on queries**                                                               |
+-------------------------------------+-----------------------------------------------------------+
| ``~ query``                         | Match elements that don't match the query                 |
+-------------------------------------+-----------------------------------------------------------+
| ``(query1) & (query2)``             | Match elements that match both queries                    |
+-------------------------------------+-----------------------------------------------------------+
| ``(query1) | (query2)``             | Match elements that match at least one of the queries     |
+-------------------------------------+-----------------------------------------------------------+

Handling Data
-------------

Next, let's look at some more ways to insert, update and retrieve data from
your database.

Inserting data
..............

As already described you can insert an element using ``db.insert(...)``.
In case you want to insert multiple elements, you can use ``db.insert_multiple(...)``:

>>> db.insert_multiple([{'name': 'John', 'age': 22}, {'name': 'John', 'age': 37}])
>>> db.insert_multiple({'int': 1, 'value': i} for i in range(2))

Updating data
.............

``db.update(fields, query)`` only allows you to update an element by adding
or overwriting its values. But sometimes you may need to e.g. remove one field
or increment its value. In that case you can pass a function instead of
``fields``:

>>> from tinydb.operations import delete
>>> db.update(delete('key1'), User.name == 'John')

This will remove the key ``key1`` from all matching elements. TinyDB comes
with these operations:

- ``delete(key)``: delete a key from the element
- ``increment(key)``: increment the value of a key
- ``decrement(key)``: decrement the value of a key

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
...     result = db.search(User.name == 'John')[0]
... except IndexError:
...     pass


you can use ``db.get(...)``:

>>> db.get(User.name == 'John')
{'name': 'John', 'age': 22}
>>> db.get(User.name == 'Bobby')
None

.. caution::

    If multiple elements match the query, probably a random one of them will
    be returned!

Often you don't want to search for elements but only know whether they are
stored in the database. In this case ``db.contains(...)`` is your friend:

>>> db.contains(User.name == 'John')

In a similar manner you can look up the number of elements matching a query:

>>> db.count(User.name == 'John')
2

Recap
^^^^^

Let's summarize the ways to handle data:

+-------------------------------+---------------------------------------------------------------+
| **Inserting data**                                                                            |
+-------------------------------+---------------------------------------------------------------+
| ``db.insert_multiple(...)``   | Insert multiple elements                                      |
+-------------------------------+---------------------------------------------------------------+
| **Updating data**                                                                             |
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

>>> db.insert({'name': 'John', 'age': 22})
3
>>> db.insert_multiple([{...}, {...}, {...}])
[4, 5, 6]

In addition you can get the ID of already inserted elements using
``element.eid``. This works both with ``get`` and ``all``:

>>> el = db.get(User.name == 'John')
>>> el.eid
3
>>> el = db.all()[0]
>>> el.eid
12

Different TinyDB methods also work with IDs, namely: ``update``, ``remove``,
``contains`` and ``get``. The first two also return a list of affected IDs.

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
| ``db.get(eid=...)``              | Get the element with the given ID                             |
+----------------------------------+---------------------------------------------------------------+
| ``db.contains(eids=[...])``      | Check if the db contains elements with one of the given IDs   |
+----------------------------------+---------------------------------------------------------------+
| ``db.update({...}, eids=[...])`` | Update all elements with the given IDs                        |
+----------------------------------+---------------------------------------------------------------+
| ``db.remove(eids=[...])``        | Remove all elements with the given IDs                        |
+----------------------------------+---------------------------------------------------------------+


Tables
------

TinyDB supports working with multiple tables. They behave just the same as
the ``TinyDB`` class. To create and use a table, use ``db.table(name)``.

>>> table = db.table('table_name')
>>> table.insert({'value': True})
>>> table.all()
[{'value': True}]
>>> for row in table:
>>>     print(row)
{'value': True}

To remove a table from a database, use:

>>> db.purge_table('table_name')

If on the other hand you want to remove all tables, use the counterpart:

>>> db.purge_tables()

Finally, you can get a list with the names of all tables in your database:

>>> db.tables()
{'_default', 'table_name'}

.. _default_table:

Default Table
.............

TinyDB uses a table named ``_default`` as the default table. All operations
on the database object (like ``db.insert(...)``) operate on this table.
The name of this table can be modified by either passing ``default_table``
to the ``TinyDB`` constructor or by setting the ``DEFAULT_TABLE`` class
variable to modify the default table name for all instances:

>>> #1: for a single instance only
>>> TinyDB(storage=SomeStorage, default_table='my-default')
>>> #2: for all instances
>>> TinyDB.DEFAULT_TABLE = 'my-default'

.. _query_caching:

Query Caching
.............

TinyDB caches query result for performance. You can optimize the query cache
size by passing the ``cache_size`` to the ``table(...)`` function:

>>> table = db.table('table_name', cache_size=30)

.. hint:: You can set ``cache_size`` to ``None`` to make the cache unlimited in
   size.

Storage & Middleware
--------------------

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

.. hint::
    All arguments except for the ``storage`` argument are forwarded to the
    underlying storage. For the JSON storage you can use this to pass
    additional keyword arguments to Python's
    `json.dump(...) <https://docs.python.org/2/library/json.html#json.dump>`_
    method.

To modify the default storage for all ``TinyDB`` instances, set the
``DEFAULT_STORAGE`` class variable:

>>> TinyDB.DEFAULT_STORAGE = MemoryStorage

Middleware
..........

Middleware wraps around existing storage allowing you to customize their
behaviour.

>>> from tinydb.storages import JSONStorage
>>> from tinydb.middlewares import CachingMiddleware
>>> db = TinyDB('/path/to/db.json', storage=CachingMiddleware(JSONStorage))

.. hint::

    You can nest middleware:

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
awesome or dive deeper into TinyDB with these resources:

- Want to learn how to customize TinyDB (storages, middlewares) and what
  extensions exist? Check out :doc:`extend` and :doc:`extensions`.
- Want to study the API in detail? Read :doc:`api`.
- Interested in contributing to the TinyDB development guide? Go on to the
  :doc:`contribute`.
