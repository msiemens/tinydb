# Copying documents from one database to another fails or silently merges into existing docs

I'm moving records from one TinyDB file to another (e.g. archiving old data). Documents read from the source keep their doc_id, which collides with ids already in the destination.

    src = TinyDB(storage=MemoryStorage)
    dst = TinyDB(storage=MemoryStorage)
    src.insert({'x': 1}); src.insert({'x': 2})
    dst.insert({'y': 9})

    dst.insert_multiple(src.all())
    # ValueError: Document with ID 1 already exists

    dst.upsert(src.get(doc_id=1))
    # no error, but dst doc 1 becomes {'y': 9, 'x': 1}  (my existing record was overwritten/merged)

Expected: I can copy documents from another database without an error, and without my existing documents in the destination being modified. New ids can be assigned in the destination.
Actual: either an exception, or silent corruption of an existing document.

TinyDB commit edff96a.
