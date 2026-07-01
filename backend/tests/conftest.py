"""Test configuration — runs before any test file is imported."""
import os

# Enable debug mode so auth middleware bypasses authentication during tests
os.environ["DEBUG"] = "true"
