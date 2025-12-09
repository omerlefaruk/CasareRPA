"""
Pytest configuration for coordinator tests.

Disables pytest-qt plugin to avoid Qt initialization issues.
All Qt dependencies are mocked in the test files.
"""

import pytest


# Disable pytest-qt for this directory
def pytest_configure(config):
    """Configure pytest to skip Qt processing for coordinator tests."""
    config.addinivalue_line(
        "markers",
        "qt_no_exception_capture: mark test to skip Qt exception capture",
    )
