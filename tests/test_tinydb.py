from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


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


def test_insert_multiple(db):
    db.purge()
    assert not db.contains(where('int') == 1)

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'a') == 1


def test_remove(db):
    db.remove(where('char') == 'b')

    assert len(db) == 2
    assert db.count(where('int') == 1) == 2


def test_remove_multiple(db):
    db.remove(where('int') == 1)

    assert len(db) == 0


def test_update(db):
    assert db.count(where('int') == 1) == 3

    db.update({'int': 2}, where('char') == 'a')

    assert db.count(where('int') == 2) == 1
    assert db.count(where('int') == 1) == 2


def test_search(db):
    assert not db._queries_cache
    assert len(db.search(where('int') == 1)) == 3

    assert len(db._queries_cache) == 1
    assert len(db.search(where('int') == 1)) == 3  # Query result from cache


def test_contians(db):
    assert db.contains(where('int') == 1)
    assert not db.contains(where('int') == 0)


def test_get(db):
    item = db.get(where('char') == 'b')
    assert item['char'] == 'b'


def test_count(db):
    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'd') == 0


def test_contains(db):
    assert db.contains(where('int') == 1)
    assert not db.contains(where('int') == 0)


def test_multiple_dbs():
    db1 = TinyDB(storage=MemoryStorage)
    db2 = TinyDB(storage=MemoryStorage)

    db1.insert({'int': 1, 'char': 'a'})
    db1.insert({'int': 1, 'char': 'b'})
    db1.insert({'int': 1, 'value': 5.0})

    db2.insert({'color': 'blue', 'animal': 'turtle'})

    assert len(db1) == 3
    assert len(db2) == 1


def test_bug_repeated_ids(tmpdir):
    """
    :type tmpdir: py._path.local.LocalPath
    """
    path = str(tmpdir.join('db.json'))

    with TinyDB(path) as _db:
        _db.insert({'x': 1})

    with TinyDB(path) as _db:
        _db.insert({'x': 1})

    with TinyDB(path) as _db:
        data = _db.all()

        assert data[0]['_id'] != data[1]['_id']
