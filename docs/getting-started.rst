:tocdepth: 3

Getting Started
===============

Installing TinyDB
-----------------

To install TinyDB from PyPI, run::

    $ pip install tinydb

You can also grab the latest development version from GitHub_. After downloading
and unpacking it, you can install it using::

    $ pip install .


Basic Usage
-----------

Let's cover the basics before going more into detail. We'll start by setting up
a TinyDB database:

>>> from tinydb import TinyDB, Query
>>> db = TinyDB('db.json')

You now have a TinyDB database that stores its data in ``db.json``.
What about inserting some data? TinyDB expects the data to be Python ``dict``\s:

>>> db.insert({'type': 'apple', 'count': 7})
>>> db.insert({'type': 'peach', 'count': 3})

.. note:: The ``insert`` method returns the inserted document's ID. Read more
          about it here: :ref:`document_ids`.


Now you can get all documents stored in the database by running:

>>> db.all()
[{'count': 7, 'type': 'apple'}, {'count': 3, 'type': 'peach'}]

You can also iter over stored documents:

>>> for item in db:
>>>     print(item)
{'count': 7, 'type': 'apple'}
{'count': 3, 'type': 'peach'}

Of course you'll also want to search for specific documents. Let's try:

>>> Fruit = Query()
>>> db.search(Fruit.type == 'peach')
[{'count': 3, 'type': 'peach'}]
>>> db.search(Fruit.count > 5)
[{'count': 7, 'type': 'apple'}]


Next we'll update the ``count`` field of the apples:

>>> db.update({'count': 10}, Fruit.type == 'apple')
>>> db.all()
[{'count': 10, 'type': 'apple'}, {'count': 3, 'type': 'peach'}]


In the same manner you can also remove documents:

>>> db.remove(Fruit.count < 5)
>>> db.all()
[{'count': 10, 'type': 'apple'}]

And of course you can throw away all data to start with an empty database:

>>> db.truncate()
>>> db.all()
[]


Recap
*****

Before we dive deeper, let's recapitulate the basics:

+-------------------------------+---------------------------------------------------------------+
| **Inserting**                                                                                 |
+-------------------------------+---------------------------------------------------------------+
| ``db.insert(...)``            | Insert a document                                             |
+-------------------------------+---------------------------------------------------------------+
| **Getting data**                                                                              |
+-------------------------------+---------------------------------------------------------------+
| ``db.all()``                  | Get all documents                                             |
+-------------------------------+---------------------------------------------------------------+
| ``iter(db)``                  | Iter over all documents                                       |
+-------------------------------+---------------------------------------------------------------+
| ``db.search(query)``          | Get a list of documents matching the query                    |
+-------------------------------+---------------------------------------------------------------+
| **Updating**                                                                                  |
+-------------------------------+---------------------------------------------------------------+
| ``db.update(fields, query)``  | Update all documents matching the query to contain ``fields`` |
+-------------------------------+---------------------------------------------------------------+
| **Removing**                                                                                  |
+-------------------------------+---------------------------------------------------------------+
| ``db.remove(query)``          | Remove all documents matching the query                       |
+-------------------------------+---------------------------------------------------------------+
| ``db.truncate()``             | Remove all documents                                          |
+-------------------------------+---------------------------------------------------------------+
| **Querying**                                                                                  |
+-------------------------------+---------------------------------------------------------------+
| ``Query()``                   | Create a new query object                                     |
+-------------------------------+---------------------------------------------------------------+
| ``Query().field == 2``        | Match any document that has a key ``field`` with value        |
|                               | ``== 2`` (also possible: ``!=``, ``>``, ``>=``, ``<``, ``<=``)|
+-------------------------------+---------------------------------------------------------------+

.. References
.. _GitHub: http://github.com/msiemens/tinydb/
