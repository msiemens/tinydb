# coding=utf-8
import sys

import pytest

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.middlewares import Middleware


def test_purge(db):
    db.purge()

    db.insert({})
    db.purge()

    assert len(db) == 0


def test_all(db):
    db.purge()

    for i in range(10):
        db.insert({})

    assert len(db.all()) == 10


def test_insert(db):
    db.purge()
    db.insert({'int': 1, 'char': 'a'})

    assert db.count(where('int') == 1) == 1

    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'a') == 1


def test_insert_ids(db):
    db.purge()
    assert db.insert({'int': 1, 'char': 'a'}) == 1
    assert db.insert({'int': 1, 'char': 'a'}) == 2


def test_insert_multiple(db):
    db.purge()
    assert not db.contains(where('int') == 1)

    # Insert multiple from list
    db.insert_multiple([{'int': 1, 'char': 'a'},
                        {'int': 1, 'char': 'b'},
                        {'int': 1, 'char': 'c'}])

    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'a') == 1

    # Insert multiple from generator function
    def generator():
        for j in range(10):
            yield {'int': j}

    db.purge()

    db.insert_multiple(generator())

    for i in range(10):
        assert db.count(where('int') == i) == 1
    assert db.count(where('int').exists()) == 10

    # Insert multiple from inline generator
    db.purge()

    db.insert_multiple({'int': i} for i in range(10))

    for i in range(10):
        assert db.count(where('int') == i) == 1


def test_insert_multiple_with_ids(db):
    db.purge()

    # Insert multiple from list
    assert db.insert_multiple([{'int': 1, 'char': 'a'},
                               {'int': 1, 'char': 'b'},
                               {'int': 1, 'char': 'c'}]) == [1, 2, 3]


def test_remove(db):
    db.remove(where('char') == 'b')

    assert len(db) == 2
    assert db.count(where('int') == 1) == 2


def test_remove_all_fails(db):
    with pytest.raises(RuntimeError):
        db.remove()


def test_remove_multiple(db):
    db.remove(where('int') == 1)

    assert len(db) == 0


def test_remove_ids(db):
    db.remove(doc_ids=[1, 2])

    assert len(db) == 1


def test_remove_returns_ids(db):
    assert db.remove(where('char') == 'b') == [2]


def test_update(db):
    assert len(db) == 3

    db.update({'int': 2}, where('char') == 'a')

    assert db.count(where('int') == 2) == 1
    assert db.count(where('int') == 1) == 2


def test_update_all(db):
    assert db.count(where('int') == 1) == 3

    db.update({'newField': True})

    assert db.count(where('newField') == True) == 3


def test_update_returns_ids(db):
    db.purge()
    assert db.insert({'int': 1, 'char': 'a'}) == 1
    assert db.insert({'int': 1, 'char': 'a'}) == 2

    assert db.update({'char': 'b'}, where('int') == 1) == [1, 2]


def test_update_transform(db):
    def increment(field):
        def transform(el):
            el[field] += 1

        return transform

    def delete(field):
        def transform(el):
            del el[field]

        return transform

    assert db.count(where('int') == 1) == 3

    db.update(increment('int'), where('char') == 'a')
    db.update(delete('char'), where('char') == 'a')

    assert db.count(where('int') == 2) == 1
    assert db.count(where('char') == 'a') == 0
    assert db.count(where('int') == 1) == 2


def test_update_ids(db):
    db.update({'int': 2}, doc_ids=[1, 2])

    assert db.count(where('int') == 2) == 2


def test_upsert(db):
    assert len(db) == 3

    # Document existing
    db.upsert({'int': 5}, where('char') == 'a')
    assert db.count(where('int') == 5) == 1

    # Document missing
    db.upsert({'int': 9, 'char': 'x'}, where('char') == 'x')
    assert db.count(where('int') == 9) == 1


def test_search(db):
    assert not db._query_cache
    assert len(db.search(where('int') == 1)) == 3

    assert len(db._query_cache) == 1
    assert len(db.search(where('int') == 1)) == 3  # Query result from cache


def test_get(db):
    item = db.get(where('char') == 'b')
    assert item['char'] == 'b'


def test_get_ids(db):
    el = db.all()[0]
    assert db.get(doc_id=el.doc_id) == el
    assert db.get(doc_id=float('NaN')) is None


def test_count(db):
    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'd') == 0


def test_contains(db):
    assert db.contains(where('int') == 1)
    assert not db.contains(where('int') == 0)


def test_contains_ids(db):
    assert db.contains(doc_ids=[1, 2])
    assert not db.contains(doc_ids=[88])


def test_get_idempotent(db):
    u = db.get(where('int') == 1)
    z = db.get(where('int') == 1)
    assert u == z


def test_multiple_dbs():
    """
    Regression test for issue #3
    """
    db1 = TinyDB(storage=MemoryStorage)
    db2 = TinyDB(storage=MemoryStorage)

    db1.insert({'int': 1, 'char': 'a'})
    db1.insert({'int': 1, 'char': 'b'})
    db1.insert({'int': 1, 'value': 5.0})

    db2.insert({'color': 'blue', 'animal': 'turtle'})

    assert len(db1) == 3
    assert len(db2) == 1


def test_storage_closed_once():
    class Storage(object):
        def __init__(self):
            self.closed = False

        def read(self):
            return {}

        def write(self, data):
            pass

        def close(self):
            assert not self.closed
            self.closed = True

    with TinyDB(storage=Storage) as db:
        db.close()

    del db
    # If db.close() is called during cleanup, the assertion will fail and throw
    # and exception


def test_unique_ids(tmpdir):
    """
    :type tmpdir: py._path.local.LocalPath
    """
    path = str(tmpdir.join('db.json'))

    # Verify ids are unique when reopening the DB and inserting
    with TinyDB(path) as _db:
        _db.insert({'x': 1})

    with TinyDB(path) as _db:
        _db.insert({'x': 1})

    with TinyDB(path) as _db:
        data = _db.all()

        assert data[0].doc_id != data[1].doc_id

    # Verify ids stay unique when inserting/removing
    with TinyDB(path) as _db:
        _db.purge()
        _db.insert_multiple({'x': i} for i in range(5))
        _db.remove(where('x') == 2)

        assert len(_db) == 4

        ids = [e.doc_id for e in _db.all()]
        assert len(ids) == len(set(ids))


def test_lastid_after_open(tmpdir):
    """
    Regression test for issue #34

    :type tmpdir: py._path.local.LocalPath
    """

    NUM = 100
    path = str(tmpdir.join('db.json'))

    with TinyDB(path) as _db:
        _db.insert_multiple({'i': i} for i in range(NUM))

    with TinyDB(path) as _db:
        assert _db._last_id == NUM


@pytest.mark.skipif(sys.version_info >= (3, 0),
                    reason="requires python2")
def test_unicode_memory(db):
    """
    Regression test for issue #28
    """
    unic_str = 'ß'.decode('utf-8')
    byte_str = 'ß'

    db.insert({'value': unic_str})
    assert db.contains(where('value') == byte_str)
    assert db.contains(where('value') == unic_str)

    db.purge()
    db.insert({'value': byte_str})
    assert db.contains(where('value') == byte_str)
    assert db.contains(where('value') == unic_str)


@pytest.mark.skipif(sys.version_info >= (3, 0),
                    reason="requires python2")
def test_unicode_json(tmpdir):
    """
    Regression test for issue #28
    """
    unic_str1 = 'a'.decode('utf-8')
    byte_str1 = 'a'

    unic_str2 = 'ß'.decode('utf-8')
    byte_str2 = 'ß'

    path = str(tmpdir.join('db.json'))

    with TinyDB(path) as _db:
        _db.purge()
        _db.insert({'value': byte_str1})
        _db.insert({'value': byte_str2})
        assert _db.contains(where('value') == byte_str1)
        assert _db.contains(where('value') == unic_str1)
        assert _db.contains(where('value') == byte_str2)
        assert _db.contains(where('value') == unic_str2)

    with TinyDB(path) as _db:
        _db.purge()
        _db.insert({'value': unic_str1})
        _db.insert({'value': unic_str2})
        assert _db.contains(where('value') == byte_str1)
        assert _db.contains(where('value') == unic_str1)
        assert _db.contains(where('value') == byte_str2)
        assert _db.contains(where('value') == unic_str2)


def test_doc_ids_json(tmpdir):
    """
    Regression test for issue #45
    """

    path = str(tmpdir.join('db.json'))

    with TinyDB(path) as _db:
        _db.purge()
        assert _db.insert({'int': 1, 'char': 'a'}) == 1
        assert _db.insert({'int': 1, 'char': 'a'}) == 2

        _db.purge()
        assert _db.insert_multiple([{'int': 1, 'char': 'a'},
                                    {'int': 1, 'char': 'b'},
                                    {'int': 1, 'char': 'c'}]) == [1, 2, 3]

        assert _db.contains(doc_ids=[1, 2])
        assert not _db.contains(doc_ids=[88])

        _db.update({'int': 2}, doc_ids=[1, 2])
        assert _db.count(where('int') == 2) == 2

        el = _db.all()[0]
        assert _db.get(doc_id=el.doc_id) == el
        assert _db.get(doc_id=float('NaN')) is None

        _db.remove(doc_ids=[1, 2])
        assert len(_db) == 1


def test_insert_string(tmpdir):
    path = str(tmpdir.join('db.json'))

    with TinyDB(path) as _db:
        data = [{'int': 1}, {'int': 2}]
        _db.insert_multiple(data)

        with pytest.raises(ValueError):
            _db.insert([1, 2, 3])  # Fails

        with pytest.raises(ValueError):
            _db.insert(set(['bark']))  # Fails

        assert data == _db.all()

        _db.insert({'int': 3})  # Does not fail


def test_insert_invalid_dict(tmpdir):
    path = str(tmpdir.join('db.json'))

    with TinyDB(path) as _db:
        data = [{'int': 1}, {'int': 2}]
        _db.insert_multiple(data)

        with pytest.raises(TypeError):
            _db.insert({'int': set(['bark'])})  # Fails

        assert data == _db.all()

        _db.insert({'int': 3})  # Does not fail


def test_gc(tmpdir):
    # See https://github.com/msiemens/tinydb/issues/92
    path = str(tmpdir.join('db.json'))
    db = TinyDB(path)
    table = db.table('foo')
    table.insert({'something': 'else'})
    table.insert({'int': 13})
    assert len(table.search(where('int') == 13)) == 1
    assert table.all() == [{'something': 'else'}, {'int': 13}]
    db.close()


def test_non_default_table():
    db = TinyDB(storage=MemoryStorage)
    assert [TinyDB.DEFAULT_TABLE] == list(db.tables())

    db = TinyDB(storage=MemoryStorage, default_table='non-default')
    assert set(['non-default']) == db.tables()

    db.purge_tables()
    default_table = TinyDB.DEFAULT_TABLE

    TinyDB.DEFAULT_TABLE = 'non-default'
    db = TinyDB(storage=MemoryStorage)
    assert set(['non-default']) == db.tables()

    TinyDB.DEFAULT_TABLE = default_table


def test_purge_table():
    db = TinyDB(storage=MemoryStorage)
    assert [TinyDB.DEFAULT_TABLE] == list(db.tables())

    db.purge_table(TinyDB.DEFAULT_TABLE)
    assert [] == list(db.tables())

    table_name = 'some-other-table'
    db = TinyDB(storage=MemoryStorage)
    db.table(table_name)
    assert set([TinyDB.DEFAULT_TABLE, table_name]) == db.tables()

    db.purge_table(table_name)
    assert set([TinyDB.DEFAULT_TABLE]) == db.tables()
    assert table_name not in db._table_cache

    db.purge_table('non-existent-table-name')
    assert set([TinyDB.DEFAULT_TABLE]) == db.tables()


def test_empty_write(tmpdir):
    path = str(tmpdir.join('db.json'))

    class ReadOnlyMiddleware(Middleware):
        def write(self, data):
            raise AssertionError('No write for unchanged db')

    TinyDB(path).close()
    TinyDB(path, storage=ReadOnlyMiddleware()).close()


def test_query_cache():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([
        {'name': 'foo', 'value': 42},
        {'name': 'bar', 'value': -1337}
    ])

    query = where('value') > 0

    results = db.search(query)
    assert len(results) == 1

    # Modify the db instance to not return any results when
    # bypassing the query cache
    db._table_cache[TinyDB.DEFAULT_TABLE]._read = lambda: {}

    # Make sure we got an independent copy of the result list
    results.extend([1])
    assert db.search(query) == [{'name': 'foo', 'value': 42}]


def test_tinydb_is_iterable(db):
    assert [r for r in db] == db.all()


def test_eids(db):
    with pytest.warns(DeprecationWarning):
        assert db.contains(eids=[1]) is True

    with pytest.warns(DeprecationWarning):
        db.update({'field': 'value'}, eids=[1])
        assert db.contains(where('field') == 'value')

    with pytest.warns(DeprecationWarning):
        doc = db.get(eid=1)

    with pytest.warns(DeprecationWarning):
        assert doc.eid == 1

    with pytest.warns(DeprecationWarning):
        db.remove(eids=[1])
        assert not db.contains(where('field') == 'value')

    with pytest.raises(TypeError):
        db.remove(eids=[1], doc_ids=[1])

    with pytest.raises(TypeError):
        db.get(eid=[1], doc_id=[1])
