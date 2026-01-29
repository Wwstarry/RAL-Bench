#!/usr/bin/env python3
"""
Test runner script with additional validation and reporting.
"""
import subprocess
import sys
from test_requests_core import main as run_core_tests


def run_validation():
    """Run additional validation checks."""
    print("Running additional validation...")
    
    # Check imports work correctly
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        from requests.exceptions import RequestException, Timeout
        
        print("✓ All imports successful")
        print(f"✓ Requests version: {requests.__version__}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
        
    return True


def main():
    """Main test runner with enhanced reporting."""
    print("🚀 Starting Requests Core API Test Suite")
    print("=" * 60)
    
    # Run validation first
    if not run_validation():
        print("❌ Validation failed")
        sys.exit(1)
    
    # Run core tests
    try:
        run_core_tests()
        print("\n🎉 All tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())