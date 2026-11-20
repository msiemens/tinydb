# update()/remove() silently do nothing when doc_ids are given as strings

I store documents and sometimes get ids back as strings (e.g. from a URL or JSON), so I call get/update/remove with '1' instead of 1.

get works:

    db = TinyDB(storage=MemoryStorage)
    db.insert({'a': 1})
    db.get(doc_id='1')                   # {'a': 1}

but update and remove do nothing, with no error:

    db.update({'a': 2}, doc_ids=['1'])   # returns [], document unchanged
    db.remove(doc_ids=['1'])             # returns [], document still there

Expected: same behaviour as get, so the id '1' matches document 1 and it is updated/removed (and its id is returned).
Actual: nothing happens and an empty list comes back, so it is easy to miss.

TinyDB commit edff96a.
