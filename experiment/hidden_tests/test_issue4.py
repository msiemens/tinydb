import pytest
from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


@pytest.fixture
def db():
    d = TinyDB(storage=MemoryStorage)
    d.insert_multiple([{'n': i, 'even': i % 2 == 0} for i in range(10)])
    return d


def test_limit_returns_first_n_in_order(db):
    res = db.search(where('even') == True, limit=2)  # noqa: E712
    assert [d['n'] for d in res] == [0, 2]


def test_limit_larger_than_matches(db):
    res = db.search(where('n') < 3, limit=50)
    assert [d['n'] for d in res] == [0, 1, 2]


def test_limit_none_returns_all(db):
    assert len(db.search(where('even') == True, limit=None)) == 5  # noqa: E712


def test_limited_search_does_not_poison_cache(db):
    q = where('even') == True  # noqa: E712
    assert len(db.search(q, limit=1)) == 1
    assert len(db.search(q)) == 5
    assert len(db.search(q, limit=3)) == 3
