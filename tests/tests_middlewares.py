import os
import tempfile
import random
from tinydb.middlewares import CachingMiddleware

random.seed()

from nose.tools import *

from tinydb.storages import JSONStorage, MemoryStorage

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
    print storage.memory
    assert_not_equal('', storage.memory)
    assert_not_equal('{}', storage.memory)
