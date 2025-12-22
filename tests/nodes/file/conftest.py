"""
Fixtures for file node tests.

Provides:
- Mock execution context
- Temporary file fixtures
- Path validation helpers
"""

import asyncio
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, AsyncMock

import pytest

from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext


@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )


@pytest.fixture
def mock_context() -> MagicMock:
    """
    Create a mock execution context for tests that need more control.

    The mock context has resolve_value that returns the input unchanged
    by default, but can be configured for variable resolution.
    """
    context = MagicMock(spec=ExecutionContext)
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    context.variables = {}
    context.resources = {}
    return context


@pytest.fixture
def temp_test_file(tmp_path: Path) -> Path:
    """Create a temporary test file with content."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Hello, World!", encoding="utf-8")
    return test_file


@pytest.fixture
def temp_csv_file(tmp_path: Path) -> Path:
    """Create a temporary CSV file with test data."""
    csv_file = tmp_path / "test_data.csv"
    csv_content = """name,age,city
Alice,30,New York
Bob,25,Los Angeles
Charlie,35,Chicago
"""
    csv_file.write_text(csv_content, encoding="utf-8")
    return csv_file


@pytest.fixture
def temp_json_file(tmp_path: Path) -> Path:
    """Create a temporary JSON file with test data."""
    import json

    json_file = tmp_path / "test_data.json"
    data = {"name": "Test", "items": [1, 2, 3], "nested": {"key": "value"}}
    json_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return json_file


@pytest.fixture
def temp_image_file(tmp_path: Path) -> Path:
    """Create a temporary PNG image file."""
    from PIL import Image

    image_file = tmp_path / "test_image.png"
    # Create a simple 10x10 red image
    img = Image.new("RGB", (10, 10), color="red")
    img.save(image_file, format="PNG")
    return image_file


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """Create a temporary directory with some files."""
    test_dir = tmp_path / "test_directory"
    test_dir.mkdir()

    # Create some test files
    (test_dir / "file1.txt").write_text("Content 1")
    (test_dir / "file2.txt").write_text("Content 2")
    (test_dir / "data.json").write_text('{"key": "value"}')

    # Create a subdirectory
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "nested.txt").write_text("Nested content")

    return test_dir


@pytest.fixture
def temp_zip_file(tmp_path: Path, temp_directory: Path) -> Path:
    """Create a temporary ZIP file for testing."""
    import zipfile

    zip_file = tmp_path / "test_archive.zip"

    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in temp_directory.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(temp_directory)
                zf.write(file_path, arcname)

    return zip_file
