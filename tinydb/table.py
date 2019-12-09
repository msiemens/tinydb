from typing import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Union,
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

    def __init__(self, storage: Storage, name: str, cache_size: int = 10):
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

        self._last_id = self.get_last_id()

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
        self._update(lambda table: table.update({doc_id: dict(document)}))

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

        self._update(updater)

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
            table = self._read()
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
            doc_ids: Optional[Iterable[int]] = None,
    ) -> bool:
        """
        Check whether the database contains a document matching a condition or
        an ID.

        If ``doc_ids`` is set, it checks if the db contains a document with
        one of the specified IDs.

        :param cond: the condition use
        :param doc_ids: the document IDs to look for
        """
        if doc_ids is not None:
            # Documents specified by ID
            return any(self.get(doc_id=doc_id) for doc_id in doc_ids)

        # Document specified by condition
        return self.get(cond) is not None

    def update(
            self,
            fields: Union[Mapping, Callable[[Mapping], None]],
            cond: Optional[Query] = None,
            doc_ids: Optional[int] = None,
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
            return self._process_docs(
                lambda data, doc_id: fields(data[doc_id]),
                cond, doc_ids
            )
        else:
            return self._process_docs(
                lambda data, doc_id: data[doc_id].update(fields),
                cond, doc_ids
            )

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
            doc_ids: Optional[int] = None,
    ) -> List[int]:
        """
        Remove all matching documents.

        :param cond: the condition to check against
        :param doc_ids: a list of document IDs
        :returns: a list containing the removed document's ID
        """
        if cond is None and doc_ids is None:
            raise RuntimeError('Use truncate() to remove all documents')

        return self._process_docs(
            lambda data, doc_id: data.pop(doc_id),
            cond, doc_ids
        )

    def truncate(self) -> None:
        """
        Truncate the table by removing all documents.
        """

        self._update(lambda table: table.clear())
        self._last_id = 0

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
        return len(self._read())

    def __iter__(self) -> Iterator[Document]:
        """
        Iter over all documents stored in the table.

        :returns: an iterator over all documents.
        """

        for doc_id, doc in self._read().items():
            yield self.document_class(doc, doc_id)

    def get_last_id(self) -> int:
        data = self._read()

        if not data:
            return 0

        return max(self.document_id_class(i) for i in data)

    def get_next_id(self):
        """
        Increment the ID used the last time and return it
        """

        current_id = self._last_id + 1
        self._last_id = current_id

        return current_id

    def _process_docs(self, func, cond=None, doc_ids=None):
        """
        Helper function for processing all documents specified by condition
        or IDs.

        A repeating pattern in TinyDB is to run some code on all documents
        that match a condition or are specified by their ID. This is
        implemented in this function.
        The function passed as ``func`` has to be a callable. Its first
        argument will be the data currently in the database. Its second
        argument is the document ID of the currently processed document.

        See: :meth:`~.update`, :meth:`.remove`

        :param func: the function to execute on every included document.
                     first argument: all data
                     second argument: the current document ID
        :param cond: query that matches documents to use, or
        :param doc_ids: list of document IDs to use
        :returns: the document IDs that were affected during processing
        """

        if doc_ids is not None:
            # Processed document specified by id
            def updater(table: dict):
                for doc_id in doc_ids:
                    func(table, doc_id)

        elif cond is not None:
            # Collect affected doc_ids
            doc_ids = []

            def updater(table: dict):
                # Processed documents specified by condition
                for doc_id in list(table):
                    if cond(table[doc_id]):
                        func(table, doc_id)
                        doc_ids.append(doc_id)

        else:
            doc_ids = []

            # Processed documents
            def updater(table: dict):
                for doc_id in table:
                    doc_ids.append(doc_id)
                    func(table, doc_id)

        self._update(updater)

        return doc_ids

    def _read(self) -> Dict[int, Mapping]:
        data = self.storage.read() or {}

        try:
            return {
                self.document_id_class(doc_id): doc
                for doc_id, doc in data[self.name].items()
            }
        except KeyError:
            return {}

    def _update(self, updater: Callable[[Dict[int, Mapping]], None]):
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
