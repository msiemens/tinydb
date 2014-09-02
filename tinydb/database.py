"""
Contains the :class:`database <tinydb.database.TinyDB>` and
:class:`tables <tinydb.database.Table>` implementation.
"""

from tinydb import JSONStorage


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

    def __init__(self, *args, **kwargs):
        """
        Create a new instance of TinyDB.

        All arguments and keyword arguments will be passed to the underlying
        storage class (default: :class:`~tinydb.storages.JSONStorage`).

        :param storage: The class of the storage to use. Will be initialized
                        with ``args`` and ``kwargs``.
        """
        storage = kwargs.pop('storage', JSONStorage)
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

        table_class = SmartCacheTable if smart_cache else Table
        table = table_class(name, self, **options)
        self._table_cache[name] = table
        return table

    def purge_tables(self):
        """
        Purge all tables from the database. **CANNOT BE REVERSED!**
        """
        self._write({})
        self._table_cache.clear()

    def _read(self, table=None):
        """
        Reading access to the backend.

        :param table: The table, we want to read, or None to read the 'all
        tables' dict.
        :type table: str or None
        :returns: all values
        :rtype: dict
        """

        if not table:
            try:
                return self._storage.read()
            except ValueError:
                return {}

        try:
            return self._read()[table]
        except (KeyError, TypeError):
            return {}

    def _write(self, values, table=None):
        """
        Writing access to the backend.

        :param table: The table, we want to write, or None to write the 'all
        tables' dict.
        :type table: str or None
        :param values: the new values to write
        :type values: list, dict
        """

        if not table:
            self._storage.write(values)
        else:
            current_data = self._read()
            current_data[table] = values

            self._write(current_data)

    def __len__(self):
        """
        Get the total number of elements in the DB.

        >>> len(db)
        0
        """
        return len(self._table)

    def __enter__(self):
        """
        See :meth:`Table.__enter__`
        """
        return self._table.__enter__()

    def __exit__(self, *args):
        """
        See :meth:`Table.__exit__`
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
        self._queries_cache = {}
        self._cache_size = cache_size or float('nan')
        self._lru = []

        try:
            self._last_id = int(sorted(self._read().keys())[-1])
        except IndexError:
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
            # Included element specified by id
            for eid in eids:
                func(data, eid)

        else:
            # Included elements specified by condition
            for eid in list(data):
                if cond(data[eid]):
                    func(data, eid)

        self._write(data)

    def _read(self):
        """
        Reading access to the DB.

        :returns: all values
        :rtype: dict
        """

        data = self._db._read(self.name)

        for eid in list(data):
            data[eid] = Element(data[eid], eid)

        return data

    def _write(self, values):
        """
        Writing access to the DB.

        :param values: the new values to write
        :type values: dict
        """

        self._clear_query_cache()
        self._db._write(values, self.name)

    def __len__(self):
        """
        Get the total number of elements in the table.
        """
        return len(self.all())

    def all(self):
        """
        Get all elements stored in the table.

        :returns: a list with all elements.
        :rtype: list[dict]
        """

        return list(self._read().values())

    def insert(self, element):
        """
        Insert a new element into the table.
        """

        current_id = self._last_id + 1
        self._last_id = current_id

        data = self._read()
        data[current_id] = element

        self._write(data)

        return current_id

    def insert_multiple(self, elements):
        """
        Insert multiple elements into the table.

        :param elements: a list of elements to insert
        """
        return [self.insert(element) for element in elements]

    def remove(self, cond=None, eids=None):
        """
        Remove the element matching the condition.

        :param cond: the condition to check against
        :type cond: query, int, list
        """
        self.process_elements(lambda data, eid: data.pop(eid), cond, eids)

    def update(self, fields, cond=None, eids=None):
        """
        Update all elements matching the condition to have a given set of
        fields.

        :param fields: the fields that the matching elements will have
        :type fields: dict
        :param cond: which elements to update
        :type cond: query
        """
        self.process_elements(lambda data, eid: data[eid].update(fields),
                              cond, eids)

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
        :rtype: list
        """

        if cond in self._queries_cache:
            self._lru.remove(cond)
            self._lru.append(cond)
            return self._queries_cache[cond]

        elems = [e for e in self.all() if cond(e)]
        self._queries_cache[cond] = elems
        self._lru.append(cond)

        # since x > float('nan') is always false,
        # no need to check for any special cases
        if len(self._queries_cache) > self._cache_size:
            self._queries_cache.pop(self._lru.pop(0))

        return elems

    def get(self, cond=None, eid=None):
        """
        Search for exactly one element matching a condition.

        :param cond: the condition to check against
        :type cond: Query

        :returns: the element or None
        :rtype: dict or None
        """

        if eid is not None:
            return self._read().get(eid, None)

        else:
            elements = self.search(cond)
            if elements:
                return elements.pop(0)

    def count(self, cond):
        """
        Count the elements matching a condition.

        :param cond: the condition use
        :type cond: Query
        """
        return len(self.search(cond))

    def contains(self, cond=None, eids=None):
        """
        Check wether the database contains an element matching a condition.

        :param cond: the condition use
        :type cond: Query
        """
        if eids is not None:
            return any(self.get(eid=eid) for eid in eids)
        else:
            return self.count(cond) > 0

    def _clear_query_cache(self):
        """
        Clear query cache.
        """
        self._queries_cache = {}
        self._lru = []

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

    The query cache gets updated on insert/update/remove. Useful when in cases
    where many searches are done but data isn't changed often.
    """

    def _write(self, values):
        self._db._write(values, self.name)

    def insert(self, element):
        """
        See :meth:`Table.insert`
        """

        eid = super(SmartCacheTable, self).insert(element)

        for query in self._queries_cache:
            cache = self._queries_cache[query]
            if query(element):
                cache.append(element)

        return eid

    def update(self, fields, cond=None, eids=None):
        """
        See :meth:`Table.update`
        """
        data = self._read()
        query_cache = tuple(self._queries_cache.items())

        for eid in (eids if eids else data.copy()):
            if eids or cond(data[eid]):

                # Update the value
                old_value = data[eid].copy()
                data[eid].update(fields)
                new_value = data[eid]

                # Update query cache
                for query, results in self._queries_cache.items():
                    if query(old_value):
                        results.remove(old_value)

                    elif query(new_value):
                        results.append(new_value)

        self._write(data)

    def remove(self,  cond=None, eids=None):
        """
        See :meth:`Table.remove`
        """
        data = self._read()
        query_cache = tuple(self._queries_cache.items())

        for eid in (eids if eids else data.copy()):
            value = data[eid]
            if eids or cond(data[eid]):

                for query, results in query_cache:
                    try:
                        results.remove(value)
                    except ValueError:
                        pass

                data.pop(eid)

        self._write(data)

    def purge(self):
        """
        See :meth:`Table.purge`
        """
        super(SmartCacheTable, self).purge()
        self._clear_query_cache()  # Query cache got invalid
