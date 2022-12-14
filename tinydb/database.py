"""
This module contains the main component of TinyDB: the database.
"""
from typing import Dict, Iterator, Set, Type

from . import JSONStorage
from .storages import Storage
from .table import Table, Document
from .utils import with_typehint

# The table's base class. This is used to add type hinting from the Table
# class to TinyDB. Currently, this supports PyCharm, Pyright/VS Code and MyPy.
TableBase: Type[Table] = with_typehint(Table)


class TinyDB(TableBase):
    """
    The main class of TinyDB.

    The ``TinyDB`` class is responsible for creating the storage class instance
    that will store this database's documents, managing the database
    tables as well as providing access to the default table.

    For table management, a simple ``dict`` is used that stores the table class
    instances accessible using their table name.

    Default table access is provided by forwarding all unknown method calls
    and property access operations to the default table by implementing
    ``__getattr__``.

    When creating a new instance, all arguments and keyword arguments (except
    for ``storage``) will be passed to the storage class that is provided. If
    no storage class is specified, :class:`~tinydb.storages.JSONStorage` will be
    used.

    .. admonition:: Customization

        For customization, the following class variables can be set:

        - ``table_class`` defines the class that is used to create tables,
        - ``default_table_name`` defines the name of the default table, and
        - ``default_storage_class`` will define the class that will be used to
          create storage instances if no other storage is passed.

        .. versionadded:: 4.0

    .. admonition:: Data Storage Model

        Data is stored using a storage class that provides persistence for a
        ``dict`` instance. This ``dict`` contains all tables and their data.
        The data is modelled like this::

            {
                'table1': {
                    0: {document...},
                    1: {document...},
                },
                'table2': {
                    ...
                }
            }

        Each entry in this ``dict`` uses the table name as its key and a
        ``dict`` of documents as its value. The document ``dict`` contains
        document IDs as keys and the documents themselves as values.

    :param storage: The class of the storage to use. Will be initialized
                    with ``args`` and ``kwargs``.
    """

    #: The class that will be used to create table instances
    #:
    #: .. versionadded:: 4.0
    table_class = Table

    #: The name of the default table
    #:
    #: .. versionadded:: 4.0
    default_table_name = '_default'

    #: The class that will be used by default to create storage instances
    #:
    #: .. versionadded:: 4.0
    default_storage_class = JSONStorage

    def __init__(self, *args, **kwargs) -> None:
        """
        Create a new instance of TinyDB.
        """

        storage = kwargs.pop('storage', self.default_storage_class)

        # Prepare the storage
        self._storage: Storage = storage(*args, **kwargs)

        self._opened = True
        self._tables: Dict[str, Table] = {}

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

    def table(self, name: str, **kwargs) -> Table:
        """
        Get access to a specific table.

        If the table hasn't been accessed yet, a new table instance will be
        created using the :attr:`~tinydb.database.TinyDB.table_class` class.
        Otherwise, the previously created table instance will be returned.

        All further options besides the name are passed to the table class which
        by default is :class:`~tinydb.table.Table`. Check its documentation
        for further parameters you can pass.

        :param name: The name of the table.
        :param kwargs: Keyword arguments to pass to the table class constructor
        """

        if name in self._tables:
            return self._tables[name]

        table = self.table_class(self.storage, name, **kwargs)
        self._tables[name] = table

        return table

    def tables(self) -> Set[str]:
        """
        Get the names of all tables in the database.

        :returns: a set of table names
        """

        # TinyDB stores data as a dict of tables like this:
        #
        #   {
        #       '_default': {
        #           0: {document...},
        #           1: {document...},
        #       },
        #       'table1': {
        #           ...
        #       }
        #   }
        #
        # To get a set of table names, we thus construct a set of this main
        # dict which returns a set of the dict keys which are the table names.
        #
        # Storage.read() may return ``None`` if the database file is empty,
        # so we need to consider this case to and return an empty set in this
        # case.

        return set(self.storage.read() or {})

    def drop_tables(self) -> None:
        """
        Drop all tables from the database. **CANNOT BE REVERSED!**
        """

        # We drop all tables from this database by writing an empty dict
        # to the storage thereby returning to the initial state with no tables.
        self.storage.write({})

        # After that we need to remember to empty the ``_tables`` dict, so we'll
        # create new table instances when a table is accessed again.
        self._tables.clear()

    def drop_table(self, name: str) -> None:
        """
        Drop a specific table from the database. **CANNOT BE REVERSED!**

        :param name: The name of the table to drop.
        """

        # If the table is currently opened, we need to forget the table class
        # instance
        if name in self._tables:
            del self._tables[name]

        data = self.storage.read()

        # The database is uninitialized, there's nothing to do
        if data is None:
            return

        # The table does not exist, there's nothing to do
        if name not in data:
            return

        # Remove the table from the data dict
        del data[name]

        # Store the updated data back to the storage
        self.storage.write(data)

    @property
    def storage(self) -> Storage:
        """
        Get the storage instance used for this TinyDB instance.

        :return: This instance's storage
        :rtype: Storage
        """
        return self._storage

    def close(self) -> None:
        """
        Close the database.

        This may be needed if the storage instance used for this database
        needs to perform cleanup operations like closing file handles.

        To ensure this method is called, the TinyDB instance can be used as a
        context manager::

            with TinyDB('data.json') as db:
                db.insert({'foo': 'bar'})

        Upon leaving this context, the ``close`` method will be called.
        """
        self._opened = False
        self.storage.close()

    def __enter__(self):
        """
        Use the database as a context manager.

        Using the database as a context manager ensures that the
        :meth:`~tinydb.database.TinyDB.close` method is called upon leaving
        the context.

        :return: The current instance
        """
        return self

    def __exit__(self, *args):
        """
        Close the storage instance when leaving a context.
        """
        if self._opened:
            self.close()

    def __getattr__(self, name):
        """
        Forward all unknown attribute calls to the default table instance.
        """
        return getattr(self.table(self.default_table_name), name)

    # Here we forward magic methods to the default table instance. These are
    # not handled by __getattr__ so we need to forward them manually here

    def __len__(self):
        """
        Get the total number of documents in the default table.

        >>> db = TinyDB('db.json')
        >>> len(db)
        0
        """
        return len(self.table(self.default_table_name))

    def __iter__(self) -> Iterator[Document]:
        """
        Return an iterator for the default table's documents.
        """
        return iter(self.table(self.default_table_name))
