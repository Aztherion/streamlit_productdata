import unittest
import os

def run_all_tests():
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=".", pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed.")
        exit(1)

if __name__ == "__main__":
    run_all_tests()
