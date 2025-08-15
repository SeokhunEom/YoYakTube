#!/usr/bin/env python3
"""Test runner for YoYakTube CLI tools"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def discover_and_run_tests():
    """Discover and run all tests"""
    
    # Set up test discovery
    test_dir = Path(__file__).parent
    loader = unittest.TestLoader()
    
    # Discover all test files
    suite = loader.discover(
        start_dir=str(test_dir),
        pattern='test_*.py',
        top_level_dir=str(test_dir.parent)
    )
    
    # Configure test runner
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=True  # Capture stdout/stderr during tests
    )
    
    # Run tests
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


def run_specific_test(test_module):
    """Run a specific test module"""
    try:
        # Import and run specific test
        module = __import__(f'tests.{test_module}', fromlist=[test_module])
        suite = unittest.TestLoader().loadTestsFromModule(module)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1
    except ImportError as e:
        print(f"Error: Could not import test module '{test_module}': {e}")
        return 1


def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run YoYakTube CLI tests')
    parser.add_argument(
        'test_module', 
        nargs='?', 
        help='Specific test module to run (e.g., test_yyt_transcript)'
    )
    parser.add_argument(
        '--list', 
        action='store_true', 
        help='List available test modules'
    )
    
    args = parser.parse_args()
    
    if args.list:
        # List available test modules
        test_dir = Path(__file__).parent
        test_files = list(test_dir.glob('test_*.py'))
        print("Available test modules:")
        for test_file in sorted(test_files):
            module_name = test_file.stem
            print(f"  - {module_name}")
        return 0
    
    if args.test_module:
        # Run specific test module
        return run_specific_test(args.test_module)
    else:
        # Run all tests
        return discover_and_run_tests()


if __name__ == '__main__':
    sys.exit(main())