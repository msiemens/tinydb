# Allow passing Document objects to update()/remove() instead of raw ids

When I read a document with get() or search(), I get a Document that already knows its doc_id. To change or delete it I have to pull the id out by hand every time.

    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'a': 1}, {'a': 2}])
    doc = db.get(doc_id=1)

    db.update({'a': 9}, doc_ids=[doc])
    # TypeError: unhashable type: 'Document'

    db.remove(doc_ids=[doc])
    # TypeError: unhashable type: 'Document'

    db.get(doc_id=doc)
    # returns None, no error

Feature request: accept Document objects wherever doc ids are accepted, using doc.doc_id, e.g.

    db.update({'a': 9}, doc_ids=[doc])
    db.remove(doc_ids=[doc])

Plain ints should keep working, and mixing ints and Documents in one list would be nice.

TinyDB commit edff96a.
