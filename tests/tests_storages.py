import os
import tempfile
import random
random.seed()

from nose.tools import *

from tinydb.storages import JSONStorage, MemoryStorage

path = None
element = {'none': [None, None], 'int': 42, 'float': 3.1415899999999999,
           'list': ['LITE', 'RES_ACID', 'SUS_DEXT'],
           'dict': {'hp': 13, 'sp': 5},
           'bool': [True, False, True, False]}


def setup():
    global path, element

    # Generate temp file
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.file.close()  # Close file handle
    path = tmp.name


def teardown():
    # Cleanup
    os.unlink(path)


def test_yaml():
    # Write contents
    backend = JSONStorage(path)
    backend.write(element)

    # Verify contents
    assert_equal(element, backend.read())


def test_in_memory():
    # Write contents
    backend = MemoryStorage()
    backend.write(element)

    # Verify contents
    assert_equal(element, backend.read())
