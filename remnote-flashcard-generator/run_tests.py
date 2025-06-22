#!/usr/bin/env python3
"""
Test runner script for RemNote Flashcard Generator.

This script runs the test suite and provides easy testing commands.
"""

import sys
import subprocess
import importlib.util

def run_tests(test_type="all", verbose=False):
    """Run tests with specified parameters."""
    
    # Check if pytest is available
    if importlib.util.find_spec("pytest") is None:
        print("❌ pytest not found. Installing test dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ])
        
    # Prepare pytest arguments
    args = ["python", "-m", "pytest"]
    
    if verbose:
        args.append("-v")
        
    if test_type == "unit":
        args.extend(["-m", "unit"])
    elif test_type == "integration":
        args.extend(["-m", "integration"])
    elif test_type == "coverage":
        args.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
        
    args.append("tests/")
    
    print(f"🧪 Running tests: {' '.join(args)}")
    return subprocess.call(args)

def main():
    """Main test runner entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RemNote Flashcard Generator tests")
    parser.add_argument("--type", choices=["all", "unit", "integration", "coverage"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    print("🚀 RemNote Flashcard Generator Test Runner")
    print("=" * 50)
    
    result = run_tests(args.type, args.verbose)
    
    if result == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        
    return result

if __name__ == "__main__":
    sys.exit(main())
