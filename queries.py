import re

__all__ = 'has'


class AndOrMixin(object):
    """
    A mixin providing methods calls '&' and '|'.

    All queries can be combined with '&' and '|'. Thus, we provide a mixin
    here to prevent repeating this code all the time.
    """
    def __or__(self, other):
        """
        Combines this query and another with logical or.

        Example:
        >>> (field('f1') == 5) | (field('f2') != 2)
        ('f1' == 5) or ('f2' != 2)

        See :class:`query_or`.
        """
        return query_or(self, other)

    def __and__(self, other):
        """
        Combines this query and another with logical and.

        Example:
        >>> (field('f1') == 5) & (field('f2') != 2)
        ('f1' == 5) and ('f2' != 2)

        See :class:`query_and`.
        """
        return query_and(self, other)


class query(AndOrMixin):
    """
    Provides methods to do tests on dict fields.

    Any type of comparison will be called in this class. In addition,
    it is aliased to :data:`field` to provide a more intuitive syntax.

    Example:
    >>> ((field('f1') == 5) & (field('f2') != 2)) | field('s').matches('^\w+$')
    (('f1' == 5) and ('f2' != 2)) or ('s' ~= ^\w+$ )
    """

    def __init__(self, key):
        self._key = key
        self._repr = 'has \'{}\''.format(key)

    def matches(self, regex):
        """
        Run a regex test against a dict value.

        >>> field('f1').matches('^\w+$')
        'f1' ~= ^\w+$

        :param regex: The regular expression to pass to ``re.match``
        """
        return query_regex(self._key, regex)

    def test(self, func):
        """
        Run an user defined test function against a dict value.

        >>> def test_func(val):
        ...     return val == 42
        ...
        >>> field('f1').test(test_func)
        'f1'.test(<function test_func at 0x029950F0>)

        :param func: The function to run. Has to accept one parameter and
        return a boolean.
        """
        return query_custom(self._key, func)

    def __eq__(self, other):
        """
        Test a dict value for equality.

        >>> field('f1') == 42
        'f1' == 42
        """
        self._value_eq = other
        self._update_repr('==', other)
        return self

    def __ne__(self, other):
        """
        Test a dict value for inequality.

        >>> field('f1') != 42
        'f1' != 42
        """
        self._value_ne = other
        self._update_repr('!=', other)
        return self

    def __lt__(self, other):
        """
        Test a dict value for being lower than another value.

        >>> field('f1') < 42
        'f1' < 42
        """
        self._value_lt = other
        self._update_repr('<', other)
        return self

    def __le__(self, other):
        """
        Test a dict value for being lower than or equal to another value.

        >>> field('f1') <= 42
        'f1' <= 42
        """
        self._value_le = other
        self._update_repr('<=', other)
        return self

    def __gt__(self, other):
        """
        Test a dict value for being greater than another value.

        >>> field('f1') > 42
        'f1' > 42
        """
        self._value_gt = other
        self._update_repr('>', other)
        return self

    def __ge__(self, other):
        """
        Test a dict value for being greater than or equal to another value.

        >>> field('f1') >= 42
        'f1' >= 42
        """
        self._value_ge = other
        self._update_repr('>=', other)
        return self

    def __invert__(self):
        """
        Negates a query.

        >>> ~(field('f1') >= 42)
        not ('f1' >= 42)

        See :class:`query_not`.
        """
        return query_not(self)

    def __call__(self, element):
        """
        Run the test on the element.

        :param element: The dict that we will run our tests against.
        :type element: dict
        """
        if self._key not in element:
            return False

        try:
            return element[self._key] == self._value_eq
        except AttributeError:
            pass

        try:
            return element[self._key] != self._value_ne
        except AttributeError:
            pass

        try:
            return element[self._key] < self._value_lt
        except AttributeError:
            pass

        try:
            return element[self._key] <= self._value_le
        except AttributeError:
            pass

        try:
            return element[self._key] > self._value_gt
        except AttributeError:
            pass

        try:
            return element[self._key] >= self._value_ge
        except AttributeError:
            pass

        return True  # _key exists in element (see above)

    def _update_repr(self, operator, value):
        """ Update the current test's ``repr``. """
        self._repr = '\'{}\' {} {}'.format(self._key, operator, value)

    def __repr__(self):
        return self._repr

    def __hash__(self):
        return hash(repr(self))

field = query


class query_not(AndOrMixin):
    """
    Negates a query.

    >>> ~(field('f1') >= 42)
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
        return 'not ({})'.format(self._cond)


class query_or(AndOrMixin):
    """
    See :meth:`AndOrMixin.__or__`.
    """
    def __init__(self, where1, where2):
        self._cond_1 = where1
        self._cond_2 = where2

    def __call__(self, element):
        """
        See :meth:`query.__call__`.
        """
        return self._cond_1(element) or self._cond_2(element)

    def __repr__(self):
        return '({}) or ({})'.format(self._cond_1, self._cond_2)


class query_and(AndOrMixin):
    """
    See :meth:`AndOrMixin.__and__`.
    """
    def __init__(self, where1, where2):
        self._cond_1 = where1
        self._cond_2 = where2

    def __call__(self, element):
        """
        See :meth:`query.__call__`.
        """
        return self._cond_1(element) and self._cond_2(element)

    def __repr__(self):
        return '({}) and ({})'.format(self._cond_1, self._cond_2)


class query_regex(AndOrMixin):
    """
    See :meth:`query.regex`.
    """
    def __init__(self, key, regex):
        self.regex = regex
        self._key = key

    def __call__(self, element):
        """
        See :meth:`query.__call__`.
        """
        return bool(self._key in element
                    and re.match(self.regex, element[self._key]))

    def __repr__(self):
        return '\'{}\' ~= {} '.format(self._key, self.regex)


class query_custom(AndOrMixin):
    """
    See :meth:`query.test`.
    """

    def __init__(self, key, test):
        self.test = test
        self._key = key

    def __call__(self, element):
        """
        See :meth:`query.__call__`.
        """
        return self._key in element and self.test(element[self._key])

    def __repr__(self):
        return '\'{}\'.test({})'.format(self._key, self.test)