from tinydb.queries import where


def test_eq():
    query = where('value') == 1
    assert query({'value': 1})
    assert not query({'value': 2})


def test_ne():
    query = where('value') != 1
    assert query({'value': 2})
    assert not query({'value': 1})


def test_lt():
    query = where('value') < 1
    assert query({'value': 0})
    assert not query({'value': 1})


def test_le():
    query = where('value') <= 1
    assert query({'value': 0})
    assert query({'value': 1})
    assert not query({'value': 2})


def test_gt():
    query = where('value') > 1
    assert query({'value': 2})
    assert not query({'value': 1})


def test_ge():
    query = where('value') >= 1
    assert query({'value': 2})
    assert query({'value': 1})
    assert not query({'value': 0})


def test_or():
    query = (
        (where('val1') == 1) |
        (where('val2') == 2)
    )
    assert query({'val1': 1})
    assert query({'val2': 2})
    assert query({'val1': 1, 'val2': 2})
    assert not query({'val1': '', 'val2': ''})


def test_and():
    query = (
        (where('val1') == 1) &
        (where('val2') == 2)
    )
    assert query({'val1': 1, 'val2': 2})
    assert not query({'val1': 1})
    assert not query({'val2': 2})
    assert not query({'val1': '', 'val2': ''})


def test_not():
    query = ~ (where('val1') == 1)
    assert query({'val1': 5, 'val2': 2})
    assert not query({'val1': 1, 'val2': 2})

    query = (
        (~ (where('val1') == 1)) &
        (where('val2') == 2)
    )
    assert query({'val1': '', 'val2': 2})
    assert query({'val2': 2})
    assert not query({'val1': 1, 'val2': 2})
    assert not query({'val1': 1})
    assert not query({'val1': '', 'val2': ''})


def test_has_key():
    query = where('val3')

    assert query({'val3': 1})
    assert not query({'val1': 1, 'val2': 2})


def test_regex():
    query = where('val').matches(r'\d{2}\.')

    assert query({'val': '42.'})
    assert not query({'val': '44'})
    assert not query({'val': 'ab.'})
    assert not query({'': None})


def test_custom():
    def test(value):
        return value == 42

    query = where('val').test(test)

    assert query({'val': 42})
    assert not query({'val': 40})
    assert not query({'val': '44'})
    assert not query({'': None})


def test_any():
    query = where('followers').any(where('name') == 'don')

    assert query({'followers': [{'name': 'don'}, {'name': 'john'}]})
    assert not query({'followers': 1})
    assert not query({})

    query = where('followers').any(where('num').matches('\\d+'))
    assert query({'followers': [{'num': '12'}, {'num': 'abc'}]})
    assert not query({'followers': [{'num': 'abc'}]})


def test_all():
    query = where('followers').all(where('name') == 'don')
    assert query({'followers': [{'name': 'don'}]})
    assert not query({'followers': [{'name': 'don'}, {'name': 'john'}]})

    query = where('followers').all(where('num').matches('\\d+'))
    assert query({'followers': [{'num': '123'}, {'num': '456'}]})
    assert not query({'followers': [{'num': '123'}, {'num': 'abc'}]})


def test_has():
    query = where('key1').has('key2')

    assert query({'key1': {'key2': 1}})
    assert not query({'key1': 3})
    assert not query({'key1': {'key1': 1}})
    assert not query({'key2': {'key1': 1}})

    query = where('key1').has('key2') == 1

    assert query({'key1': {'key2': 1}})
    assert not query({'key1': {'key2': 2}})

    # Nested has: key exists
    query = where('key1').has('key2').has('key3')
    assert query({'key1': {'key2': {'key3': 1}}})
    # Not a dict
    assert not query({'key1': 1})
    assert not query({'key1': {'key2': 1}})
    # Wrong key
    assert not query({'key1': {'key2': {'key0': 1}}})
    assert not query({'key1': {'key0': {'key3': 1}}})
    assert not query({'key0': {'key2': {'key3': 1}}})

    # Nested has: check for value
    query = where('key1').has('key2').has('key3') == 1
    assert query({'key1': {'key2': {'key3': 1}}})
    assert not query({'key1': {'key2': {'key3': 0}}})

    # Test special methods: regex
    query = where('key1').has('value').matches(r'\d+')
    assert query({'key1': {'value': '123'}})
    assert not query({'key2': {'value': '123'}})
    assert not query({'key2': {'value': 'abc'}})

    # Test special methods: nested has and regex
    query = where('key1').has('x').has('y').matches(r'\d+')
    assert query({'key1': {'x': {'y': '123'}}})
    assert not query({'key1': {'x': {'y': 'abc'}}})

    # Test special methods: custom test
    query = where('key1').has('int').test(lambda x: x == 3)
    assert query({'key1': {'int': 3}})
