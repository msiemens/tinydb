"""
Contains the :class:`database <tinydb.database.TinyDB>` and
:class:`tables <tinydb.database.Table>` implementation.
"""
from collections.abc import Mapping

from . import JSONStorage
from .storages import Storage
from .utils import LRUCache


class Document(dict):
    """
    Represents a document stored in the database.

    This is a transparent proxy for database records. It exists
    to provide a way to access a record's id via ``el.doc_id``.
    """

    def __init__(self, value, doc_id):
        super().__init__(value)
        self.doc_id = int(doc_id)


class TinyDB:
    """
    The main class of TinyDB.

    Gives access to the database, provides methods to insert/search/remove
    and getting tables.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new instance of TinyDB.

        All arguments and keyword arguments will be passed to the underlying
        storage class (default: :class:`~tinydb.storages.JSONStorage`).

        :param storage: The class of the storage to use. Will be initialized
                        with ``args`` and ``kwargs``.
        :param default_table: The name of the default table to populate.
        """

        storage = kwargs.pop('storage', JSONStorage)

        # Prepare the storage
        #: :type: Storage
        self._storage = storage(*args, **kwargs)

        self._opened = True

        # Prepare the default table
        self._tables = {}

    def __repr__(self):
        args = [
            'tables={}'.format(list(self.tables())),
            'tables_count={}'.format(len(self.tables())),
            'default_table_documents_count={}'.format(self.__len__()),
            'all_tables_documents_count={}'.format(
                ['{}={}'.format(table, len(self.table(table)))
                 for table in self.tables()]),
        ]

        return '<{} {}>'.format(type(self).__name__, ', '.join(args))

    def table(self, name='_default', **options):
        """
        Get access to a specific table.

        Creates a new table, if it hasn't been created before, otherwise it
        returns the cached :class:`~tinydb.Table` object.

        :param name: The name of the table.
        :type name: str
        :param cache_size: How many query results to cache.
        :rtype: Table
        """

        if name in self._tables:
            return self._tables[name]

        self._tables[name] = Table(self.storage, name, **options)

        return self._tables[name]

    def tables(self):
        """
        Get the names of all tables in the database.

        :returns: a set of table names
        :rtype: set[str]
        """

        return set(self.storage.read() or {})

    def drop_tables(self):
        """
        Drop all tables from the database. **CANNOT BE REVERSED!**
        """

        self.storage.write({})
        self._tables.clear()

    def drop_table(self, name):
        """
        Drop a specific table from the database. **CANNOT BE REVERSED!**

        :param name: The name of the table.
        :type name: str
        """
        if name in self._tables:
            del self._tables[name]

        data = self.storage.read()

        if name not in data:
            return

        del data[name]
        self.storage.write(data)

    @property
    def storage(self):
        """
        Access the storage used for this TinyDB instance.

        :return: This instance's storage
        """
        return self._storage

    def close(self):
        """
        Close the database.
        """
        self._opened = False
        self.storage.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self._opened:
            self.close()

    def __getattr__(self, name):
        """
        Forward all unknown attribute calls to the underlying default table.
        """
        return getattr(self.table(), name)

    # Methods that are executed on the default table
    # Because magic methods are not handled by __getattr__ we need to forward
    # them manually here

    def __len__(self):
        """
        Get the total number of documents in the default table.

        >>> db = TinyDB('db.json')
        >>> len(db)
        0
        """
        return len(self.table())

    def __iter__(self):
        """
        Iter over all documents from default table.
        """
        return iter(self.table())


class Table:
    """
    Represents a single TinyDB Table.
    """

    def __init__(self, storage: Storage, name: str, cache_size: int = 10):
        """
        Get access to a table.

        :param storage: Access to the storage
        :param name: The table name
        :param cache_size: Maximum size of query cache.
        """

        self._storage = storage
        self._name = name
        self._query_cache = LRUCache(capacity=cache_size)

        self._last_id = self._get_last_id()

    def __repr__(self):
        args = [
            'name={!r}'.format(self.name),
            'total={}'.format(len(self)),
            'storage={}'.format(self.storage),
        ]

        return '<{} {}>'.format(type(self).__name__, ', '.join(args))

    def _get_last_id(self):
        data = self._read()

        if not data:
            return 0

        return max(int(i) for i in data)

    @property
    def name(self):
        """
        Get the table name.
        """
        return self._name

    @property
    def storage(self):
        """
        Get the table storage.
        """
        return self._storage

    def insert(self, document):
        """
        Insert a new document into the table.

        :param document: the document to insert
        :returns: the inserted document's ID
        """
        if not isinstance(document, Mapping):
            raise ValueError('Document is not a Mapping')

        doc_id = self._get_next_id()
        self._update(lambda table: table.update({doc_id: dict(document)}))

        return doc_id

    def insert_multiple(self, documents):
        """
        Insert multiple documents into the table.

        :param documents: a list of documents to insert
        :returns: a list containing the inserted documents' IDs
        """
        doc_ids = []

        def updater(table: dict):
            for document in documents:
                if not isinstance(document, Mapping):
                    raise ValueError('Document is not a Mapping')

                doc_id = self._get_next_id()
                doc_ids.append(doc_id)

                table[doc_id] = dict(document)

        self._update(updater)

        return doc_ids

    def all(self):
        """
        Get all documents stored in the table.

        :returns: a list with all documents.
        :rtype: list[Element]
        """

        return list(iter(self))

    def search(self, cond):
        """
        Search for all documents matching a 'where' cond.

        :param cond: the condition to check against
        :type cond: Query

        :returns: list of matching documents
        :rtype: list[Element]
        """

        if cond in self._query_cache:
            return self._query_cache.get(cond, [])[:]

        docs = [doc for doc in self if cond(doc)]
        self._query_cache[cond] = docs[:]

        return docs

    def get(self, cond=None, doc_id=None):
        """
        Get exactly one document specified by a query or and ID.

        Returns ``None`` if the document doesn't exist

        :param cond: the condition to check against
        :type cond: Query

        :param doc_id: the document's ID

        :returns: the document or None
        :rtype: Element | None
        """
        # Cannot use process_elements here because we want to return a
        # specific document

        if doc_id is not None:
            # Document specified by ID
            doc = self._read().get(doc_id, None)
            if doc is None:
                return None

            return Document(doc, doc_id)

        # Document specified by condition
        for doc in self:
            if cond(doc):
                return doc

    def contains(self, cond=None, doc_ids=None):
        """
        Check wether the database contains a document matching a condition or
        an ID.

        If ``doc_ids`` is set, it checks if the db contains a document with
        one of the specified IDs.

        :param cond: the condition use
        :type cond: Query
        :param doc_ids: the document IDs to look for
        """
        if doc_ids is not None:
            # Documents specified by ID
            return any(self.get(doc_id=doc_id) for doc_id in doc_ids)

        # Document specified by condition
        return self.get(cond) is not None

    def update(self, fields, cond=None, doc_ids=None):
        """
        Update all matching documents to have a given set of fields.

        :param fields: the fields that the matching documents will have
                       or a method that will update the documents
        :type fields: dict | dict -> None
        :param cond: which documents to update
        :type cond: query
        :param doc_ids: a list of document IDs
        :type doc_ids: list
        :returns: a list containing the updated document's ID
        """
        if callable(fields):
            return self._process_docs(
                lambda data, doc_id: fields(data[doc_id]),
                cond, doc_ids
            )
        else:
            return self._process_docs(
                lambda data, doc_id: data[doc_id].update(fields),
                cond, doc_ids
            )

    def upsert(self, document, cond):
        """
        Update a document, if it exist - insert it otherwise.

        Note: this will update *all* documents matching the query.

        :param document: the document to insert or the fields to update
        :param cond: which document to look for
        :returns: a list containing the updated document's ID
        """
        updated_docs = self.update(document, cond)

        if updated_docs:
            return updated_docs
        else:
            return [self.insert(document)]

    def remove(self, cond=None, doc_ids=None):
        """
        Remove all matching documents.

        :param cond: the condition to check against
        :type cond: query
        :param doc_ids: a list of document IDs
        :type doc_ids: list
        :returns: a list containing the removed document's ID
        """
        if cond is None and doc_ids is None:
            raise RuntimeError('Use truncate() to remove all documents')

        return self._process_docs(
            lambda data, doc_id: data.pop(doc_id),
            cond, doc_ids
        )

    def truncate(self):
        """
        Truncate the table by removing all documents.
        """

        self._update(lambda table: table.clear())
        self._last_id = 0

    def count(self, cond):
        """
        Count the documents matching a condition.

        :param cond: the condition use
        :type cond: Query
        """

        return len(self.search(cond))

    def clear_cache(self):
        """
        Clear the query cache.

        A simple helper that clears the internal query cache.
        """
        self._query_cache.clear()

    def __len__(self):
        """
        Get the total number of documents in the table.
        """
        return len(self._read())

    def __iter__(self):
        """
        Iter over all documents stored in the table.

        :returns: an iterator over all documents.
        :rtype: listiterator[Element]
        """

        data = self.storage.read() or {}

        try:
            #: :type: dict
            raw_table = data[self.name]
        except KeyError:
            return {}

        for doc_id, doc in raw_table.items():
            yield Document(doc, doc_id)

    def _get_next_id(self):
        """
        Increment the ID used the last time and return it
        """

        current_id = self._last_id + 1
        self._last_id = current_id

        return current_id

    def _process_docs(self, func, cond=None, doc_ids=None):
        """
        Helper function for processing all documents specified by condition
        or IDs.

        A repeating pattern in TinyDB is to run some code on all documents
        that match a condition or are specified by their ID. This is
        implemented in this function.
        The function passed as ``func`` has to be a callable. Its first
        argument will be the data currently in the database. Its second
        argument is the document ID of the currently processed document.

        See: :meth:`~.update`, :meth:`.remove`

        :param func: the function to execute on every included document.
                     first argument: all data
                     second argument: the current document ID
        :param cond: query that matches documents to use, or
        :param doc_ids: list of document IDs to use
        :returns: the document IDs that were affected during processing
        """

        if doc_ids is not None:
            # Processed document specified by id
            def updater(table: dict):
                for doc_id in doc_ids:
                    func(table, doc_id)

        elif cond is not None:
            # Collect affected doc_ids
            doc_ids = []

            def updater(table: dict):
                # Processed documents specified by condition
                for doc_id in list(table):
                    if cond(table[doc_id]):
                        func(table, doc_id)
                        doc_ids.append(doc_id)

        else:
            doc_ids = []

            # Processed documents
            def updater(table: dict):
                for doc_id in table:
                    doc_ids.append(doc_id)
                    func(table, doc_id)

        self._update(updater)

        return doc_ids

    def _read(self):
        data = self.storage.read() or {}

        try:
            return {
                int(doc_id): doc
                for doc_id, doc in data[self.name].items()
            }
        except KeyError:
            return {}

    def _update(self, updater):
        data = self.storage.read() or {}

        try:
            table = data[self.name]
        except KeyError:
            table = {}

        table = {int(doc_id): doc for doc_id, doc in table.items()}

        updater(table)

        data[self.name] = table

        self.storage.write(data)
        self.clear_cache()
