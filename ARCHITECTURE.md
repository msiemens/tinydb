# TinyDB architecture

This file describes TinyDB at `edff96a` so the design stage can name real modules. It is not the Assignment 2 architecture document. That document describes Python-Markdown, a different repository, and reading it here would send an agent to modules this fork does not have.

Library usage for humans is in `README.rst`. This file is the map of where behaviour lives.

## Shape

`TinyDB` in `tinydb/database.py` owns a `Storage` and a dict of `Table` objects. Attribute access that `TinyDB` does not define is forwarded to the default table `_default` through `__getattr__`. A caller who writes `db.insert(...)` is calling `Table.insert`.

`Table` in `tinydb/table.py` is the read and write API: `insert`, `insert_multiple`, `all`, `search`, `get`, `contains`, `update`, `update_multiple`, `upsert`, `remove`, `truncate`, `count`, `clear_cache`.

`Document` is a `dict` subclass with a `doc_id` attribute. `document_class` and `document_id_class` are class attributes on `Table`. The id class is `int`.

`Storage` in `tinydb/storages.py` is read and write of the whole database dict. `JSONStorage` is the default. `MemoryStorage` keeps that dict in memory. Both expose string keys to `Table`, because `Table._update_table` writes ids back with `str(doc_id)`.

`Query` and `where` live in `tinydb/queries.py`. Middlewares in `tinydb/middlewares.py` wrap a storage. `operations.py` holds update callables such as `delete` and `increment`.

## Document ids

On the write path, `_update_table` copies the raw table and converts every key with `document_id_class` before the updater runs. After the updater, it writes the keys back as strings.

`Table.get` does not use that converted dict. For a single `doc_id` it calls `table.get(str(doc_id))` on the raw storage dict. For `doc_ids` it compares `str(doc_id)` values.

`Table.update` and `Table.remove`, when given `doc_ids`, keep the caller's ids and test `doc_id in table` against the converted dict, whose keys are ints. `Table.insert_multiple` keeps a `Document`'s `doc_id` when the value is already a `Document`, and raises `ValueError` if that id is already in the table. `Table.upsert` treats a `Document` as an update targeted at `document.doc_id`, and `update` merges fields into the existing record.

`Table.search` stores results in an `LRUCache` keyed by the query. A later search with the same query is served from that cache. Writes clear the cache. `Table.count` is `len(self.search(cond))` and requires `cond`.

## Tests and CI

Tests are pytest modules under `tests/`. `pyproject.toml` installs them with uv through the `dev` dependency group. `.github/workflows/ci-workflow.yml` runs on a pull request whose base is `master`. It does not run for a pull request into `main`.

## Where a change goes

A change to insert, search, get, update, remove, upsert, or count belongs in `Table` (`tinydb/table.py`). A change to which class is constructed, or to forwarding onto the default table, belongs in `TinyDB` (`tinydb/database.py`). A change to how bytes hit disk belongs in `tinydb/storages.py`. A change to query operators belongs in `tinydb/queries.py`. New tests belong under `tests/`, next to the module they cover.
