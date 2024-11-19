import pytest
import os
from threading import Thread
from tinydb import TinyDB, where, Query
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage, MemoryStorage, Storage

doc = {
    'none': [None, None],
    'int': 42,
    'float': 3.1415899999999999,
    'list': ['LITE', 'RES_ACID', 'SUS_DEXT'],
    'dict': {'hp': 13, 'sp': 5},
    'bool': [True, False, True, False]
}

# 1. Tests for empty or null inputs
def test_empty_insertion(db: TinyDB):
    db.drop_tables()
    db.insert({})
    assert len(db) == 1
    assert db.all() == [{}]

def test_empty_search(db: TinyDB):
    db.drop_tables()
    db.insert({"key": "value"})
    results = db.search(where('nonexistent').exists())
    assert results == []

def test_insert_none(db: TinyDB):
    with pytest.raises(ValueError):
        db.insert(None)


# 2. Large data insertion
def test_large_document(db: TinyDB):
    large_data = {"key": "value" * 10**6}  
    db.insert(large_data)
    result = db.get(where('key').exists())
    assert result is not None
    assert len(result['key']) == len("value"*10**6)

# 3. Special keys and values
def test_special_keys(db: TinyDB):
    db.insert({"": "empty_key"})
    db.insert({"null": None})
    db.insert({"weird key!@#$%^&*()": "value"})

    assert db.contains(where('') == "empty_key")
    assert db.contains(where('null') == None)
    assert db.contains(where("weird key!@#$%^&*()") == "value")

def test_nested_structure(db: TinyDB):
    nested_data = {"key": {"subkey": {"deepkey": "deepvalue"}}}
    db.insert(nested_data)
    result = db.get(where("key")["subkey"]["deepkey"] == "deepvalue")
    assert result == nested_data


# 4. Nonexistent keys
def test_nonexistent_keys(db: TinyDB):
    db.insert({'key': 'value'})
    assert db.get(where('nonexistent') == 'value') is None
    assert not db.contains(where('nonexistent') == 'value')

# 5. Operations on empty databases
def test_operations_on_empty_db(db: TinyDB):
    db.drop_tables()
    assert db.all() == []
    assert db.get(where('key') == 'value') is None
    assert db.count(where('key').exists()) == 0
    assert db.search(where('key') == 'value') == []

def test_update_on_empty_db(db: TinyDB):
    db.drop_tables()
    db.update({'key': 'value'}, where('nonexistent') == 'value')
    assert db.all() == []  # Ensure no entries were added

# 6. Invalid configurations
def test_invalid_storage_usage():
    class InvalidStorage(Storage):
        pass

    with pytest.raises(TypeError):
        TinyDB(storage=InvalidStorage)

# 7. Exceptions in transformations
def test_transform_exceptions(storage):
    def faulty_transform(el):
        raise ValueError("Simulated error")

    storage.write(doc)

    with pytest.raises(ValueError, match="Simulated error"):
        faulty_transform(storage.read())

def test_partial_transform(db: TinyDB):
    db.insert({'key': 1})
    db.insert({'key': 2})

    def faulty_transform(el):
        if el['key'] == 2:
            raise ValueError("Simulated error")
        el['key'] += 1

    with pytest.raises(ValueError, match="Simulated error"):
        db.update(faulty_transform, where('key').exists())

# 8. Caching behavior
def test_caching_behavior(storage):
    storage.write(doc)
    assert doc == storage.read()

    storage.flush()
    assert doc == storage.read()

# 9. Caching with multiple writes
def test_caching_multiple_writes(storage):
    storage.WRITE_CACHE_SIZE = 3
    for _ in range(2):
        storage.write(doc)
        assert storage.memory is None

    storage.write(doc)
    assert storage.memory

# 10. JSON storage and file size validation
def test_caching_json_write(tmp_path):
    path = str(tmp_path / "test.db")

    with TinyDB(path, storage=CachingMiddleware(JSONStorage)) as db:
        db.insert({'key': 'value'})

    statinfo = os.stat(path)
    assert statinfo.st_size != 0

    assert db._storage._handle.closed

    with TinyDB(path, storage=CachingMiddleware(JSONStorage)) as db:
        assert db.all() == [{'key': 'value'}]
