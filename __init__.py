from tinydb.storages import Storage, JSONStorage
from tinydb.queries import field

__all__ = ('TinyDB',)


class TinyDB(object):
    """
    A plain & simple DB.

    TinyDB stores all types of python objects using a configurable backend.
    It has support for handy querying and tables.

    >>> db = TinyDB('<memory>', backend=MemoryBackend)
    >>> db.insert({'data': 5})  # Insert into '_default' table
    >>> db.search(field('data') == 5)
    [{'data': 5, '_id': 1}]
    >>> # Now let's use a table
    >>> tbl = db.table('our_table')
    >>> for i in range(10):
    ...     tbl.insert({'data': i % 2})
    >>> len(tbl.search(field('data') == 0))
    5
    >>>

    """

    _table_cache = {}

    def __init__(self, *args, **kwargs):
        storage = kwargs.pop('storage', JSONStorage)
        #: :type: Storage
        self._storage = storage(*args, **kwargs)
        self._table = self.table('_default')

    def table(self, name='_default'):
        """
        Get access to a specific table.

        :param name: The name of the table.
        :type name: str
        """
        if name in self._table_cache:
            return self._table_cache[name]

        table = Table(name, self)
        self._table_cache[name] = table
        return table

    def purge_all(self):
        """
        Purge all tables from the database. CANT BE REVERSED!
        """
        self._write({})

    def _read(self, table=None):
        """
        Reading access to the backend.

        :param table: The table, we want to read, or None to read the 'all
        tables' dict.
        :type table: dict or None
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
        Writing access to the backend

        :param table: The table, we want to write, or None to write the 'all
        tables' dict.
        :type table: dict or None
        :param values: the new values to write
        :type values: dict
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
        """
        return len(self._table)

    def __contains__(self, item):
        """
        A shorthand for ``field(...) == ... in db.table()``
        """
        return item in self.table()

    def __getattr__(self, name):
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
        :type db: TinyDB
        """
        self.name = name
        self._db = db
        self._queries_cache = {}

        try:
            self._last_id = self._read().keys().pop()
        except IndexError:
            self._last_id = 0

    def _read(self):
        """
        Reading access to the DB.

        :returns: all values
        :rtype: dict
        """

        return self._db._read(self.name)

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

    def __contains__(self, where):
        """
        Equals to bool(table.search(where)))
        """
        return bool(self.search(where))

    def all(self):
        """
        Get all elements stored in the table.

        :returns: a list of all elements.
        :rtype: list
        """

        return self._read().values()

    def insert(self, element):
        """
        Insert a new element into the table.

        element has to be a dict, not containing the key 'id'.
        """

        self._last_id += 1
        next_id = self._last_id

        data = self._read()
        data[next_id] = element

        self._write(data)

    def remove(self, where):
        """
        Remove the element matching the condition.

        :param where: the condition
        :type where: has
        """

        to_remove = self.search(where)
        new_values = dict(
            [(id, val) for id, val in self._read().iteritems()
             if val not in to_remove]
        )  # We don't use the new dict comprehension to support Python 2.6 :/

        self._write(new_values)

    def purge(self):
        """
        Purge the table by removing all elements.
        """
        self._write({})

    def search(self, where):
        """
        Search for all elements matching a 'where' condition.

        :param where: the condition
        :type where: has

        :returns: list of matching elements
        :rtype: list
        """

        if where in self._queries_cache:
            return self._queries_cache[where]
        else:
            elems = [e for e in self.all() if where(e)]
            self._queries_cache[where] = elems

            return elems

    def get(self, where):
        """
        Search for exactly one element matching a 'where' condition.

        :param where: the condition
        :type where: has

        :returns: the element or None
        :rtype: dict or None
        """

        for el in self.all():
            if where(el):
                return el

    def _clear_query_cache(self):
        """

        """
        self._queries_cache = {}
