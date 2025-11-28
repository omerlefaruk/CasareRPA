"""
Test DBOS Integration for Project Aether.

Tests the basic DBOS workflow runner functionality with a simple workflow.

Prerequisites:
- PostgreSQL running (local or Supabase)
- DB_PASSWORD environment variable set
- DBOS initialized: dbos migrate
"""

import pytest
import asyncio
from pathlib import Path

# Skip these tests if DBOS is not configured
pytest_skip_reason = "DBOS not configured (set DB_PASSWORD env var)"

try:
    from casare_rpa.infrastructure.dbos.config import DBOSConfig
    from casare_rpa.infrastructure.dbos.workflow_runner import DBOSWorkflowRunner
    from casare_rpa.domain.value_objects.workflow import Workflow, WorkflowMetadata
    from casare_rpa.domain.value_objects.node import Node, NodeMetadata
    from casare_rpa.domain.value_objects.types import NodeType, NodeId

    DBOS_AVAILABLE = True
except ImportError as e:
    DBOS_AVAILABLE = False
    pytest_skip_reason = f"DBOS dependencies not available: {e}"


@pytest.mark.skipif(not DBOS_AVAILABLE, reason=pytest_skip_reason)
class TestDBOSIntegration:
    """Test suite for DBOS integration."""

    def test_config_from_env(self, monkeypatch):
        """Test loading DBOS configuration from environment variables."""
        monkeypatch.setenv(
            "DBOS_DATABASE_URL", "postgresql://postgres:test@localhost:5432/test"
        )
        monkeypatch.setenv("DBOS_APP_NAME", "test-app")
        monkeypatch.setenv("DBOS_LOCAL_MODE", "true")

        config = DBOSConfig.from_env()

        assert config.database_url == "postgresql://postgres:test@localhost:5432/test"
        assert config.app_name == "test-app"
        assert config.enable_local_mode is True

    def test_config_from_local_postgres(self):
        """Test creating DBOS configuration for local PostgreSQL."""
        config = DBOSConfig.from_local_postgres(
            host="localhost",
            port=5432,
            database="casare_test",
            user="postgres",
            password="testpass",
        )

        assert (
            "postgresql://postgres:testpass@localhost:5432/casare_test"
            == config.database_url
        )
        assert config.enable_local_mode is True

    def test_config_from_supabase(self):
        """Test creating DBOS configuration for Supabase."""
        config = DBOSConfig.from_supabase(
            supabase_url="https://abcdefgh.supabase.co",
            supabase_key="test_key",
            supabase_db_password="test_password",
        )

        assert (
            "postgresql://postgres:test_password@db.abcdefgh.supabase.co:5432/postgres"
            == config.database_url
        )
        assert config.enable_local_mode is False

    def test_config_to_yaml(self):
        """Test generating YAML configuration."""
        config = DBOSConfig.from_local_postgres()
        yaml_content = config.to_yaml_config()

        assert "name: casare-rpa-aether" in yaml_content
        assert "language: python" in yaml_content
        assert "hostname: localhost" in yaml_content
        assert "port: 5432" in yaml_content

    def test_create_simple_workflow(self):
        """Test creating a minimal workflow for DBOS execution."""
        # Create a simple workflow with Start and End nodes
        metadata = WorkflowMetadata(
            name="test_workflow",
            description="Simple test workflow for DBOS",
            version="1.0",
            author="test",
        )

        start_node = Node(
            metadata=NodeMetadata(
                node_id=NodeId("start_1"),
                name="Start",
                node_type=NodeType.START,
            ),
            inputs={},
            outputs={},
        )

        end_node = Node(
            metadata=NodeMetadata(
                node_id=NodeId("end_1"),
                name="End",
                node_type=NodeType.END,
            ),
            inputs={},
            outputs={},
        )

        workflow = Workflow(
            metadata=metadata,
            nodes=[start_node, end_node],
            connections=[],
        )

        assert workflow.metadata.name == "test_workflow"
        assert len(workflow.nodes) == 2

    @pytest.mark.asyncio
    async def test_workflow_runner_initialization(self):
        """Test DBOS workflow runner initialization."""
        # Create minimal workflow
        metadata = WorkflowMetadata(name="test", version="1.0", author="test")
        workflow = Workflow(metadata=metadata, nodes=[], connections=[])

        # Initialize runner (without DBOS instance for now)
        runner = DBOSWorkflowRunner(workflow, dbos_instance=None)

        assert runner.workflow == workflow
        assert runner.use_case is not None

    def test_yaml_file_creation(self, tmp_path):
        """Test creating dbos.yaml configuration file."""
        config = DBOSConfig.from_local_postgres()

        # Create config file in temporary directory
        config_path = config.create_yaml_file(tmp_path / "dbos.yaml")

        assert config_path.exists()
        content = config_path.read_text()
        assert "casare-rpa-aether" in content


@pytest.mark.integration
@pytest.mark.skipif(not DBOS_AVAILABLE, reason=pytest_skip_reason)
class TestDBOSWorkflowExecution:
    """
    Integration tests for DBOS workflow execution.

    These tests require:
    - PostgreSQL running (local or Supabase)
    - DB_PASSWORD environment variable set
    - DBOS migrated: dbos migrate

    Run with: pytest tests/infrastructure/test_dbos_integration.py -m integration
    """

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self):
        """
        Test executing a simple workflow with DBOS.

        Note: This is a placeholder test. Full implementation will be done
        in Phase 3 when @workflow and @step decorators are integrated.
        """
        # TODO: Implement full DBOS workflow execution test
        # This requires DBOS runtime initialization and database setup

        pytest.skip("Full DBOS workflow execution test pending Phase 3 implementation")


# ============================================================================
# Test Utilities
# ============================================================================


def create_test_workflow(name: str = "test_workflow") -> Workflow:
    """
    Create a minimal test workflow.

    Args:
        name: Workflow name

    Returns:
        Workflow instance
    """
    metadata = WorkflowMetadata(
        name=name,
        description="Test workflow",
        version="1.0",
        author="test",
    )

    start_node = Node(
        metadata=NodeMetadata(
            node_id=NodeId("start_1"),
            name="Start",
            node_type=NodeType.START,
        ),
        inputs={},
        outputs={},
    )

    workflow = Workflow(
        metadata=metadata,
        nodes=[start_node],
        connections=[],
    )

    return workflow
