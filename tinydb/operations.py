def delete(field):
    """
    Delete a given field from the element.
    """
    def transform(element):
        del element[field]

    return transform


def increment(field):
    """
    Increment a given field in the element.
    """
    def transform(element):
        element[field] += 1

    return transform


def decrement(field):
    """
    Decrement a given field in the element.
    """
    def transform(element):
        element[field] -= 1

    return transform
