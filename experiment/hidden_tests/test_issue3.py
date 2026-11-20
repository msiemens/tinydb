import pytest
from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


@pytest.fixture
def db():
    d = TinyDB(storage=MemoryStorage)
    d.insert_multiple([{'a': 1}, {'a': 2}, {'a': 3}])
    return d


def test_update_with_document(db):
    doc = db.get(doc_id=1)
    assert db.update({'a': 9}, doc_ids=[doc]) == [1]
    assert db.get(doc_id=1)['a'] == 9
    assert db.get(doc_id=2)['a'] == 2


def test_remove_with_document(db):
    docs = db.search(where('a') > 1)
    assert sorted(db.remove(doc_ids=docs)) == [2, 3]
    assert [d['a'] for d in db.all()] == [1]


def test_mixed_documents_and_ints(db):
    doc = db.get(doc_id=1)
    assert sorted(db.update({'a': 0}, doc_ids=[doc, 3])) == [1, 3]
    assert db.get(doc_id=2)['a'] == 2


def test_int_ids_still_work(db):
    assert db.update({'a': 5}, doc_ids=[2]) == [2]
    assert db.remove(doc_ids=[1]) == [1]
    assert len(db) == 2
