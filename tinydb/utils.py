"""
Utility functions.
"""

import warnings
from collections import OrderedDict
from contextlib import contextmanager

# Python 2/3 independant dict iteration
iteritems = getattr(dict, 'iteritems', dict.items)
itervalues = getattr(dict, 'itervalues', dict.values)


class LRUCache:
    # @param capacity, an integer
    def __init__(self, capacity=None):
        self.capacity = capacity
        self.__cache = OrderedDict()

    @property
    def lru(self):
        return list(self.__cache.keys())

    @property
    def length(self):
        return len(self.__cache)

    def clear(self):
        self.__cache.clear()

    def __len__(self):
        return self.length

    def __contains__(self, key):
        return key in self.__cache

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        del self.__cache[key]

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)

        return self.get(key)

    def __iter__(self):
        return iter(self.__cache)

    def get(self, key, default=None):
        value = self.__cache.get(key)

        if value is not None:
            # Put the key back to the front of the ordered dict by
            # re-insertig it
            del self.__cache[key]
            self.__cache[key] = value
            return value

        return default

    def set(self, key, value):
        if self.__cache.get(key):
            del self.__cache[key]
            self.__cache[key] = value
        else:
            self.__cache[key] = value
            # Check, if the cache is full and we have to remove old items
            # If the queue is of unlimited size, self.capacity is NaN and
            # x > NaN is always False in Python and the cache won't be cleared.
            if self.capacity is not None and self.length > self.capacity:
                self.__cache.popitem(last=False)


# Source: https://github.com/PythonCharmers/python-future/blob/466bfb2dfa36d865285dc31fe2b0c0a53ff0f181/future/utils/__init__.py#L102-L134
def with_metaclass(meta, *bases):
    """
    Function from jinja2/_compat.py. License: BSD.

    Use it like this::

        class BaseForm(object):
            pass

        class FormType(type):
            pass

        class Form(with_metaclass(FormType, BaseForm)):
            pass

    This requires a bit of explanation: the basic idea is to make a
    dummy metaclass for one level of class instantiation that replaces
    itself with the actual metaclass.  Because of internal type checks
    we also need to make sure that we downgrade the custom metaclass
    for one level to something closer to type (that's why __call__ and
    __init__ comes back from type etc.).

    This has the advantage over six.with_metaclass of not introducing
    dummy classes into the final MRO.
    """

    class Metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)

    return Metaclass('temporary_class', None, {})


@contextmanager
def catch_warning(warning_cls):
    with warnings.catch_warnings():
        warnings.filterwarnings('error', category=warning_cls)

        yield


class FrozenDict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))

    def _immutable(self, *args, **kws):
        raise TypeError('object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable
    pop = _immutable
    popitem = _immutable


def freeze(obj):
    if isinstance(obj, dict):
        return FrozenDict((k, freeze(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return tuple(freeze(el) for el in obj)
    elif isinstance(obj, set):
        return frozenset(obj)
    else:
        return obj
