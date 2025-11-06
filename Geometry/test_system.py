"""
Test script for the Geometry Learning API Server

This script tests the basic functionality of the API without requiring Flask to be installed.
It verifies that the core modules can be imported and basic operations work.
"""

import sys
import os

def test_imports():
    """Test that all core modules can be imported."""
    print("Testing module imports...")
    
    try:
        from geometry_manager import GeometryManager
        print("✓ geometry_manager imported successfully")
    except Exception as e:
        print(f"✗ Failed to import geometry_manager: {e}")
        return False
    
    try:
        from session import Session
        print("✓ session imported successfully")
    except Exception as e:
        print(f"✗ Failed to import session: {e}")
        return False
    
    try:
        from session_db import SessionDB
        print("✓ session_db imported successfully")
    except Exception as e:
        print(f"✗ Failed to import session_db: {e}")
        return False
    
    return True


def test_geometry_manager():
    """Test basic GeometryManager functionality."""
    print("\nTesting GeometryManager...")
    
    try:
        from geometry_manager import GeometryManager
        
        # Create manager
        gm = GeometryManager()
        print("✓ GeometryManager instantiated")
        
        # Check database connection
        if not os.path.exists(gm.db_path):
            print(f"✗ Database file not found: {gm.db_path}")
            return False
        print(f"✓ Database file exists: {gm.db_path}")
        
        # Test getting first question
        try:
            question = gm.get_first_question()
            if "error" in question:
                print(f"✗ Error getting first question: {question['error']}")
                return False
            print(f"✓ Got first question: {question.get('question_id')}")
        except Exception as e:
            print(f"✗ Failed to get first question: {e}")
            return False
        
        # Close connection
        gm.close()
        print("✓ GeometryManager closed successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ GeometryManager test failed: {e}")
        return False


def test_session():
    """Test Session class functionality."""
    print("\nTesting Session...")
    
    try:
        from session import Session
        
        # Create session
        sess = Session()
        print(f"✓ Session created with ID: {sess.session_id}")
        
        # Add interaction
        sess.add_interaction(1, 1)
        print("✓ Interaction added")
        
        # Set feedback
        sess.set_feedback(5)
        print("✓ Feedback set")
        
        # Convert to dict
        data = sess.to_dict()
        if not isinstance(data, dict):
            print("✗ to_dict() did not return a dictionary")
            return False
        print("✓ Session converted to dict")
        
        # Convert to JSON
        json_str = sess.to_json()
        if not isinstance(json_str, str):
            print("✗ to_json() did not return a string")
            return False
        print("✓ Session converted to JSON")
        
        return True
        
    except Exception as e:
        print(f"✗ Session test failed: {e}")
        return False


def test_session_db():
    """Test SessionDB functionality."""
    print("\nTesting SessionDB...")
    
    try:
        from session_db import SessionDB
        from session import Session
        
        # Create session DB
        session_db = SessionDB()
        print("✓ SessionDB instantiated")
        
        # Load sessions
        sessions = session_db.load_all_sessions()
        print(f"✓ Loaded {len(sessions)} sessions from database")
        
        return True
        
    except Exception as e:
        print(f"✗ SessionDB test failed: {e}")
        return False


def test_api_server_syntax():
    """Test that api_server.py has valid syntax."""
    print("\nTesting api_server.py syntax...")
    
    try:
        import py_compile
        py_compile.compile('api_server.py', doraise=True)
        print("✓ api_server.py syntax is valid")
        return True
    except Exception as e:
        print(f"✗ api_server.py syntax error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Geometry Learning System - Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("GeometryManager", test_geometry_manager()))
    results.append(("Session", test_session()))
    results.append(("SessionDB", test_session_db()))
    results.append(("API Server Syntax", test_api_server_syntax()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("\nTo start the API server, install dependencies and run:")
        print("  pip install -r requirements.txt")
        print("  python api_server.py")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
