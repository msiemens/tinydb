from typing import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Union,
    cast
)

from tinydb import Storage, Query
from tinydb.utils import LRUCache


class Document(dict):
    """
    Represents a document stored in the database.

    This is a transparent proxy for database records. It exists
    to provide a way to access a record's id via ``el.doc_id``.
    """

    def __init__(self, value: Mapping, doc_id: int):
        super().__init__(value)
        self.doc_id = doc_id


class Table:
    """
    Represents a single TinyDB Table.
    """

    document_class = Document
    document_id_class = int
    query_cache_class = LRUCache
    default_query_cache_capacity = 10

    def __init__(
        self,
        storage: Storage,
        name: str,
        cache_size: int = default_query_cache_capacity
    ):
        """
        Get access to a table.

        :param storage: Access to the storage
        :param name: The table name
        :param cache_size: Maximum size of query cache.
        """

        self._storage = storage
        self._name = name
        self._query_cache = self.query_cache_class(capacity=cache_size) \
            # type: LRUCache[Query, List[Document]]

        self._next_id = None

    def __repr__(self):
        args = [
            'name={!r}'.format(self.name),
            'total={}'.format(len(self)),
            'storage={}'.format(self.storage),
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
        Get the table storage.
        """
        return self._storage

    def insert(self, document: Mapping) -> int:
        """
        Insert a new document into the table.

        :param document: the document to insert
        :returns: the inserted document's ID
        """
        if not isinstance(document, Mapping):
            raise ValueError('Document is not a Mapping')

        doc_id = self.get_next_id()
        self._update_table(lambda table: table.update({doc_id: dict(document)}))

        return doc_id

    def insert_multiple(self, documents: Iterable[Mapping]) -> List[int]:
        """
        Insert multiple documents into the table.

        :param documents: a list of documents to insert
        :returns: a list containing the inserted documents' IDs
        """
        doc_ids = []

        def updater(table: dict):
            for document in documents:
                if not isinstance(document, Mapping):
                    raise ValueError('Document is not a Mapping')

                doc_id = self.get_next_id()
                doc_ids.append(doc_id)

                table[doc_id] = dict(document)

        self._update_table(updater)

        return doc_ids

    def all(self) -> List[Document]:
        """
        Get all documents stored in the table.

        :returns: a list with all documents.
        """

        return list(iter(self))

    def search(self, cond: Query) -> List[Document]:
        """
        Search for all documents matching a 'where' cond.

        :param cond: the condition to check against
        :returns: list of matching documents
        """

        if cond in self._query_cache:
            docs = self._query_cache.get(cond)
            if docs is None:
                return []

            return docs[:]

        docs = [doc for doc in self if cond(doc)]
        self._query_cache[cond] = docs[:]

        return docs

    def get(
            self,
            cond: Optional[Query] = None,
            doc_id: Optional[int] = None,
    ) -> Optional[Document]:
        """
        Get exactly one document specified by a query or and ID.

        Returns ``None`` if the document doesn't exist

        :param cond: the condition to check against
        :param doc_id: the document's ID

        :returns: the document or None
        """
        # Cannot use process_elements here because we want to return a
        # specific document

        if doc_id is not None:
            # Document specified by ID
            table = self._read_table()
            raw_doc = table.get(doc_id, None)
            if raw_doc is None:
                return None

            return self.document_class(raw_doc, doc_id)

        elif cond is not None:
            # Document specified by condition
            for doc in self:
                if cond(doc):
                    return doc

        else:
            raise RuntimeError('You have to pass either cond or doc_id')

        return None

    def contains(
            self,
            cond: Optional[Query] = None,
            doc_id: Optional[int] = None,
    ) -> bool:
        """
        Check whether the database contains a document matching a condition or
        an ID.

        If ``doc_ids`` is set, it checks if the db contains a document with
        one of the specified IDs.

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
        cond: Optional[Query] = None,
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
        if callable(fields):
            def perform_update(table, doc_id):
                fields(table[doc_id])
        else:
            def perform_update(table, doc_id):
                table[doc_id].update(fields)

        if doc_ids is not None:
            updated_ids = list(doc_ids)

            def updater(table: dict):
                for doc_id in updated_ids:
                    perform_update(table, doc_id)

            self._update_table(updater)

            return updated_ids

        elif cond is not None:
            updated_ids = []

            def updater(table: dict):
                _cond = cast('Query', cond)

                for doc_id in list(table.keys()):
                    if _cond(table[doc_id]):
                        perform_update(table, doc_id)
                        updated_ids.append(doc_id)

            self._update_table(updater)

            return updated_ids

        else:
            updated_ids = []

            def updater(table: dict):
                # Process all documents
                for doc_id in list(table.keys()):
                    updated_ids.append(doc_id)
                    perform_update(table, doc_id)

            self._update_table(updater)

            return updated_ids

    def upsert(self, document: Mapping, cond: Query) -> List[int]:
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

    def remove(
        self,
        cond: Optional[Query] = None,
        doc_ids: Optional[Iterable[int]] = None,
    ) -> List[int]:
        """
        Remove all matching documents.

        :param cond: the condition to check against
        :param doc_ids: a list of document IDs
        :returns: a list containing the removed documents' ID
        """
        if cond is None and doc_ids is None:
            raise RuntimeError('Use truncate() to remove all documents')

        if cond is not None:
            removed_ids = []

            def updater(table: dict):
                _cond = cast('Query', cond)

                for doc_id in list(table.keys()):
                    if _cond(table[doc_id]):
                        removed_ids.append(doc_id)
                        table.pop(doc_id)

            self._update_table(updater)

            return removed_ids

        if doc_ids is not None:
            removed_ids = list(doc_ids)

            def updater(table: dict):
                for doc_id in removed_ids:
                    table.pop(doc_id)

            self._update_table(updater)

            return removed_ids

        raise RuntimeError('This should never happen')

    def truncate(self) -> None:
        """
        Truncate the table by removing all documents.
        """

        self._update_table(lambda table: table.clear())
        self._next_id = None

    def count(self, cond: Query) -> int:
        """
        Count the documents matching a condition.

        :param cond: the condition use
        """

        return len(self.search(cond))

    def clear_cache(self) -> None:
        """
        Clear the query cache.

        A simple helper that clears the internal query cache.
        """
        self._query_cache.clear()

    def __len__(self):
        """
        Get the total number of documents in the table.
        """

        # Using self._read_table() will convert all documents into
        # the document class. But for counting the number of documents
        # this conversion is not necessary, thus we read the storage
        # directly here

        tables = self._storage.read()

        return len(tables[self.name])

    def __iter__(self) -> Iterator[Document]:
        """
        Iter over all documents stored in the table.

        :returns: an iterator over all documents.
        """

        for doc_id, doc in self._read_table().items():
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
            self._next_id = 1  # TODO: change to 0

            return self._next_id

        # Find the maximum ID that is currently in use
        max_id = max(self.document_id_class(i) for i in table.keys())

        self._next_id = max_id + 1

        return self._next_id

    def _read_table(self) -> Dict[int, Mapping]:
        data = self.storage.read() or {}

        try:
            return {
                self.document_id_class(doc_id): doc
                for doc_id, doc in data[self.name].items()
            }
        except KeyError:
            return {}

    def _update_table(self, updater: Callable[[Dict[int, Mapping]], None]):
        data = self.storage.read() or {}

        try:
            raw_table = data[self.name]
        except KeyError:
            raw_table = {}

        table = {
            self.document_id_class(doc_id): doc
            for doc_id, doc in raw_table.items()
        }

        updater(table)

        data[self.name] = {
            str(doc_id): doc
            for doc_id, doc in table.items()
        }

        self.storage.write(data)
        self.clear_cache()
