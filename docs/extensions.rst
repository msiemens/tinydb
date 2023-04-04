Extensions
==========

Here are some extensions that might be useful to you:

``aiotinydb``
*************

| **Repo:**        https://github.com/ASMfreaK/aiotinydb
| **Status:**      *stable*
| **Description:** asyncio compatibility shim for TinyDB. Enables usage of
                   TinyDB in asyncio-aware contexts without slow synchronous
                   IO.


``BetterJSONStorage``
*********************

| **Repo:**        https://github.com/MrPigss/BetterJSONStorage
| **Status:**      *stable*
| **Description:** BetterJSONStorage is a faster 'Storage Type' for TinyDB. It
                   uses the faster Orjson library for parsing the JSON and BLOSC
                   for compression.


``tinydb-appengine``
********************

| **Repo:**        https://github.com/imalento/tinydb-appengine
| **Status:**      *stable*
| **Description:** ``tinydb-appengine`` provides TinyDB storage for
                   App Engine. You can use JSON readonly.


``tinydb-serialization``
************************

| **Repo:**        https://github.com/msiemens/tinydb-serialization
| **Status:**      *stable*
| **Description:** ``tinydb-serialization`` provides serialization for objects
                   that TinyDB otherwise couldn't handle.


``tinydb-smartcache``
*********************

| **Repo:**        https://github.com/msiemens/tinydb-smartcache
| **Status:**      *stable*
| **Description:** ``tinydb-smartcache`` provides a smart query cache for
                   TinyDB. It updates the query cache when
                   inserting/removing/updating documents so the cache doesn't
                   get invalidated. It's useful if you perform lots of queries
                   while the data changes only little.


``TinyDBTimestamps``
********************

| **Repo:**        https://github.com/pachacamac/TinyDBTimestamps
| **Status:**      *experimental*
| **Description:** Automatically add create at/ update at timestamps to TinyDB
                   documents.


``tinyindex``
*************

| **Repo:**        https://github.com/eugene-eeo/tinyindex
| **Status:**      *experimental*
| **Description:** Document indexing for TinyDB. Basically ensures deterministic
                   (as long as there aren't any changes to the table) yielding
                   of documents.


``tinymongo``
*************

| **Repo:**        https://github.com/schapman1974/tinymongo
| **Status:**      *experimental*
| **Description:** A simple wrapper that allows to use TinyDB as a flat file
                   drop-in replacement for MongoDB.


``TinyMP``
*************

| **Repo:**        https://github.com/alshapton/TinyMP
| **Status:**      *no longer maintained*
| **Description:** A MessagePack-based storage extension to tinydb using
                   http://msgpack.org

.. _tinyrecord:

``tinyrecord``
**************

| **Repo:**        https://github.com/eugene-eeo/tinyrecord
| **Status:**      *stable*
| **Description:** Tinyrecord is a library which implements experimental atomic
                   transaction support for the TinyDB NoSQL database. It uses a
                   record-first then execute architecture which allows us to
                   minimize the time that we are within a thread lock.
