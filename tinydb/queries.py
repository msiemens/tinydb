"""
Contains the querying interface.

Starting with :class:`~tinydb.queries.Query` you can construct complex
queries:

>>> ((where('f1') == 5) & (where('f2') != 2)) | where('s').matches(r'^\w+$')
(('f1' == 5) and ('f2' != 2)) or ('s' ~= ^\w+$ )

Queries are executed by using the ``__call__``:

>>> q = where('val') == 5
>>> q({'val': 5})
True
>>> q({'val': 1})
False
"""

import re
import sys

from tinydb.utils import catch_warning

__all__ = ('Query', 'where')


def is_sequence(obj):
    return hasattr(obj, '__iter__')


class QueryImpl(object):
    """
    A query implementation.

    This query implementation wraps a test function which is run when the
    query is evaluated by calling the object.

    Queries can be combined with logical and/or and modified with logical not.
    """
    def __init__(self, test, hashval):
        self.test = test
        self.hashval = hashval

    def __call__(self, value):
        return self.test(value)

    def __hash__(self):
        return hash(self.hashval)

    def __repr__(self):
        return 'Query{0}'.format(self.hashval)

    def __eq__(self, other):
        return self.hashval == other.hashval

    # --- Query modifiers -----------------------------------------------------

    def __and__(self, other):
        return QueryImpl(lambda value: self(value) and other(value),
                         ('and', self.hashval, other.hashval))

    def __or__(self, other):
        return QueryImpl(lambda value: self(value) or other(value),
                         ('or', self.hashval, other.hashval))

    def __invert__(self):
        return QueryImpl(lambda value: not self(value),
                         ('not', self.hashval))


class Query(object):
    """
    Builds queries.

    TODO: Docs
    """

    def __init__(self, path=None):
        if path is None:
            self.path = []
        else:
            self.path = path

    def __getattr__(self, item):
        return Query(self.path + [item])

    __getitem__ = __getattr__

    def _generate_test(self, test, hashval):
        if not self.path:
            raise ValueError('Query has no path')

        def impl(value):
            try:
                # Resolve the path
                for part in self.path:
                    value = value[part]
            except (KeyError, TypeError):
                return False
            else:
                return test(value)

        return QueryImpl(impl, hashval)

    def __eq__(self, rhs):
        if sys.version_info <= (3, 0):  # pragma: no cover
            # Special UTF-8 handling on Python 2
            def test(value):
                with catch_warning(UnicodeWarning):
                    try:
                        return value == rhs
                    except UnicodeWarning:
                        # Dealing with a case, where 'value' or 'rhs'
                        # is unicode and the other is a byte string.
                        if isinstance(value, str):
                            return value.decode('utf-8') == rhs
                        elif isinstance(rhs, str):
                            return value == rhs.decode('utf-8')

        else:  # pragma: no cover
            def test(value):
                return value == rhs

        return self._generate_test(lambda value: test(value),
                                   ('==', tuple(self.path), rhs))

    def __ne__(self, rhs):
        return self._generate_test(lambda value: value != rhs,
                                   ('!=', tuple(self.path), rhs))

    def __lt__(self, rhs):
        return self._generate_test(lambda value: value < rhs,
                                   ('<', tuple(self.path), rhs))

    def __le__(self, rhs):
        return self._generate_test(lambda value: value <= rhs,
                                   ('<=', tuple(self.path), rhs))

    def __gt__(self, rhs):
        return self._generate_test(lambda value: value > rhs,
                                   ('>', tuple(self.path), rhs))

    def __ge__(self, rhs):
        return self._generate_test(lambda value: value >= rhs,
                                   ('>=', tuple(self.path), rhs))

    def exists(self):
        return self._generate_test(lambda _: True,
                                   ('exists', tuple(self.path)))

    def matches(self, regex):
        return self._generate_test(lambda value: re.match(regex, value),
                                   ('matches', tuple(self.path), regex))

    def search(self, regex):
        return self._generate_test(lambda value: re.search(regex, value),
                                   ('search', tuple(self.path), regex))

    def test(self, func, *args):
        return self._generate_test(lambda value: func(value, *args),
                                   ('test', tuple(self.path), func, args))

    def any(self, cond):
        if callable(cond):
            def _cmp(value):
                return is_sequence(value) and any(cond(e) for e in value)

        else:
            def _cmp(value):
                return is_sequence(value) and any(e in cond for e in value)

        return self._generate_test(lambda value: _cmp(value),
                                   ('any', tuple(self.path), cond))

    def all(self, cond):
        if callable(cond):
            def _cmp(value):
                return is_sequence(value) and all(cond(e) for e in value)

        else:
            def _cmp(value):
                return is_sequence(value) and all(e in value for e in cond)

        return self._generate_test(lambda value: _cmp(value),
                                   ('all', tuple(self.path), cond))


def where(key):
    return Query()[key]
