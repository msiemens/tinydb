.. TinyDB documentation master file, created by
   sphinx-quickstart on Sat Jul 13 20:14:55 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TinyDB!
==================================

>>> from tinydb import TinyDB, where
>>> db = TinyDB('/path/to/db.json')
>>> db.insert({'int': 1, 'char': 'a'})
>>> db.search(where('int') == 1)
[{'int': 1, 'char': 'a'}]

Welcome to TinyDB, your tiny, document oriented database optimized for your
happiness :) If you're new here, consider reading the :doc:`introduction
<intro>`, otherwise feel free to choose one of:

.. toctree::
   :maxdepth: 1

   Introduction <intro>
   Usage <usage>
   Extend TinyDB <extend>
   Limitations <limitations>
   api
   changelog