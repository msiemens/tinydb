import pytest

from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage
from tinydb import TinyDB


@pytest.fixture
def db():
    db = TinyDB(storage=MemoryStorage)

    db.insert_multiple({'int': 1, 'char': c} for c in 'abc')

    return db


@pytest.fixture
def storage():
    _storage = CachingMiddleware(MemoryStorage)
    return _storage()  # Initialize MemoryStorage
