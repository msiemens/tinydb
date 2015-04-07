from datetime import datetime

from tinydb import TinyDB, where
from tinydb.middlewares import SerializationMiddleware
from tinydb.serialize import Serializer
from tinydb.storages import JSONStorage


class DateTimeSerializer(Serializer):
    OBJ_CLASS = datetime
    FORMAT = '%Y-%m-%dT%H:%M:%S'

    def encode(self, obj):
        return obj.strftime(self.FORMAT)

    def decode(self, s):
        return datetime.strptime(s, self.FORMAT)


def test_serializer(tmpdir):
    path = str(tmpdir.join('db.json'))

    serializer = SerializationMiddleware(JSONStorage)
    serializer.register_serializer(DateTimeSerializer(), 'TinyDate')
    db = TinyDB(path, storage=serializer)

    date = datetime(2000, 1, 1, 12, 0, 0)

    db.insert({'date': date})
    db.insert({'int': 2})
    assert db.count(where('date') == date) == 1
    assert db.count(where('int') == 2) == 1
