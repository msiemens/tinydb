"""
Contains the querying interface.

Starting with :class:`~tinydb.queries.Query` you can construct complex
queries:

>>> ((where('f1') == 5) & (where('f2') != 2)) | where('s').matches('^\w+$')
(('f1' == 5) and ('f2' != 2)) or ('s' ~= ^\w+$ )

Queries are executed by using the ``__call__``:

>>> q = where('val') == 5
>>> q({'val': 5})
True
>>> q({'val': 1})
False
"""

import re

__all__ = ('Query',)


def methodproxy(attribute, method):
    """
    Utility function for delegating a specific method to another
    given attribute.

    :param attribute: The instance attribute to delegate to
    :param method: A method that the attribute object must have
    """
    def fn(self, *args, **kwargs):
        getattr(getattr(self, attribute), method)(*args, **kwargs)
        return self
    return fn


def haskey(key, datum):
    """
    Checks whether a nested key is in a datum.

    :param key: A sequence of keys splitted by '.'
    :param datum: The datum to test
    """
    keys = key.split('.')
    for key in keys[:-1]:
        if not isinstance(datum, dict) or key not in datum:
            return False
        datum = datum[key]
    return keys[-1] in datum


def getkey(key, datum):
    """
    Provides nested fetching of values.

    :param key: A sequence of keys splitted by '.'
    :param datum: The datum to select from
    """
    for item in key.split('.'):
        datum = datum[item]
    return datum


class AndOrMixin(object):
    """
    A mixin providing methods calls ``&`` and ``|``.

    All queries can be combined with ``&`` and ``|``. Thus, we provide a mixin
    here to prevent repeating this code all the time.
    """
    def __or__(self, other):
        """
        Combines this query and another with logical or.

        Example:

        >>> (where('f1') == 5) | (where('f2') != 2)
        ('f1' == 5) or ('f2' != 2)

        :rtype: QueryOr
        """
        return QueryOr(self, other)

    def __and__(self, other):
        """
        Combines this query and another with logical and.

        Example:

        >>> (where('f1') == 5) & (where('f2') != 2)
        ('f1' == 5) and ('f2' != 2)

        :rtype: QueryAnd
        """
        return QueryAnd(self, other)

    def any(self, key):
        """
        Create a compound query that will check if any of the
        data under a given key (which must be an iterable) is
        said to be correct with a given query function.

        Example:
        >>> (where('key').any('a') == 2)({'key': {'a': [1,2,3]}})
        True
        """
        return QueryAny(self._key, Query(key))


class Query(AndOrMixin):
    """
    Provides methods to do tests on dict fields.

    Any type of comparison will be called in this class. In addition,
    it is aliased to :data:`where` to provide a more intuitive syntax.

    When not using any comparison operation, this simply tests for existence
    of the given key.
    """

    def __init__(self, key):
        self._key = key
        self._func = lambda x: True
        self._repr = 'has \'{0}\''.format(key)

    def matches(self, regex):
        """
        Run a regex test against a dict value.

        >>> where('f1').matches('^\w+$')
        'f1' ~= ^\w+$

        :param regex: The regular expression to pass to ``re.match``
        :rtype: QueryRegex
        """
        return QueryRegex(self._key, regex)

    def test(self, func):
        """
        Run a user-defined test function against a dict value.

        >>> def test_func(val):
        ...     return val == 42
        ...
        >>> where('f1').test(test_func)
        'f1'.test(<function test_func at 0x029950F0>)

        :param func: The function to run. Has to accept one parameter and
            return a boolean.
        :rtype: QueryCustom
        """
        return QueryCustom(self._key, func)

    def __eq__(self, other):
        """
        Test a dict value for equality.

        >>> where('f1') == 42
        'f1' == 42
        """
        if isinstance(other, Query):
            return self._repr == other._repr
        else:
            self._func = lambda x: x == other
            self._update_repr('==', other)
            return self

    def __ne__(self, other):
        """
        Test a dict value for inequality.

        >>> where('f1') != 42
        'f1' != 42
        """
        self._func = lambda x: x != other
        self._update_repr('!=', other)
        return self

    def __lt__(self, other):
        """
        Test a dict value for being lower than another value.

        >>> where('f1') < 42
        'f1' < 42
        """
        self._func = lambda x: x < other
        self._update_repr('<', other)
        return self

    def __le__(self, other):
        """
        Test a dict value for being lower than or equal to another value.

        >>> where('f1') <= 42
        'f1' <= 42
        """
        self._func = lambda x: x <= other
        self._update_repr('<=', other)
        return self

    def __gt__(self, other):
        """
        Test a dict value for being greater than another value.

        >>> where('f1') > 42
        'f1' > 42
        """
        self._func = lambda x: x > other
        self._update_repr('>', other)
        return self

    def __ge__(self, other):
        """
        Test a dict value for being greater than or equal to another value.

        >>> where('f1') >= 42
        'f1' >= 42
        """
        self._func = lambda x: x >= other
        self._update_repr('>=', other)
        return self

    def __invert__(self):
        """
        Negates a query.

        >>> ~(where('f1') >= 42)
        not ('f1' >= 42)

        :rtype: tinydb.queries.QueryNot
        """
        return QueryNot(self)

    def __call__(self, element):
        """
        Run the test on the element.

        :param element: The dict that we will run our tests against.
        :type element: dict
        """
        return (haskey(self._key, element)
                and self._func(getkey(self._key, element)))

    def _update_repr(self, operator, value):
        """ Update the current test's ``repr``. """
        self._repr = '\'{0}\' {1} {2}'.format(self._key, operator, value)

    def __repr__(self):
        return self._repr

    def __hash__(self):
        return hash(repr(self))

where = Query


class QueryNot(AndOrMixin):
    """
    Negates a query.

    >>> ~(where('f1') >= 42)
    not ('f1' >= 42)
    """
    def __init__(self, cond):
        self._cond = cond

    def __call__(self, element):
        """
        Run the test on the element.

        :param element: The dict that we will run our tests against.
        :type element: dict
        """
        return not self._cond(element)

    def __repr__(self):
        return 'not ({0})'.format(self._cond)


class QueryOr(AndOrMixin):
    """
    Combines this query and another with logical or.

    See :meth:`AndOrMixin.__or__`.
    """
    def __init__(self, where1, where2):
        self._cond_1 = where1
        self._cond_2 = where2

    def __call__(self, element):
        """
        See :meth:`Query.__call__`.
        """
        return self._cond_1(element) or self._cond_2(element)

    def __repr__(self):
        return '({0}) or ({1})'.format(self._cond_1, self._cond_2)


class QueryAnd(AndOrMixin):
    """
    Combines this query and another with logical and.

    See :meth:`AndOrMixin.__and__`.
    """
    def __init__(self, where1, where2):
        self._cond_1 = where1
        self._cond_2 = where2

    def __call__(self, element):
        """
        See :meth:`Query.__call__`.
        """
        return self._cond_1(element) and self._cond_2(element)

    def __repr__(self):
        return '({0}) and ({1})'.format(self._cond_1, self._cond_2)


class QueryRegex(AndOrMixin):
    """
    Run a regex test against a dict value.

    See :meth:`Query.matches`.
    """
    def __init__(self, key, regex):
        self.regex = regex
        self._func = lambda x: re.match(self.regex, x)
        self._key = key

    def __call__(self, element):
        """
        See :meth:`Query.__call__`.
        """
        return haskey(self._key, element) and self._func(getkey(self._key, element))

    def __repr__(self):
        return '\'{0}\' ~= {1} '.format(self._key, self.regex)


class QueryCustom(AndOrMixin):
    """
    Run a user-defined test function against a dict value.

    See :meth:`Query.test`.
    """

    def __init__(self, key, test):
        self._func = test
        self._key = key

    def __call__(self, element):
        """
        See :meth:`Query.__call__`.
        """
        return haskey(self._key, element) and self._func(getkey(self._key, element))

    def __repr__(self):
        return '\'{0}\'.test({1})'.format(self._key, self._func)


class QueryAny(Query):
    def __init__(self, key, query):
        self._key = key
        self._query = query

    __eq__ = methodproxy('_query', '__eq__')
    __ne__ = methodproxy('_query', '__ne__')
    __gt__ = methodproxy('_query', '__gt__')
    __ge__ = methodproxy('_query', '__ge__')
    __lt__ = methodproxy('_query', '__lt__')
    __le__ = methodproxy('_query', '__le__')

    def matches(self, *args, **kwargs):
        self._query = self._query.matches(*args, **kwargs)
        return self

    def test(self, *args, **kwargs):
        self._query = self._query.test(*args, **kwargs)
        return self

    def __repr__(self):
        return "'{0}'.each({1})".format(self._key, self._query)

    def __call__(self, element):
        if haskey(self._key, element):
            datum = getkey(self._key, element)
            if haskey(self._query._key, datum):
                iterable = getkey(self._query._key, datum)
                if not hasattr(iterable, '__iter__'):
                    return False
                return any(self._query._func(e) for e in iterable)
        return False
