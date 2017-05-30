import os
import random
import tempfile

import pytest


random.seed()

from tinydb import TinyDB, where
from tinydb.storages import JSONStorage, MemoryStorage, Storage

element = {'none': [None, None], 'int': 42, 'float': 3.1415899999999999,
           'list': ['LITE', 'RES_ACID', 'SUS_DEXT'],
           'dict': {'hp': 13, 'sp': 5},
           'bool': [True, False, True, False]}


def test_json(tmpdir):
    # Write contents
    path = str(tmpdir.join('test.db'))
    storage = JSONStorage(path)
    storage.write(element)

    # Verify contents
    assert element == storage.read()
    storage.close()


def test_json_kwargs(tmpdir):
    db_file = tmpdir.join('test.db')
    db = TinyDB(str(db_file), sort_keys=True, indent=4, separators=(',', ': '))

    # Write contents
    db.insert({'b': 1})
    db.insert({'a': 1})

    assert db_file.read() == '''{
    "_default": {
        "1": {
            "b": 1
        },
        "2": {
            "a": 1
        }
    }
}'''
    db.close()


def test_json_readwrite(tmpdir):
    """
    Regression test for issue #1
    """
    path = str(tmpdir.join('test.db'))

    # Create TinyDB instance
    db = TinyDB(path, storage=JSONStorage)

    item = {'name': 'A very long entry'}
    item2 = {'name': 'A short one'}

    get = lambda s: db.get(where('name') == s)

    db.insert(item)
    assert get('A very long entry') == item

    db.remove(where('name') == 'A very long entry')
    assert get('A very long entry') is None

    db.insert(item2)
    assert get('A short one') == item2

    db.remove(where('name') == 'A short one')
    assert get('A short one') is None

    db.close()


def test_create_dirs():
    temp_dir = tempfile.gettempdir()
    db_dir = ''
    db_file = ''

    while True:
        dname = os.path.join(temp_dir, str(random.getrandbits(20)))
        if not os.path.exists(dname):
            db_dir = dname
            db_file = os.path.join(db_dir, 'db.json')
            break

    db_conn = JSONStorage(db_file, create_dirs=True)
    db_conn.close()

    db_exists = os.path.exists(db_file)

    os.remove(db_file)
    os.rmdir(db_dir)

    assert db_exists


def test_json_invalid_directory():
    with pytest.raises(IOError):
        with TinyDB('/this/is/an/invalid/path/db.json', storage=JSONStorage):
            pass


def test_in_memory():
    # Write contents
    storage = MemoryStorage()
    storage.write(element)

    # Verify contents
    assert element == storage.read()

    # Test case for #21
    other = MemoryStorage()
    other.write({})
    assert other.read() != storage.read()


def test_in_memory_close():
    with TinyDB(storage=MemoryStorage) as db:
        db.insert({})


def test_custom():
    # noinspection PyAbstractClass
    class MyStorage(Storage):
        pass

    with pytest.raises(TypeError):
        MyStorage()
