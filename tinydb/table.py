"""
This module implements tables, the central place for accessing and manipulating
data in TinyDB.
"""

from typing import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Union,
    cast,
    Tuple
)

from .queries import QueryLike
from .storages import Storage
from .utils import LRUCache

__all__ = ('Document', 'Table')


class Document(dict):
    """
    A document stored in the database.

    This class provides a way to access both a document's content as well as
    its ID using ``doc.doc_id``.
    """

    def __init__(self, value: Mapping, doc_id: int):
        super().__init__(value)
        self.doc_id = doc_id


class Table:
    """
    Represents a single TinyDB table.

    It provides methods for accessing and manipulating documents.

    .. admonition:: Query Cache

        As an optimization, a query cache is implemented using a
        :class:`~tinydb.utils.LRUCache`. This class mimics the interface of
        a normal ``dict``, but starts to remove the least-recently used entries
        once a threshold is reached.

        The query cache is updated on every search operation. When writing
        data, the whole cache is discareded as the query results may have
        changed.

    .. admonition:: Customization

        For customization, the following class variables can be set:

        - ``document_class`` defines the class that is used to represent
          documents,
        - ``document_id_class`` defines the class that is used to represent
          document IDs,
        - ``query_cache_class`` defines the class that is used for the query
          cache
        - ``default_query_cache_capacity`` defines the default capacity of
          the query cache

        .. versionadded:: 4.0


    :param storage: The storage instance to use for this table
    :param name: The table name
    :param cache_size: Maximum capacity of query cache
    """

    #: The class used to represent documents
    #:
    #: .. versionadded:: 4.0
    document_class = Document

    #: The class used to represent a document ID
    #:
    #: .. versionadded:: 4.0
    document_id_class = int

    #: The class used for caching query results
    #:
    #: .. versionadded:: 4.0
    query_cache_class = LRUCache

    #: The default capacity of the query cache
    #:
    #: .. versionadded:: 4.0
    default_query_cache_capacity = 10

    def __init__(
        self,
        storage: Storage,
        name: str,
        cache_size: int = default_query_cache_capacity
    ):
        """
        Create a table instance.
        """

        self._storage = storage
        self._name = name
        self._query_cache: LRUCache[QueryLike, List[Document]] \
            = self.query_cache_class(capacity=cache_size)

        self._next_id = None

    def __repr__(self):
        args = [
            'name={!r}'.format(self.name),
            'total={}'.format(len(self)),
            'storage={}'.format(self._storage),
        ]

        return '<{} {}>'.format(type(self).__name__, ', '.join(args))

    @property
    def name(self) -> str:
        """
        Get the table name.
        """
        return self._name

    @property
    def storage(self) -> Storage:
        """
        Get the table storage instance.
        """
        return self._storage

    def insert(self, document: Mapping) -> int:
        """
        Insert a new document into the table.

        :param document: the document to insert
        :returns: the inserted document's ID
        """

        # Make sure the document implements the ``Mapping`` interface
        if not isinstance(document, Mapping):
            raise ValueError('Document is not a Mapping')

        # First, we get the document ID for the new document
        if isinstance(document, Document):
            # For a `Document` object we use the specified ID
            doc_id = document.doc_id

            # We also reset the stored next ID so the next insert won't
            # re-use document IDs by accident when storing an old value
            self._next_id = None
        else:
            # In all other cases we use the next free ID
            doc_id = self._get_next_id()

        # Now, we update the table and add the document
        def updater(table: dict):
            assert doc_id not in table, 'doc_id '+str(doc_id)+' already exists'

            # By calling ``dict(document)`` we convert the data we got to a
            # ``dict`` instance even if it was a different class that
            # implemented the ``Mapping`` interface
            table[doc_id] = dict(document)

        # See below for details on ``Table._update``
        self._update_table(updater)

        return doc_id

    def insert_multiple(self, documents: Iterable[Mapping]) -> List[int]:
        """
        Insert multiple documents into the table.

        :param documents: a Iterable of documents to insert
        :returns: a list containing the inserted documents' IDs
        """
        doc_ids = []

        def updater(table: dict):
            for document in documents:
                # Make sure the document implements the ``Mapping`` interface
                if not isinstance(document, Mapping):
                    raise ValueError('Document is not a Mapping')

                # Get the document ID for this document and store it so we
                # can return all document IDs later
                doc_id = self._get_next_id()
                doc_ids.append(doc_id)

                # Convert the document to a ``dict`` (see Table.insert) and
                # store it
                table[doc_id] = dict(document)

        # See below for details on ``Table._update``
        self._update_table(updater)

        return doc_ids

    def all(self) -> List[Document]:
        """
        Get all documents stored in the table.

        :returns: a list with all documents.
        """

        # iter(self) (implemented in Table.__iter__ provides an iterator
        # that returns all documents in this table. We use it to get a list
        # of all documents by using the ``list`` constructor to perform the
        # conversion.

        return list(iter(self))

    def search(self, cond: QueryLike) -> List[Document]:
        """
        Search for all documents matching a 'where' cond.

        :param cond: the condition to check against
        :returns: list of matching documents
        """

        # First, we check the query cache to see if it has results for this
        # query
        cached_results = self._query_cache.get(cond)
        if cached_results is not None:
            return cached_results[:]

        # Perform the search by applying the query to all documents
        docs = [doc for doc in self if cond(doc)]

        # Update the query cache
        self._query_cache[cond] = docs[:]

        return docs

    def get(
        self,
        cond: Optional[QueryLike] = None,
        doc_id: Optional[int] = None,
    ) -> Optional[Document]:
        """
        Get exactly one document specified by a query or a document ID.

        Returns ``None`` if the document doesn't exist.

        :param cond: the condition to check against
        :param doc_id: the document's ID

        :returns: the document or ``None``
        """

        if doc_id is not None:
            # Retrieve a document specified by its ID
            table = self._read_table()
            raw_doc = table.get(doc_id, None)

            if raw_doc is None:
                return None

            # Convert the raw data to the document class
            return self.document_class(raw_doc, doc_id)

        elif cond is not None:
            # Find a document specified by a query
            for doc in self:
                if cond(doc):
                    return doc

            return None

        raise RuntimeError('You have to pass either cond or doc_id')

    def contains(
        self,
        cond: Optional[QueryLike] = None,
        doc_id: Optional[int] = None
    ) -> bool:
        """
        Check whether the database contains a document matching a query or
        an ID.

        If ``doc_id`` is set, it checks if the db contains the specified ID.

        :param cond: the condition use
        :param doc_id: the document ID to look for
        """
        if doc_id is not None:
            # Documents specified by ID
            return self.get(doc_id=doc_id) is not None

        elif cond is not None:
            # Document specified by condition
            return self.get(cond) is not None

        raise RuntimeError('You have to pass either cond or doc_id')

    def update(
        self,
        fields: Union[Mapping, Callable[[Mapping], None]],
        cond: Optional[QueryLike] = None,
        doc_ids: Optional[Iterable[int]] = None,
    ) -> List[int]:
        """
        Update all matching documents to have a given set of fields.

        :param fields: the fields that the matching documents will have
                       or a method that will update the documents
        :param cond: which documents to update
        :param doc_ids: a list of document IDs
        :returns: a list containing the updated document's ID
        """

        # Define the function that will perform the update
        if callable(fields):
            def perform_update(table, doc_id):
                # Update documents by calling the update function provided by
                # the user
                fields(table[doc_id])
        else:
            def perform_update(table, doc_id):
                # Update documents by setting all fields from the provided data
                table[doc_id].update(fields)

        if doc_ids is not None:
            # Perform the update operation for documents specified by a list
            # of document IDs

            updated_ids = list(doc_ids)

            def updater(table: dict):
                # Call the processing callback with all document IDs
                for doc_id in updated_ids:
                    perform_update(table, doc_id)

            # Perform the update operation (see _update_table for details)
            self._update_table(updater)

            return updated_ids

        elif cond is not None:
            # Perform the update operation for documents specified by a query

            # Collect affected doc_ids
            updated_ids = []

            def updater(table: dict):
                _cond = cast(QueryLike, cond)

                # We need to convert the keys iterator to a list because
                # we may remove entries from the ``table`` dict during
                # iteration and doing this without the list conversion would
                # result in an exception (RuntimeError: dictionary changed size
                # during iteration)
                for doc_id in list(table.keys()):
                    # Pass through all documents to find documents matching the
                    # query. Call the processing callback with the document ID
                    if _cond(table[doc_id]):
                        # Add ID to list of updated documents
                        updated_ids.append(doc_id)

                        # Perform the update (see above)
                        perform_update(table, doc_id)

            # Perform the update operation (see _update_table for details)
            self._update_table(updater)

            return updated_ids

        else:
            # Update all documents unconditionally

            updated_ids = []

            def updater(table: dict):
                # Process all documents
                for doc_id in list(table.keys()):
                    # Add ID to list of updated documents
                    updated_ids.append(doc_id)

                    # Perform the update (see above)
                    perform_update(table, doc_id)

            # Perform the update operation (see _update_table for details)
            self._update_table(updater)

            return updated_ids

    def update_multiple(
        self,
        updates: Iterable[
            Tuple[Union[Mapping, Callable[[Mapping], None]], QueryLike]
        ],
    ) -> List[int]:
        """
        Update all matching documents to have a given set of fields.

        :returns: a list containing the updated document's ID
        """

        # Define the function that will perform the update
        def perform_update(fields, table, doc_id):
            if callable(fields):
                # Update documents by calling the update function provided
                # by the user
                fields(table[doc_id])
            else:
                # Update documents by setting all fields from the provided
                # data
                table[doc_id].update(fields)

        # Perform the update operation for documents specified by a query

        # Collect affected doc_ids
        updated_ids = []

        def updater(table: dict):
            # We need to convert the keys iterator to a list because
            # we may remove entries from the ``table`` dict during
            # iteration and doing this without the list conversion would
            # result in an exception (RuntimeError: dictionary changed size
            # during iteration)
            for doc_id in list(table.keys()):
                for fields, cond in updates:
                    _cond = cast(QueryLike, cond)

                    # Pass through all documents to find documents matching the
                    # query. Call the processing callback with the document ID
                    if _cond(table[doc_id]):
                        # Add ID to list of updated documents
                        updated_ids.append(doc_id)

                        # Perform the update (see above)
                        perform_update(fields, table, doc_id)

        # Perform the update operation (see _update_table for details)
        self._update_table(updater)

        return updated_ids

    def upsert(self, document: Mapping, cond: Optional[QueryLike] = None) -> List[int]:
        """
        Update documents, if they exist, insert them otherwise.

        Note: This will update *all* documents matching the query. Document
        argument can be a tinydb.table.Document object if you want to specify a
        doc_id.

        :param document: the document to insert or the fields to update
        :param cond: which document to look for, optional if you've passed a
        Document with a doc_id
        :returns: a list containing the updated documents' IDs
        """

        # Extract doc_id
        if isinstance(document, Document) and hasattr(document, 'doc_id'):
            doc_ids: Optional[List[int]] = [document.doc_id]
        else:
            doc_ids = None

        # Make sure we can actually find a matching document
        if doc_ids is None and cond is None:
            raise ValueError("If you don't specify a search query, you must "
                             "specify a doc_id. Hint: use a table.Document "
                             "object.")

        # Perform the update operation
        try:
            updated_docs: Optional[List[int]] = self.update(document, cond, doc_ids)
        except KeyError:
            # This happens when a doc_id is specified, but it's missing
            updated_docs = None

        # If documents have been updated: return their IDs
        if updated_docs:
            return updated_docs

        # There are no documents that match the specified query -> insert the
        # data as a new document
        return [self.insert(document)]

    def remove(
        self,
        cond: Optional[QueryLike] = None,
        doc_ids: Optional[Iterable[int]] = None,
    ) -> List[int]:
        """
        Remove all matching documents.

        :param cond: the condition to check against
        :param doc_ids: a list of document IDs
        :returns: a list containing the removed documents' ID
        """
        if cond is not None:
            removed_ids = []

            # This updater function will be called with the table data
            # as its first argument. See ``Table._update`` for details on this
            # operation
            def updater(table: dict):
                # We need to convince MyPy (the static type checker) that
                # the ``cond is not None`` invariant still holds true when
                # the updater function is called
                _cond = cast(QueryLike, cond)

                # We need to convert the keys iterator to a list because
                # we may remove entries from the ``table`` dict during
                # iteration and doing this without the list conversion would
                # result in an exception (RuntimeError: dictionary changed size
                # during iteration)
                for doc_id in list(table.keys()):
                    if _cond(table[doc_id]):
                        # Add document ID to list of removed document IDs
                        removed_ids.append(doc_id)

                        # Remove document from the table
                        table.pop(doc_id)

            # Perform the remove operation
            self._update_table(updater)

            return removed_ids

        if doc_ids is not None:
            # This function returns the list of IDs for the documents that have
            # been removed. When removing documents identified by a set of
            # document IDs, it's this list of document IDs we need to return
            # later.
            # We convert the document ID iterator into a list so we can both
            # use the document IDs to remove the specified documents as well as
            # to return the list of affected document IDs
            removed_ids = list(doc_ids)

            def updater(table: dict):
                for doc_id in removed_ids:
                    table.pop(doc_id)

            # Perform the remove operation
            self._update_table(updater)

            return removed_ids

        raise RuntimeError('Use truncate() to remove all documents')

    def truncate(self) -> None:
        """
        Truncate the table by removing all documents.
        """

        # Update the table by resetting all data
        self._update_table(lambda table: table.clear())

        # Reset document ID counter
        self._next_id = None

    def count(self, cond: QueryLike) -> int:
        """
        Count the documents matching a query.

        :param cond: the condition use
        """

        return len(self.search(cond))

    def clear_cache(self) -> None:
        """
        Clear the query cache.
        """

        self._query_cache.clear()

    def __len__(self):
        """
        Count the total number of documents in this table.
        """

        # Using self._read_table() will convert all documents into
        # the document class. But for counting the number of documents
        # this conversion is not necessary, thus we read the storage
        # directly here

        tables = self._storage.read()

        if tables is None:
            return 0

        try:
            return len(tables[self.name])
        except KeyError:
            return 0

    def __iter__(self) -> Iterator[Document]:
        """
        Iterate over all documents stored in the table.

        :returns: an iterator over all documents.
        """

        # Iterate all documents and their IDs
        for doc_id, doc in self._read_table().items():
            # Convert documents to the document class
            yield self.document_class(doc, doc_id)

    def _get_next_id(self):
        """
        Return the ID for a newly inserted document.
        """

        # If we already know the next ID
        if self._next_id is not None:
            next_id = self._next_id
            self._next_id = next_id + 1

            return next_id

        # Determine the next document ID by finding out the max ID value
        # of the current table documents

        # Read the table documents
        table = self._read_table()

        # If the table is empty, set the initial ID
        if not table:
            next_id = 1
            self._next_id = next_id + 1

            return next_id

        # Determine the next ID based on the maximum ID that's currently in use
        max_id = max(self.document_id_class(i) for i in table.keys())
        next_id = max_id + 1

        # The next ID we wil return AFTER this call needs to be larger than
        # the current next ID we calculated
        self._next_id = next_id + 1

        return next_id

    def _read_table(self) -> Dict[int, Mapping]:
        """
        Read the table data from the underlying storage.

        Here we read the data from the underlying storage and convert all
        IDs to the document ID class. Documents themselves are NOT yet
        transformed into the document class, we may not want to convert
        *all* documents when returning only one document for example.
        """

        # Retrieve the tables from the storage
        tables = self._storage.read()

        if tables is None:
            # The database is empty
            return {}

        # Retrieve the current table's data
        try:
            table = tables[self.name]
        except KeyError:
            # The table does not exist yet, so it is empty
            return {}

        # Convert all document IDs to the correct document ID class and return
        # the table data dict
        return {
            self.document_id_class(doc_id): doc
            for doc_id, doc in table.items()
        }

    def _update_table(self, updater: Callable[[Dict[int, Mapping]], None]):
        """
        Perform an table update operation.

        The storage interface used by TinyDB only allows to read/write the
        complete database data, but not modifying only portions of it. Thus
        to only update portions of the table data, we first perform a read
        operation, perform the update on the table data and then write
        the updated data back to the storage.

        As a further optimization, we don't convert the documents into the
        document class, as the table data will *not* be returned to the user.
        """

        tables = self._storage.read()

        if tables is None:
            # The database is empty
            tables = {}

        try:
            raw_table = tables[self.name]
        except KeyError:
            # The table does not exist yet, so it is empty
            raw_table = {}

        # Convert the document IDs to the document ID class.
        # This is required as the rest of TinyDB expects the document IDs
        # to be an instance of ``self.document_id_class`` but the storage
        # might convert dict keys to strings.
        table = {
            self.document_id_class(doc_id): doc
            for doc_id, doc in raw_table.items()
        }

        # Perform the table update operation
        updater(table)

        # Convert the document IDs back to strings.
        # This is required as some storages (most notably the JSON file format)
        # don't support IDs other than strings.
        tables[self.name] = {
            str(doc_id): doc
            for doc_id, doc in table.items()
        }

        # Write the newly updated data back to the storage
        self._storage.write(tables)

        # Clear the query cache, as the table contents have changed
        self.clear_cache()
