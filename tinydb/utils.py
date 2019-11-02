"""
Utility functions.
"""

import warnings
from collections import OrderedDict
from contextlib import contextmanager


class LRUCache:
    # @param capacity, an integer
    def __init__(self, capacity=None):
        self.capacity = capacity
        self.cache = OrderedDict()

    @property
    def lru(self):
        return list(self.cache.keys())

    @property
    def length(self):
        return len(self.cache)

    def clear(self):
        self.cache.clear()

    def __len__(self):
        return self.length

    def __contains__(self, key):
        return key in self.cache

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        del self.cache[key]

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)

        return self.get(key)

    def __iter__(self):
        return iter(self.cache)

    def get(self, key, default=None):
        value = self.cache.get(key)

        if value is not None:
            # Put the key back to the front of the ordered dict by
            # re-insertig it
            del self.cache[key]
            self.cache[key] = value
            return value

        return default

    def set(self, key, value):
        if self.cache.get(key):
            del self.cache[key]
            self.cache[key] = value
        else:
            self.cache[key] = value
            # Check, if the cache is full and we have to remove old items
            # If the queue is of unlimited size, self.capacity is NaN and
            # x > NaN is always False in Python and the cache won't be cleared.
            if self.capacity is not None and self.length > self.capacity:
                self.cache.popitem(last=False)


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
