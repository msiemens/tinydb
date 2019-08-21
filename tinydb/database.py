"""
Contains the :class:`database <tinydb.database.TinyDB>` and
:class:`tables <tinydb.database.Table>` implementation.
"""
# Python 2/3 independent Mapping import
try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping
import warnings

from . import JSONStorage
from .utils import LRUCache, iteritems, itervalues


class Document(dict):
    """
    Represents a document stored in the database.

    This is a transparent proxy for database records. It exists
    to provide a way to access a record's id via ``el.doc_id``.
    """

    def __init__(self, value, doc_id, **kwargs):
        super(Document, self).__init__(**kwargs)

        self.update(value)
        self.doc_id = doc_id

    @property
    def eid(self):
        warnings.warn('eid has been renamed to doc_id', DeprecationWarning)
        return self.doc_id


Element = Document


def _get_doc_id(doc_id, eid):
    # Backwards-compatibility shim
    if eid is not None:
        if doc_id is not None:
            raise TypeError('cannot pass both eid and doc_id')

        warnings.warn('eid has been renamed to doc_id', DeprecationWarning)
        return eid
    else:
        return doc_id


def _get_doc_ids(doc_ids, eids):
    # Backwards-compatibility shim
    if eids is not None:
        if doc_ids is not None:
            raise TypeError('cannot pass both eids and doc_ids')

        warnings.warn('eids has been renamed to doc_ids', DeprecationWarning)
        return eids
    else:
        return doc_ids


class DataProxy(dict):
    """
    A proxy to a table's data that remembers the storage's
    data dictionary.
    """

    def __init__(self, table, raw_data, **kwargs):
        super(DataProxy, self).__init__(**kwargs)
        self.update(table)
        self.raw_data = raw_data


class StorageProxy(object):
    """
    A proxy that only allows to read a single table from a
    storage.
    """

    def __init__(self, storage, table_name):
        self._storage = storage
        self._table_name = table_name

    def _new_document(self, key, val):
        doc_id = int(key)
        return Document(val, doc_id)

    def read(self):
        raw_data = self._storage.read() or {}

        try:
            table = raw_data[self._table_name]
        except KeyError:
            raw_data.update({self._table_name: {}})
            self._storage.write(raw_data)

            return DataProxy({}, raw_data)

        docs = {}
        for key, val in iteritems(table):
            doc = self._new_document(key, val)
            docs[doc.doc_id] = doc

        return DataProxy(docs, raw_data)

    def write(self, data):
        try:
            # Try accessing the full data dict from the data proxy
            raw_data = data.raw_data
        except AttributeError:
            # Not a data proxy, fall back to regular reading
            raw_data = self._storage.read()

        raw_data[self._table_name] = dict(data)
        self._storage.write(raw_data)

    def purge_table(self):
        try:
            data = self._storage.read() or {}
            del data[self._table_name]
            self._storage.write(data)
        except KeyError:
            pass


class TinyDB(object):
    """
    The main class of TinyDB.

    Gives access to the database, provides methods to insert/search/remove
    and getting tables.
    """

    DEFAULT_TABLE = '_default'
    DEFAULT_TABLE_KWARGS = {}
    DEFAULT_STORAGE = JSONStorage

    def __init__(self, *args, **kwargs):
        """
        Create a new instance of TinyDB.

        All arguments and keyword arguments will be passed to the underlying
        storage class (default: :class:`~tinydb.storages.JSONStorage`).

        :param storage: The class of the storage to use. Will be initialized
                        with ``args`` and ``kwargs``.
        :param default_table: The name of the default table to populate.
        """

        storage = kwargs.pop('storage', self.DEFAULT_STORAGE)
        default_table = kwargs.pop('default_table', self.DEFAULT_TABLE)
        self._cls_table = kwargs.pop('table_class', self.table_class)
        self._cls_storage_proxy = kwargs.pop('storage_proxy_class',
                                             self.storage_proxy_class)

        # Prepare the storage
        #: :type: Storage
        self._storage = storage(*args, **kwargs)

        self._opened = True

        # Prepare the default table

        self._table_cache = {}
        #: :type: Table
        self._table = self.table(default_table)

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

    def table(self, name=DEFAULT_TABLE, **options):
        """
        Get access to a specific table.

        Creates a new table, if it hasn't been created before, otherwise it
        returns the cached :class:`~tinydb.Table` object.

        :param name: The name of the table.
        :type name: str
        :param cache_size: How many query results to cache.
        :param table_class: Which table class to use.
        """

        if name in self._table_cache:
            return self._table_cache[name]

        table_class = options.pop('table_class', self._cls_table)

        table_kwargs = self.DEFAULT_TABLE_KWARGS.copy()
        table_kwargs.update(options)

        table = table_class(self._cls_storage_proxy(self._storage, name), name,
                            **table_kwargs)

        self._table_cache[name] = table

        return table

    def tables(self):
        """
        Get the names of all tables in the database.

        :returns: a set of table names
        :rtype: set[str]
        """

        return set(self._storage.read())

    def purge_tables(self):
        """
        Purge all tables from the database. **CANNOT BE REVERSED!**
        """

        self._storage.write({})
        self._table_cache.clear()

    def purge_table(self, name):
        """
        Purge a specific table from the database. **CANNOT BE REVERSED!**

        :param name: The name of the table.
        :type name: str
        """
        if name in self._table_cache:
            del self._table_cache[name]

        proxy = StorageProxy(self._storage, name)
        proxy.purge_table()

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
        self._storage.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self._opened:
            self.close()

    def __getattr__(self, name):
        """
        Forward all unknown attribute calls to the underlying standard table.
        """
        return getattr(self._table, name)

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
        return len(self._table)

    def __iter__(self):
        """
        Iter over all documents from default table.
        """
        return self._table.__iter__()


class Table(object):
    """
    Represents a single TinyDB Table.
    """

    def __init__(self, storage, name, cache_size=10):
        """
        Get access to a table.

        :param storage: Access to the storage
        :type storage: StorageProxy
        :param name: The table name
        :param cache_size: Maximum size of query cache.
        """

        self._storage = storage
        self._name = name
        self._query_cache = LRUCache(capacity=cache_size)

        data = self._read()
        self._init_last_id(data)

    def __repr__(self):
        args = [
            'name={!r}'.format(self.name),
            'total={}'.format(self.__len__()),
            'storage={}'.format(self._storage),
        ]

        return '<{} {}>'.format(type(self).__name__, ', '.join(args))

    def _init_last_id(self, data):
        if data:
            self._last_id = max(i for i in data)
        else:
            self._last_id = 0

    @property
    def name(self):
        """
        Get the table name.
        """
        return self._name

    def process_elements(self, func, cond=None, doc_ids=None, eids=None):
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
                     second argument: the current eid
        :param cond: query that matches documents to use, or
        :param doc_ids: list of document IDs to use
        :param eids: list of document IDs to use (deprecated)
        :returns: the document IDs that were affected during processing
        """

        doc_ids = _get_doc_ids(doc_ids, eids)
        data = self._read()

        if doc_ids is not None:
            # Processed document specified by id
            for doc_id in doc_ids:
                func(data, doc_id)

        elif cond is not None:
            # Collect affected doc_ids
            doc_ids = []

            # Processed documents specified by condition
            for doc_id in list(data):
                if cond(data[doc_id]):
                    func(data, doc_id)
                    doc_ids.append(doc_id)
        else:
            # Processed documents
            doc_ids = list(data)

            for doc_id in doc_ids:
                func(data, doc_id)

        self._write(data)

        return doc_ids

    def clear_cache(self):
        """
        Clear the query cache.

        A simple helper that clears the internal query cache.
        """
        self._query_cache.clear()

    def _get_next_id(self):
        """
        Increment the ID used the last time and return it
        """

        current_id = self._last_id + 1
        self._last_id = current_id

        return current_id

    def _read(self):
        """
        Reading access to the DB.

        :returns: all values
        :rtype: DataProxy
        """

        return self._storage.read()

    def _write(self, values):
        """
        Writing access to the DB.

        :param values: the new values to write
        :type values: DataProxy | dict
        """

        self.clear_cache()
        self._storage.write(values)

    def __len__(self):
        """
        Get the total number of documents in the table.
        """
        return len(self._read())

    def all(self):
        """
        Get all documents stored in the table.

        :returns: a list with all documents.
        :rtype: list[Element]
        """

        return list(itervalues(self._read()))

    def __iter__(self):
        """
        Iter over all documents stored in the table.

        :returns: an iterator over all documents.
        :rtype: listiterator[Element]
        """

        for value in itervalues(self._read()):
            yield value

    def insert(self, document):
        """
        Insert a new document into the table.

        :param document: the document to insert
        :returns: the inserted document's ID
        """
        if not isinstance(document, Mapping):
            raise ValueError('Document is not a Mapping')

        doc_id = self._get_next_id()
        data = self._read()
        data[doc_id] = dict(document)
        self._write(data)

        return doc_id

    def insert_multiple(self, documents):
        """
        Insert multiple documents into the table.

        :param documents: a list of documents to insert
        :returns: a list containing the inserted documents' IDs
        """
        doc_ids = []
        data = self._read()

        for document in documents:
            if not isinstance(document, Mapping):
                raise ValueError('Document is not a Mapping')

            doc_id = self._get_next_id()
            doc_ids.append(doc_id)

            data[doc_id] = dict(document)

        self._write(data)

        return doc_ids

    def remove(self, cond=None, doc_ids=None, eids=None):
        """
        Remove all matching documents.

        :param cond: the condition to check against
        :type cond: query
        :param doc_ids: a list of document IDs
        :type doc_ids: list
        :returns: a list containing the removed document's ID
        """
        doc_ids = _get_doc_ids(doc_ids, eids)

        if cond is None and doc_ids is None:
            raise RuntimeError('Use purge() to remove all documents')

        return self.process_elements(
            lambda data, doc_id: data.pop(doc_id),
            cond, doc_ids
        )

    def update(self, fields, cond=None, doc_ids=None, eids=None):
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
        doc_ids = _get_doc_ids(doc_ids, eids)

        if callable(fields):
            return self.process_elements(
                lambda data, doc_id: fields(data[doc_id]),
                cond, doc_ids
            )
        else:
            return self.process_elements(
                lambda data, doc_id: data[doc_id].update(fields),
                cond, doc_ids
            )

    def write_back(self, documents, doc_ids=None, eids=None):
        """
        Write back documents by doc_id

        :param documents: a list of document to write back
        :param doc_ids: a list of document IDs which need to be written back
        :returns: a list of document IDs that have been written
        """
        doc_ids = _get_doc_ids(doc_ids, eids)

        if doc_ids is not None and not len(documents) == len(doc_ids):
            raise ValueError(
                'The length of documents and doc_ids is not match.')

        if doc_ids is None:
            doc_ids = [doc.doc_id for doc in documents]

        # Since this function will write docs back like inserting, to ensure
        # here only process existing or removed instead of inserting new,
        # raise error if doc_id exceeded the last.
        if len(doc_ids) > 0 and max(doc_ids) > self._last_id:
            raise IndexError(
                'ID exceeds table length, use existing or removed doc_id.')

        data = self._read()

        # Document specified by ID
        documents.reverse()
        for doc_id in doc_ids:
            data[doc_id] = dict(documents.pop())

        self._write(data)

        return doc_ids

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

    def purge(self):
        """
        Purge the table by removing all documents.
        """

        self._write({})
        self._last_id = 0

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

        docs = [doc for doc in self.all() if cond(doc)]
        self._query_cache[cond] = docs

        return docs[:]

    def get(self, cond=None, doc_id=None, eid=None):
        """
        Get exactly one document specified by a query or and ID.

        Returns ``None`` if the document doesn't exist

        :param cond: the condition to check against
        :type cond: Query

        :param doc_id: the document's ID

        :returns: the document or None
        :rtype: Element | None
        """
        doc_id = _get_doc_id(doc_id, eid)

        # Cannot use process_elements here because we want to return a
        # specific document

        if doc_id is not None:
            # Document specified by ID
            return self._read().get(doc_id, None)

        # Document specified by condition
        for doc in self.all():
            if cond(doc):
                return doc

    def count(self, cond):
        """
        Count the documents matching a condition.

        :param cond: the condition use
        :type cond: Query
        """

        return len(self.search(cond))

    def contains(self, cond=None, doc_ids=None, eids=None):
        """
        Check wether the database contains a document matching a condition or
        an ID.

        If ``eids`` is set, it checks if the db contains a document with one
        of the specified.

        :param cond: the condition use
        :type cond: Query
        :param doc_ids: the document IDs to look for
        """
        doc_ids = _get_doc_ids(doc_ids, eids)

        if doc_ids is not None:
            # Documents specified by ID
            return any(self.get(doc_id=doc_id) for doc_id in doc_ids)

        # Document specified by condition
        return self.get(cond) is not None


# Set the default table class
TinyDB.table_class = Table

# Set the default storage proxy class
TinyDB.storage_proxy_class = StorageProxy
