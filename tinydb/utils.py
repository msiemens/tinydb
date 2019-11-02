"""
Utility functions.
"""

from collections import OrderedDict, abc
from typing import List, Iterator, TypeVar, Generic, Union, Optional

K = TypeVar('K')
V = TypeVar('V')
D = TypeVar('D')


class LRUCache(abc.MutableMapping, Generic[K, V]):
    def __init__(self, capacity=None):
        self.capacity = capacity
        self.cache = OrderedDict()  # type: OrderedDict[K, V]

    @property
    def lru(self) -> List[K]:
        return list(self.cache.keys())

    @property
    def length(self) -> int:
        return len(self.cache)

    def clear(self) -> None:
        self.cache.clear()

    def __len__(self) -> int:
        return self.length

    def __contains__(self, key: object) -> bool:
        return key in self.cache

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

    def __delitem__(self, key: K) -> None:
        del self.cache[key]

    def __getitem__(self, key) -> V:
        value = self.get(key)
        if value is None:
            raise KeyError(key)

        return value

    def __iter__(self) -> Iterator[K]:
        return iter(self.cache)

    def get(self, key: K, default: D = None) -> Optional[Union[V, D]]:
        value = self.cache.get(key)

        if value is not None:
            # Put the key back to the front of the ordered dict by
            # re-insertig it
            del self.cache[key]
            self.cache[key] = value
            return value

        return default

    def set(self, key: K, value: V):
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
    setdefault = _immutable
    popitem = _immutable

    def update(self, e=None, **f):
        raise TypeError('object is immutable')

    def pop(self, k, d=None):
        raise TypeError('object is immutable')


def freeze(obj):
    if isinstance(obj, dict):
        return FrozenDict((k, freeze(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return tuple(freeze(el) for el in obj)
    elif isinstance(obj, set):
        return frozenset(obj)
    else:
        return obj
