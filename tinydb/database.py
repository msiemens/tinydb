"""
Contains the :class:`database <tinydb.database.TinyDB>` and
:class:`tables <tinydb.database.Table>` implementation.
"""
from tinydb import JSONStorage
from tinydb.utils import LRUCache, iteritems, itervalues


class Element(dict):
    """
    Represents an element stored in the database.

    This is a transparent proxy for database elements. It exists
    to provide a way to access an element's id via ``el.eid``.
    """
    def __init__(self, value=None, eid=None, **kwargs):
        super(Element, self).__init__(**kwargs)

        if value is not None:
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

        storage = kwargs.pop('storage', TinyDB.DEFAULT_STORAGE)
        table = kwargs.pop('default_table', TinyDB.DEFAULT_TABLE)

        # Prepare the storage
        self._opened = False

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

        table = self.table_class(StorageProxy(self._storage, name), **options)

        self._table_cache[name] = table

        if not table._read():
            table._write({})

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
        if self._opened is True:
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
        Get the total number of elements in the default table.

        >>> db = TinyDB('db.json')
        >>> len(db)
        0
        """
        return len(self._table)


class Table(object):
    """
    Represents a single TinyDB Table.
    """

    def __init__(self, storage, cache_size=10):
        """
        Get access to a table.

        :param storage: Access to the storage
        :type storage: StorageProxyus
        :param cache_size: Maximum size of query cache.
        """

        self._storage = storage
        self._query_cache = LRUCache(capacity=cache_size)

        data = self._read()
        if data:
            self._last_id = max(i for i in data)
        else:
            self._last_id = 0

    def process_elements(self, func, cond=None, eids=None):
        """
        Helper function for processing all elements specified by condition
        or IDs.

        A repeating pattern in TinyDB is to run some code on all elements
        that match a condition or are specified by their ID. This is
        implemented in this function.
        The function passed as ``func`` has to be a callable. It's first
        argument will be the data currently in the database. It's second
        argument is the element ID of the currently processed element.

        See: :meth:`~.update`, :meth:`.remove`

        :param func: the function to execute on every included element.
                     first argument: all data
                     second argument: the current eid
        :param cond: elements to use, or
        :param eids: elements to use
        :returns: the element IDs that were affected during processed
        """

        data = self._read()

        if eids is not None:
            # Processed element specified by id
            for eid in eids:
                func(data, eid)

        else:
            # Collect affected eids
            eids = []

            # Processed elements specified by condition
            for eid in list(data):
                if cond(data[eid]):
                    func(data, eid)
                    eids.append(eid)

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
        Get the total number of elements in the table.
        """
        return len(self._read())

    def all(self):
        """
        Get all elements stored in the table.

        :returns: a list with all elements.
        :rtype: list[Element]
        """

        return list(itervalues(self._read()))

    def insert(self, element):
        """
        Insert a new element into the table.

        :param element: the element to insert
        :returns: the inserted element's ID
        """

        eid = self._get_next_id()

        if not isinstance(element, dict):
            raise ValueError('Element is not a dictionary')

        data = self._read()
        data[eid] = element
        self._write(data)

        return eid

    def insert_multiple(self, elements):
        """
        Insert multiple elements into the table.

        :param elements: a list of elements to insert
        :returns: a list containing the inserted elements' IDs
        """

        eids = []
        data = self._read()

        for element in elements:
            eid = self._get_next_id()
            eids.append(eid)

            data[eid] = element

        self._write(data)

        return eids

    def remove(self, cond=None, eids=None):
        """
        Remove all matching elements.

        :param cond: the condition to check against
        :type cond: query
        :param eids: a list of element IDs
        :type eids: list
        :returns: a list containing the removed element's ID
        """

        return self.process_elements(lambda data, eid: data.pop(eid),
                                     cond, eids)

    def update(self, fields, cond=None, eids=None):
        """
        Update all matching elements to have a given set of fields.

        :param fields: the fields that the matching elements will have
                       or a method that will update the elements
        :type fields: dict | dict -> None
        :param cond: which elements to update
        :type cond: query
        :param eids: a list of element IDs
        :type eids: list
        :returns: a list containing the updated element's ID
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
        Purge the table by removing all elements.
        """

        self._write({})
        self._last_id = 0

    def search(self, cond):
        """
        Search for all elements matching a 'where' cond.

        :param cond: the condition to check against
        :type cond: Query

        :returns: list of matching elements
        :rtype: list[Element]
        """

        if cond in self._query_cache:
            return self._query_cache[cond]

        elements = [element for element in self.all() if cond(element)]
        self._query_cache[cond] = elements

        return elements

    def get(self, cond=None, eid=None):
        """
        Get exactly one element specified by a query or and ID.

        Returns ``None`` if the element doesn't exist

        :param cond: the condition to check against
        :type cond: Query

        :param eid: the element's ID

        :returns: the element or None
        :rtype: Element | None
        """

        # Cannot use process_elements here because we want to return a
        # specific element

        if eid is not None:
            # Element specified by ID
            return self._read().get(eid, None)

        # Element specified by condition
        for element in self.all():
            if cond(element):
                return element

    def count(self, cond):
        """
        Count the elements matching a condition.

        :param cond: the condition use
        :type cond: Query
        """

        return len(self.search(cond))

    def contains(self, cond=None, eids=None):
        """
        Check wether the database contains an element matching a condition or
        an ID.

        If ``eids`` is set, it checks if the db contains an element with one
        of the specified.

        :param cond: the condition use
        :type cond: Query
        :param eids: the element IDs to look for
        """

        if eids is not None:
            # Elements specified by ID
            return any(self.get(eid=eid) for eid in eids)

        # Element specified by condition
        return self.get(cond) is not None

# Set the default table class
TinyDB.table_class = Table
