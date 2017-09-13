"""
Contains the :class:`database <tinydb.database.TinyDB>` and
:class:`tables <tinydb.database.Table>` implementation.
"""
from . import JSONStorage
from .utils import LRUCache, iteritems, itervalues


class Element(dict):
    """
    Represents a document stored in the database.

    This is a transparent proxy for database records. It exists
    to provide a way to access an record's id via ``el.eid``.
    """
    def __init__(self, value, eid, **kwargs):
        super(Element, self).__init__(**kwargs)

        self.update(value)
        self.eid = eid


class StorageProxy(object):
    def __init__(self, storage, table_name):
        self._storage = storage
        self._table_name = table_name

    def read(self):
        try:
            raw_data = (self._storage.read() or {})[self._table_name]
        except KeyError:
            self.write({})
            return {}

        data = {}
        for key, val in iteritems(raw_data):
            eid = int(key)
            data[eid] = Element(val, eid)

        return data

    def write(self, values):
        data = self._storage.read() or {}
        data[self._table_name] = values
        self._storage.write(data)

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
    DEFAULT_STORAGE = JSONStorage

    def __init__(self, *args, **kwargs):
        """
        Create a new instance of TinyDB.

        All arguments and keyword arguments will be passed to the underlying
        storage class (default: :class:`~tinydb.storages.JSONStorage`).

        :param storage: The class of the storage to use. Will be initialized
                        with ``args`` and ``kwargs``.
        """

        storage = kwargs.pop('storage', self.DEFAULT_STORAGE)
        table = kwargs.pop('default_table', self.DEFAULT_TABLE)

        # Prepare the storage
        #: :type: Storage
        self._storage = storage(*args, **kwargs)

        self._opened = True

        # Prepare the default table

        self._table_cache = {}
        self._table = self.table(table)

    def table(self, name=DEFAULT_TABLE, **options):
        """
        Get access to a specific table.

        Creates a new table, if it hasn't been created before, otherwise it
        returns the cached :class:`~tinydb.Table` object.

        :param name: The name of the table.
        :type name: str
        :param cache_size: How many query results to cache.
        """

        if name in self._table_cache:
            return self._table_cache[name]

        table = self.table_class(StorageProxy(self._storage, name), name, **options)

        self._table_cache[name] = table

        # table._read will create an empty table in the storage, if necessary
        table._read()

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
    # Because magic methods are not handlet by __getattr__ we need to forward
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

    def process_elements(self, func, cond=None, eids=None):
        """
        Helper function for processing all documents specified by condition
        or IDs.

        A repeating pattern in TinyDB is to run some code on all documents
        that match a condition or are specified by their ID. This is
        implemented in this function.
        The function passed as ``func`` has to be a callable. It's first
        argument will be the data currently in the database. It's second
        argument is the document ID of the currently processed document.

        See: :meth:`~.update`, :meth:`.remove`

        :param func: the function to execute on every included document.
                     first argument: all data
                     second argument: the current eid
        :param cond: query that matches documents to use, or
        :param eids: list of document IDs to use
        :returns: the document IDs that were affected during processed
        """

        data = self._read()

        if eids is not None:
            # Processed document specified by id
            for eid in eids:
                func(data, eid)

        elif cond is not None:
            # Collect affected eids
            eids = []

            # Processed documents specified by condition
            for eid in list(data):
                if cond(data[eid]):
                    func(data, eid)
                    eids.append(eid)
        else:
            # Processed documents
            eids = list(data)

            for eid in eids:
                func(data, eid)

        self._write(data)

        return eids

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
        :rtype: dict
        """

        return self._storage.read()

    def _write(self, values):
        """
        Writing access to the DB.

        :param values: the new values to write
        :type values: dict
        """

        self._query_cache.clear()
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

        eid = self._get_next_id()

        if not isinstance(document, dict):
            raise ValueError('Document is not a dictionary')

        data = self._read()
        data[eid] = document
        self._write(data)

        return eid

    def insert_multiple(self, documents):
        """
        Insert multiple documents into the table.

        :param documents: a list of documents to insert
        :returns: a list containing the inserted documents' IDs
        """

        eids = []
        data = self._read()

        for doc in documents:
            eid = self._get_next_id()
            eids.append(eid)

            data[eid] = doc

        self._write(data)

        return eids

    def remove(self, cond=None, eids=None):
        """
        Remove all matching documents.

        :param cond: the condition to check against
        :type cond: query
        :param eids: a list of document IDs
        :type eids: list
        :returns: a list containing the removed document's ID
        """
        if cond is None and eids is None:
            raise RuntimeError('Use purge() to remove all documents')

        return self.process_elements(
            lambda data, eid: data.pop(eid),
            cond, eids
        )

    def update(self, fields, cond=None, eids=None):
        """
        Update all matching documents to have a given set of fields.

        :param fields: the fields that the matching documents will have
                       or a method that will update the documents
        :type fields: dict | dict -> None
        :param cond: which documents to update
        :type cond: query
        :param eids: a list of document IDs
        :type eids: list
        :returns: a list containing the updated document's ID
        """

        if callable(fields):
            return self.process_elements(
                lambda data, eid: fields(data[eid]),
                cond, eids
            )
        else:
            return self.process_elements(
                lambda data, eid: data[eid].update(fields),
                cond, eids
            )

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
            return self._query_cache[cond][:]

        docs = [doc for doc in self.all() if cond(doc)]
        self._query_cache[cond] = docs

        return docs[:]

    def get(self, cond=None, eid=None):
        """
        Get exactly one document specified by a query or and ID.

        Returns ``None`` if the document doesn't exist

        :param cond: the condition to check against
        :type cond: Query

        :param eid: the document's ID

        :returns: the document or None
        :rtype: Element | None
        """

        # Cannot use process_elements here because we want to return a
        # specific document

        if eid is not None:
            # Document specified by ID
            return self._read().get(eid, None)

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

    def contains(self, cond=None, eids=None):
        """
        Check wether the database contains a document matching a condition or
        an ID.

        If ``eids`` is set, it checks if the db contains a document with one
        of the specified.

        :param cond: the condition use
        :type cond: Query
        :param eids: the document IDs to look for
        """

        if eids is not None:
            # Documents specified by ID
            return any(self.get(eid=eid) for eid in eids)

        # Document specified by condition
        return self.get(cond) is not None

# Set the default table class
TinyDB.table_class = Table
