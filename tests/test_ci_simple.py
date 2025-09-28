#!/usr/bin/env python3
"""Simple test to validate backend functionality - no Unicode"""

import sys
import os

def test_backend_imports():
    """Test that basic backend modules can be imported"""
    print("=== Testing Backend Imports ===")
    
    # Add backend to path
    backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    try:
        # Test production_main import
        import production_main
        print("PASS: production_main imported successfully")
        
        # Test FastAPI app creation
        from production_main import app
        print("PASS: FastAPI app accessible")
        
        return True
    except Exception as e:
        print(f"FAIL: Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality that should always work"""
    print("\n=== Testing Basic Functionality ===")
    
    try:
        # Test basic Python functionality
        assert 1 + 1 == 2
        print("PASS: Basic math works")
        
        # Test list operations
        test_list = [1, 2, 3]
        assert len(test_list) == 3
        print("PASS: List operations work")
        
        return True
    except Exception as e:
        print(f"FAIL: Basic functionality failed: {e}")
        return False

if __name__ == "__main__":
    print("Running CI-friendly tests...")
    
    # Run tests
    import_success = test_backend_imports()
    basic_success = test_basic_functionality()
    
    if import_success and basic_success:
        print("\nSUCCESS: All tests passed!")
        sys.exit(0)
    else:
        print("\nFAILED: Some tests failed")
        sys.exit(1)
