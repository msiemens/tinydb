"""
A collection of update operations for TinyDB.

They are used for updates like this:

>>> db.update(delete('foo'), where('foo') == 2)

This would delete the ``foo`` field from all documents where ``foo`` equals 2.
"""


from typing import Callable, Mapping, Any, Union


def delete(field: str) -> Callable[[Mapping], None]:
    """
    Delete a given field from the document.
    """
    def transform(doc: Mapping):
        del doc[field]

    return transform


def add(field: str, n: Union[int, float]) -> Callable[[Mapping], None]:
    """
    Add ``n`` to a given field in the document.
    """
    def transform(doc: Mapping):
        doc[field] += n

    return transform


def subtract(field: str, n: Union[int, float]) -> Callable[[Mapping], None]:
    """
    Subtract ``n`` to a given field in the document.
    """
    def transform(doc: Mapping):
        doc[field] -= n

    return transform


def set(field: str, val: Any) -> Callable[[Mapping], None]:
    """
    Set a given field to ``val``.
    """
    def transform(doc: Mapping):
        doc[field] = val

    return transform


def increment(field: str) -> Callable[[Mapping], None]:
    """
    Increment a given field in the document by 1.
    """
    def transform(doc: Mapping):
        doc[field] += 1

    return transform


def decrement(field: str) -> Callable[[Mapping], None]:
    """
    Decrement a given field in the document by 1.
    """
    def transform(doc: Mapping):
        doc[field] -= 1

    return transform
