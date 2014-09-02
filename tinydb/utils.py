"""
Utility functions.
"""


class LRUCache(dict):
    """
    A simple LRU cache.
    """

    def __init__(self, *args, **kwargs):
        """
        :param capacity: How many items to store before cleaning up old items
                         or ``None`` for an unlimited cache size
        """

        self.capacity = kwargs.pop('capacity', None)
        if self.capacity is None:
            self.capacity = float('nan')
        self.lru = []

        super(LRUCache, self).__init__(*args, **kwargs)

    def refresh(self, key):
        """
        Push a key to the head of the LRU queue
        """
        if key in self.lru:
            self.lru.remove(key)
        self.lru.append(key)

    def get(self, key, default=None):
        self.refresh(key)

        return super(LRUCache, self).get(key, default)

    def __getitem__(self, key):
        self.refresh(key)

        return super(LRUCache, self).__getitem__(key)

    def __setitem__(self, key, value):
        super(LRUCache, self).__setitem__(key, value)

        self.refresh(key)

        # Check, if the cache is full and we have to remove old items
        # If the queue is of unlimited size, self.capacity is NaN and
        # x > NaN is always False in Python and the cache won't be cleared.
        if len(self) > self.capacity:
            self.pop(self.lru.pop(0))

    def __delitem__(self, key):
        super(LRUCache, self).__delitem__(key)
        self.lru.remove(key)

    def clear(self):
        super(LRUCache, self).clear()
        del self.lru[:]
