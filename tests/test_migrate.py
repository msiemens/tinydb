import pytest

from tinydb import TinyDB, where
from tinydb.migrate import migrate

v1_0 = """
{
    "_default": [{"key": "value", "_id": 1}],
    "table": [{"key": "value", "_id": 2}]
}
"""


def test_open_old(tmpdir):
    # Make sure that opening an old database results in an exception and not
    # in data loss
    db_file = tmpdir.join('db.json')
    db_file.write(v1_0)

    with pytest.raises(Exception):
        TinyDB(str(db_file))


def test_upgrade(tmpdir):
    db_file = tmpdir.join('db.json')
    db_file.write(v1_0)

    # Run upgrade
    migrate(str(db_file))
    db = TinyDB(str(db_file))

    assert db.count(where('key') == 'value') == 1
