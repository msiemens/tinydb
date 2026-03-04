"""
Bloom Filter implementation for fast negative lookups.

A Bloom Filter is a space-efficient probabilistic data structure that is used
to test whether an element is a member of a set. False positive matches are
possible, but false negatives are not: if the filter says an element is not
present, it is **definitely** not present.

This is used by TinyDB to avoid unnecessary storage reads when looking up
documents by their ID that do not exist in the database.

Usage example:

>>> bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
>>> bf.add('42')
>>> bf.test('42')
True
>>> bf.test('99')
False
"""

import hashlib
import math
from typing import Any, Dict, Iterable, List

__all__ = ('BloomFilter',)


class BloomFilter:
    """
    A space-efficient probabilistic data structure for membership testing.

    Guarantees zero false negatives: if :meth:`test` returns ``False``, the
    element is **definitely** not in the set.

    Uses double hashing (MD5 + SHA-256) to generate ``k`` independent hash
    positions from two base hash functions, following the technique described
    by Kirsch & Mitzenmacher (2004).

    :param expected_items: Expected number of items to be stored
    :param false_positive_rate: Desired false positive probability (0 < p < 1)
    """

    def __init__(
        self,
        expected_items: int = 10_000,
        false_positive_rate: float = 0.01,
    ):
        if expected_items <= 0:
            raise ValueError('expected_items must be positive')

        if not (0 < false_positive_rate < 1):
            raise ValueError('false_positive_rate must be between 0 and 1')

        self._expected_items = expected_items
        self._fp_rate = false_positive_rate

        # Optimal bit array size: m = -(n * ln(p)) / (ln(2))^2
        self._size = self._optimal_size(expected_items, false_positive_rate)

        # Optimal number of hash functions: k = (m / n) * ln(2)
        self._num_hashes = self._optimal_hashes(self._size, expected_items)

        self._bit_array = bytearray(math.ceil(self._size / 8))
        self._count = 0

    def __repr__(self):
        return (
            f'<BloomFilter size={self._size}, hashes={self._num_hashes}, '
            f'count={self._count}, fp_rate={self._fp_rate}>'
        )

    @staticmethod
    def _optimal_size(n: int, p: float) -> int:
        """
        Calculate the optimal bit array size.

        Formula: m = -(n * ln(p)) / (ln(2))^2

        :param n: Expected number of items
        :param p: Desired false positive rate
        :returns: Optimal bit array size
        """
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(math.ceil(m))

    @staticmethod
    def _optimal_hashes(m: int, n: int) -> int:
        """
        Calculate the optimal number of hash functions.

        Formula: k = (m / n) * ln(2)

        :param m: Bit array size
        :param n: Expected number of items
        :returns: Optimal number of hash functions
        """
        k = (m / n) * math.log(2)
        return max(1, int(round(k)))

    def _get_hash_values(self, item: str) -> List[int]:
        """
        Generate ``k`` hash positions using double hashing.

        Uses the scheme: h_i(x) = (h1(x) + i * h2(x)) mod m

        where h1 is derived from MD5 and h2 from SHA-256.

        :param item: The string representation of the item to hash
        :returns: A list of ``k`` bit positions
        """
        item_bytes = item.encode('utf-8')
        h1 = int(hashlib.md5(item_bytes).hexdigest(), 16)
        h2 = int(hashlib.sha256(item_bytes).hexdigest(), 16)

        return [(h1 + i * h2) % self._size for i in range(self._num_hashes)]

    def add(self, item: Any) -> None:
        """
        Add an item to the filter.

        :param item: The item to add (will be converted to string)
        """
        for pos in self._get_hash_values(str(item)):
            byte_idx, bit_idx = divmod(pos, 8)
            self._bit_array[byte_idx] |= (1 << bit_idx)

        self._count += 1

    def test(self, item: Any) -> bool:
        """
        Test whether an item **might** be in the set.

        - Returns ``False``: the item is **definitely not** in the set
        - Returns ``True``: the item is **probably** in the set
          (subject to the configured false positive rate)

        :param item: The item to test (will be converted to string)
        :returns: Whether the item might be present
        """
        for pos in self._get_hash_values(str(item)):
            byte_idx, bit_idx = divmod(pos, 8)
            if not (self._bit_array[byte_idx] & (1 << bit_idx)):
                return False

        return True

    def rebuild(self, items: Iterable[Any]) -> None:
        """
        Clear the filter and rebuild it from a new set of items.

        This is used after remove operations, since standard Bloom Filters
        do not support element deletion.

        :param items: The items to populate the filter with
        """
        self._bit_array = bytearray(math.ceil(self._size / 8))
        self._count = 0

        for item in items:
            self.add(item)

    @property
    def count(self) -> int:
        """
        Get the number of items that have been added to the filter.

        .. note::

            This does not account for duplicate additions.
        """
        return self._count

    @property
    def size(self) -> int:
        """
        Get the size of the bit array in bits.
        """
        return self._size

    @property
    def num_hashes(self) -> int:
        """
        Get the number of hash functions used.
        """
        return self._num_hashes

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the filter state to a dictionary.

        This can be used to persist the filter alongside the database.

        :returns: A dictionary containing the filter state
        """
        return {
            'expected_items': self._expected_items,
            'fp_rate': self._fp_rate,
            'size': self._size,
            'num_hashes': self._num_hashes,
            'bit_array': list(self._bit_array),
            'count': self._count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BloomFilter':
        """
        Reconstruct a filter from a serialized dictionary.

        :param data: The dictionary produced by :meth:`to_dict`
        :returns: A new :class:`BloomFilter` instance
        """
        bf = cls.__new__(cls)
        bf._expected_items = data['expected_items']
        bf._fp_rate = data['fp_rate']
        bf._size = data['size']
        bf._num_hashes = data['num_hashes']
        bf._bit_array = bytearray(data['bit_array'])
        bf._count = data['count']

        return bf
