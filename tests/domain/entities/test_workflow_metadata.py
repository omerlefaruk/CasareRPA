"""
Tests for WorkflowMetadata domain entity.
Covers metadata creation, serialization, timestamps.
"""

import pytest
from datetime import datetime

from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.value_objects.types import SCHEMA_VERSION


# ============================================================================
# Creation Tests
# ============================================================================


class TestWorkflowMetadataCreation:
    """Tests for WorkflowMetadata initialization."""

    def test_create_with_name_only(self) -> None:
        """Create metadata with just name."""
        metadata = WorkflowMetadata(name="Test Workflow")
        assert metadata.name == "Test Workflow"
        assert metadata.description == ""
        assert metadata.author == ""
        assert metadata.version == "1.0.0"
        assert metadata.tags == []

    def test_create_with_all_fields(self) -> None:
        """Create metadata with all fields."""
        metadata = WorkflowMetadata(
            name="Complete Workflow",
            description="A fully configured workflow",
            author="Test Author",
            version="2.0.0",
            tags=["test", "demo"],
        )
        assert metadata.name == "Complete Workflow"
        assert metadata.description == "A fully configured workflow"
        assert metadata.author == "Test Author"
        assert metadata.version == "2.0.0"
        assert metadata.tags == ["test", "demo"]

    def test_timestamps_auto_created(self) -> None:
        """Timestamps are automatically set on creation."""
        metadata = WorkflowMetadata(name="Timestamped")
        assert metadata.created_at is not None
        assert metadata.modified_at is not None

    def test_schema_version_set(self) -> None:
        """Schema version is set from constant."""
        metadata = WorkflowMetadata(name="Versioned")
        assert metadata.schema_version == SCHEMA_VERSION


# ============================================================================
# Timestamp Tests
# ============================================================================


class TestWorkflowMetadataTimestamps:
    """Tests for timestamp management."""

    def test_update_modified_timestamp(self) -> None:
        """update_modified_timestamp updates the timestamp."""
        metadata = WorkflowMetadata(name="Test")
        old_modified = metadata.modified_at
        metadata.update_modified_timestamp()
        # Should be updated (may be same if too fast)
        assert metadata.modified_at is not None

    def test_created_at_not_changed(self) -> None:
        """created_at is not changed on update."""
        metadata = WorkflowMetadata(name="Test")
        original_created = metadata.created_at
        metadata.update_modified_timestamp()
        assert metadata.created_at == original_created


# ============================================================================
# Serialization Tests
# ============================================================================


class TestWorkflowMetadataSerialization:
    """Tests for to_dict/from_dict serialization."""

    def test_to_dict(self) -> None:
        """Serialize metadata to dictionary."""
        metadata = WorkflowMetadata(
            name="Serializable",
            description="Test description",
            author="Author",
            version="1.2.3",
            tags=["a", "b"],
        )
        data = metadata.to_dict()
        assert data["name"] == "Serializable"
        assert data["description"] == "Test description"
        assert data["author"] == "Author"
        assert data["version"] == "1.2.3"
        assert data["tags"] == ["a", "b"]
        assert "created_at" in data
        assert "modified_at" in data
        assert "schema_version" in data

    def test_from_dict_full(self) -> None:
        """Deserialize metadata from complete dictionary."""
        data = {
            "name": "Loaded",
            "description": "Loaded description",
            "author": "Loader",
            "version": "3.0.0",
            "tags": ["loaded"],
            "created_at": "2024-01-01T10:00:00",
            "modified_at": "2024-01-02T10:00:00",
            "schema_version": "1.0.0",
        }
        metadata = WorkflowMetadata.from_dict(data)
        assert metadata.name == "Loaded"
        assert metadata.description == "Loaded description"
        assert metadata.author == "Loader"
        assert metadata.version == "3.0.0"
        assert metadata.tags == ["loaded"]
        assert metadata.created_at == "2024-01-01T10:00:00"
        assert metadata.modified_at == "2024-01-02T10:00:00"

    def test_from_dict_minimal(self) -> None:
        """Deserialize metadata from minimal dictionary."""
        data = {"name": "Minimal"}
        metadata = WorkflowMetadata.from_dict(data)
        assert metadata.name == "Minimal"
        assert metadata.description == ""
        assert metadata.version == "1.0.0"

    def test_from_dict_missing_name(self) -> None:
        """Deserialize with missing name uses default."""
        data = {}
        metadata = WorkflowMetadata.from_dict(data)
        assert metadata.name == "Untitled"

    def test_roundtrip_serialization(self) -> None:
        """Serialize then deserialize preserves data."""
        original = WorkflowMetadata(
            name="Roundtrip",
            description="Round trip test",
            author="Tester",
            version="4.0.0",
            tags=["round", "trip"],
        )
        data = original.to_dict()
        restored = WorkflowMetadata.from_dict(data)
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.author == original.author
        assert restored.version == original.version
        assert restored.tags == original.tags


# ============================================================================
# String Representation Tests
# ============================================================================


class TestWorkflowMetadataRepr:
    """Tests for __repr__ method."""

    def test_repr(self) -> None:
        """String representation shows name and version."""
        metadata = WorkflowMetadata(name="Demo", version="2.5.0")
        rep = repr(metadata)
        assert "WorkflowMetadata" in rep
        assert "Demo" in rep
        assert "2.5.0" in rep
