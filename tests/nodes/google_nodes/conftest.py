"""
Fixtures for Google node tests.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext


@dataclass
class MockDriveFile:
    """Mock DriveFile for testing."""

    id: str
    name: str
    mime_type: str
    size: int | None = None
    created_time: str | None = None
    modified_time: str | None = None
    parents: list[str] = field(default_factory=list)
    web_view_link: str | None = None
    web_content_link: str | None = None
    description: str | None = None
    starred: bool = False
    trashed: bool = False
    shared: bool = False
    owners: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )


@pytest.fixture
def mock_drive_client() -> MagicMock:
    """Create a mock GoogleDriveClient."""
    client = MagicMock()

    # download_file returns the destination path
    async def mock_download_file(file_id: str, destination_path: str) -> Path:
        return Path(destination_path)

    client.download_file = AsyncMock(side_effect=mock_download_file)

    # get_file returns file metadata (needed for downloads)
    client.get_file = AsyncMock(
        return_value=MockDriveFile(
            id="file_123",
            name="test_file.pdf",
            mime_type="application/pdf",
        )
    )

    # list_files returns (files, next_page_token)
    client.list_files = AsyncMock(return_value=([], None))

    # upload_file returns a DriveFile
    client.upload_file = AsyncMock(
        return_value=MockDriveFile(
            id="uploaded_file_id",
            name="uploaded.pdf",
            mime_type="application/pdf",
            web_view_link="https://drive.google.com/file/d/uploaded_file_id/view",
        )
    )

    return client


@pytest.fixture
def sample_drive_files() -> list[MockDriveFile]:
    """Create sample DriveFile objects for testing."""
    return [
        MockDriveFile(
            id="file_001",
            name="document.pdf",
            mime_type="application/pdf",
            size=1024,
        ),
        MockDriveFile(
            id="file_002",
            name="spreadsheet.xlsx",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size=2048,
        ),
        MockDriveFile(
            id="file_003",
            name="image.png",
            mime_type="image/png",
            size=512,
        ),
    ]


@pytest.fixture
def sample_google_workspace_files() -> list[MockDriveFile]:
    """Create sample Google Workspace files (should be skipped in downloads)."""
    return [
        MockDriveFile(
            id="gdoc_001",
            name="Google Doc",
            mime_type="application/vnd.google-apps.document",
        ),
        MockDriveFile(
            id="gsheet_001",
            name="Google Sheet",
            mime_type="application/vnd.google-apps.spreadsheet",
        ),
    ]


@pytest.fixture
def tmp_download_dir(tmp_path: Path) -> Path:
    """Create a temporary download directory."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    return download_dir
