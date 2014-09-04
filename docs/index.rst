Welcome to TinyDB!
==================

Welcome to TinyDB, your tiny, document oriented database optimized for your
happiness :)

>>> from tinydb import TinyDB, where
>>> db = TinyDB('path/to/db.json')
>>> db.insert({'int': 1, 'char': 'a'})
>>> db.search(where('int') == 1)
[{'int': 1, 'char': 'a'}]

User's Guide
------------

.. toctree::
   :maxdepth: 2

   intro
   getting-started
   usage
   contribute

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
