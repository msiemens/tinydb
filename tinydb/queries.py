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

__all__ = ('Query',)


def is_sequence(obj):
    return hasattr(obj, '__iter__')


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
        self._cmp = None
        self._repr = 'has \'{0}\''.format(key)

    def matches(self, regex):
        """
        Run a regex test against a dict value (whole string has to match).

        >>> where('f1').matches(r'^\w+$')
        'f1' ~= ^\w+$

        :param regex: The regular expression to pass to ``re.match``
        :rtype: QueryRegex
        """

        return QueryRegex(self._key, regex, re_method='match')

    def contains(self, regex):
        """
        Run a regex test against a dict value (only substring has to match).

        >>> where('f1').contains(r'\d+')
        'f1' ~= \d+

        :param regex: The regular expression to pass to ``re.search``
        :rtype: QueryRegex
        """

        return QueryRegex(self._key, regex, re_method='search')

    def test(self, func, *args):
        """
        Run a user-defined test function against a dict value.

        >>> def test_func(val):
        ...     return val == 42
        ...
        >>> where('f1').test(test_func)
        'f1'.test(<function test_func at 0xXXXXXXXX>)

        >>> def test_func_with_params(val, minimum, maximum):
        ...     return minimum <= val <= maximum
        ...
        >>> where('f2').test(test_func_with_params, 1, 10)
        'f2'.test(<function test_func_with_params at 0xXXXXXXXX>)

        :param func: The function to run. Has to accept one parameter and
            return a boolean.
        :param args: Optional list of additional parameters to pass
            to the function.
        :rtype: QueryCustom
        """

        return QueryCustom(self._key, func, args)

    def has(self, key):
        """
        Run test on a nested dict.

        >>> where('x').has('y') == 2
        has 'x' => ('y' == 2)

        Matches::

            {'x': {'y': 2}}

        :param key: the key to search for in the nested dict
        :rtype: QueryHas
        """

        return QueryHas(self._key, key)

    def any(self, cond):
        """
        Checks if a condition is met by any element in a list,
        where a condition can also be a sequence (e.g. list).

        >>> where('f1').any(where('f2') == 1)
        'f1' has any 'f2' == 1

        Matches::

            {'f1': [{'f2': 1}, {'f2': 0}]}

        >>> where('f1').any([1, 2, 3])
        'f1' has any [1, 2, 3]

        Matches::

            {'f1': [1, 2]}
            {'f1': [3, 4, 5]}

        :param cond: The condition to check
        :rtype: tinydb.queries.Query
        """

        # Check for condition type
        if callable(cond):
            def _cmp(value):
                return is_sequence(value) and any(cond(e) for e in value)

        else:
            def _cmp(value):
                return is_sequence(value) and any(e in cond for e in value)

        self._cmp = _cmp
        self._repr = '\'{0}\' has any {1}'.format(self._key, cond)
        return self

    def all(self, cond):
        """
        Checks if a condition is met by any element in a list,
        where a condition can also be a sequence (e.g. list).

        >>> where('f1').all(where('f2') == 1)
        'f1' all have 'f2' == 1

        Matches::

            {'f1': [{'f2': 1}, {'f2': 1}]}

        >>> where('f1').all([{'f2': 1}, {'f3': 2}])
        'f1' all have [{'f2': 1}, {'f3': 2}]

        Matches::

            {'f1': [{'f2': 1}, {'f3': 2}]}
            {'f1': [{'f2': 1}, {'f3': 2}, {'f4': 3}]}

        :param cond: The condition to check
        :rtype: tinydb.queries.Query
        """

        # Check for condition type
        if callable(cond):
            def _cmp(value):
                return is_sequence(value) and all(cond(e) for e in value)

        else:
            def _cmp(value):
                return is_sequence(value) and all(e in value for e in cond)

        self._cmp = _cmp
        self._repr = '\'{0}\' all have {1}'.format(self._key, cond)
        return self

    def __eq__(self, other):
        """
        Test a dict value for equality.

        >>> where('f1') == 42
        'f1' == 42
        """

        if isinstance(other, Query):
            return self._repr == other._repr

        if sys.version_info <= (3, 0):  # pragma: no cover
            # Special UTF-8 handling on Python 2
            def _cmp(value):
                with catch_warning(UnicodeWarning):
                    try:
                        return value == other
                    except UnicodeWarning:
                        # Dealing with a case, where 'value' or 'other'
                        # is unicode and the other is a byte string.
                        if isinstance(value, str):
                            return value.decode('utf-8') == other
                        elif isinstance(other, str):
                            return value == other.decode('utf-8')

            self._cmp = _cmp

        else:  # pragma: no cover
            self._cmp = lambda value: value == other

        self._update_repr('==', other)
        return self

    def __ne__(self, other):
        """
        Test a dict value for inequality.

        >>> where('f1') != 42
        'f1' != 42
        """

        self._cmp = lambda value: value != other
        self._update_repr('!=', other)
        return self

    def __lt__(self, other):
        """
        Test a dict value for being lower than another value.

        >>> where('f1') < 42
        'f1' < 42
        """

        self._cmp = lambda value: value < other
        self._update_repr('<', other)
        return self

    def __le__(self, other):
        """
        Test a dict value for being lower than or equal to another value.

        >>> where('f1') <= 42
        'f1' <= 42
        """

        self._cmp = lambda value: value <= other
        self._update_repr('<=', other)
        return self

    def __gt__(self, other):
        """
        Test a dict value for being greater than another value.

        >>> where('f1') > 42
        'f1' > 42
        """

        self._cmp = lambda value: value > other
        self._update_repr('>', other)
        return self

    def __ge__(self, other):
        """
        Test a dict value for being greater than or equal to another value.

        >>> where('f1') >= 42
        'f1' >= 42
        """

        self._cmp = lambda value: value >= other
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

    def __and__(self, other):
        """
        Combines this query and another with logical and.

        Example:

        >>> (where('f1') == 5) & (where('f2') != 2)
        ('f1' == 5) and ('f2' != 2)

        :rtype: QueryAnd
        """

        return super(Query, self).__and__(other)

    def __or__(self, other):
        """
        Combines this query and another with logical or.

        Example:

        >>> (where('f1') == 5) | (where('f2') != 2)
        ('f1' == 5) or ('f2' != 2)

        :rtype: QueryOr
        """

        return super(Query, self).__or__(other)

    def __call__(self, element):
        """
        Run the test on the element.

        :param element: The dict that we will run our tests against.
        :type element: dict
        """

        # Check for key existence
        if self._key not in element:
            return False

        # Check, if a comparator has been set
        if self._cmp:
            return self._cmp(element[self._key])
        else:
            return True  # Key exists

    def _update_repr(self, operator, value):
        """
        Update the current test's ``repr``.
        """

        self._repr = '{0!r} {1} {2!r}'.format(self._key, operator, value)

    def __repr__(self):
        return self._repr

    def __hash__(self):
        # Queries have to be hashable because the query cache is implemented
        # as an dict where the keys are Query objects. The hash should be
        # the same for objects with the same, so we can use the repr for this.
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

    See :meth:`.AndOrMixin.__or__`.
    """

    def __init__(self, where1, where2):
        self._cond_1 = where1
        self._cond_2 = where2

    def __call__(self, element):
        """
        See :meth:`.Query.__call__`.
        """

        return self._cond_1(element) or self._cond_2(element)

    def __repr__(self):
        return '({0}) or ({1})'.format(self._cond_1, self._cond_2)


class QueryAnd(AndOrMixin):
    """
    Combines this query and another with logical and.

    See :meth:`.AndOrMixin.__and__`.
    """

    def __init__(self, where1, where2):
        self._cond_1 = where1
        self._cond_2 = where2

    def __call__(self, element):
        """
        See :meth:`.Query.__call__`.
        """

        return self._cond_1(element) and self._cond_2(element)

    def __repr__(self):
        return '({0}) and ({1})'.format(self._cond_1, self._cond_2)


class QueryRegex(AndOrMixin):
    """
    Run a regex test against a dict value.

    See :meth:`.Query.matches`.
    """

    def __init__(self, key, regex, re_method):
        self.regex = regex
        self._key = key
        self._re_method = re_method

    def __call__(self, element):
        """
        See :meth:`.Query.__call__`.
        """

        if self._key not in element:
            return False

        if self._re_method == 'match':
            return re.match(self.regex, element[self._key])

        if self._re_method == 'search':
            return re.search(self.regex, element[self._key])

    def __repr__(self):
        return '\'{0}\' {1} /{2}/'.format(self._key, self._re_method,
                                          self.regex)

    def __hash__(self):
        return hash(repr(self))


class QueryCustom(AndOrMixin):
    """
    Run a user-defined test function against a dict value.

    See :meth:`.Query.test`.
    """

    def __init__(self, key, test, args):
        self.test = test
        self.args = args
        self.key = key

    def __call__(self, element):
        """
        See :meth:`.Query.__call__`.
        """

        if self.key not in element:
            return False

        return self.test(element[self.key], *self.args)

    def __repr__(self):
        return '\'{0}\'.test({1})'.format(self.key, self.test)


class QueryHas(Query):
    """
    Run a query on a nested dict.

    See :meth:`.Query.has`
    """

    def __init__(self, root, key):
        super(QueryHas, self).__init__(key)
        self._special = None
        self._path = [root]  # Store the path to the element to check

    def matches(self, regex):
        """
        See :meth:`.Query.matches`.
        """

        self._special = QueryRegex(self._key, regex, re_method='match')
        return self

    def contains(self, regex):
        """
        See :meth:`.Query.search`.
        """

        self._special = QueryRegex(self._key, regex, re_method='search')
        return self

    def test(self, func, *args):
        """
        See :meth:`.Query.test`.
        """

        self._special = QueryCustom(self._key, func, args)
        return self

    def has(self, key):
        """
        See :meth:`.Query.has`.
        """

        # Nested has: Append old key to path and use given key from now on
        self._path.append(self._key)
        self._key = key
        return self

    def __call__(self, element):
        """
        See :meth:`.Query.__call__`.
        """

        # Retrieve value from given path
        for key in self._path:
            try:
                # Check, if requested key exists
                if key not in element:
                    return False

            except (KeyError, TypeError):
                # We can't continue searching because either ...
                # - the element contains a value instead of a dict (TypeError)
                # - or doesn't contain the key (KeyError)
                return False

            # Follow the path and continue searching
            element = element[key]

        # Verify the element is a dict where we can run the test
        # Fixes searching for 'x' => 'y' in {'x': {'y': 2}}
        if not isinstance(element, dict):
            return False

        if self._special:
            # Process special test
            return self._special(element)

        else:
            # Process like a normal query
            return super(QueryHas, self).__call__(element)

    def __repr__(self):
        path = self._path[:]

        if not self._special and not self._cmp:
            path += [self._key]

        repr_str = 'has '
        # 'key1' => 'key2' => ...
        repr_str += '\'' + '\' => \''.join(path) + '\''

        if self._special:
            repr_str += ' => ({})'.format(self._special)

        elif self._cmp:
            repr_str += ' => ({})'.format(super(QueryHas, self).__repr__())

        return repr_str
