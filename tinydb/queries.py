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

from .utils import catch_warning, freeze

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
        return 'QueryImpl{0}'.format(self.hashval)

    def __eq__(self, other):
        return self.hashval == other.hashval

    # --- Query modifiers -----------------------------------------------------

    def __and__(self, other):
        # We use a frozenset for the hash as the AND operation is commutative
        # (a | b == b | a)
        return QueryImpl(lambda value: self(value) and other(value),
                         ('and', frozenset([self.hashval, other.hashval])))

    def __or__(self, other):
        # We use a frozenset for the hash as the OR operation is commutative
        # (a & b == b & a)
        return QueryImpl(lambda value: self(value) or other(value),
                         ('or', frozenset([self.hashval, other.hashval])))

    def __invert__(self):
        return QueryImpl(lambda value: not self(value),
                         ('not', self.hashval))


class Query(object):
    """
    TinyDB Queries.

    Allows to build queries for TinyDB databases. There are two main ways of
    using queries:

    1) ORM-like usage:

    >>> User = Query()
    >>> db.search(User.name == 'John Doe')
    >>> db.search(User['logged-in'] == True)

    2) Classical usage:

    >>> db.search(where('value') == True)

    Note that ``where(...)`` is a shorthand for ``Query(...)`` allowing for
    a more fluent syntax.

    Besides the methods documented here you can combine queries using the
    binary AND and OR operators:

    >>> db.search(where('field1').exists() & where('field2') == 5) # Binary AND
    >>> db.search(where('field1').exists() | where('field2') == 5) # Binary OR

    Queries are executed by calling the resulting object. They expect to get
    the document to test as the first argument and return ``True`` or
    ``False`` depending on whether the documents matches the query or not.
    """

    def __init__(self):
        self._path = []

    def __getattr__(self, item):
        query = Query()
        query._path = self._path + [item]

        return query

    __getitem__ = __getattr__

    def _generate_test(self, test, hashval):
        """
        Generate a query based on a test function.

        :param test: The test the query executes.
        :param hashval: The hash of the query.
        :return: A :class:`~tinydb.queries.QueryImpl` object
        """
        if not self._path:
            raise ValueError('Query has no path')

        def impl(value):
            try:
                # Resolve the path
                for part in self._path:
                    value = value[part]
            except (KeyError, TypeError):
                return False
            else:
                return test(value)

        return QueryImpl(impl, hashval)

    def __eq__(self, rhs):
        """
        Test a dict value for equality.

        >>> Query().f1 == 42

        :param rhs: The value to compare against
        """
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
                                   ('==', tuple(self._path), freeze(rhs)))

    def __ne__(self, rhs):
        """
        Test a dict value for inequality.

        >>> Query().f1 != 42

        :param rhs: The value to compare against
        """
        return self._generate_test(lambda value: value != rhs,
                                   ('!=', tuple(self._path), freeze(rhs)))

    def __lt__(self, rhs):
        """
        Test a dict value for being lower than another value.

        >>> Query().f1 < 42

        :param rhs: The value to compare against
        """
        return self._generate_test(lambda value: value < rhs,
                                   ('<', tuple(self._path), rhs))

    def __le__(self, rhs):
        """
        Test a dict value for being lower than or equal to another value.

        >>> where('f1') <= 42

        :param rhs: The value to compare against
        """
        return self._generate_test(lambda value: value <= rhs,
                                   ('<=', tuple(self._path), rhs))

    def __gt__(self, rhs):
        """
        Test a dict value for being greater than another value.

        >>> Query().f1 > 42

        :param rhs: The value to compare against
        """
        return self._generate_test(lambda value: value > rhs,
                                   ('>', tuple(self._path), rhs))

    def __ge__(self, rhs):
        """
        Test a dict value for being greater than or equal to another value.

        >>> Query().f1 >= 42

        :param rhs: The value to compare against
        """
        return self._generate_test(lambda value: value >= rhs,
                                   ('>=', tuple(self._path), rhs))

    def exists(self):
        """
        Test for a dict where a provided key exists.

        >>> Query().f1.exists() >= 42

        :param rhs: The value to compare against
        """
        return self._generate_test(lambda _: True,
                                   ('exists', tuple(self._path)))

    def matches(self, regex):
        """
        Run a regex test against a dict value (whole string has to match).

        >>> Query().f1.matches(r'^\w+$')

        :param regex: The regular expression to use for matching
        """
        return self._generate_test(lambda value: re.match(regex, value),
                                   ('matches', tuple(self._path), regex))

    def search(self, regex):
        """
        Run a regex test against a dict value (only substring string has to
        match).

        >>> Query().f1.search(r'^\w+$')

        :param regex: The regular expression to use for matching
        """
        return self._generate_test(lambda value: re.search(regex, value),
                                   ('search', tuple(self._path), regex))

    def test(self, func, *args):
        """
        Run a user-defined test function against a dict value.

        >>> def test_func(val):
        ...     return val == 42
        ...
        >>> Query().f1.test(test_func)

        :param func: The function to call, passing the dict as the first
                     argument
        :param args: Additional arguments to pass to the test function
        """
        return self._generate_test(lambda value: func(value, *args),
                                   ('test', tuple(self._path), func, args))

    def any(self, cond):
        """
        Check if a condition is met by any document in a list,
        where a condition can also be a sequence (e.g. list).

        >>> Query().f1.any(Query().f2 == 1)

        Matches::

            {'f1': [{'f2': 1}, {'f2': 0}]}

        >>> Query().f1.any([1, 2, 3])

        Matches::

            {'f1': [1, 2]}
            {'f1': [3, 4, 5]}

        :param cond: Either a query that at least one document has to match or
                     a list of which at least one document has to be contained
                     in the tested document.
-       """
        if callable(cond):
            def _cmp(value):
                return is_sequence(value) and any(cond(e) for e in value)

        else:
            def _cmp(value):
                return is_sequence(value) and any(e in cond for e in value)

        return self._generate_test(lambda value: _cmp(value),
                                   ('any', tuple(self._path), freeze(cond)))

    def all(self, cond):
        """
        Check if a condition is met by any document in a list,
        where a condition can also be a sequence (e.g. list).

        >>> Query().f1.all(Query().f2 == 1)

        Matches::

            {'f1': [{'f2': 1}, {'f2': 1}]}

        >>> Query().f1.all([1, 2, 3])

        Matches::

            {'f1': [1, 2, 3, 4, 5]}

        :param cond: Either a query that all documents have to match or a list
                     which has to be contained in the tested document.
        """
        if callable(cond):
            def _cmp(value):
                return is_sequence(value) and all(cond(e) for e in value)

        else:
            def _cmp(value):
                return is_sequence(value) and all(e in value for e in cond)

        return self._generate_test(lambda value: _cmp(value),
                                   ('all', tuple(self._path), freeze(cond)))

    def one_of(self, items):
        """
        Check if the value is contained in a list or generator.

        >>> Query().f1.one_of(['value 1', 'value 2'])

        :param items: The list of items to check with
        """
        return self._generate_test(lambda value: value in items,
                                   ('one_of', tuple(self._path), freeze(items)))


def where(key):
    return Query()[key]
