from nose.tools import *

from tinydb.queries import field


def test_eq():
    query = field('value') == 1
    assert_true(query({'value': 1}))
    assert_false(query({'value': 2}))


def test_ne():
    query = field('value') != 1
    assert_true(query({'value': 2}))
    assert_false(query({'value': 1}))


def test_lt():
    query = field('value') < 1
    assert_true(query({'value': 0}))
    assert_false(query({'value': 1}))


def test_le():
    query = field('value') <= 1
    assert_true(query({'value': 0}))
    assert_true(query({'value': 1}))
    assert_false(query({'value': 2}))

def test_gt():
    query = field('value') > 1
    assert_true(query({'value': 2}))
    assert_false(query({'value': 1}))


def test_ge():
    query = field('value') >= 1
    assert_true(query({'value': 2}))
    assert_true(query({'value': 1}))
    assert_false(query({'value': 0}))


def test_or():
    query = (
        (field('val1') == 1) |
        (field('val2') == 2)
    )
    assert_true(query({'val1': 1}))
    assert_true(query({'val2': 2}))
    assert_true(query({'val1': 1, 'val2': 2}))
    assert_false(query({'val1': '', 'val2': ''}))


def test_and():
    query = (
        (field('val1') == 1) &
        (field('val2') == 2)
    )
    assert_true(query({'val1': 1, 'val2': 2}))
    assert_false(query({'val1': 1}))
    assert_false(query({'val2': 2}))
    assert_false(query({'val1': '', 'val2': ''}))


def test_not():
    query = ~ (field('val1') == 1)
    assert_true(query({'val1': 5, 'val2': 2}))
    assert_false(query({'val1': 1, 'val2': 2}))

    query = (
        (~ (field('val1') == 1)) &
        (field('val2') == 2)
    )
    assert_true(query({'val1': '', 'val2': 2}))
    assert_true(query({'val2': 2}))
    assert_false(query({'val1': 1, 'val2': 2}))
    assert_false(query({'val1': 1}))
    assert_false(query({'val1': '', 'val2': ''}))


def test_has_key():
    query = field('val3')

    assert_true(query({'val3': 1}))
    assert_false(query({'val1': 1, 'val2': 2}))


def test_regex():
    query = field('val').matches(r'\d{2}\.')

    assert_true(query({'val': '42.'}))
    assert_false(query({'val': '44'}))
    assert_false(query({'val': 'ab.'}))
    assert_false(query({'': None}))


def test_custom():
    def test(value):
        return value == 42

    query = field('val').test(test)

    assert_true(query({'val': 42}))
    assert_false(query({'val': 40}))
    assert_false(query({'val': '44'}))
    assert_false(query({'': None}))
