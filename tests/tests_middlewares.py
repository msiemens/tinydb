from threading import Thread

from tinydb.middlewares import CachingMiddleware, ConcurrencyMiddleware
from tinydb.storages import MemoryStorage

from nose.tools import *


backend = None
element = {'none': [None, None], 'int': 42, 'float': 3.1415899999999999,
           'list': ['LITE', 'RES_ACID', 'SUS_DEXT'],
           'dict': {'hp': 13, 'sp': 5},
           'bool': [True, False, True, False]}


def setup_caching():
    global backend
    backend = CachingMiddleware(MemoryStorage)
    backend()  # Initialize MemoryStorage


@with_setup(setup_caching)
def test_caching():
    # Write contents
    backend.write(element)

    # Verify contents
    assert_equal(element, backend.read())


def setup_caching_write_many():
    global backend
    backend = CachingMiddleware(MemoryStorage)
    backend.WRITE_CACHE_SIZE = 3
    backend()  # Initialize MemoryStorage


@with_setup(setup_caching_write_many)
def test_caching_write_many():
    # Write contents
    global backend

    for x in xrange(4):
        backend.write(element)

    storage = backend.storage

    # Verify contents: Storage shouldn't be empty
    assert_not_equal('', storage.memory)
    assert_not_equal('{}', storage.memory)



def setup_caching_write():
    global backend
    backend = CachingMiddleware(MemoryStorage)
    backend()  # Initialize MemoryStorage


@with_setup(setup_caching_write)
def test_caching_write():
    # Write contents
    global backend
    backend.write(element)

    storage = backend.storage
    backend = None  # Delete backend

    # Verify contents: Storage shouldn't be empty
    assert_not_equal('', storage.memory)
    assert_not_equal('{}', storage.memory)


def setup_concurrency():
    global backend
    backend = ConcurrencyMiddleware(MemoryStorage)
    backend()  # Initialize MemoryStorage


@with_setup(setup_concurrency)
def test_concurrency():
    global backend
    threads = []
    run_count = 42

    class WriteThread(Thread):
        def run(self):
            try:
                current_contents = backend.read()
            except ValueError:
                current_contents = []
            backend.write(current_contents + [element])

    # Start threads
    for i in xrange(run_count):
        thread = WriteThread()
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for t in threads:
        t.join()

    # Verify contents: Storage shouldn't be empty
    assert_equal(len(backend.storage.memory), run_count)
