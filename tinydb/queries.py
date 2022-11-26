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
import sys
from typing import Mapping, Tuple, Callable, Any, Union, List, Optional

from .utils import freeze

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

__all__ = ('Query', 'QueryLike', 'where')


def is_sequence(obj):
    return hasattr(obj, '__iter__')


class QueryLike(Protocol):
    """
    A typing protocol that acts like a query.

    Something that we use as a query must have two properties:

    1. It must be callable, accepting a `Mapping` object and returning a
       boolean that indicates whether the value matches the query, and
    2. it must have a stable hash that will be used for query caching.

    In addition, to mark a query as non-cacheable (e.g. if it involves
    some remote lookup) it needs to have a method called ``is_cacheable``
    that returns ``False``.

    This query protocol is used to make MyPy correctly support the query
    pattern that TinyDB uses.

    See also https://mypy.readthedocs.io/en/stable/protocols.html#simple-user-defined-protocols
    """
    def __call__(self, value: Mapping) -> bool: ...

    def __hash__(self) -> int: ...


class QueryInstance:
    """
    A query instance.

    This is the object on which the actual query operations are performed. The
    :class:`~tinydb.queries.Query` class acts like a query builder and
    generates :class:`~tinydb.queries.QueryInstance` objects which will
    evaluate their query against a given document when called.

    Query instances can be combined using logical OR and AND and inverted using
    logical NOT.

    In order to be usable in a query cache, a query needs to have a stable hash
    value with the same query always returning the same hash. That way a query
    instance can be used as a key in a dictionary.
    """

    def __init__(self, test: Callable[[Mapping], bool], hashval: Optional[Tuple]):
        self._test = test
        self._hash = hashval

    def is_cacheable(self) -> bool:
        return self._hash is not None

    def __call__(self, value: Mapping) -> bool:
        """
        Evaluate the query to check if it matches a specified value.

        :param value: The value to check.
        :return: Whether the value matches this query.
        """
        return self._test(value)

    def __hash__(self) -> int:
        # We calculate the query hash by using the ``hashval`` object which
        # describes this query uniquely, so we can calculate a stable hash
        # value by simply hashing it
        return hash(self._hash)

    def __repr__(self):
        return 'QueryImpl{}'.format(self._hash)

    def __eq__(self, other: object):
        if isinstance(other, QueryInstance):
            return self._hash == other._hash

        return False

    # --- Query modifiers -----------------------------------------------------

    def __and__(self, other: 'QueryInstance') -> 'QueryInstance':
        # We use a frozenset for the hash as the AND operation is commutative
        # (a & b == b & a) and the frozenset does not consider the order of
        # elements
        if self.is_cacheable() and other.is_cacheable():
            hashval = ('and', frozenset([self._hash, other._hash]))
        else:
            hashval = None
        return QueryInstance(lambda value: self(value) and other(value), hashval)

    def __or__(self, other: 'QueryInstance') -> 'QueryInstance':
        # We use a frozenset for the hash as the OR operation is commutative
        # (a | b == b | a) and the frozenset does not consider the order of
        # elements
        if self.is_cacheable() and other.is_cacheable():
            hashval = ('or', frozenset([self._hash, other._hash]))
        else:
            hashval = None
        return QueryInstance(lambda value: self(value) or other(value), hashval)

    def __invert__(self) -> 'QueryInstance':
        hashval = ('not', self._hash) if self.is_cacheable() else None
        return QueryInstance(lambda value: not self(value), hashval)


class Query(QueryInstance):
    """
    TinyDB Queries.

    Allows building queries for TinyDB databases. There are two main ways of
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
    ``False`` depending on whether the documents match the query or not.
    """

    def __init__(self) -> None:
        # The current path of fields to access when evaluating the object
        self._path: Tuple[Union[str, Callable], ...] = ()

        # Prevent empty queries to be evaluated
        def notest(_):
            raise RuntimeError('Empty query was evaluated')

        super().__init__(
            test=notest,
            hashval=(None,)
        )

    def __repr__(self):
        return '{}()'.format(type(self).__name__)

    def __hash__(self):
        return super().__hash__()

    def __getattr__(self, item: str):
        # Generate a new query object with the new query path
        # We use type(self) to get the class of the current query in case
        # someone uses a subclass of ``Query``
        query = type(self)()

        # Now we add the accessed item to the query path ...
        query._path = self._path + (item,)

        # ... and update the query hash
        query._hash = ('path', query._path) if self.is_cacheable() else None

        return query

    def __getitem__(self, item: str):
        # A different syntax for ``__getattr__``

        # We cannot call ``getattr(item)`` here as it would try to resolve
        # the name as a method name first, only then call our ``__getattr__``
        # method. By calling ``__getattr__`` directly, we make sure that
        # calling e.g. ``Query()['test']`` will always generate a query for a
        # document's ``test`` field instead of returning a reference to the
        # ``Query.test`` method
        return self.__getattr__(item)

    def _generate_test(
            self,
            test: Callable[[Any], bool],
            hashval: Tuple,
            allow_empty_path: bool = False
    ) -> QueryInstance:
        """
        Generate a query based on a test function that first resolves the query
        path.

        :param test: The test the query executes.
        :param hashval: The hash of the query.
        :return: A :class:`~tinydb.queries.QueryInstance` object
        """
        if not self._path and not allow_empty_path:
            raise ValueError('Query has no path')

        def runner(value):
            try:
                # Resolve the path
                for part in self._path:
                    if isinstance(part, str):
                        value = value[part]
                    else:
                        value = part(value)
            except (KeyError, TypeError):
                return False
            else:
                # Perform the specified test
                return test(value)

        return QueryInstance(
            lambda value: runner(value),
            (hashval if self.is_cacheable() else None)
        )

    def __eq__(self, rhs: Any):
        """
        Test a dict value for equality.

        >>> Query().f1 == 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value == rhs,
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

    def __lt__(self, rhs: Any) -> QueryInstance:
        """
        Test a dict value for being lower than another value.

        >>> Query().f1 < 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value < rhs,
            ('<', self._path, rhs)
        )

    def __le__(self, rhs: Any) -> QueryInstance:
        """
        Test a dict value for being lower than or equal to another value.

        >>> where('f1') <= 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value <= rhs,
            ('<=', self._path, rhs)
        )

    def __gt__(self, rhs: Any) -> QueryInstance:
        """
        Test a dict value for being greater than another value.

        >>> Query().f1 > 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value > rhs,
            ('>', self._path, rhs)
        )

    def __ge__(self, rhs: Any) -> QueryInstance:
        """
        Test a dict value for being greater than or equal to another value.

        >>> Query().f1 >= 42

        :param rhs: The value to compare against
        """
        return self._generate_test(
            lambda value: value >= rhs,
            ('>=', self._path, rhs)
        )

    def exists(self) -> QueryInstance:
        """
        Test for a dict where a provided key exists.

        >>> Query().f1.exists()
        """
        return self._generate_test(
            lambda _: True,
            ('exists', self._path)
        )

    def matches(self, regex: str, flags: int = 0) -> QueryInstance:
        """
        Run a regex test against a dict value (whole string has to match).

        >>> Query().f1.matches(r'^\\w+$')

        :param regex: The regular expression to use for matching
        :param flags: regex flags to pass to ``re.match``
        """
        def test(value):
            if not isinstance(value, str):
                return False

            return re.match(regex, value, flags) is not None

        return self._generate_test(test, ('matches', self._path, regex))

    def search(self, regex: str, flags: int = 0) -> QueryInstance:
        """
        Run a regex test against a dict value (only substring string has to
        match).

        >>> Query().f1.search(r'^\\w+$')

        :param regex: The regular expression to use for matching
        :param flags: regex flags to pass to ``re.match``
        """

        def test(value):
            if not isinstance(value, str):
                return False

            return re.search(regex, value, flags) is not None

        return self._generate_test(test, ('search', self._path, regex))

    def test(self, func: Callable[[Mapping], bool], *args) -> QueryInstance:
        """
        Run a user-defined test function against a dict value.

        >>> def test_func(val):
        ...     return val == 42
        ...
        >>> Query().f1.test(test_func)

        .. warning::

            The test function provided needs to be deterministic (returning the
            same value when provided with the same arguments), otherwise this
            may mess up the query cache that :class:`~tinydb.table.Table`
            implements.

        :param func: The function to call, passing the dict as the first
                     argument
        :param args: Additional arguments to pass to the test function
        """
        return self._generate_test(
            lambda value: func(value, *args),
            ('test', self._path, func, args)
        )

    def any(self, cond: Union[QueryInstance, List[Any]]) -> QueryInstance:
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
            def test(value):
                return is_sequence(value) and any(cond(e) for e in value)

        else:
            def test(value):
                return is_sequence(value) and any(e in cond for e in value)

        return self._generate_test(
            lambda value: test(value),
            ('any', self._path, freeze(cond))
        )

    def all(self, cond: Union['QueryInstance', List[Any]]) -> QueryInstance:
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
            def test(value):
                return is_sequence(value) and all(cond(e) for e in value)

        else:
            def test(value):
                return is_sequence(value) and all(e in value for e in cond)

        return self._generate_test(
            lambda value: test(value),
            ('all', self._path, freeze(cond))
        )

    def one_of(self, items: List[Any]) -> QueryInstance:
        """
        Check if the value is contained in a list or generator.

        >>> Query().f1.one_of(['value 1', 'value 2'])

        :param items: The list of items to check with
        """
        return self._generate_test(
            lambda value: value in items,
            ('one_of', self._path, freeze(items))
        )

    def fragment(self, document: Mapping) -> QueryInstance:
        def test(value):
            for key in document:
                if key not in value or value[key] != document[key]:
                    return False

            return True

        return self._generate_test(
            lambda value: test(value),
            ('fragment', freeze(document)),
            allow_empty_path=True
        )

    def noop(self) -> QueryInstance:
        """
        Always evaluate to ``True``.

        Useful for having a base value when composing queries dynamically.
        """

        return QueryInstance(
            lambda value: True,
            ()
        )

    def map(self, fn: Callable[[Any], Any]) -> 'Query':
        """
        Add a function to the query path. Similar to __getattr__ but for
        arbitrary functions.
        """
        query = type(self)()

        # Now we add the callable to the query path ...
        query._path = self._path + (fn,)

        # ... and kill the hash - callable objects can be mutable, so it's
        # harmful to cache their results.
        query._hash = None

        return query

def where(key: str) -> Query:
    """
    A shorthand for ``Query()[key]``
    """
    return Query()[key]
