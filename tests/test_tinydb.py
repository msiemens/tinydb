import pytest

from . conftest import get_db

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage

dbs = lambda: [get_db(), get_db(smart_cache=True)]


@pytest.mark.parametrize('db', dbs())
def test_purge(db):
    db.purge()

    db.insert({})
    db.purge()

    assert len(db) == 0


@pytest.mark.parametrize('db', dbs())
def test_all(db):
    db.purge()

    for i in range(10):
        db.insert({})

    assert len(db.all()) == 10


@pytest.mark.parametrize('db', dbs())
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


@pytest.mark.parametrize('db', dbs())
def test_insert_ids(db):
    db.purge()
    assert db.insert({'int': 1, 'char': 'a'}) == 1
    assert db.insert({'int': 1, 'char': 'a'}) == 2


@pytest.mark.parametrize('db', dbs())
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
    assert db.count(where('int')) == 10

    # Insert multiple from inline generator
    db.purge()

    db.insert_multiple({'int': i} for i in range(10))

    for i in range(10):
        assert db.count(where('int') == i) == 1


@pytest.mark.parametrize('db', dbs())
def test_insert_multiple_with_ids(db):
    db.purge()

    # Insert multiple from list
    assert db.insert_multiple([{'int': 1, 'char': 'a'},
                               {'int': 1, 'char': 'b'},
                               {'int': 1, 'char': 'c'}]) == [1, 2, 3]


@pytest.mark.parametrize('db', dbs())
def test_remove(db):
    db.remove(where('char') == 'b')

    assert len(db) == 2
    assert db.count(where('int') == 1) == 2


@pytest.mark.parametrize('db', dbs())
def test_remove_multiple(db):
    db.remove(where('int') == 1)

    assert len(db) == 0


@pytest.mark.parametrize('db', dbs())
def test_remove_ids(db):
    db.remove(eids=[1, 2])

    assert len(db) == 1


@pytest.mark.parametrize('db', dbs())
def test_update(db):
    assert db.count(where('int') == 1) == 3

    db.update({'int': 2}, where('char') == 'a')

    assert db.count(where('int') == 2) == 1
    assert db.count(where('int') == 1) == 2


@pytest.mark.parametrize('db', dbs())
def test_update_ids(db):
    db.update({'int': 2}, eids=[1, 2])

    assert db.count(where('int') == 2) == 2


@pytest.mark.parametrize('db', dbs())
def test_search(db):
    assert not db._query_cache
    assert len(db.search(where('int') == 1)) == 3

    assert len(db._query_cache) == 1
    assert len(db.search(where('int') == 1)) == 3  # Query result from cache


@pytest.mark.parametrize('db', dbs())
def test_contians(db):
    assert db.contains(where('int') == 1)
    assert not db.contains(where('int') == 0)


@pytest.mark.parametrize('db', dbs())
def test_contains_ids(db):
    assert db.contains(eids=[1, 2])
    assert not db.contains(eids=[88])


@pytest.mark.parametrize('db', dbs())
def test_get(db):
    item = db.get(where('char') == 'b')
    assert item['char'] == 'b'


@pytest.mark.parametrize('db', dbs())
def test_get_ids(db):
    el = db.all()[0]
    assert db.get(eid=el.eid) == el
    assert db.get(eid=float('NaN')) is None


@pytest.mark.parametrize('db', dbs())
def test_count(db):
    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'd') == 0


@pytest.mark.parametrize('db', dbs())
def test_contains(db):
    assert db.contains(where('int') == 1)
    assert not db.contains(where('int') == 0)


@pytest.mark.parametrize('db', dbs())
def test_contains_ids(db):
    assert db.contains(eids=[1, 2])


def test_multiple_dbs():
    db1 = TinyDB(storage=MemoryStorage)
    db2 = TinyDB(storage=MemoryStorage)

    db1.insert({'int': 1, 'char': 'a'})
    db1.insert({'int': 1, 'char': 'b'})
    db1.insert({'int': 1, 'value': 5.0})

    db2.insert({'color': 'blue', 'animal': 'turtle'})

    assert len(db1) == 3
    assert len(db2) == 1


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

        assert data[0].eid != data[1].eid

    # Verify ids stay unique when inserting/removing
    with TinyDB(path) as _db:
        _db.purge()
        _db.insert_multiple({'x': i} for i in range(5))
        _db.remove(where('x') == 2)

        assert len(_db) == 4

        ids = [e.eid for e in _db.all()]
        assert len(ids) == len(set(ids))
