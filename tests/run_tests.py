#!/usr/bin/env python3
"""
Test Runner for MLOps Assignment - CI/CD Tests

This script discovers and runs tests organized by CI/CD pipeline stage:
- ci/: Tests that run in CI pipeline (builds, manifests)
- config/: Tests for configuration validation (dataset config)
- deploy/: Tests that run after deployment (require kubectl/service access)

Usage:
    python3 run_tests.py              # Run all tests
    python3 run_tests.py -v           # Verbose output
    python3 run_tests.py --ci-only    # Only CI and config tests
    python3 run_tests.py --local      # Only local tests (no CI env needed)
"""

import unittest
import sys
import os


def run_tests(test_dirs, verbosity=1):
    """
    Discover and run tests in specified directories.
    
    Args:
        test_dirs: List of directories to search for tests
        verbosity: Test output verbosity (1=normal, 2=verbose)
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Get the tests directory path
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Discover tests in each directory
    for test_dir in test_dirs:
        test_path = os.path.join(tests_dir, test_dir)
        if os.path.exists(test_path):
            discovered = loader.discover(test_path, pattern='test_*.py', top_level_dir=tests_dir)
            suite.addTests(discovered)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    if result.wasSuccessful():
        print(" All tests passed!")
    else:
        print(" Some tests failed or were skipped")
        if result.failures:
            print(f"Failures: {len(result.failures)}")
        if result.errors:
            print(f"Errors: {len(result.errors)}")
        if result.skipped:
            print(f"Skipped: {len(result.skipped)}")
    
    print(f"\nTests run: {result.testsRun}")
    print("="*70)
    
    # Print PVC protection reminder
    print("\n  PVC PROTECTION REMINDER")
    print("   Production PVC: /home/caiogrossi/project2-pv/")
    print("    All tests use READ-ONLY operations")
    print("    NO POST /train calls")
    print("    NO kubectl exec commands")
    print("    NO PVC mounts in test containers\n")
    
    return 0 if result.wasSuccessful() else 1


def main():
    """Main entry point"""
    # Change to tests directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Parse arguments
    verbosity = 2 if '-v' in sys.argv or '--verbose' in sys.argv else 1
    ci_only = '--ci-only' in sys.argv
    local_only = '--local' in sys.argv
    
    # Determine which test directories to run
    if ci_only:
        # Run only CI and config tests (no deployment tests)
        test_dirs = ['ci', 'config']
        print("Running CI pipeline tests only (ci/, config/)")
    elif local_only:
        # Run only tests that work locally (no CI environment needed)
        test_dirs = ['config']
        print("Running local tests only (config/)")
    else:
        # Run all tests
        test_dirs = ['ci', 'config', 'deploy']
        print("Running all CI/CD tests (ci/, config/, deploy/)")
    
    print("="*70 + "\n")
    
    # Run tests
    exit_code = run_tests(test_dirs, verbosity)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
