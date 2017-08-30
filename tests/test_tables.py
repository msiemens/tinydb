import pytest

from tinydb import where


def test_tables_list(db):
    db.table('table1')
    db.table('table2')

    assert db.tables() == set(['_default', 'table1', 'table2'])


def test_one_table(db):
    table1 = db.table('table1')

    table1.insert_multiple({'int': 1, 'char': c} for c in 'abc')

    assert table1.get(where('int') == 1)['char'] == 'a'
    assert table1.get(where('char') == 'b')['char'] == 'b'


def test_multiple_tables(db):
    table1 = db.table('table1')
    table2 = db.table('table2')
    table3 = db.table('table3')

    table1.insert({'int': 1, 'char': 'a'})
    table2.insert({'int': 1, 'char': 'b'})
    table3.insert({'int': 1, 'char': 'c'})

    assert table1.count(where('char') == 'a') == 1
    assert table2.count(where('char') == 'b') == 1
    assert table3.count(where('char') == 'c') == 1

    db.purge_tables()

    assert len(table1) == 0
    assert len(table2) == 0
    assert len(table3) == 0


def test_caching(db):
    table1 = db.table('table1')
    table2 = db.table('table1')

    assert table1 is table2


def test_query_cache_size(db):
    table = db.table('table3', cache_size=1)
    query = where('int') == 1

    table.insert({'int': 1})
    table.insert({'int': 1})

    assert table.count(query) == 2
    assert table.count(where('int') == 2) == 0
    assert len(table._query_cache) == 1


def test_lru_cache(db):
    # Test integration into TinyDB
    table = db.table('table3', cache_size=2)
    query = where('int') == 1

    table.search(query)
    table.search(where('int') == 2)
    table.search(where('int') == 3)
    assert query not in table._query_cache

    table.remove(where('int') == 1)
    assert not table._query_cache.lru

    table.search(query)

    assert len(table._query_cache) == 1
    table.clear_cache()
    assert len(table._query_cache) == 0


def test_table_is_iterable(db):
    table = db.table('table1')

    table.insert_multiple({'int': i} for i in range(3))

    assert [r for r in table] == table.all()


def test_table_name(db):
    name = 'table3'
    table = db.table(name)
    assert name == table.name

    with pytest.raises(AttributeError):
        table.name = 'foo'
