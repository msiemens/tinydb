import os
import random
import tempfile
import json
from typing import Union
from unittest.mock import MagicMock, patch

import pytest  # type: ignore

from tinydb import TinyDB, where
from tinydb.storages import JSONStorage, MemoryStorage, Storage, touch, GCSStorage, GCSBucketDoesntExists
from tinydb.table import Document

from google.cloud.storage import Client as GCSClient, Bucket as GCSBucket

random.seed()

doc = {'none': [None, None], 'int': 42, 'float': 3.1415899999999999,
       'list': ['LITE', 'RES_ACID', 'SUS_DEXT'],
       'dict': {'hp': 13, 'sp': 5},
       'bool': [True, False, True, False]}


def test_json(tmpdir):
    # Write contents
    path = str(tmpdir.join('test.db'))
    storage = JSONStorage(path)
    storage.write(doc)

    # Verify contents
    assert doc == storage.read()
    storage.close()


def test_json_kwargs(tmpdir):
    db_file = tmpdir.join('test.db')
    db = TinyDB(str(db_file), sort_keys=True, indent=4, separators=(',', ': '))

    # Write contents
    db.insert({'b': 1})
    db.insert({'a': 1})

    assert db_file.read() == '''{
    "_default": {
        "1": {
            "b": 1
        },
        "2": {
            "a": 1
        }
    }
}'''
    db.close()


def test_json_readwrite(tmpdir):
    """
    Regression test for issue #1
    """
    path = str(tmpdir.join('test.db'))

    # Create TinyDB instance
    db = TinyDB(path, storage=JSONStorage)

    item = {'name': 'A very long entry'}
    item2 = {'name': 'A short one'}

    def get(s):
        return db.get(where('name') == s)

    db.insert(item)
    assert get('A very long entry') == item

    db.remove(where('name') == 'A very long entry')
    assert get('A very long entry') is None

    db.insert(item2)
    assert get('A short one') == item2

    db.remove(where('name') == 'A short one')
    assert get('A short one') is None

    db.close()


def test_json_read(tmpdir):
    r"""Open a database only for reading"""
    path = str(tmpdir.join('test.db'))
    with pytest.raises(FileNotFoundError):
        db = TinyDB(path, storage=JSONStorage, access_mode='r')
    # Create small database
    db = TinyDB(path, storage=JSONStorage)
    db.insert({'b': 1})
    db.insert({'a': 1})
    db.close()
    # Access in read mode
    db = TinyDB(path, storage=JSONStorage, access_mode='r')
    assert db.get(where('a') == 1) == {'a': 1}  # reading is fine
    with pytest.raises(IOError):
        db.insert({'c': 1})  # writing is not
    db.close()


def test_create_dirs():
    temp_dir = tempfile.gettempdir()

    while True:
        dname = os.path.join(temp_dir, str(random.getrandbits(20)))
        if not os.path.exists(dname):
            db_dir = dname
            db_file = os.path.join(db_dir, 'db.json')
            break

    with pytest.raises(IOError):
        JSONStorage(db_file)

    JSONStorage(db_file, create_dirs=True).close()
    assert os.path.exists(db_file)

    # Use create_dirs with already existing directory
    JSONStorage(db_file, create_dirs=True).close()
    assert os.path.exists(db_file)

    os.remove(db_file)
    os.rmdir(db_dir)


def test_json_invalid_directory():
    with pytest.raises(IOError):
        with TinyDB('/this/is/an/invalid/path/db.json', storage=JSONStorage):
            pass


def test_in_memory():
    # Write contents
    storage = MemoryStorage()
    storage.write(doc)

    # Verify contents
    assert doc == storage.read()

    # Test case for #21
    other = MemoryStorage()
    other.write({})
    assert other.read() != storage.read()


def test_in_memory_close():
    with TinyDB(storage=MemoryStorage) as db:
        db.insert({})


def test_custom():
    # noinspection PyAbstractClass
    class MyStorage(Storage):
        pass

    with pytest.raises(TypeError):
        MyStorage()


def test_read_once():
    count = 0

    # noinspection PyAbstractClass
    class MyStorage(Storage):
        def __init__(self):
            self.memory = None

        def read(self):
            nonlocal count
            count += 1

            return self.memory

        def write(self, data):
            self.memory = data

    with TinyDB(storage=MyStorage) as db:
        assert count == 0

        db.table(db.default_table_name)

        assert count == 0

        db.all()

        assert count == 1

        db.insert({'foo': 'bar'})

        assert count == 3  # One for getting the next ID, one for the insert

        db.all()

        assert count == 4


def test_custom_with_exception():
    class MyStorage(Storage):
        def read(self):
            pass

        def write(self, data):
            pass

        def __init__(self):
            raise ValueError()

        def close(self):
            raise RuntimeError()

    with pytest.raises(ValueError):
        with TinyDB(storage=MyStorage) as db:
            pass


def test_yaml(tmpdir):
    """
    :type tmpdir: py._path.local.LocalPath
    """

    try:
        import yaml
    except ImportError:
        return pytest.skip('PyYAML not installed')

    def represent_doc(dumper, data):
        # Represent `Document` objects as their dict's string representation
        # which PyYAML understands
        return dumper.represent_data(dict(data))

    yaml.add_representer(Document, represent_doc)

    class YAMLStorage(Storage):
        def __init__(self, filename):
            self.filename = filename
            touch(filename, False)

        def read(self):
            with open(self.filename) as handle:
                data = yaml.safe_load(handle.read())
                return data

        def write(self, data):
            with open(self.filename, 'w') as handle:
                yaml.dump(data, handle)

        def close(self):
            pass

    # Write contents
    path = str(tmpdir.join('test.db'))
    db = TinyDB(path, storage=YAMLStorage)
    db.insert(doc)
    assert db.all() == [doc]

    db.update({'name': 'foo'})

    assert '!' not in tmpdir.join('test.db').read()

    assert db.contains(where('name') == 'foo')
    assert len(db) == 1


def test_encoding(tmpdir):
    japanese_doc = {"Test": u"こんにちは世界"}

    path = str(tmpdir.join('test.db'))
    # cp936 is used for japanese encodings
    jap_storage = JSONStorage(path, encoding="cp936")
    jap_storage.write(japanese_doc)

    try:
        exception = json.decoder.JSONDecodeError
    except AttributeError:
        exception = ValueError

    with pytest.raises(exception):
        # cp037 is used for english encodings
        eng_storage = JSONStorage(path, encoding="cp037")
        eng_storage.read()

    jap_storage = JSONStorage(path, encoding="cp936")
    assert japanese_doc == jap_storage.read()


@patch("google.cloud.storage.Client", autospec=True)
def test_gcs_storage_get_blob(client_mock: Union[GCSClient, MagicMock]):
    path = "gs://temporary-bucket/test/tiny_db.db"
    storage = GCSStorage(path, client_mock)
    blob = storage.get_blob()
    assert blob.name == "test/tiny_db.db"


@patch("google.cloud.storage.Client", autospec=True)
def test_gcs_storage_get_bucket(client_mock: Union[GCSClient, MagicMock]):
    path = "gs://temporary-bucket/tiny_db.db"
    storage = GCSStorage(path, client_mock)
    bucket = storage.get_bucket()
    assert bucket.name == "temporary-bucket"


@patch("google.cloud.storage.Client", autospec=True)
def test_gcs_storage_read_bucket_doesnt_exists(client_mock: Union[GCSClient, MagicMock]):
    path = "gs://temporary-bucket/tiny_db.db"
    with patch("tinydb.storages.GCSStorage.bucket_exists", MagicMock(return_value=False)):
        with pytest.raises(GCSBucketDoesntExists):
            storage = GCSStorage(path, client_mock)
            storage.read()


@patch("google.cloud.storage.Client", autospec=True)
def test_gcs_storage_write_bucket_doesnt_exists(client_mock: Union[GCSClient, MagicMock]):
    path = "gs://temporary-bucket/tiny_db.db"
    with patch("tinydb.storages.GCSStorage.bucket_exists", MagicMock(return_value=False)):
        with pytest.raises(GCSBucketDoesntExists):
            storage = GCSStorage(path, client_mock)
            storage.write(doc)


@patch("google.cloud.storage.Client", autospec=True)
def test_gcs_storage_read_bucket_blob_doesnt_exists(client_mock: Union[GCSClient, MagicMock]):
    path = "gs://temporary-bucket/tiny_db.db"

    with patch("tinydb.storages.GCSStorage.get_blob", MagicMock()):
        storage = GCSStorage(path, client_mock)

        # Mock exists method of blob
        storage.get_blob.return_value.exists.return_value = False

        result = storage.read()
        assert result is None

@patch("google.cloud.storage.Client", autospec=True)
def test_gcs_storage_read_bucket(client_mock: Union[GCSClient, MagicMock]):
    path = "gs://temporary-bucket/tiny_db.db"

    with patch("tinydb.storages.GCSStorage.get_blob", MagicMock()):
        storage = GCSStorage(path, client_mock)

        # Return value from blob
        storage.get_blob.return_value.download_as_string.return_value = "{}"

        result = storage.read()
        assert result == {}
