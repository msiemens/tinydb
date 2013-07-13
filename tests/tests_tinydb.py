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


def test_remove_by_id():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    db.remove(db._last_id - 1)

    assert_equal(len(db), 2)


def test_remove_by_id_list():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    ids = db.all(as_dict=True).keys()[0:-1]  # Don't delete the last one
    db.remove(ids)

    assert_equal(len(db), 1)


def test_remove_multiple():
    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    db.remove(where('int') == 1)
    assert_equal(len(db), 0)


def test_search():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    results = db.search(where('int') == 1)
    assert_equal(len(results), 3)


def test_search_by_ids():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    ids = db.all(as_dict=True).keys()[0:-1]  # Don't search fot the last ID

    results = db.search(ids)
    assert_equal(len(results), 2)


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


def test_get_by_id():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    data = db.all(as_dict=True)

    for id in data.keys():
        assert_equal(db.get(id)['int'], 1)
