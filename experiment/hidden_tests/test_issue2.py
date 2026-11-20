import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage


@pytest.fixture
def dbs():
    src = TinyDB(storage=MemoryStorage)
    dst = TinyDB(storage=MemoryStorage)
    src.insert({'x': 1})
    src.insert({'x': 2})
    dst.insert({'y': 9})
    return src, dst


def test_insert_multiple_from_other_db_no_error(dbs):
    src, dst = dbs
    ids = dst.insert_multiple(src.all())
    assert len(ids) == 2
    assert len(dst) == 3


def test_existing_destination_doc_untouched(dbs):
    src, dst = dbs
    dst.insert_multiple(src.all())
    assert dst.get(doc_id=1) == {'y': 9}


def test_upsert_foreign_document_does_not_merge(dbs):
    src, dst = dbs
    dst.upsert(src.get(doc_id=1))
    assert dst.get(doc_id=1) == {'y': 9}
    assert {'x': 1} in [dict(d) for d in dst.all()]


def test_all_source_data_present_after_copy(dbs):
    src, dst = dbs
    dst.insert_multiple(src.all())
    assert sorted(d['x'] for d in dst.all() if 'x' in d) == [1, 2]
