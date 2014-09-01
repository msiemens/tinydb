from tinydb import where


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
    assert len(table._queries_cache) == 1


def test_smart_query_cache(db):
    table = db.table('table3', smart_cache=True)
    query = where('int') == 1
    dummy = where('int') == 2

    assert not table.search(query)
    assert not table.search(dummy)

    # Test insert
    table.insert({'int': 1})

    assert len(table._queries_cache) == 2
    assert len(table._queries_cache[query]) == 1

    # Test update
    table.update({'int': 2}, where('int') == 1)

    assert len(table._queries_cache[dummy]) == 1
    assert table.count(query) == 0

    # Test remove
    table.insert({'int': 1})
    table.remove(where('int') == 1)

    assert table.count(where('int') == 1) == 0


def test_lru_cache(db):
    table = db.table('table3', cache_size=2)
    query = where('int') == 1

    table.search(query)
    table.search(where('int') == 2)
    table.search(where('int') == 3)
    assert query not in table._queries_cache

    table.remove(where('int') == 1)
    assert not table._lru
