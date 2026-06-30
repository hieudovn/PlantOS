"""Run pytest and print summary."""
import sys
sys.path.insert(0, ".")

import pytest

exit_code = pytest.main([
    "tests/test_asset_api.py",
    "-v",
    "--tb=short",
])
