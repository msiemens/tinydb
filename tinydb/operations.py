def delete(field):
    """
    Delete a given field from the element.
    """
    def transform(element):
        del element[field]

    return transform

def add(field, n):
    """
    Add n to a given field in the element.
    """
    def transform(element):
        element[field] += n

    return transform

def subtract(field, n):
    """
    Subtract n from a given field in the element.
    """
    def transform(element):
        element[field] -= n

    return transform

def set(field, val):
    """
    Set a given field to val.
    """
    def transform(element):
        element[field] = val

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
