import pytest

from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage
from tinydb import TinyDB


def get_db(smart_cache=False):
    db_ = TinyDB(storage=MemoryStorage)
    db_.purge_tables()

    if smart_cache:
        db_ = db_.table('_default', smart_cache=True)

    db_.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    return db_


@pytest.fixture
def db():
    return get_db()


@pytest.fixture
def storage():
    _storage = CachingMiddleware(MemoryStorage)
    return _storage()  # Initialize MemoryStorage
