import pytest

from tinydb.utils import LRUCache, freeze, FrozenDict


def test_lru_cache():
    cache = LRUCache(capacity=3)
    cache["a"] = 1
    cache["b"] = 2
    cache["c"] = 3
    _ = cache["a"]  # move to front in lru queue
    cache["d"] = 4  # move oldest item out of lru queue

    try:
        _ = cache['f']
    except KeyError:
        pass

    assert cache.lru == ["c", "a", "d"]


def test_lru_cache_set_multiple():
    cache = LRUCache(capacity=3)
    cache["a"] = 1
    cache["a"] = 2
    cache["a"] = 3
    cache["a"] = 4

    assert cache.lru == ["a"]


def test_lru_cache_set_update():
    cache = LRUCache(capacity=3)
    cache["a"] = 1
    cache["a"] = 2

    assert cache["a"] == 2


def test_lru_cache_get():
    cache = LRUCache(capacity=3)
    cache["a"] = 1
    cache["b"] = 1
    cache["c"] = 1
    cache.get("a")
    cache["d"] = 4

    assert cache.lru == ["c", "a", "d"]


def test_lru_cache_delete():
    cache = LRUCache(capacity=3)
    cache["a"] = 1
    cache["b"] = 2
    del cache["a"]

    try:
        del cache['f']
    except KeyError:
        pass

    assert cache.lru == ["b"]


def test_lru_cache_clear():
    cache = LRUCache(capacity=3)
    cache["a"] = 1
    cache["b"] = 2
    cache.clear()

    assert cache.lru == []


def test_lru_cache_unlimited():
    cache = LRUCache()
    for i in range(100):
        cache[i] = i

    assert len(cache.lru) == 100


def test_lru_cache_unlimited_explicit():
    cache = LRUCache(capacity=None)
    for i in range(100):
        cache[i] = i

    assert len(cache.lru) == 100


def test_lru_cache_iteration_works():
    cache = LRUCache()
    count = 0
    for _ in cache:
        assert False, 'there should be no elements in the cache'

    assert count == 0


def test_freeze():
    frozen = freeze([0, 1, 2, {'a': [1, 2, 3]}, {1, 2}])
    assert isinstance(frozen, tuple)
    assert isinstance(frozen[3], FrozenDict)
    assert isinstance(frozen[3]['a'], tuple)
    assert isinstance(frozen[4], frozenset)

    with pytest.raises(TypeError):
        frozen[0] = 10

    with pytest.raises(TypeError):
        frozen[3]['a'] = 10

    with pytest.raises(TypeError):
        frozen[3].pop('a')

    with pytest.raises(TypeError):
        frozen[3].update({'a': 9})
