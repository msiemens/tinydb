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


def test_nested_query():
    query = where('user.name') == 'john'

    assert query({'user':{'name':'john'}})
    assert not query({'user':{'name':'don'}})
    assert not query({})
