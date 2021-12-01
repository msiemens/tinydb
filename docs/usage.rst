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
library like `pickle <http://docs.python.org/library/pickle.html>`_ or
`PyYAML <http://pyyaml.org/>`_.

.. hint:: Opening multiple TinyDB instances on the same data (e.g. with the
   ``JSONStorage``) may result in unexpected behavior due to query caching.
   See query_caching_ on how to disable the query cache.

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

In addition, you can use arbitrary transform function where a field would be,
for example:

>>> from unidecode import unidecode
>>> db.search(User.name.map(unidecode) == 'Jose')
>>> # will match 'José' etc.

The second, traditional way of constructing queries is as follows:

>>> from tinydb import where
>>> db.search(where('field') == 'value')

Using ``where('field')`` is a shorthand for the following code:

>>> db.search(Query()['field'] == 'value')

Accessing nested fields with this syntax can be achieved like this:

>>> db.search(where('birthday').year == 1900)
>>> db.search(where('birthday')['year'] == 1900)

Advanced queries
................

In the :doc:`getting-started` you've learned about the basic comparisons
(``==``, ``<``, ``>``, ...). In addition to these TinyDB supports the following
queries:

>>> # Existence of a field:
>>> db.search(User.name.exists())

>>> # Regex:
>>> # Full item has to match the regex:
>>> db.search(User.name.matches('[aZ]*'))
>>> # Case insensitive search for 'John':
>>> import re
>>> db.search(User.name.matches('John', flags=re.IGNORECASE))
>>> # Any part of the item has to match the regex:
>>> db.search(User.name.search('b+'))

>>> # Custom test:
>>> test_func = lambda s: s == 'John'
>>> db.search(User.name.test(test_func))

>>> # Custom test with parameters:
>>> def test_func(val, m, n):
>>>     return m <= val <= n
>>> db.search(User.age.test(test_func, 0, 21))
>>> db.search(User.age.test(test_func, 21, 99))

Another case is if you have a ``dict`` where you want to find all documents
that match this ``dict``. We call this searching for a fragment:

>>> db.search(Query().fragment({'foo': True, 'bar': False}))
[{'foo': True, 'bar': False, 'foobar: 'yes!'}]

You also can search for documents where a specific field matches the fragment:

>>> db.search(Query().field.fragment({'foo': True, 'bar': False}))
[{'field': {'foo': True, 'bar': False, 'foobar: 'yes!'}]

When a field contains a list, you also can use the ``any`` and ``all`` methods.
There are two ways to use them: with lists of values and with nested queries.
Let's start with the first one. Assuming we have a user object with a groups list
like this:

>>> db.insert({'name': 'user1', 'groups': ['user']})
>>> db.insert({'name': 'user2', 'groups': ['admin', 'user']})
>>> db.insert({'name': 'user3', 'groups': ['sudo', 'user']})

Now we can use the following queries:

>>> # User's groups include at least one value from ['admin', 'sudo']
>>> db.search(User.groups.any(['admin', 'sudo']))
[{'name': 'user2', 'groups': ['admin', 'user']},
 {'name': 'user3', 'groups': ['sudo', 'user']}]
>>>
>>> # User's groups include all values from ['admin', 'user']
>>> db.search(User.groups.all(['admin', 'user']))
[{'name': 'user2', 'groups': ['admin', 'user']}]

In some cases you may want to have more complex ``any``/``all`` queries.
This is where nested queries come in as helpful. Let's set up a table like this:

>>> Group = Query()
>>> Permission = Query()
>>> groups = db.table('groups')
>>> groups.insert({
        'name': 'user',
        'permissions': [{'type': 'read'}]})
>>> groups.insert({
        'name': 'sudo',
        'permissions': [{'type': 'read'}, {'type': 'sudo'}]})
>>> groups.insert({
        'name': 'admin',
        'permissions': [{'type': 'read'}, {'type': 'write'}, {'type': 'sudo'}]})

Now let's search this table using nested ``any``/``all`` queries:

>>> # Group has a permission with type 'read'
>>> groups.search(Group.permissions.any(Permission.type == 'read'))
[{'name': 'user', 'permissions': [{'type': 'read'}]},
 {'name': 'sudo', 'permissions': [{'type': 'read'}, {'type': 'sudo'}]},
 {'name': 'admin', 'permissions':
        [{'type': 'read'}, {'type': 'write'}, {'type': 'sudo'}]}]
>>> # Group has ONLY permission 'read'
>>> groups.search(Group.permissions.all(Permission.type == 'read'))
[{'name': 'user', 'permissions': [{'type': 'read'}]}]


As you can see, ``any`` tests if there is *at least one* document matching
the query while ``all`` ensures *all* documents match the query.

The opposite operation, checking if a single item is contained in a list,
is also possible using ``one_of``:

>>> db.search(User.name.one_of(['jane', 'john']))

Query modifiers
...............

TinyDB also allows you to use logical operations to modify and combine
queries:

>>> # Negate a query:
>>> db.search(~ (User.name == 'John'))

>>> # Logical AND:
>>> db.search((User.name == 'John') & (User.age <= 30))

>>> # Logical OR:
>>> db.search((User.name == 'John') | (User.name == 'Bob'))

.. note::

    When using ``&`` or ``|``, make sure you wrap the conditions on both sides
    with parentheses or Python will mess up the comparison.

    Also, when using negation (``~``) you'll have to wrap the query you want
    to negate in parentheses.

    The reason for these requirements is that Python's binary operators that are
    used for query modifiers have a higher operator precedence than comparison
    operators. Simply put, ``~ User.name == 'John'`` is parsed by Python as
    ``(~User.name) == 'John'`` instead of ``~(User.name == 'John')``. See also the
    Python `docs on operator precedence
    <https://docs.python.org/3/reference/expressions.html#operator-precedence>`_
    for details.

Recap
.....

Let's review the query operations we've learned:

+-------------------------------------+-------------------------------------------------------------+
| **Queries**                                                                                       |
+-------------------------------------+-------------------------------------------------------------+
| ``Query().field.exists()``          | Match any document where a field called ``field`` exists    |
+-------------------------------------+-------------------------------------------------------------+
| ``Query().field.matches(regex)``    | Match any document with the whole field matching the        |
|                                     | regular expression                                          |
+-------------------------------------+-------------------------------------------------------------+
| ``Query().field.search(regex)``     | Match any document with a substring of the field matching   |
|                                     | the regular expression                                      |
+-------------------------------------+-------------------------------------------------------------+
| ``Query().field.test(func, *args)`` | Matches any document for which the function returns         |
|                                     | ``True``                                                    |
+-------------------------------------+-------------------------------------------------------------+
| ``Query().field.all(query | list)`` | If given a query, matches all documents where all documents |
|                                     | in the list ``field`` match the query.                      |
|                                     | If given a list, matches all documents where all documents  |
|                                     | in the list ``field`` are a member of the given list        |
+-------------------------------------+-------------------------------------------------------------+
| ``Query().field.any(query | list)`` | If given a query, matches all documents where at least one  |
|                                     | document in the list ``field`` match the query.             |
|                                     | If given a list, matches all documents where at least one   |
|                                     | documents in the list ``field`` are a member of the given   |
|                                     | list                                                        |
+-------------------------------------+-------------------------------------------------------------+
| ``Query().field.one_of(list)``      | Match if the field is contained in the list                 |
+-------------------------------------+-------------------------------------------------------------+
| **Logical operations on queries**                                                                 |
+-------------------------------------+-------------------------------------------------------------+
| ``~ (query)``                       | Match documents that don't match the query                  |
+-------------------------------------+-------------------------------------------------------------+
| ``(query1) & (query2)``             | Match documents that match both queries                     |
+-------------------------------------+-------------------------------------------------------------+
| ``(query1) | (query2)``             | Match documents that match at least one of the queries      |
+-------------------------------------+-------------------------------------------------------------+

Handling Data
-------------

Next, let's look at some more ways to insert, update and retrieve data from
your database.

Inserting data
..............

As already described you can insert a document using ``db.insert(...)``.
In case you want to insert multiple documents, you can use ``db.insert_multiple(...)``:

>>> db.insert_multiple([
        {'name': 'John', 'age': 22},
        {'name': 'John', 'age': 37}])
>>> db.insert_multiple({'int': 1, 'value': i} for i in range(2))

Also in some cases it may be useful to specify the document ID yourself when
inserting data. You can do that by using the :class:`~tinydb.table.Document`
class:

>>> db.insert(Document({'name': 'John', 'age': 22}, doc_id=12))
12

Updating data
.............

Sometimes you want to update all documents in your database. In this case, you
can leave out the ``query`` argument:

>>> db.update({'foo': 'bar'})

When passing a dict to ``db.update(fields, query)``, it only allows you to
update a document by adding or overwriting its values. But sometimes you may
need to e.g. remove one field or increment its value. In that case you can
pass a function instead of ``fields``:

>>> from tinydb.operations import delete
>>> db.update(delete('key1'), User.name == 'John')

This will remove the key ``key1`` from all matching documents. TinyDB comes
with these operations:

- ``delete(key)``: delete a key from the document
- ``increment(key)``: increment the value of a key
- ``decrement(key)``: decrement the value of a key
- ``add(key, value)``: add ``value`` to the value of a key (also works for strings)
- ``subtract(key, value)``: subtract ``value`` from the value of a key
- ``set(key, value)``: set ``key`` to ``value``

Of course you also can write your own operations:

>>> def your_operation(your_arguments):
...     def transform(doc):
...         # do something with the document
...         # ...
...     return transform
...
>>> db.update(your_operation(arguments), query)

In order to perform multiple update operations at once, you can use the
``update_multiple`` method like this:

>>> db.update_multiple([
...     ({'int': 2}, where('char') == 'a'),
...     ({'int': 4}, where('char') == 'b'),
... ])

You also can use mix normal updates with update operations:

>>> db.update_multiple([
...     ({'int': 2}, where('char') == 'a'),
...     ({delete('int'), where('char') == 'b'),
... ])

Data access and modification
----------------------------

Upserting data
..............

In some cases you'll need a mix of both ``update`` and ``insert``: ``upsert``.
This operation is provided a document and a query. If it finds any documents
matching the query, they will be updated with the data from the provided document.
On the other hand, if no matching document is found, it inserts the provided
document into the table:

>>> db.upsert({'name': 'John', 'logged-in': True}, User.name == 'John')

This will update all users with the name John to have ``logged-in`` set to ``True``.
If no matching user is found, a new document is inserted with both the name set
and the ``logged-in`` flag.

To use the ID of the document as matching criterion a :class:`~tinydb.table.Document`
with ``doc_id`` is passed instead of a query:

>>> db.upsert(Document({'name': 'John', 'logged-in': True}, doc_id=12))

Retrieving data
...............

There are several ways to retrieve data from your database. For instance you
can get the number of stored documents:

>>> len(db)
3

.. hint::
    This will return the number of documents in the default table
    (see the notes on the :ref:`default table <default_table>`).

Then of course you can use ``db.search(...)`` as described in the :doc:`getting-started`
section. But sometimes you want to get only one matching document. Instead of using

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

    If multiple documents match the query, probably a random one of them will
    be returned!

Often you don't want to search for documents but only know whether they are
stored in the database. In this case ``db.contains(...)`` is your friend:

>>> db.contains(User.name == 'John')

In a similar manner you can look up the number of documents matching a query:

>>> db.count(User.name == 'John')
2

Recap
^^^^^

Let's summarize the ways to handle data:

+-------------------------------+---------------------------------------------------------------+
| **Inserting data**                                                                            |
+-------------------------------+---------------------------------------------------------------+
| ``db.insert_multiple(...)``   | Insert multiple documents                                     |
+-------------------------------+---------------------------------------------------------------+
| **Updating data**                                                                             |
+-------------------------------+---------------------------------------------------------------+
| ``db.update(operation, ...)`` | Update all matching documents with a special operation        |
+-------------------------------+---------------------------------------------------------------+
| **Retrieving data**                                                                           |
+-------------------------------+---------------------------------------------------------------+
| ``len(db)``                   | Get the number of documents in the database                   |
+-------------------------------+---------------------------------------------------------------+
| ``db.get(query)``             | Get one document matching the query                           |
+-------------------------------+---------------------------------------------------------------+
| ``db.contains(query)``        | Check if the database contains a matching document            |
+-------------------------------+---------------------------------------------------------------+
| ``db.count(query)``           | Get the number of matching documents                          |
+-------------------------------+---------------------------------------------------------------+


.. note::

    This was a new feature in v3.6.0

.. _document_ids:

Using Document IDs
------------------

Internally TinyDB associates an ID with every document you insert. It's returned
after inserting a document:

>>> db.insert({'name': 'John', 'age': 22})
3
>>> db.insert_multiple([{...}, {...}, {...}])
[4, 5, 6]

In addition you can get the ID of already inserted documents using
``document.doc_id``. This works both with ``get`` and ``all``:

>>> el = db.get(User.name == 'John')
>>> el.doc_id
3
>>> el = db.all()[0]
>>> el.doc_id
1
>>> el = db.all()[-1]
>>> el.doc_id
12

Different TinyDB methods also work with IDs, namely: ``update``, ``remove``,
``contains`` and ``get``. The first two also return a list of affected IDs.

>>> db.update({'value': 2}, doc_ids=[1, 2])
>>> db.contains(doc_id=1)
True
>>> db.remove(doc_ids=[1, 2])
>>> db.get(doc_id=3)
{...}

Using ``doc_id`` instead of ``Query()`` again is slightly faster in operation.

Recap
.....

Let's sum up the way TinyDB supports working with IDs:

+-------------------------------------+------------------------------------------------------------+
| **Getting a document's ID**                                                                      |
+-------------------------------------+------------------------------------------------------------+
| ``db.insert(...)``                  | Returns the inserted document's ID                         |
+-------------------------------------+------------------------------------------------------------+
| ``db.insert_multiple(...)``         | Returns the inserted documents' ID                         |
+-------------------------------------+------------------------------------------------------------+
| ``document.doc_id``                 | Get the ID of a document fetched from the db               |
+-------------------------------------+------------------------------------------------------------+
| **Working with IDs**                                                                             |
+-------------------------------------+------------------------------------------------------------+
| ``db.get(doc_id=...)``              | Get the document with the given ID                         |
+-------------------------------------+------------------------------------------------------------+
| ``db.contains(doc_id=...)``         | Check if the db contains a document with the given         |
|                                     | IDs                                                        |
+-------------------------------------+------------------------------------------------------------+
| ``db.update({...}, doc_ids=[...])`` | Update all documents with the given IDs                    |
+-------------------------------------+------------------------------------------------------------+
| ``db.remove(doc_ids=[...])``        | Remove all documents with the given IDs                    |
+-------------------------------------+------------------------------------------------------------+


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

>>> db.drop_table('table_name')

If on the other hand you want to remove all tables, use the counterpart:

>>> db.drop_tables()

Finally, you can get a list with the names of all tables in your database:

>>> db.tables()
{'_default', 'table_name'}

.. _default_table:

Default Table
.............

TinyDB uses a table named ``_default`` as the default table. All operations
on the database object (like ``db.insert(...)``) operate on this table.
The name of this table can be modified by setting the ``default_table_name``
class variable to modify the default table name for all instances:

>>> #1: for a single instance only
>>> db = TinyDB(storage=SomeStorage)
>>> db.default_table_name = 'my-default'
>>> #2: for all instances
>>> TinyDB.default_table_name = 'my-default'

.. _query_caching:

Query Caching
.............

TinyDB caches query result for performance. That way re-running a query won't
have to read the data from the storage as long as the database hasn't been
modified. You can optimize the query cache size by passing the ``cache_size``
to the ``table(...)`` function:

>>> table = db.table('table_name', cache_size=30)

.. hint:: You can set ``cache_size`` to ``None`` to make the cache unlimited in
   size. Also, you can set ``cache_size`` to 0 to disable it.

.. hint:: It's not possible to open the same table multiple times with different
   settings. After the first invocation, all the subsequent calls will return
   the same table with the same settings as the first one.

.. hint:: The TinyDB query cache doesn't check if the underlying storage
   that the database uses has been modified by an external process. In this
   case the query cache may return outdated results. To clear the cache and
   read data from the storage again you can use ``db.clear_cache()``.

.. hint:: When using an unlimited cache size and ``test()`` queries, TinyDB
   will store a reference to the test function. As a result of that behavior
   long-running applications that use ``lambda`` functions as a test function
   may experience memory leaks.

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
    method. For example, you can set it to create prettified JSON files like
    this:

    >>> db = TinyDB('db.json', sort_keys=True, indent=4, separators=(',', ': '))

To modify the default storage for all ``TinyDB`` instances, set the
``default_storage_class`` class variable:

>>> TinyDB.default_storage_class = MemoryStorage

In case you need to access the storage instance directly, you can use the
``storage`` property of your TinyDB instance. This may be useful to call
method directly on the storage or middleware:

>>> db = TinyDB(storage=CachingMiddleware(MemoryStorage))
<tinydb.middlewares.CachingMiddleware at 0x10991def0>
>>> db.storage.flush()

Middleware
..........

Middleware wraps around existing storage allowing you to customize their
behaviour.

>>> from tinydb.storages import JSONStorage
>>> from tinydb.middlewares import CachingMiddleware
>>> db = TinyDB('/path/to/db.json', storage=CachingMiddleware(JSONStorage))

.. hint::
    You can nest middleware:

    >>> db = TinyDB('/path/to/db.json',
                    storage=FirstMiddleware(SecondMiddleware(JSONStorage)))

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

.. _mypy_type_checking:

MyPy Type Checking
------------------

TinyDB comes with type annotations that MyPy can use to make sure you're using
the API correctly. Unfortunately, MyPy doesn't understand all code patterns
that TinyDB uses. For that reason TinyDB ships a MyPy plugin that helps
correctly type checking code that uses TinyDB. To use it, add it to the
plugins list in the `MyPy configuration file
<https://mypy.readthedocs.io/en/latest/config_file.html>`_
(typically located in ``setup.cfg`` or ``mypy.ini``):

.. code-block:: ini

    [mypy]
    plugins = tinydb.mypy_plugin

What's next
-----------

Congratulations, you've made through the user guide! Now go and build something
awesome or dive deeper into TinyDB with these resources:

- Want to learn how to customize TinyDB (storages, middlewares) and what
  extensions exist? Check out :doc:`extend` and :doc:`extensions`.
- Want to study the API in detail? Read :doc:`api`.
- Interested in contributing to the TinyDB development guide? Go on to the
  :doc:`contribute`.
