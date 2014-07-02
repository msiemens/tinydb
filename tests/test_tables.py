from tinydb import where


def test_one_table(db):
    table1 = db.table('table1')

    table1.insert({'int': 1, 'char': 'a'})
    table1.insert({'int': 1, 'char': 'b'})
    table1.insert({'int': 1, 'char': 'c'})

    assert table1.get(where('int') == 1)['char'] == 'a'
    assert table1.get(where('char') == 'b')['char'] == 'b'


def test_multiple_tables(db):
    table1 = db.table('table1')
    table2 = db.table('table2')
    table3 = db.table('table3')

    table1.insert({'int': 1, 'char': 'a'})
    table2.insert({'int': 1, 'char': 'b'})
    table3.insert({'int': 1, 'char': 'c'})

    assert len(table1.search(where('int') == 1)) == 1
    assert len(table2.search(where('int') == 1)) == 1
    assert len(table3.search(where('int') == 1)) == 1


def test_caching(db):
    table1 = db.table('table1')
    table2 = db.table('table1')

    table1.insert({'int': 1, 'char': 'a'})
    table2.insert({'int': 1, 'char': 'b'})

    assert len(table1.search(where('int') == 1)) == 2
    assert len(table2.search(where('int') == 1)) == 2
