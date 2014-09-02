.. TinyDB documentation master file, created by
   sphinx-quickstart on Sat Jul 13 20:14:55 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TinyDB!
==================

>>> from tinydb import TinyDB, where
>>> db = TinyDB('path/to/db.json')
>>> db.insert({'int': 1, 'char': 'a'})
>>> db.search(where('int') == 1)
[{'int': 1, 'char': 'a'}]

Welcome to TinyDB, your tiny, document oriented database optimized for your
happiness :)

User's Guide
------------

.. toctree::
   :maxdepth: 2

   Introduction <intro>
   Getting Started <getting-started>
   Advanced Usage <usage>

Extending TinyDB
----------------

.. toctree::
   :maxdepth: 2

   Extending TinyDB <extend>
   TinyDB Extensions <extensions>

API Reference
-------------

.. toctree::
   :maxdepth: 2

   api

Additional Notes
----------------

.. toctree::
   :maxdepth: 2

   changelog
   Upgrade Notes <upgrade>
