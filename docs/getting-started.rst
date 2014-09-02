:tocdepth: 3

Getting Started
===============

Installing TinyDB
-----------------

To install TinyDB from PyPI, run::

    $ pip install tinydb

You can also grab the latest development version from GitHub_. After downloading
and unpacking it, you can install it using::

    $ python setup.py install


Basic Usage
-----------

Let's cover the basics before going more into detail. We'll start by setting up
a TinyDB database:

>>> from tinydb import TinyDB, where
>>> db = TinyDB('db.json')

You now have a TinyDB database that stores its data in ``db.json``.
What about inserting some data? TinyDB expects the data to be Python ``dict``\s:

>>> db.insert({'type': 'apple', 'count': 7})
1
>>> db.insert({'type': 'peach', 'count': 3})
2

.. note:: The ``insert`` method returns the inserted element's ID. Read more
          about it here: :ref:`element_ids`.


Now you can get all elements stored in the database by running:

>>> db.all()
[{'count': 7, 'type': 'apple'}, {'count': 3, 'type': 'peach'}]

Of course you'll also want to search for specific elements. Let's try:

>>> db.search(where('type') == 'peach')
[{'count': 3, 'type': 'peach'}]
>>> db.search(where('count') > 5)
[{'count': 7, 'type': 'apple'}]


Next we'll update the ``count`` field of the apples:

>>> db.update({'count': 10}, where('type') == 'apple')
>>> db.all()
[{'count': 10, 'type': 'apple'}, {'count': 3, 'type': 'peach'}]


In the same manner you can also remove elements:

>>> db.remove(where('count') < 5)
>>> db.all()
[{'count': 10, 'type': 'apple'}]

And of course you can throw away all data to start with an empty database:

>>> db.purge()
>>> db.all()
[]


Recap
-----

Before we dive deeper, let's recapitulate the basics:

+-------------------------------+---------------------------------------------------------------+
| **Inserting**                                                                                 |
+-------------------------------+---------------------------------------------------------------+
| ``db.insert(...)``            | Insert an element                                             |
+-------------------------------+---------------------------------------------------------------+
| **Getting data**                                                                              |
+-------------------------------+---------------------------------------------------------------+
| ``db.all()``                  | Get all elements                                              |
+-------------------------------+---------------------------------------------------------------+
| ``db.search(query)``          | Get a list of elements matching the query                     |
+-------------------------------+---------------------------------------------------------------+
| **Updating**                                                                                  |
+-------------------------------+---------------------------------------------------------------+
| ``db.update(fields, query)``  | Update all elements matching the query to contain ``fields``  |
+-------------------------------+---------------------------------------------------------------+
| **Removing**                                                                                  |
+-------------------------------+---------------------------------------------------------------+
| ``db.remove(query)``          | Remove all elements matching the query                        |
+-------------------------------+---------------------------------------------------------------+
| ``db.purge()``                | Purge all elements                                            |
+-------------------------------+---------------------------------------------------------------+
| **Querying**                                                                                  |
+-------------------------------+---------------------------------------------------------------+
| ``where('field') == 2``       | Match any element that has a key ``field`` with value         |
|                               | ``== 2`` (also possible: ``!=`` ``>`` ``>=`` ``<`` ``<=``)    |
+-------------------------------+---------------------------------------------------------------+

.. References
.. _GitHub: http://github.com/msiemens/tinydb/
