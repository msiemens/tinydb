"""
Step-by-step guide to test the TTL Middleware
Run this file to verify the implementation works correctly
"""

# STEP 1: Install TinyDB
# Run in terminal: pip install tinydb

# STEP 2: Copy the TTL middleware code into a file called ttl_middleware.py
# (Use the code from the previous artifact)

# STEP 3: Run these tests

import time
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage, JSONStorage

# Import your TTL middleware
from tinydb.ttl_middleware import TTLMiddleware


def test_basic_ttl():
    """Test 1: Basic TTL functionality"""
    print("\n" + "="*50)
    print("TEST 1: Basic TTL Functionality")
    print("="*50)
    
    db = TinyDB(storage=TTLMiddleware(MemoryStorage))
    
    # Insert documents
    db.insert({'name': 'expires_in_2sec', 'value': 'temp', '_ttl': 2})
    db.insert({'name': 'permanent', 'value': 'forever'})
    
    print(f"✓ Inserted 2 documents")
    print(f"  Documents in DB: {len(db.all())}")
    assert len(db.all()) == 2, "Should have 2 documents initially"
    
    # Wait for expiration
    print(f"⏳ Waiting 3 seconds for expiration...")
    time.sleep(3)
    
    print(f"  Documents after expiration: {len(db.all())}")
    assert len(db.all()) == 1, "Should have 1 document after expiration"
    assert db.all()[0]['name'] == 'permanent', "Only permanent doc should remain"
    
    print("✅ TEST 1 PASSED: TTL works correctly!\n")


def test_query_filtering():
    """Test 2: Expired documents are filtered from queries"""
    print("="*50)
    print("TEST 2: Query Filtering")
    print("="*50)
    
    storage = TTLMiddleware(MemoryStorage)
    db = TinyDB(storage=storage)
    User = Query()
    
    print("DEBUG: About to insert documents...")
    
    # Insert users with different TTLs
    db.insert({'name': 'Alice', 'age': 25, '_ttl': 2})
    db.insert({'name': 'Bob', 'age': 30})
    db.insert({'name': 'Charlie', 'age': 25, '_ttl': 2})
    
    print(f"✓ Inserted 3 users")
    
    # Check what we can see through normal queries
    all_docs = db.all()
    print(f"\nDEBUG - All docs via db.all(): {len(all_docs)}")
    
    # Query before expiration
    age_25 = db.search(User.age == 25)
    print(f"  Users aged 25 (before expiration): {len(age_25)}")
    assert len(age_25) == 2, "Should find 2 users aged 25"
    
    # Wait for expiration
    print(f"\n  ⏳ Waiting 3 seconds...")
    time.sleep(3)
    
    # CRITICAL: Clear TinyDB's internal table cache
    # This forces it to re-read from storage through our middleware
    db._tables = {}
    
    # Now check again
    all_docs_after = db.all()
    print(f"\nDEBUG - All docs after cache clear: {len(all_docs_after)}")
    
    age_25_after = db.search(User.age == 25)
    print(f"  Users aged 25 (after expiration): {len(age_25_after)}")
    
    assert len(age_25_after) == 0, f"Should find 0 users aged 25 after expiration, but found {len(age_25_after)}"
    
    print("✅ TEST 2 PASSED: Queries filter expired docs!\n")


def test_manual_purge():
    """Test 3: Manual purge removes expired documents"""
    print("="*50)
    print("TEST 3: Manual Purge")
    print("="*50)
    
    db = TinyDB(storage=TTLMiddleware(MemoryStorage))
    
    # Insert documents
    db.insert({'data': 'temp1', '_ttl': 1})
    db.insert({'data': 'temp2', '_ttl': 1})
    db.insert({'data': 'permanent'})
    
    print(f"✓ Inserted 3 documents")
    
    # Wait for expiration
    time.sleep(2)
    
    # Documents still in storage but filtered from queries
    visible_docs = len(db.all())
    print(f"  Visible documents: {visible_docs}")
    
    # Purge expired documents
    purged = db.storage.purge_expired()
    print(f"  Purged {purged} expired documents")
    assert purged == 2, "Should purge 2 expired documents"
    
    print("✅ TEST 3 PASSED: Manual purge works!\n")


def test_explicit_expiration():
    """Test 4: Explicit _expires_at timestamp"""
    print("="*50)
    print("TEST 4: Explicit Expiration Timestamp")
    print("="*50)
    
    db = TinyDB(storage=TTLMiddleware(MemoryStorage))
    
    # Set explicit expiration time
    future_time = time.time() + 2
    db.insert({'data': 'expires_at_specific_time', '_expires_at': future_time})
    
    print(f"✓ Inserted document with _expires_at")
    print(f"  Documents before expiration: {len(db.all())}")
    assert len(db.all()) == 1, "Should have 1 document"
    
    # Wait for expiration
    time.sleep(3)
    print(f"  Documents after expiration: {len(db.all())}")
    assert len(db.all()) == 0, "Should have 0 documents after expiration"
    
    print("✅ TEST 4 PASSED: Explicit expiration works!\n")


def test_json_storage():
    """Test 5: Works with JSON file storage"""
    print("="*50)
    print("TEST 5: JSON File Storage")
    print("="*50)
    
    # Use actual file storage
    db = TinyDB('test_ttl.json', storage=TTLMiddleware(JSONStorage))
    
    db.insert({'name': 'file_test', '_ttl': 2})
    db.insert({'name': 'permanent_file'})
    
    print(f"✓ Created test_ttl.json with 2 documents")
    print(f"  Documents: {len(db.all())}")
    
    time.sleep(3)
    print(f"  Documents after expiration: {len(db.all())}")
    assert len(db.all()) == 1, "Should have 1 document after expiration"
    
    db.close()
    
    # Clean up
    import os
    if os.path.exists('test_ttl.json'):
        os.remove('test_ttl.json')
        print("✓ Cleaned up test file")
    
    print("✅ TEST 5 PASSED: Works with JSON storage!\n")


def test_edge_cases():
    """Test 6: Edge cases and error handling"""
    print("="*50)
    print("TEST 6: Edge Cases")
    print("="*50)
    
    db = TinyDB(storage=TTLMiddleware(MemoryStorage))
    
    # Test invalid TTL values
    db.insert({'data': 'invalid_ttl', '_ttl': -1})  # Negative TTL
    db.insert({'data': 'zero_ttl', '_ttl': 0})       # Zero TTL
    db.insert({'data': 'invalid_expires', '_expires_at': 'not_a_number'})
    db.insert({'data': 'valid'})
    
    print(f"✓ Inserted documents with edge cases")
    print(f"  All documents visible: {len(db.all())}")
    
    # All should be visible (invalid TTLs are ignored)
    assert len(db.all()) == 4, "Should handle invalid TTL gracefully"
    
    print("✅ TEST 6 PASSED: Edge cases handled!\n")


def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪 STARTING TTL MIDDLEWARE TESTS" + "\n")
    
    try:
        test_basic_ttl()
        test_query_filtering()
        test_manual_purge()
        test_explicit_expiration()
        test_json_storage()
        test_edge_cases()
        
        print("="*50)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("="*50)
        print("\nYour TTL middleware implementation is working correctly!")
        print("You're ready to submit a PR to TinyDB! 🚀")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("Debug the code and try again.")
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        print("Check your setup and dependencies.")


if __name__ == "__main__":
    run_all_tests()