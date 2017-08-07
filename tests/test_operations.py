from tinydb import where
from tinydb.operations import delete, increment, decrement, add, subtract, set


def test_delete(db):
    db.update(delete('int'), where('char') == 'a')
    assert 'int' not in db.get(where('char') == 'a')


def test_add_int(db):
    db.update(add('int', 5), where('char') == 'a')
    assert db.get(where('char') == 'a')['int'] == 6


def test_add_str(db):
    db.update(add('char', 'xyz'), where('char') == 'a')
    assert db.get(where('char') == 'axyz')['int'] == 1


def test_subtract(db):
    db.update(subtract('int', 5), where('char') == 'a')
    assert db.get(where('char') == 'a')['int'] == -4


def test_set(db):
    db.update(set('char', 'xyz'), where('char') == 'a')
    assert db.get(where('char') == 'xyz')['int'] == 1


def test_increment(db):
    db.update(increment('int'), where('char') == 'a')
    assert db.get(where('char') == 'a')['int'] == 2


def test_decrement(db):
    db.update(decrement('int'), where('char') == 'a')
    assert db.get(where('char') == 'a')['int'] == 0
