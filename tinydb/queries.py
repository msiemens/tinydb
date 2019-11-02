"""
Contains the querying interface.

Starting with :class:`~tinydb.queries.Query` you can construct complex
queries:

>>> ((where('f1') == 5) & (where('f2') != 2)) | where('s').matches(r'^\\w+$')
(('f1' == 5) and ('f2' != 2)) or ('s' ~= ^\\w+$ )

Queries are executed by using the ``__call__``:

>>> q = where('val') == 5
>>> q({'val': 5})
True
>>> q({'val': 1})
False
"""

import re
from typing import Mapping, Tuple, Callable, Any, Union, List, overload

from .utils import freeze

__all__ = ('Query', 'where')


def is_sequence(obj):
    return hasattr(obj, '__iter__')


class QueryImpl:
    """
    A query implementation.

    This query implementation wraps a test function which is run when the
    query is evaluated by calling the object.

    Queries can be combined with logical and/or and modified with logical not.
    """

    def __init__(self, test: Callable[[Mapping], bool], hashval: Tuple):
        self._test = test
        self.hashval = hashval

    def __call__(self, value: Mapping) -> bool:
        return self._test(value)

    def __hash__(self):
        return hash(self.hashval)

    def __repr__(self):
        return 'QueryImpl{}'.format(self.hashval)

    def __eq__(self, other: object):
        if isinstance(other, QueryImpl):
            return self.hashval == other.hashval

        return False

    # --- Query modifiers -----------------------------------------------------

    def __and__(self, other: 'QueryImpl') -> 'QueryImpl':
        # We use a frozenset for the hash as the AND operation is commutative
        # (a & b == b & a)
        return QueryImpl(lambda value: self(value) and other(value),
                         ('and', frozenset([self.hashval, other.hashval])))

    def __or__(self, other: 'QueryImpl') -> 'QueryImpl':
        # We use a frozenset for the hash as the OR operation is commutative
        # (a | b == b | a)
        return QueryImpl(lambda value: self(value) or other(value),
                         ('or', frozenset([self.hashval, other.hashval])))

    def __invert__(self) -> 'QueryImpl':
        return QueryImpl(lambda value: not self(value),
                         ('not', self.hashval))


class Query(QueryImpl):
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

    >>> # Binary AND:
    >>> db.search((where('field1').exists()) & (where('field2') == 5))
    >>> # Binary OR:
    >>> db.search((where('field1').exists()) | (where('field2') == 5))

    Queries are executed by calling the resulting object. They expect to get
    the document to test as the first argument and return ``True`` or
    ``False`` depending on whether the documents matches the query or not.
    """

    def __init__(self):
        self._path = ()
        super().__init__(
            self._prepare_test(lambda _: True),
            ('path', self._path)
        )

    def __repr__(self):
        return '{}()'.format(type(self).__name__)

    def __hash__(self):
        return super().__hash__()

    def __getattr__(self, item: str):
        query = type(self)()
        query._path = self._path + (item,)
        query.hashval = ('path', query._path)

        return query

    def __getitem__(self, item: str):
        return getattr(self, item)

    def _prepare_test(
            self,
            test: Callable[[Mapping], bool],
    ) -> Callable[[Mapping], bool]:
        def runner(value):
            try:
                # Resolve the path
                for part in self._path:
                    value = value[part]
            except (KeyError, TypeError):
                return False
            else:
                return test(value)

        return runner

    def _generate_test(
            self,
            test: Callable[[Any], bool],
            hashval: Tuple,
    ) -> QueryImpl:
        """
        Generate a query based on a test function.

        :param test: The test the query executes.
        :param hashval: The hash of the query.
        :return: A :class:`~tinydb.queries.QueryImpl` object
        """
        if not self._path:
            raise ValueError('Query has no path')

        return QueryImpl(self._prepare_test(test), hashval)

    def __eq__(self, rhs: Any):
        """
        Test a dict value for equality.

        >>> Query().f1 == 42

        :param rhs: The value to compare against
        """

        def test(value):
            return value == rhs

        return self._generate_test(
            lambda value: test(value),
            ('==', self._path, freeze(rhs))
        )

    def __ne__(self, rhs: Any):
        """
        Test a dict value for inequality.

        >>> Query().f1 != 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value != rhs,
            ('!=', self._path, freeze(rhs))
        )

    def __lt__(self, rhs: Any) -> QueryImpl:
        """
        Test a dict value for being lower than another value.

        >>> Query().f1 < 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value < rhs,
            ('<', self._path, rhs)
        )

    def __le__(self, rhs: Any) -> QueryImpl:
        """
        Test a dict value for being lower than or equal to another value.

        >>> where('f1') <= 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value <= rhs,
            ('<=', self._path, rhs)
        )

    def __gt__(self, rhs: Any) -> QueryImpl:
        """
        Test a dict value for being greater than another value.

        >>> Query().f1 > 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value > rhs,
            ('>', self._path, rhs)
        )

    def __ge__(self, rhs: Any) -> QueryImpl:
        """
        Test a dict value for being greater than or equal to another value.

        >>> Query().f1 >= 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value >= rhs,
            ('>=', self._path, rhs)
        )

    def exists(self) -> QueryImpl:
        """
        Test for a dict where a provided key exists.

        >>> Query().f1.exists()
        """
        return self._generate_test(
            lambda _: True,
            ('exists', self._path)
        )

    def matches(self, regex: str, flags: int = 0) -> QueryImpl:
        """
        Run a regex test against a dict value (whole string has to match).

        >>> Query().f1.matches(r'^\\w+$')

        :param regex: The regular expression to use for matching
        :param flags: regex flags to pass to ``re.match``
        """
        return self._generate_test(
            lambda value: re.match(regex, value, flags) is not None,
            ('matches', self._path, regex)
        )

    def search(self, regex: str, flags: int = 0) -> QueryImpl:
        """
        Run a regex test against a dict value (only substring string has to
        match).

        >>> Query().f1.search(r'^\\w+$')

        :param regex: The regular expression to use for matching
        :param flags: regex flags to pass to ``re.match``
        """
        return self._generate_test(
            lambda value: re.search(regex, value, flags) is not None,
            ('search', self._path, regex)
        )

    def test(self, func: Callable[[Mapping], bool], *args) -> QueryImpl:
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
        return self._generate_test(
            lambda value: func(value, *args),
            ('test', self._path, func, args)
        )

    def any(self, cond: Union[QueryImpl, List[Any]]) -> QueryImpl:
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
        """
        if callable(cond):
            def _cmp(value):
                return is_sequence(value) and any(cond(e) for e in value)

        else:
            def _cmp(value):
                return is_sequence(value) and any(e in cond for e in value)

        return self._generate_test(
            lambda value: _cmp(value),
            ('any', self._path, freeze(cond))
        )

    def all(self, cond: Union['QueryImpl', List[Any]]) -> QueryImpl:
        """
        Check if a condition is met by all documents in a list,
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

        return self._generate_test(
            lambda value: _cmp(value),
            ('all', self._path, freeze(cond))
        )

    def one_of(self, items: List[Any]) -> QueryImpl:
        """
        Check if the value is contained in a list or generator.

        >>> Query().f1.one_of(['value 1', 'value 2'])

        :param items: The list of items to check with
        """
        return self._generate_test(
            lambda value: value in items,
            ('one_of', self._path, freeze(items))
        )


def where(key: str) -> Query:
    return Query()[key]
