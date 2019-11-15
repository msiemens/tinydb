"""
Contains the :class:`database <tinydb.database.TinyDB>` and
:class:`tables <tinydb.database.Table>` implementation.
"""
from typing import Dict, Set, Iterator

from tinydb.table import Table, Document
from . import JSONStorage
from .storages import Storage


class TinyDB:
    """
    The main class of TinyDB.

    Gives access to the database, provides methods to insert/search/remove
    and getting tables.
    """

    table_class = Table
    default_storage_class = JSONStorage

    def __init__(self, *args, **kwargs):
        """
        Create a new instance of TinyDB.

        All arguments and keyword arguments will be passed to the underlying
        storage class (default: :class:`~tinydb.storages.JSONStorage`).

        :param storage: The class of the storage to use. Will be initialized
                        with ``args`` and ``kwargs``.
        :param default_table: The name of the default table to populate.
        """

        storage = kwargs.pop('storage', self.default_storage_class)

        # Prepare the storage
        self._storage = storage(*args, **kwargs)  # type: Storage

        self._opened = True

        # Prepare the default table
        self._tables = {}  # type: Dict[str, Table]

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

    def table(self, name: str = '_default', **options) -> Table:
        """
        Get access to a specific table.

        Creates a new table, if it hasn't been created before, otherwise it
        returns the cached :class:`~tinydb.Table` object.

        :param name: The name of the table.
        :param cache_size: How many query results to cache.
        """

        if name in self._tables:
            return self._tables[name]

        self._tables[name] = self.table_class(self.storage, name, **options)

        return self._tables[name]

    def tables(self) -> Set[str]:
        """
        Get the names of all tables in the database.

        :returns: a set of table names
        """

        return set(self.storage.read() or {})

    def drop_tables(self) -> None:
        """
        Drop all tables from the database. **CANNOT BE REVERSED!**
        """

        self.storage.write({})
        self._tables.clear()

    def drop_table(self, name: str) -> None:
        """
        Drop a specific table from the database. **CANNOT BE REVERSED!**

        :param name: The name of the table.
        """
        if name in self._tables:
            del self._tables[name]

        data = self.storage.read()

        if data is None:
            return

        if name not in data:
            return

        del data[name]
        self.storage.write(data)

    @property
    def storage(self) -> Storage:
        """
        Access the storage used for this TinyDB instance.

        :return: This instance's storage
        """
        return self._storage

    def close(self) -> None:
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

    def __iter__(self) -> Iterator[Document]:
        """
        Iter over all documents from default table.
        """
        return iter(self.table())
