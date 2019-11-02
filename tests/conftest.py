import pytest  # type: ignore

from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage
from tinydb import TinyDB


@pytest.fixture
def db():
    db_ = TinyDB(storage=MemoryStorage)
    db_.drop_tables()
    db_.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    return db_


@pytest.fixture
def storage():
    return CachingMiddleware(MemoryStorage)()
