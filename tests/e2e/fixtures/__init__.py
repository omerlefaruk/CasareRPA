"""
CasareRPA - E2E Test Fixtures.

Static test assets for E2E testing:
- test_pages/form.html: HTML form for browser interaction tests
- test_pages/table.html: HTML table for scraping tests

These files are served by the pytest-aiohttp test_server fixture.
"""

from pathlib import Path

# Path to test pages directory
TEST_PAGES_DIR = Path(__file__).parent / "test_pages"


def get_test_page_path(filename: str) -> Path:
    """
    Get the absolute path to a test page file.

    Args:
        filename: Name of the file (e.g., "form.html")

    Returns:
        Absolute path to the file

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    path = TEST_PAGES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Test page not found: {path}")
    return path


__all__ = [
    "TEST_PAGES_DIR",
    "get_test_page_path",
]
