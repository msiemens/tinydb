from threading import Thread

from tinydb.middlewares import CachingMiddleware, ConcurrencyMiddleware
from tinydb.storages import MemoryStorage

from nose.tools import *

if not 'xrange' in dir(__builtins__):
    xrange = range  # Python 3 support


storage = None
element = {'none': [None, None], 'int': 42, 'float': 3.1415899999999999,
           'list': ['LITE', 'RES_ACID', 'SUS_DEXT'],
           'dict': {'hp': 13, 'sp': 5},
           'bool': [True, False, True, False]}


def setup_caching():
    global storage
    _storage = CachingMiddleware(MemoryStorage)
    storage = _storage()  # Initialize MemoryStorage


@with_setup(setup_caching)
def test_caching():
    # Write contents
    storage.write(element)

    # Verify contents
    assert_equal(element, storage.read())


def setup_caching_write_many():
    global storage
    storage = CachingMiddleware(MemoryStorage)
    storage.WRITE_CACHE_SIZE = 3
    storage()  # Initialize MemoryStorage


@with_setup(setup_caching_write_many)
def test_caching_write_many():
    # Write contents
    global storage

    for x in xrange(4):
        storage.write(element)

    # Verify contents: Storage shouldn't be empty
    assert_not_equal('', storage.memory)
    assert_not_equal('{}', storage.memory)


def setup_caching_flush():
    global storage
    _storage = CachingMiddleware(MemoryStorage)
    storage = _storage()  # Initialize MemoryStorage


@with_setup(setup_caching_flush)
def test_caching_flush():
    # Write contents
    global storage

    for x in xrange(5):
        storage.write(element)

    storage.flush()

    # Verify contents: Storage shouldn't be empty
    assert_not_equal('', storage.memory)
    assert_not_equal('{}', storage.memory)


def setup_caching_write():
    global storage
    _storage = CachingMiddleware(MemoryStorage)
    storage = _storage()  # Initialize MemoryStorage


@with_setup(setup_caching_write)
def test_caching_write():
    # Write contents
    global storage
    storage.write(element)

    _storage = storage.storage
    storage = None  # Delete storage

    # Verify contents: Storage shouldn't be empty
    assert_not_equal('', _storage.memory)
    assert_not_equal('{}', _storage.memory)


def setup_concurrency():
    global storage
    _storage = ConcurrencyMiddleware(MemoryStorage)
    storage = _storage()  # Initialize MemoryStorage


@with_setup(setup_concurrency)
def test_concurrency():
    global storage
    threads = []
    run_count = 5

    class WriteThread(Thread):
        def run(self):
            try:
                current_contents = storage.read()
            except ValueError:
                current_contents = []
            storage.write(current_contents + [element])

    # Start threads
    for i in xrange(run_count):
        thread = WriteThread()
        threads.append(thread)

    for thread in threads:
        thread.start()

    # Wait for all threads to finish
    for t in threads:
        t.join()

    # Verify contents: Storage shouldn't be empty
    assert_equal(len(storage.memory), run_count)


def setup_nested():
    global storage
    _storage = ConcurrencyMiddleware(CachingMiddleware(MemoryStorage))
    storage = _storage()  # Initialize MemoryStorage


@with_setup(setup_nested)
def test_nested():
    global storage
    # Write contents
    storage.write(element)

    # Verify contents
    assert_equal(element, storage.read())
