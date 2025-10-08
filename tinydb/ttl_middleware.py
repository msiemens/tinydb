"""
TinyDB TTL (Time-To-Live) Middleware
Automatically handles document expiration based on TTL values.
"""

import time
from typing import Dict, Any, Optional
from tinydb.middlewares import Middleware


class TTLMiddleware(Middleware):
    """
    Middleware that provides TTL (Time-To-Live) functionality for TinyDB documents.
    
    Usage:
        from tinydb import TinyDB
        from tinydb.storages import JSONStorage
        
        db = TinyDB('db.json', storage=TTLMiddleware(JSONStorage))
        
        # Insert with TTL (in seconds)
        db.insert({'name': 'temp_data', '_ttl': 3600})  # Expires in 1 hour
        
        # Or set explicit expiration timestamp
        db.insert({'name': 'cache', '_expires_at': time.time() + 3600})
        
        # Manually purge expired documents
        db.storage.purge_expired()
    """
    
    def __init__(self, storage_cls=None, auto_purge_interval: Optional[int] = None):
        """
        Initialize TTL Middleware.
        
        Args:
            storage_cls: The storage class to wrap
            auto_purge_interval: If set, automatically purge expired docs every N seconds
        """
        super().__init__(storage_cls)
        self._auto_purge_interval = auto_purge_interval
        self._last_purge = time.time()
    
    def read(self) -> Dict[str, Dict[int, Dict[str, Any]]]:
        """
        Read data from storage, filtering out expired documents.
        
        Returns:
            Dictionary of tables with non-expired documents only
        """
        data = self.storage.read()
        current_time = time.time()
        
        # Handle None or empty data
        if data is None:
            return {}
        
        # Check if we should auto-purge
        if self._auto_purge_interval:
            if current_time - self._last_purge >= self._auto_purge_interval:
                self._purge_expired_from_storage()
                self._last_purge = current_time
                data = self.storage.read()  # Re-read after purge
                if data is None:
                    return {}
        
        # Filter expired documents from all tables
        filtered_data = {}
        for table_name, documents in data.items():
            if documents is None:
                filtered_data[table_name] = {}
            else:
                filtered_data[table_name] = {
                    doc_id: doc
                    for doc_id, doc in documents.items()
                    if not self._is_expired(doc, current_time)
                }
        
        return filtered_data
    
    def write(self, data: Dict[str, Dict[int, Dict[str, Any]]]) -> None:
        """
        Write data to storage, converting TTL values to expiration timestamps.
        
        Args:
            data: Dictionary of tables with documents to write
        """
        current_time = time.time()
        
        # Handle None data
        if data is None:
            self.storage.write(None)
            return
        
        # Process TTL fields before writing
        processed_data = {}
        for table_name, documents in data.items():
            if documents is None:
                processed_data[table_name] = None
                continue
                
            processed_data[table_name] = {}
            for doc_id, doc in documents.items():
                # Make a copy to avoid modifying the original
                processed_doc = dict(doc)
                
                # Convert _ttl to _expires_at if present
                if '_ttl' in processed_doc:
                    ttl_seconds = processed_doc.pop('_ttl')
                    if ttl_seconds is not None and ttl_seconds > 0:
                        # Set expiration time
                        processed_doc['_expires_at'] = current_time + ttl_seconds
                
                processed_data[table_name][doc_id] = processed_doc
        
        self.storage.write(processed_data)
    
    def _is_expired(self, doc: Dict[str, Any], current_time: float) -> bool:
        """
        Check if a document has expired.
        
        Args:
            doc: Document to check
            current_time: Current timestamp
            
        Returns:
            True if document is expired, False otherwise
        """
        if '_expires_at' not in doc:
            return False
        
        expires_at = doc.get('_expires_at')
        if expires_at is None:
            return False
        
        try:
            return float(expires_at) < current_time
        except (ValueError, TypeError):
            # Invalid expiration value, treat as not expired
            return False
    
    def purge_expired(self) -> int:
        """
        Manually purge all expired documents from storage.
        
        Returns:
            Number of documents purged
        """
        return self._purge_expired_from_storage()
    
    def _purge_expired_from_storage(self) -> int:
        """
        Remove expired documents from the underlying storage.
        
        Returns:
            Number of documents purged
        """
        data = self.storage.read()
        current_time = time.time()
        purged_count = 0
        
        # Handle None or empty data
        if data is None:
            return 0
        
        # Remove expired documents from all tables
        for table_name, documents in data.items():
            if documents is None:
                continue
                
            expired_ids = [
                doc_id
                for doc_id, doc in documents.items()
                if self._is_expired(doc, current_time)
            ]
            
            for doc_id in expired_ids:
                del documents[doc_id]
                purged_count += 1
        
        # Write cleaned data back to storage
        if purged_count > 0:
            self.storage.write(data)
        
        return purged_count


# Example usage and tests
if __name__ == "__main__":
    from tinydb import TinyDB
    from tinydb.storages import MemoryStorage
    
    print("Testing TTL Middleware...\n")
    
    # Example 1: Basic TTL usage
    print("Example 1: Basic TTL")
    db = TinyDB(storage=TTLMiddleware(MemoryStorage))
    
    # Insert document with 2-second TTL
    db.insert({'name': 'expires_soon', 'data': 'temporary', '_ttl': 2})
    db.insert({'name': 'permanent', 'data': 'stays forever'})
    
    print(f"Initial documents: {db.all()}")
    print(f"Count: {len(db.all())}")
    
    time.sleep(3)
    print(f"\nAfter 3 seconds: {db.all()}")
    print(f"Count: {len(db.all())}")
    
    # Example 2: Verify _ttl was converted to _expires_at
    print("\n\nExample 2: Checking _expires_at conversion")
    db2 = TinyDB(storage=TTLMiddleware(MemoryStorage))
    db2.insert({'name': 'test', '_ttl': 10})
    
    # Read directly from storage to see the actual data
    raw_data = db2.storage.storage.read()
    print(f"Raw storage data: {raw_data}")
    
    # Example 3: Manual purge
    print("\n\nExample 3: Manual purge")
    db3 = TinyDB(storage=TTLMiddleware(MemoryStorage))
    
    db3.insert({'name': 'temp1', '_ttl': 1})
    db3.insert({'name': 'temp2', '_ttl': 1})
    db3.insert({'name': 'permanent'})
    
    print(f"Before expiration: {len(db3.all())} documents")
    time.sleep(2)
    
    print(f"After expiration (filtered): {len(db3.all())} documents")
    
    purged = db3.storage.purge_expired()
    print(f"Purged {purged} expired documents")
    print(f"After purge: {len(db3.all())} documents")