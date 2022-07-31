"""
Contains the :class:`base class <tinydb.storages.Storage>` for storages and
implementations.
"""

import io
import json
import os
import tempfile
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

__all__ = ('Storage', 'JSONStorage', 'MemoryStorage')


def touch(path: str, create_dirs: bool):
    """
    Create a file if it doesn't exist yet.

    :param path: The file to create.
    :param create_dirs: Whether to create all missing parent directories.
    """
    if create_dirs:
        base_dir = os.path.dirname(path)

        # Check if we need to create missing parent directories
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

    # Create the file by opening it in 'a' mode which creates the file if it
    # does not exist yet but does not modify its contents
    with open(path, 'a'):
        pass


class Storage(ABC):
    """
    The abstract base class for all Storages.

    A Storage (de)serializes the current state of the database and stores it in
    some place (memory, file on disk, ...).
    """

    # Using ABCMeta as metaclass allows instantiating only storages that have
    # implemented read and write

    @abstractmethod
    def read(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Read the current state.

        Any kind of deserialization should go here.

        Return ``None`` here to indicate that the storage is empty.
        """

        raise NotImplementedError('To be overridden!')

    @abstractmethod
    def write(self, data: Dict[str, Dict[str, Any]]) -> None:
        """
        Write the current state of the database to the storage.

        Any kind of serialization should go here.

        :param data: The current state of the database.
        """

        raise NotImplementedError('To be overridden!')

    def close(self) -> None:
        """
        Optional: Close open file handles, etc.
        """

        pass


class JSONStorage(Storage):
    """
    Store the data in a JSON file.
    """

    def __init__(self, path: str, create_dirs=False, encoding=None, access_mode='r+', **kwargs):
        """
        Create a new instance.

        Also creates the storage file, if it doesn't exist and the access mode is appropriate for writing.

        :param path: Where to store the JSON data.
        :param access_mode: mode in which the file is opened (r, r+, w, a, x, b, t, +, U)
        :type access_mode: str
        """

        super().__init__()

        self._mode = access_mode
        self.kwargs = kwargs

        # Create the file if it doesn't exist and creating is allowed by the
        # access mode
        if any([character in self._mode for character in ('+', 'w', 'a')]):  # any of the writing modes
            touch(path, create_dirs=create_dirs)

        # Open the file for reading/writing
        self._handle = open(path, mode=self._mode, encoding=encoding)

    def close(self) -> None:
        self._handle.close()

    def read(self) -> Optional[Dict[str, Dict[str, Any]]]:
        # Get the file size by moving the cursor to the file end and reading
        # its location
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()

        if not size:
            # File is empty, so we return ``None`` so TinyDB can properly
            # initialize the database
            return None
        else:
            # Return the cursor to the beginning of the file
            self._handle.seek(0)

            # Load the JSON contents of the file
            return json.load(self._handle)

    def write(self, data: Dict[str, Dict[str, Any]]):
        if self._handle.closed:
            # imitate what would be raised by calling `write()` on a closed file
            raise ValueError("I/O operation on a closed file.")

        file_name = self._handle.name

        # Create a temporary file in the same folder
        temp_file = tempfile.NamedTemporaryFile(mode=self._mode, prefix=file_name, delete=False)

        # Serialize the database state using the user-provided arguments
        serialized = json.dumps(data, **self.kwargs)

        # Write the serialized data to the file
        try:
            temp_file.write(serialized)
        except io.UnsupportedOperation:
            raise IOError('Cannot write to the database. Access mode is "{0}"'.format(self._mode))

        # Ensure the file has been written
        temp_file.flush()
        os.fsync(temp_file.fileno())

        # Replace the current file with the temporary file
        temp_file.close()
        self._handle.close()
        os.replace(temp_file.name, file_name)

        # Reopen the file
        self._handle = open(file_name, mode=self._mode, encoding=self._handle.encoding)


class MemoryStorage(Storage):
    """
    Store the data as JSON in memory.
    """

    def __init__(self):
        """
        Create a new instance.
        """

        super().__init__()
        self.memory = None

    def read(self) -> Optional[Dict[str, Dict[str, Any]]]:
        return self.memory

    def write(self, data: Dict[str, Dict[str, Any]]):
        self.memory = data
