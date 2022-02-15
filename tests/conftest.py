import os.path
import tempfile

import pytest  # type: ignore

from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage
from tinydb import TinyDB, JSONStorage


@pytest.fixture(params=['memory', 'json'])
def db(request):
    with tempfile.TemporaryDirectory() as tmpdir:
        if request.param == 'json':
            db_ = TinyDB(os.path.join(tmpdir, 'test.db'), storage=JSONStorage)
        else:
            db_ = TinyDB(storage=MemoryStorage)

        db_.drop_tables()
        db_.insert_multiple({'int': 1, 'char': c} for c in 'abc')

        yield db_


@pytest.fixture
def storage():
    return CachingMiddleware(MemoryStorage)()
