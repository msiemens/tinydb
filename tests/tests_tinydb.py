from tinydb import TinyDB, field
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
    assert_equal(len(db.search(field('int') == 1)), 1)


def test_insert_multiple():
    db.purge()

    assert_equal(len(db.search(field('int') == 1)), 0)

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    assert_equal(len(db.search(field('int') == 1)), 3)
    assert_equal(len(db.search(field('char') == 'a')), 1)


def test_remove():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    db.remove(field('char') == 'b')

    assert_equal(len(db), 2)
    assert_equal(len(db.search(field('int') == 1)), 2)


def test_remove_multiple():
    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    db.remove(field('int') == 1)
    assert_equal(len(db), 0)


def test_search():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    results = db.search(field('int') == 1)
    assert_equal(len(results), 3)

    assert_equal(results[0]['char'], 'a')
    assert_equal(results[1]['char'], 'b')
    assert_equal(results[2]['char'], 'c')


def test_contians():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    if (field('int') == 1) in db:
        assert_true(True, True)
    else:
        assert_true(True, False)

    if (field('int') == 0) in db:
        assert_true(True, False)
    else:
        assert_true(True, True)


def test_get():
    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    assert_equal(db.get(field('int') == 1)['char'], 'a')
    assert_equal(db.get(field('char') == 'b')['char'], 'b')