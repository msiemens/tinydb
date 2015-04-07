"""
Contains the :class:`database <tinydb.database.TinyDB>` and
:class:`tables <tinydb.database.Table>` implementation.
"""
import warnings
from tinydb import JSONStorage
from tinydb.utils import LRUCache


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


class TinyDB(object):
    """
    The main class of TinyDB.

    Gives access to the database, provides methods to insert/search/remove
    and getting tables.
    """

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
        #: :type: Storage
        self._storage = storage(*args, **kwargs)

        self._table_cache = {}
        self._table = self.table('_default')

    def table(self, name='_default', smart_cache=False, **options):
        """
        Get access to a specific table.

        Creates a new table, if it hasn't been created before, otherwise it
        returns the cached :class:`~tinydb.Table` object.

        :param name: The name of the table.
        :type name: str
        :param smart_cache: Use a smarter query caching.
                            See :class:`tinydb.database.SmartCacheTable`
        :param cache_size: How many query results to cache.
        """

        if name in self._table_cache:
            return self._table_cache[name]

        if smart_cache:
            warnings.warn('Passing the smart_cache argument is deprecated. '
                          'Please set the table class to use via '
                          '`db.table_class = SmartCacheTable` or '
                          '`TinyDB.table_class = SmartCacheTable` instead.',
                          DeprecationWarning)

        # If smart_cache is set, use SmartCacheTable to retain backwards
        # compatibility
        table_class = SmartCacheTable if smart_cache else self.table_class
        table = table_class(name, self, **options)

        self._table_cache[name] = table

        if name not in self._read():
            self._write_table({}, name)

        return table

    def tables(self):
        """
        Get the names of all tables in the database.

        :returns: a set of table names
        :rtype: set[str]
        """

        return set(self._read().keys())

    def purge_tables(self):
        """
        Purge all tables from the database. **CANNOT BE REVERSED!**
        """

        self._write({})
        self._table_cache.clear()

    def _read(self):
        """
        Reading access to the backend.

        :returns: all tables
        :rtype: dict
        """

        try:
            return self._storage.read()
        except ValueError:
            return {}

    def _read_table(self, table):
        """
        Read a table from the backend.

        :param table: The name of the table to read
        :return: dict
        """

        try:
            return self._read()[table]
        except (KeyError, TypeError):
            return {}

    def _write(self, tables):
        """
        Writing access to the backend.

        :param tables: The new tables to write
        :type tables: dict
        """

        # Write all tables
        self._storage.write(tables)

    def _write_table(self, values, table):
        """
        Write data for a table.

        :param values: The values contained in the table
        :type values: dict
        :param table: The name of the table to write
        :type table: str
        """

        # Write specific table
        data = self._read()
        data[table] = values

        self._write(data)

    # Methods that are executed on the default table
    # Because magic methods are not handlet by __getattr__ we need to forward
    # them manually here

    def __len__(self):
        """
        Get the total number of elements in the DB.

        >>> db = TinyDB('db.json')
        >>> len(db)
        0
        """
        return len(self._table)

    def __enter__(self):
        """
        See :meth:`.Table.__enter__`
        """
        return self._table.__enter__()

    def __exit__(self, *args):
        """
        See :meth:`.Table.__exit__`
        """
        return self._table.__exit__(*args)

    def __getattr__(self, name):
        """
        Forward all unknown attribute calls to the underlying standard table.
        """
        return getattr(self._table, name)


class Table(object):
    """
    Represents a single TinyDB Table.
    """

    def __init__(self, name, db, cache_size=10):
        """
        Get access to a table.

        :param name: The name of the table.
        :type name: str
        :param db: The parent database.
        :type db: tinydb.database.TinyDB
        :param cache_size: Maximum size of query cache.
        """

        self.name = name
        self._db = db
        self._query_cache = LRUCache(capacity=cache_size)

        old_ids = self._read().keys()
        if old_ids:
            self._last_id = max(i for i in old_ids)
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
        :param cond: elements to use
        :param eids: elements to use
        """

        data = self._read()

        if eids is not None:
            # Processed element specified by id
            for eid in eids:
                func(data, eid)

        else:
            # Processed elements specified by condition
            for eid in list(data):
                if cond(data[eid]):
                    func(data, eid)

        self._write(data)

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

        raw_data = self._db._read_table(self.name)
        data = {}
        for key in list(raw_data):
            eid = int(key)
            data[eid] = Element(raw_data[key], eid)

        return data

    def _write(self, values):
        """
        Writing access to the DB.

        :param values: the new values to write
        :type values: dict
        """

        self._query_cache.clear()
        self._db._write_table(values, self.name)

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

        return list(self._read().values())

    def insert(self, element):
        """
        Insert a new element into the table.

        :param element: the element to insert
        :returns: the inserted element's ID
        """

        eid = self._get_next_id()

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
        """

        self.process_elements(lambda data, eid: data.pop(eid), cond, eids)

    def update(self, fields, cond=None, eids=None):
        """
        Update all matching elements to have a given set of fields.

        :param fields: the fields that the matching elements will have
                       or a method that will update the elements
        :type fields: dict | (dict, int) -> None
        :param cond: which elements to update
        :type cond: query
        :param eids: a list of element IDs
        :type eids: list
        """

        if callable(fields):
            _update = lambda data, eid: fields(data[eid])
        else:
            _update = lambda data, eid: data[eid].update(fields)

        self.process_elements(_update, cond, eids)

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

    def __enter__(self):
        """
        Allow the database to be used as a context manager.

        :return: the table instance
        """

        return self

    def __exit__(self, *args):
        """
        Try to close the storage after being used as a context manager.
        """

        _ = args
        self._db._storage.close()

    close = __exit__


class SmartCacheTable(Table):
    """
    A Table with a smarter query cache.

    Provides the same methods as :class:`~tinydb.database.Table`.

    The query cache gets updated on insert/update/remove. Useful when in cases
    where many searches are done but data isn't changed often.
    """

    def _write(self, values):
        # Just write data, don't clear the query cache
        self._db._write_table(values, self.name)

    def insert(self, element):
        # See Table.insert

        # Insert element
        eid = super(SmartCacheTable, self).insert(element)

        # Update query cache
        for query in self._query_cache:
            results = self._query_cache[query]
            if query(element):
                results.append(element)

        return eid

    def insert_multiple(self, elements):
        # See Table.insert_multiple

        # We have to call `SmartCacheTable.insert` here because
        # `Table.insert_multiple` doesn't call `insert()` for every element
        return [self.insert(element) for element in elements]

    def update(self, fields, cond=None, eids=None):
        # See Table.update

        if callable(fields):
            _update = lambda data, eid: fields(data[eid])
        else:
            _update = lambda data, eid: data[eid].update(fields)

        def process(data, eid):
            old_value = data[eid].copy()

            # Update element
            _update(data, eid)
            new_value = data[eid]

            # Update query cache
            for query in self._query_cache:
                results = self._query_cache[query]

                if query(old_value):
                    # Remove old value from cache
                    results.remove(old_value)

                elif query(new_value):
                    # Add new value to cache
                    results.append(new_value)

        self.process_elements(process, cond, eids)

    def remove(self, cond=None, eids=None):
        # See Table.remove

        def process(data, eid):
            # Update query cache
            for query in self._query_cache:

                results = self._query_cache[query]
                try:
                    results.remove(data[eid])
                except ValueError:
                    pass

            # Remove element
            data.pop(eid)

        self.process_elements(process, cond, eids)

    def purge(self):
        # See Table.purge

        super(SmartCacheTable, self).purge()
        self._query_cache.clear()  # Query cache got invalid


# Set the default table class
TinyDB.table_class = Table
