def delete(field):
    """
    Delete a given field from the element.
    """
    def transform(el):
        del el[field]

    return transform


def increment(field):
    """
    Increment a given field in the element.
    """
    def transform(el):
        el[field] += 1

    return transform


def decrement(field):
    """
    Decrement a given field in the element.
    """
    def transform(el):
        el[field] -= 1

    return transform
