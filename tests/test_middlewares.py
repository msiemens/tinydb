import os

from tinydb import TinyDB
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage, JSONStorage

if 'xrange' not in dir(__builtins__):
    # noinspection PyShadowingBuiltins
    xrange = range  # Python 3 support

doc = {'none': [None, None], 'int': 42, 'float': 3.1415899999999999,
       'list': ['LITE', 'RES_ACID', 'SUS_DEXT'],
       'dict': {'hp': 13, 'sp': 5},
       'bool': [True, False, True, False]}


def test_caching(storage):
    # Write contents
    storage.write(doc)

    # Verify contents
    assert doc == storage.read()


def test_caching_read():
    db = TinyDB(storage=CachingMiddleware(MemoryStorage))
    assert db.all() == []


def test_caching_write_many(storage):
    storage.WRITE_CACHE_SIZE = 3

    # Storage should be still empty
    assert storage.memory is None

    # Write contents
    for x in xrange(2):
        storage.write(doc)
        assert storage.memory is None  # Still cached

    storage.write(doc)

    # Verify contents: Cache should be emptied and written to storage
    assert storage.memory


def test_caching_flush(storage):
    # Write contents
    for _ in range(CachingMiddleware.WRITE_CACHE_SIZE - 1):
        storage.write(doc)

    # Not yet flushed...
    assert storage.memory is None

    storage.write(doc)

    # Verify contents: Cache should be emptied and written to storage
    assert storage.memory


def test_caching_flush_manually(storage):
    # Write contents
    storage.write(doc)

    storage.flush()

    # Verify contents: Cache should be emptied and written to storage
    assert storage.memory


def test_caching_write(storage):
    # Write contents
    storage.write(doc)

    storage.close()

    # Verify contents: Cache should be emptied and written to storage
    assert storage.storage.memory


def test_nested():
    storage = CachingMiddleware(MemoryStorage)
    storage()  # Initialization

    # Write contents
    storage.write(doc)

    # Verify contents
    assert doc == storage.read()


def test_caching_json_write(tmpdir):
    path = str(tmpdir.join('test.db'))

    with TinyDB(path, storage=CachingMiddleware(JSONStorage)) as db:
        db.insert({'key': 'value'})

    # Verify database filesize
    statinfo = os.stat(path)
    assert statinfo.st_size != 0

    # Assert JSON file has been closed
    assert db._storage._handle.closed

    del db

    # Repoen database
    with TinyDB(path, storage=CachingMiddleware(JSONStorage)) as db:
        assert db.all() == [{'key': 'value'}]
