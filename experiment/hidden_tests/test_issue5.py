import pytest
from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


@pytest.fixture
def db():
    d = TinyDB(storage=MemoryStorage)
    d.insert_multiple([{'t': 'a'}, {'t': 'b'}, {'t': 'a'}])
    return d


def test_count_without_args_is_total(db):
    assert db.count() == 3


def test_count_without_args_matches_len(db):
    assert db.count() == len(db)


def test_count_with_condition_unchanged(db):
    assert db.count(where('t') == 'a') == 2


def test_count_on_empty_table(db):
    db.truncate()
    assert db.count() == 0
