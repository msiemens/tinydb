from threading import Thread

from tinydb.middlewares import CachingMiddleware, ConcurrencyMiddleware
from tinydb.storages import MemoryStorage

if not 'xrange' in dir(__builtins__):
    xrange = range  # Python 3 support


element = {'none': [None, None], 'int': 42, 'float': 3.1415899999999999,
           'list': ['LITE', 'RES_ACID', 'SUS_DEXT'],
           'dict': {'hp': 13, 'sp': 5},
           'bool': [True, False, True, False]}


def test_caching(storage):
    # Write contents
    storage.write(element)

    # Verify contents
    assert element == storage.read()


def test_caching_write_many(storage):
    storage.WRITE_CACHE_SIZE = 3

    # Storage should be still empty
    assert storage.memory is None

    # Write contents
    for x in xrange(2):
        storage.write(element)
        assert storage.memory is None  # Still cached

    storage.write(element)

    # Verify contents: Cache should be emptied and written to storage
    assert storage.memory


def test_caching_flush(storage):
    # Write contents
    storage.write(element)

    storage.flush()

    # Verify contents: Cache should be emptied and written to storage
    assert storage.memory


def test_caching_write(storage):
    # Write contents
    storage.write(element)

    storage.__del__()  # Assume, the storage got deleted

    # Verify contents: Cache should be emptied and written to storage
    assert storage.storage.memory


def test_concurrency():
    storage = ConcurrencyMiddleware(MemoryStorage)
    storage()  # Initialization

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
    assert len(storage.memory) == run_count


def test_nested():
    storage = ConcurrencyMiddleware(CachingMiddleware(MemoryStorage))
    storage()  # Initialization

    # Write contents
    storage.write(element)

    # Verify contents
    assert element == storage.read()
