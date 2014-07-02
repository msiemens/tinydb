import tempfile
import os
import gc

from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage

from nose.tools import *

#: :type: TinyDB
db = None


def setup():
    global db
    db = TinyDB(storage=MemoryStorage)


def test_purge():
    db.insert({})
    db.purge()

    assert_equal(len(db), 0)


def test_all():
    db.purge()

    for i in range(10):
        db.insert({})

    assert_equal(len(db), 10)


def test_insert():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    assert_equal(len(db.search(where('int') == 1)), 1)


def test_insert_multiple():
    db.purge()

    assert_equal(len(db.search(where('int') == 1)), 0)

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    assert_equal(len(db.search(where('int') == 1)), 3)
    assert_equal(len(db.search(where('char') == 'a')), 1)


def test_remove():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    db.remove(where('char') == 'b')

    assert_equal(len(db), 2)
    assert_equal(len(db.search(where('int') == 1)), 2)


def test_remove_multiple():
    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    db.remove(where('int') == 1)
    assert_equal(len(db), 0)


def test_update():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    assert_equal(len(db.search(where('int') == 1)), 3)

    db.update({'int': 2}, where('char') == 'a')

    assert_equal(len(db.search(where('int') == 2)), 1)
    assert_equal(len(db.search(where('int') == 1)), 2)


def test_search():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    results = db.search(where('int') == 1)
    assert_equal(len(results), 3)


def test_contians():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    if (where('int') == 1) in db:
        assert_true(True, True)
    else:
        assert_true(True, False)

    if (where('int') == 0) in db:
        assert_true(True, False)
    else:
        assert_true(True, True)


def test_get():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    assert_equal(db.get(where('char') == 'b')['char'], 'b')


def setup_multiple_dbs():
    global db1, db2
    db1 = TinyDB(storage=MemoryStorage)
    db2 = TinyDB(storage=MemoryStorage)


@with_setup(setup_multiple_dbs)
def test_multiple_dbs():
    db1.insert({'int': 1, 'char': 'a'})
    db1.insert({'int': 1, 'char': 'b'})
    db1.insert({'int': 1, 'value': 5.0})

    db2.insert({'color': 'blue', 'animal': 'turtle'})

    assert_equal(len(db1), 3)
    assert_equal(len(db2), 1)


def setup_bug_repeated_ids():
    global path
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()

    path = tmp.name


@with_setup(setup_bug_repeated_ids)
def test_bug_repeated_ids():
    TinyDB(path).insert({'x': 1})
    TinyDB(path).insert({'x': 2})
    data = TinyDB(path).all()

    assert_not_equal(data[0]['_id'], data[1]['_id'])

    gc.collect()  # Let TinyDB close the file handles. FIXME: Better solution
    os.unlink(path)
