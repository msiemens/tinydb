import pytest
from tinydb.queries import Query


def test_no_path():
    with pytest.raises(ValueError):
        Query() == 2


def test_eq():
    query = Query().value == 1
    assert query({'value': 1})
    assert not query({'value': 2})
    assert hash(query)

    query = Query().value == [0, 1]
    assert query({'value': [0, 1]})
    assert not query({'value': [0, 1, 2]})
    assert hash(query)


def test_ne():
    query = Query().value != 1
    assert query({'value': 0})
    assert query({'value': 2})
    assert not query({'value': 1})
    assert hash(query)

    query = Query().value != [0, 1]
    assert query({'value': [0, 1, 2]})
    assert not query({'value': [0, 1]})
    assert hash(query)


def test_lt():
    query = Query().value < 1
    assert query({'value': 0})
    assert not query({'value': 1})
    assert not query({'value': 2})
    assert hash(query)


def test_le():
    query = Query().value <= 1
    assert query({'value': 0})
    assert query({'value': 1})
    assert not query({'value': 2})
    assert hash(query)


def test_gt():
    query = Query().value > 1
    assert query({'value': 2})
    assert not query({'value': 1})
    assert hash(query)


def test_ge():
    query = Query().value >= 1
    assert query({'value': 2})
    assert query({'value': 1})
    assert not query({'value': 0})
    assert hash(query)


def test_or():
    query = (
        (Query().val1 == 1) |
        (Query().val2 == 2)
    )
    assert query({'val1': 1})
    assert query({'val2': 2})
    assert query({'val1': 1, 'val2': 2})
    assert not query({'val1': '', 'val2': ''})
    assert hash(query)


def test_and():
    query = (
        (Query().val1 == 1) &
        (Query().val2 == 2)
    )
    assert query({'val1': 1, 'val2': 2})
    assert not query({'val1': 1})
    assert not query({'val2': 2})
    assert not query({'val1': '', 'val2': ''})
    assert hash(query)


def test_not():
    query = ~ (Query().val1 == 1)
    assert query({'val1': 5, 'val2': 2})
    assert not query({'val1': 1, 'val2': 2})
    assert hash(query)

    query = (
        (~ (Query().val1 == 1)) &
        (Query().val2 == 2)
    )
    assert query({'val1': '', 'val2': 2})
    assert query({'val2': 2})
    assert not query({'val1': 1, 'val2': 2})
    assert not query({'val1': 1})
    assert not query({'val1': '', 'val2': ''})
    assert hash(query)


def test_has_key():
    query = Query().val3.exists()

    assert query({'val3': 1})
    assert not query({'val1': 1, 'val2': 2})
    assert hash(query)


def test_regex():
    query = Query().val.matches(r'\d{2}\.')

    assert query({'val': '42.'})
    assert not query({'val': '44'})
    assert not query({'val': 'ab.'})
    assert not query({'': None})
    assert hash(query)

    query = Query().val.search(r'\d+')

    assert query({'val': 'ab3'})
    assert not query({'val': 'abc'})
    assert not query({'val': ''})
    assert not query({'': None})
    assert hash(query)


def test_custom():
    def test(value):
        return value == 42

    query = Query().val.test(test)

    assert query({'val': 42})
    assert not query({'val': 40})
    assert not query({'val': '44'})
    assert not query({'': None})
    assert hash(query)

    def in_list(value, l):
        return value in l

    query = Query().val.test(in_list, tuple([25, 35]))
    assert not query({'val': 20})
    assert query({'val': 25})
    assert not query({'val': 30})
    assert query({'val': 35})
    assert not query({'val': 36})
    assert hash(query)


def test_custom_with_params():
    def test(value, minimum, maximum):
        return minimum <= value <= maximum

    query = Query().val.test(test, 1, 10)

    assert query({'val': 5})
    assert not query({'val': 0})
    assert not query({'val': 11})
    assert not query({'': None})
    assert hash(query)


def test_any():
    query = Query().followers.any(Query().name == 'don')

    assert query({'followers': [{'name': 'don'}, {'name': 'john'}]})
    assert not query({'followers': 1})
    assert not query({})
    assert hash(query)

    query = Query().followers.any(Query().num.matches('\\d+'))
    assert query({'followers': [{'num': '12'}, {'num': 'abc'}]})
    assert not query({'followers': [{'num': 'abc'}]})
    assert hash(query)

    query = Query().followers.any(['don', 'jon'])
    assert query({'followers': ['don', 'greg', 'bill']})
    assert not query({'followers': ['greg', 'bill']})
    assert not query({})
    assert hash(query)

    query = Query().followers.any([{'name': 'don'}, {'name': 'john'}])
    assert query({'followers': [{'name': 'don'}, {'name': 'greg'}]})
    assert not query({'followers': [{'name': 'greg'}]})
    assert hash(query)


def test_all():
    query = Query().followers.all(Query().name == 'don')
    assert query({'followers': [{'name': 'don'}]})
    assert not query({'followers': [{'name': 'don'}, {'name': 'john'}]})
    assert hash(query)

    query = Query().followers.all(Query().num.matches('\\d+'))
    assert query({'followers': [{'num': '123'}, {'num': '456'}]})
    assert not query({'followers': [{'num': '123'}, {'num': 'abc'}]})
    assert hash(query)

    query = Query().followers.all(['don', 'john'])
    assert query({'followers': ['don', 'john', 'greg']})
    assert not query({'followers': ['don', 'greg']})
    assert not query({})
    assert hash(query)

    query = Query().followers.all([{'name': 'jane'}, {'name': 'john'}])
    assert query({'followers': [{'name': 'john'}, {'name': 'jane'}]})
    assert query({'followers': [{'name': 'john'},
                                {'name': 'jane'},
                                {'name': 'bob'}]})
    assert not query({'followers': [{'name': 'john'}, {'name': 'bob'}]})
    assert hash(query)


def test_has():
    query = Query().key1.key2.exists()
    str(query)  # This used to cause a bug...

    assert query({'key1': {'key2': {'key3': 1}}})
    assert query({'key1': {'key2': 1}})
    assert not query({'key1': 3})
    assert not query({'key1': {'key1': 1}})
    assert not query({'key2': {'key1': 1}})
    assert hash(query)

    query = Query().key1.key2 == 1

    assert query({'key1': {'key2': 1}})
    assert not query({'key1': {'key2': 2}})
    assert hash(query)

    # Nested has: key exists
    query = Query().key1.key2.key3.exists()
    assert query({'key1': {'key2': {'key3': 1}}})
    # Not a dict
    assert not query({'key1': 1})
    assert not query({'key1': {'key2': 1}})
    # Wrong key
    assert not query({'key1': {'key2': {'key0': 1}}})
    assert not query({'key1': {'key0': {'key3': 1}}})
    assert not query({'key0': {'key2': {'key3': 1}}})

    assert hash(query)

    # Nested has: check for value
    query = Query().key1.key2.key3 == 1
    assert query({'key1': {'key2': {'key3': 1}}})
    assert not query({'key1': {'key2': {'key3': 0}}})
    assert hash(query)

    # Test special methods: regex matches
    query = Query().key1.value.matches(r'\d+')
    assert query({'key1': {'value': '123'}})
    assert not query({'key2': {'value': '123'}})
    assert not query({'key2': {'value': 'abc'}})
    assert hash(query)

    # Test special methods: regex contains
    query = Query().key1.value.search(r'\d+')
    assert query({'key1': {'value': 'a2c'}})
    assert not query({'key2': {'value': 'a2c'}})
    assert not query({'key2': {'value': 'abc'}})
    assert hash(query)

    # Test special methods: nested has and regex matches
    query = Query().key1.x.y.matches(r'\d+')
    assert query({'key1': {'x': {'y': '123'}}})
    assert not query({'key1': {'x': {'y': 'abc'}}})
    assert hash(query)

    # Test special method: nested has and regex contains
    query = Query().key1.x.y.search(r'\d+')
    assert query({'key1': {'x': {'y': 'a2c'}}})
    assert not query({'key1': {'x': {'y': 'abc'}}})
    assert hash(query)

    # Test special methods: custom test
    query = Query().key1.int.test(lambda x: x == 3)
    assert query({'key1': {'int': 3}})
    assert hash(query)


def test_one_of():
    query = Query().key1.one_of(['value 1', 'value 2'])
    assert query({'key1': 'value 1'})
    assert query({'key1': 'value 2'})
    assert not query({'key1': 'value 3'})


def test_hash():
    d = {
        Query().key1 == 2: True,
        Query().key1.key2.key3.exists(): True,
        Query().key1.exists() & Query().key2.exists(): True,
        Query().key1.exists() | Query().key2.exists(): True,
    }

    assert (Query().key1 == 2) in d
    assert (Query().key1.key2.key3.exists()) in d
    assert (Query()['key1.key2'].key3.exists()) not in d

    # Commutative property of & and |
    assert (Query().key1.exists() & Query().key2.exists()) in d
    assert (Query().key2.exists() & Query().key1.exists()) in d
    assert (Query().key1.exists() | Query().key2.exists()) in d
    assert (Query().key2.exists() | Query().key1.exists()) in d


def test_orm_usage():
    data = {'name': 'John', 'age': {'year': 2000}}

    User = Query()
    query1 = User.name == 'John'
    query2 = User.age.year == 2000
    assert query1(data)
    assert query2(data)
