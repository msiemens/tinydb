Extensions
==========

.. _tinyrecord:

``tinyrecord``
**************

| **Repo:**        https://github.com/eugene-eeo/tinyrecord
| **Status:**      *experimental*
| **Description:** Tinyrecord is a library which implements experimental atomic
                   transaction support for the TinyDB NoSQL database. It uses a
                   record-first then execute architecture which allows us to
                   minimize the time that we are within a thread lock.

``tinyindex``
*************

| **Repo:**        https://github.com/eugene-eeo/tinyindex
| **Status:**      *experimental*
| **Description:** Document indexing for TinyDB. Basically ensures deterministic
                   (as long as there aren't any changes to the table) yielding
                   of documents.
