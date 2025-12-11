"""
CasareRPA - Basic RPA Workflow Tests

Tests the three basic RPA workflows in workflows/ directory:
1. Invoice Processing - PDF/OCR/Regex/CSV pipeline
2. Web Scraping Leads - Browser automation workflow
3. Data Reconciliation - Excel comparison workflow

Follows project testing standards:
- Infrastructure layer mocked (no real browsers/files)
- Uses pytest-asyncio for async tests
- Uses existing test infrastructure (QtHeadlessRunner)
"""

import json
import pytest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.data_operation.compare_node import DataCompareNode
from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict


# =============================================================================
# PATHS AND CONSTANTS
# =============================================================================

WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"

INVOICE_WORKFLOW = WORKFLOWS_DIR / "invoice_processing.json"
WEB_SCRAPING_WORKFLOW = WORKFLOWS_DIR / "web_scraping_leads.json"
DATA_RECONCILIATION_WORKFLOW = WORKFLOWS_DIR / "data_reconciliation.json"


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def invoice_workflow() -> Dict[str, Any]:
    """Load invoice_processing.json workflow data."""
    with open(INVOICE_WORKFLOW, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def web_scraping_workflow() -> Dict[str, Any]:
    """Load web_scraping_leads.json workflow data."""
    with open(WEB_SCRAPING_WORKFLOW, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def data_reconciliation_workflow() -> Dict[str, Any]:
    """Load data_reconciliation.json workflow data."""
    with open(DATA_RECONCILIATION_WORKFLOW, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_execution_context() -> Mock:
    """Create mock execution context for node testing."""
    context = Mock(spec=ExecutionContext)
    context.variables = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables
    return context


# =============================================================================
# WORKFLOW STRUCTURE TESTS
# =============================================================================


class TestInvoiceProcessingWorkflowStructure:
    """Tests for invoice_processing.json workflow structure."""

    def test_workflow_file_exists(self) -> None:
        """Verify invoice_processing.json exists."""
        assert INVOICE_WORKFLOW.exists(), f"Workflow file not found: {INVOICE_WORKFLOW}"

    def test_workflow_has_valid_json(self, invoice_workflow: Dict[str, Any]) -> None:
        """Verify workflow is valid JSON with expected structure."""
        assert "metadata" in invoice_workflow
        assert "nodes" in invoice_workflow
        assert "connections" in invoice_workflow
        assert "variables" in invoice_workflow
        assert "settings" in invoice_workflow

    def test_workflow_metadata(self, invoice_workflow: Dict[str, Any]) -> None:
        """Verify workflow metadata is correct."""
        metadata = invoice_workflow["metadata"]
        assert metadata["name"] == "Invoice Processing Workflow"
        assert "pdf" in metadata["tags"]
        assert "ocr" in metadata["tags"]
        assert "invoice" in metadata["tags"]

    def test_node_types_exist(self, invoice_workflow: Dict[str, Any]) -> None:
        """Validate required node types exist in workflow."""
        nodes = invoice_workflow["nodes"]
        node_types = {node["node_type"] for node in nodes.values()}

        expected_types = {
            "StartNode",
            "EndNode",
            "FileWatchTriggerNode",
            "ReadPDFTextNode",
            "RegexMatchNode",
            "WriteCSVNode",
        }

        for expected in expected_types:
            assert expected in node_types, f"Missing node type: {expected}"

    def test_node_count(self, invoice_workflow: Dict[str, Any]) -> None:
        """Verify correct number of nodes."""
        nodes = invoice_workflow["nodes"]
        assert len(nodes) == 7  # start, file_watch, read_pdf, 2x regex, write_csv, end

    def test_connection_count(self, invoice_workflow: Dict[str, Any]) -> None:
        """Verify correct number of connections."""
        connections = invoice_workflow["connections"]
        # Workflow has execution flow + data flow connections
        assert len(connections) == 10

    def test_execution_flow_exists(self, invoice_workflow: Dict[str, Any]) -> None:
        """Verify execution flow from start to end exists."""
        connections = invoice_workflow["connections"]
        exec_connections = [c for c in connections if c["source_port"] == "exec_out"]

        # Should have exec_out connections for flow
        assert len(exec_connections) >= 5

    def test_data_flow_connections(self, invoice_workflow: Dict[str, Any]) -> None:
        """Verify data flow connections exist (file_path, text, etc)."""
        connections = invoice_workflow["connections"]

        # Check for file_path data flow
        file_path_conn = [c for c in connections if c["source_port"] == "file_path"]
        assert len(file_path_conn) >= 1

        # Check for text data flow to regex nodes
        text_conn = [c for c in connections if c["source_port"] == "text"]
        assert len(text_conn) >= 2

    def test_workflow_loads_via_loader(self, invoice_workflow: Dict[str, Any]) -> None:
        """Verify workflow can be loaded via workflow_loader."""
        workflow_schema = load_workflow_from_dict(invoice_workflow)

        assert workflow_schema is not None
        assert isinstance(workflow_schema, WorkflowSchema)
        assert workflow_schema.metadata.name == "Invoice Processing Workflow"


class TestWebScrapingWorkflowStructure:
    """Tests for web_scraping_leads.json workflow structure."""

    def test_workflow_file_exists(self) -> None:
        """Verify web_scraping_leads.json exists."""
        assert (
            WEB_SCRAPING_WORKFLOW.exists()
        ), f"Workflow not found: {WEB_SCRAPING_WORKFLOW}"

    def test_workflow_has_valid_json(
        self, web_scraping_workflow: Dict[str, Any]
    ) -> None:
        """Verify workflow is valid JSON with expected structure."""
        assert "metadata" in web_scraping_workflow
        assert "nodes" in web_scraping_workflow
        assert "connections" in web_scraping_workflow

    def test_workflow_metadata(self, web_scraping_workflow: Dict[str, Any]) -> None:
        """Verify workflow metadata is correct."""
        metadata = web_scraping_workflow["metadata"]
        assert metadata["name"] == "Web Scraping Leads Workflow"
        assert "web" in metadata["tags"]
        assert "scraping" in metadata["tags"]
        assert "browser" in metadata["tags"]

    def test_browser_node_types_exist(
        self, web_scraping_workflow: Dict[str, Any]
    ) -> None:
        """Validate browser-related node types exist."""
        nodes = web_scraping_workflow["nodes"]
        node_types = {node["node_type"] for node in nodes.values()}

        browser_types = {
            "LaunchBrowserNode",
            "GoToURLNode",
            "TypeTextNode",
            "ClickElementNode",
            "WaitForElementNode",
            "TableScraperNode",
            "CloseBrowserNode",
        }

        for expected in browser_types:
            assert expected in node_types, f"Missing browser node: {expected}"

    def test_node_count(self, web_scraping_workflow: Dict[str, Any]) -> None:
        """Verify correct number of nodes."""
        nodes = web_scraping_workflow["nodes"]
        assert len(nodes) == 12

    def test_page_connection_chain(self, web_scraping_workflow: Dict[str, Any]) -> None:
        """Verify page object is passed through node chain."""
        connections = web_scraping_workflow["connections"]

        # Count page connections (browser context passing)
        page_connections = [c for c in connections if c["source_port"] == "page"]

        # Page should be passed through multiple nodes
        assert len(page_connections) >= 7

    def test_browser_launch_config(self, web_scraping_workflow: Dict[str, Any]) -> None:
        """Verify browser launch configuration."""
        launch_node = web_scraping_workflow["nodes"]["launch_browser_2"]

        assert launch_node["config"]["browser_type"] == "chromium"
        assert launch_node["config"]["viewport_width"] == 1920
        assert launch_node["config"]["viewport_height"] == 1080

    def test_login_sequence(self, web_scraping_workflow: Dict[str, Any]) -> None:
        """Verify login sequence nodes exist."""
        nodes = web_scraping_workflow["nodes"]

        # Check username field
        username_node = nodes.get("type_username_4")
        assert username_node is not None
        assert username_node["config"]["selector"] == "#username"

        # Check password field
        password_node = nodes.get("type_password_5")
        assert password_node is not None
        assert password_node["config"]["selector"] == "#password"

        # Check login button
        login_node = nodes.get("click_login_6")
        assert login_node is not None

    def test_workflow_loads_via_loader(
        self, web_scraping_workflow: Dict[str, Any]
    ) -> None:
        """Verify workflow can be loaded via workflow_loader."""
        workflow_schema = load_workflow_from_dict(web_scraping_workflow)

        assert workflow_schema is not None
        assert isinstance(workflow_schema, WorkflowSchema)
        assert workflow_schema.metadata.name == "Web Scraping Leads Workflow"


class TestDataReconciliationWorkflowStructure:
    """Tests for data_reconciliation.json workflow structure."""

    def test_workflow_file_exists(self) -> None:
        """Verify data_reconciliation.json exists."""
        assert DATA_RECONCILIATION_WORKFLOW.exists()

    def test_workflow_has_valid_json(
        self, data_reconciliation_workflow: Dict[str, Any]
    ) -> None:
        """Verify workflow is valid JSON with expected structure."""
        assert "metadata" in data_reconciliation_workflow
        assert "nodes" in data_reconciliation_workflow
        assert "connections" in data_reconciliation_workflow

    def test_workflow_metadata(
        self, data_reconciliation_workflow: Dict[str, Any]
    ) -> None:
        """Verify workflow metadata is correct."""
        metadata = data_reconciliation_workflow["metadata"]
        assert metadata["name"] == "Data Reconciliation Workflow"
        assert "excel" in metadata["tags"]
        assert "reconciliation" in metadata["tags"]
        assert "comparison" in metadata["tags"]

    def test_excel_node_types_exist(
        self, data_reconciliation_workflow: Dict[str, Any]
    ) -> None:
        """Validate Excel-related node types exist."""
        nodes = data_reconciliation_workflow["nodes"]
        node_types = {node["node_type"] for node in nodes.values()}

        excel_types = {
            "ExcelOpenNode",
            "ExcelGetRangeNode",
            "ExcelCloseNode",
        }

        for expected in excel_types:
            assert expected in node_types, f"Missing Excel node: {expected}"

    def test_comparison_node_exists(
        self, data_reconciliation_workflow: Dict[str, Any]
    ) -> None:
        """Verify ComparisonNode exists for data comparison."""
        nodes = data_reconciliation_workflow["nodes"]
        node_types = {node["node_type"] for node in nodes.values()}

        assert "ComparisonNode" in node_types

    def test_node_count(self, data_reconciliation_workflow: Dict[str, Any]) -> None:
        """Verify correct number of nodes."""
        nodes = data_reconciliation_workflow["nodes"]
        # start, 2x excel_open, 2x excel_range, 2x excel_close, compare, write_json, end
        assert len(nodes) == 10

    def test_data_flow_connections(
        self, data_reconciliation_workflow: Dict[str, Any]
    ) -> None:
        """Verify data flow from Excel ranges to comparison node."""
        connections = data_reconciliation_workflow["connections"]

        # Check workbook connections
        workbook_connections = [
            c for c in connections if c["source_port"] == "workbook"
        ]
        assert len(workbook_connections) >= 4

        # Check data connections to compare node
        data_to_compare = [
            c
            for c in connections
            if c["target_node"] == "compare_data_8" and c["source_port"] == "data"
        ]
        assert len(data_to_compare) == 2

    def test_dual_workbook_processing(
        self, data_reconciliation_workflow: Dict[str, Any]
    ) -> None:
        """Verify workflow processes two separate workbooks."""
        nodes = data_reconciliation_workflow["nodes"]

        # Should have two ExcelOpenNode instances
        open_nodes = [n for n in nodes.values() if n["node_type"] == "ExcelOpenNode"]
        assert len(open_nodes) == 2

        # Check file paths are different
        paths = {n["config"]["file_path"] for n in open_nodes}
        assert len(paths) == 2

    def test_workflow_loads_via_loader(
        self, data_reconciliation_workflow: Dict[str, Any]
    ) -> None:
        """Verify workflow can be loaded via workflow_loader."""
        workflow_schema = load_workflow_from_dict(data_reconciliation_workflow)

        assert workflow_schema is not None
        assert isinstance(workflow_schema, WorkflowSchema)
        assert workflow_schema.metadata.name == "Data Reconciliation Workflow"


# =============================================================================
# DATA COMPARE NODE EXECUTION TESTS
# =============================================================================


class TestDataCompareNodeExecution:
    """Tests for DataCompareNode execution logic."""

    @pytest.mark.asyncio
    async def test_compare_identical_datasets(
        self, mock_execution_context: Mock
    ) -> None:
        """Test comparing two identical datasets."""
        node = DataCompareNode(
            node_id="test_compare",
            config={"key_columns": "id", "compare_all_columns": True},
        )

        data_a = [
            {"id": 1, "name": "Alice", "value": 100},
            {"id": 2, "name": "Bob", "value": 200},
        ]
        data_b = [
            {"id": 1, "name": "Alice", "value": 100},
            {"id": 2, "name": "Bob", "value": 200},
        ]

        node.set_input_value("data_a", data_a)
        node.set_input_value("data_b", data_b)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert len(node.get_output_value("only_in_a")) == 0
        assert len(node.get_output_value("only_in_b")) == 0
        assert len(node.get_output_value("matched")) == 2
        assert node.get_output_value("has_differences") is False

    @pytest.mark.asyncio
    async def test_compare_with_only_in_a(self, mock_execution_context: Mock) -> None:
        """Test detecting rows only in dataset A."""
        node = DataCompareNode(
            node_id="test_compare",
            config={"key_columns": "id", "compare_all_columns": True},
        )

        data_a = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},  # Only in A
        ]
        data_b = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

        node.set_input_value("data_a", data_a)
        node.set_input_value("data_b", data_b)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

        only_in_a = node.get_output_value("only_in_a")
        assert len(only_in_a) == 1
        assert only_in_a[0]["id"] == 3
        assert only_in_a[0]["name"] == "Charlie"

        assert len(node.get_output_value("only_in_b")) == 0
        assert node.get_output_value("has_differences") is True

    @pytest.mark.asyncio
    async def test_compare_with_only_in_b(self, mock_execution_context: Mock) -> None:
        """Test detecting rows only in dataset B."""
        node = DataCompareNode(
            node_id="test_compare",
            config={"key_columns": "id", "compare_all_columns": True},
        )

        data_a = [
            {"id": 1, "name": "Alice"},
        ]
        data_b = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},  # Only in B
            {"id": 3, "name": "Charlie"},  # Only in B
        ]

        node.set_input_value("data_a", data_a)
        node.set_input_value("data_b", data_b)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

        only_in_b = node.get_output_value("only_in_b")
        assert len(only_in_b) == 2
        assert node.get_output_value("has_differences") is True

    @pytest.mark.asyncio
    async def test_compare_with_modifications(
        self, mock_execution_context: Mock
    ) -> None:
        """Test detecting modified rows (same key, different values)."""
        node = DataCompareNode(
            node_id="test_compare",
            config={"key_columns": "id", "compare_all_columns": True},
        )

        data_a = [
            {"id": 1, "name": "Alice", "value": 100},
            {"id": 2, "name": "Bob", "value": 200},
        ]
        data_b = [
            {"id": 1, "name": "Alice", "value": 150},  # Modified value
            {"id": 2, "name": "Bob", "value": 200},
        ]

        node.set_input_value("data_a", data_a)
        node.set_input_value("data_b", data_b)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

        matched = node.get_output_value("matched")
        assert len(matched) == 2

        # First match should be modified
        modified_matches = [m for m in matched if m["is_modified"]]
        assert len(modified_matches) == 1
        assert "value" in modified_matches[0]["different_columns"]

        diff_summary = node.get_output_value("diff_summary")
        assert diff_summary["modified_count"] == 1
        assert node.get_output_value("has_differences") is True

    @pytest.mark.asyncio
    async def test_compare_mixed_differences(
        self, mock_execution_context: Mock
    ) -> None:
        """Test all difference types: only_in_a, only_in_b, and matched."""
        node = DataCompareNode(
            node_id="test_compare",
            config={"key_columns": "id", "compare_all_columns": True},
        )

        data_a = [
            {"id": 1, "name": "Alice", "value": 100},
            {"id": 2, "name": "Bob", "value": 200},
            {"id": 4, "name": "Dave", "value": 400},  # Only in A
        ]
        data_b = [
            {"id": 1, "name": "Alice", "value": 100},  # Matched
            {"id": 2, "name": "Bob", "value": 250},  # Modified
            {"id": 3, "name": "Charlie", "value": 300},  # Only in B
        ]

        node.set_input_value("data_a", data_a)
        node.set_input_value("data_b", data_b)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

        only_in_a = node.get_output_value("only_in_a")
        only_in_b = node.get_output_value("only_in_b")
        matched = node.get_output_value("matched")
        diff_summary = node.get_output_value("diff_summary")

        assert len(only_in_a) == 1
        assert only_in_a[0]["id"] == 4

        assert len(only_in_b) == 1
        assert only_in_b[0]["id"] == 3

        assert len(matched) == 2
        assert diff_summary["matched_count"] == 2
        assert diff_summary["modified_count"] == 1
        assert diff_summary["removed_count"] == 1
        assert diff_summary["added_count"] == 1

    @pytest.mark.asyncio
    async def test_compare_empty_datasets(self, mock_execution_context: Mock) -> None:
        """Test comparing empty datasets."""
        node = DataCompareNode(
            node_id="test_compare",
            config={"key_columns": "id"},
        )

        node.set_input_value("data_a", [])
        node.set_input_value("data_b", [])

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert len(node.get_output_value("only_in_a")) == 0
        assert len(node.get_output_value("only_in_b")) == 0
        assert len(node.get_output_value("matched")) == 0
        assert node.get_output_value("has_differences") is False

    @pytest.mark.asyncio
    async def test_compare_case_insensitive(self, mock_execution_context: Mock) -> None:
        """Test case-insensitive comparison."""
        node = DataCompareNode(
            node_id="test_compare",
            config={
                "key_columns": "name",
                "compare_all_columns": True,
                "case_sensitive": False,
            },
        )

        data_a = [{"name": "ALICE", "value": "TEST"}]
        data_b = [{"name": "alice", "value": "test"}]

        node.set_input_value("data_a", data_a)
        node.set_input_value("data_b", data_b)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert len(node.get_output_value("matched")) == 1
        assert node.get_output_value("has_differences") is False


# =============================================================================
# WORKFLOW LOADING TESTS VIA HEADLESS RUNNER
# =============================================================================


class TestWorkflowLoadingViaHeadlessRunner:
    """Tests for loading workflows via QtHeadlessRunner."""

    def test_invoice_workflow_loads_without_errors(
        self, invoice_workflow: Dict[str, Any]
    ) -> None:
        """Verify invoice workflow loads without errors."""
        try:
            from tests.integration.runners import QtHeadlessRunner

            runner = QtHeadlessRunner()
            workflow = runner.load_workflow_from_dict(invoice_workflow)

            assert workflow is not None
            assert workflow.metadata.name == "Invoice Processing Workflow"
            assert len(workflow.nodes) > 0

            runner.cleanup()
        except ImportError:
            pytest.skip("QtHeadlessRunner not available")

    def test_web_scraping_workflow_loads_without_errors(
        self, web_scraping_workflow: Dict[str, Any]
    ) -> None:
        """Verify web scraping workflow loads without errors."""
        try:
            from tests.integration.runners import QtHeadlessRunner

            runner = QtHeadlessRunner()
            workflow = runner.load_workflow_from_dict(web_scraping_workflow)

            assert workflow is not None
            assert workflow.metadata.name == "Web Scraping Leads Workflow"
            assert len(workflow.nodes) > 0

            runner.cleanup()
        except ImportError:
            pytest.skip("QtHeadlessRunner not available")

    def test_data_reconciliation_workflow_loads_without_errors(
        self, data_reconciliation_workflow: Dict[str, Any]
    ) -> None:
        """Verify data reconciliation workflow loads without errors."""
        try:
            from tests.integration.runners import QtHeadlessRunner

            runner = QtHeadlessRunner()
            workflow = runner.load_workflow_from_dict(data_reconciliation_workflow)

            assert workflow is not None
            assert workflow.metadata.name == "Data Reconciliation Workflow"
            assert len(workflow.nodes) > 0

            runner.cleanup()
        except ImportError:
            pytest.skip("QtHeadlessRunner not available")

    def test_load_workflow_from_file_path(self) -> None:
        """Test loading workflow directly from file path."""
        try:
            from tests.integration.runners import QtHeadlessRunner

            runner = QtHeadlessRunner()
            workflow = runner.load_workflow(INVOICE_WORKFLOW)

            assert workflow is not None
            assert isinstance(workflow, WorkflowSchema)

            runner.cleanup()
        except ImportError:
            pytest.skip("QtHeadlessRunner not available")

    def test_all_workflows_have_start_node(
        self,
        invoice_workflow: Dict[str, Any],
        web_scraping_workflow: Dict[str, Any],
        data_reconciliation_workflow: Dict[str, Any],
    ) -> None:
        """Verify all workflows have a StartNode."""
        for workflow_data in [
            invoice_workflow,
            web_scraping_workflow,
            data_reconciliation_workflow,
        ]:
            node_types = {n["node_type"] for n in workflow_data["nodes"].values()}
            assert "StartNode" in node_types

    def test_all_workflows_have_end_node(
        self,
        invoice_workflow: Dict[str, Any],
        web_scraping_workflow: Dict[str, Any],
        data_reconciliation_workflow: Dict[str, Any],
    ) -> None:
        """Verify all workflows have an EndNode."""
        for workflow_data in [
            invoice_workflow,
            web_scraping_workflow,
            data_reconciliation_workflow,
        ]:
            node_types = {n["node_type"] for n in workflow_data["nodes"].values()}
            assert "EndNode" in node_types


# =============================================================================
# WORKFLOW VALIDATION TESTS
# =============================================================================


class TestWorkflowValidation:
    """Tests for workflow validation rules."""

    def test_all_connections_reference_valid_nodes(
        self,
        invoice_workflow: Dict[str, Any],
        web_scraping_workflow: Dict[str, Any],
        data_reconciliation_workflow: Dict[str, Any],
    ) -> None:
        """Verify all connections reference nodes that exist."""
        for workflow_data in [
            invoice_workflow,
            web_scraping_workflow,
            data_reconciliation_workflow,
        ]:
            node_ids = set(workflow_data["nodes"].keys())
            for conn in workflow_data["connections"]:
                assert (
                    conn["source_node"] in node_ids
                ), f"Invalid source_node: {conn['source_node']}"
                assert (
                    conn["target_node"] in node_ids
                ), f"Invalid target_node: {conn['target_node']}"

    def test_no_orphan_nodes(
        self,
        invoice_workflow: Dict[str, Any],
        web_scraping_workflow: Dict[str, Any],
        data_reconciliation_workflow: Dict[str, Any],
    ) -> None:
        """Verify no nodes are disconnected (except Start which has no incoming)."""
        for workflow_data in [
            invoice_workflow,
            web_scraping_workflow,
            data_reconciliation_workflow,
        ]:
            node_ids = set(workflow_data["nodes"].keys())
            connected_nodes = set()

            for conn in workflow_data["connections"]:
                connected_nodes.add(conn["source_node"])
                connected_nodes.add(conn["target_node"])

            # All nodes should be connected
            for node_id in node_ids:
                assert node_id in connected_nodes, f"Orphan node: {node_id}"

    def test_workflows_have_settings(
        self,
        invoice_workflow: Dict[str, Any],
        web_scraping_workflow: Dict[str, Any],
        data_reconciliation_workflow: Dict[str, Any],
    ) -> None:
        """Verify workflows have settings section."""
        for workflow_data in [
            invoice_workflow,
            web_scraping_workflow,
            data_reconciliation_workflow,
        ]:
            assert "settings" in workflow_data
            settings = workflow_data["settings"]
            # Common settings should exist
            assert isinstance(settings, dict)


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config) -> None:
    """Configure pytest markers for basic workflow tests."""
    config.addinivalue_line("markers", "workflow: mark test as workflow structure test")
    config.addinivalue_line("markers", "node: mark test as node execution test")
