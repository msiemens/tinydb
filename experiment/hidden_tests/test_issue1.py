import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage


@pytest.fixture
def db():
    d = TinyDB(storage=MemoryStorage)
    d.insert_multiple([{'a': 1}, {'a': 2}, {'a': 3}])
    return d


def test_update_with_string_ids(db):
    assert db.update({'a': 99}, doc_ids=['1']) == [1]
    assert db.get(doc_id=1)['a'] == 99
    assert db.get(doc_id=2)['a'] == 2


def test_remove_with_string_ids(db):
    assert db.remove(doc_ids=['1', '3']) == [1, 3]
    assert [d['a'] for d in db.all()] == [2]


def test_mixed_int_and_string_ids(db):
    assert sorted(db.update({'a': 0}, doc_ids=['1', 2])) == [1, 2]
    assert db.get(doc_id=3)['a'] == 3


def test_unknown_string_id_still_skipped(db):
    assert db.update({'a': 0}, doc_ids=['42']) == []
    assert db.remove(doc_ids=['42']) == []
    assert len(db) == 3
