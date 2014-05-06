"""
Contains the :class:`database <tinydb.database.TinyDB>` and
:class:`tables <tinydb.database.Table>` implementation.
"""

from tinydb import JSONStorage, where


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
        """
        storage = kwargs.pop('storage', JSONStorage)
        #: :type: Storage
        self._storage = storage(*args, **kwargs)

        self._table_cache = {}
        self._table = self.table('_default')

    def table(self, name='_default'):
        """
        Get access to a specific table.

        Creates a new table, if it hasn't been created before, otherwise it
        returns the cached :class:`~tinydb.Table` object.

        :param name: The name of the table.
        :type name: str
        """

        if name in self._table_cache:
            return self._table_cache[name]

        table = Table(name, self)
        self._table_cache[name] = table
        return table

    def purge_tables(self):
        """
        Purge all tables from the database. **CANT BE REVERSED!**
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
        :rtype: dict, list
        """

        if not table:
            try:
                return self._storage.read()
            except ValueError:
                return {}

        try:
            return self._read()[table]
        except (KeyError, TypeError):
            return []

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

    def __contains__(self, item):
        """
        A shorthand for ``query(...) == ... in db.table()``. Intendet to be
        used in if-clauses (avoiding ``if len(db.serach(...)):``)

        >>> if where('field') == 'value' in db:
        ...     print True
        """
        return item in self._table

    def __getattr__(self, name):
        """
        Forward all unknown attribute calls to the underlying standard table.
        """
        return getattr(self._table, name)


class Table(object):
    """
    Represents a single TinyDB Table.
    """

    def __init__(self, name, db):
        """
        Get access to a table.

        :param name: The name of the table.
        :type name: str
        :param db: The parent database.
        :type db: tinydb.database.TinyDB
        """
        self.name = name
        self._db = db
        self._queries_cache = {}

        try:
            self._last_id = self._read().pop()['_id']
        except IndexError:
            self._last_id = 0

    def _read(self):
        """
        Reading access to the DB.

        :returns: all values
        :rtype: list
        """

        return self._db._read(self.name)

    def _write(self, values):
        """
        Writing access to the DB.

        :param values: the new values to write
        :type values: list
        """

        self._clear_query_cache()
        self._db._write(values, self.name)

    def __len__(self):
        """
        Get the total number of elements in the table.
        """
        return len(self.all())

    def __contains__(self, condition):
        """
        Equals to ``bool(table.search(condition)))``.
        """
        return bool(self.search(condition))

    def all(self):
        """
        Get all elements stored in the table.

        Note: all elements will have an `_id` key.

        :returns: a list with all elements.
        :rtype: list
        """

        return self._read()

    def insert(self, element):
        """
        Insert a new element into the table.

        element has to be a dict, not containing the key 'id'.
        """

        next_id = self._last_id
        self._last_id += 1

        element['_id'] = next_id

        data = self._read()
        data.append(element)

        self._write(data)

    def remove(self, cond):
        """
        Remove the element matching the condition.

        :param cond: the condition to check against
        :type cond: query, int, list
        """

        to_remove = self.search(cond)
        self._write([e for e in self.all() if e not in to_remove])

    def purge(self):
        """
        Purge the table by removing all elements.
        """
        self._write([])

    def search(self, cond):
        """
        Search for all elements matching a 'where' cond.

        Note: all elements will have an `_id` key.

        :param cond: the condition to check against
        :type cond: Query

        :returns: list of matching elements
        :rtype: list
        """

        if cond in self._queries_cache:
            return self._queries_cache[where]
        else:
            elems = [e for e in self.all() if cond(e)]
            self._queries_cache[where] = elems

            return elems

    def get(self, cond):
        """
        Search for exactly one element matching a 'where' condition.

        Note: all elements will have an `_id` key.

        :param cond: the condition to check against
        :type cond: Query

        :returns: the element or None
        :rtype: dict or None
        """

        for el in self.all():
            if cond(el):
                return el

    def _clear_query_cache(self):
        """
        Clear query cache.
        """
        self._queries_cache = {}
