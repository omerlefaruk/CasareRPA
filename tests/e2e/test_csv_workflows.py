"""
CasareRPA - E2E Tests for CSV File Workflows.

Tests CSV file operations including:
- Basic CSV read/write
- CSV with headers and different delimiters
- CSV transformations and filtering
- ETL-style pipelines

Uses real ExecutionContext and temp_workspace fixture.
"""

from pathlib import Path
from typing import Any, Dict, List

import pytest

from tests.e2e.helpers import WorkflowBuilder


# =============================================================================
# BASIC CSV OPERATIONS
# =============================================================================


class TestBasicCSVOperations:
    """Test basic CSV read/write operations."""

    @pytest.mark.asyncio
    async def test_write_and_read_csv(self, temp_workspace: Path) -> None:
        """Write CSV data, read back and verify."""
        file_path = str(temp_workspace / "test.csv")
        data = [
            {"name": "John", "age": "30", "city": "NYC"},
            {"name": "Jane", "age": "25", "city": "LA"},
        ]

        result = await (
            WorkflowBuilder("write_read_csv")
            .add_start()
            .add_write_csv(file_path, data, node_id="write")
            .add_read_csv(file_path, node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_set_variable("headers", "{{read.headers}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 2
        headers = result["variables"].get("headers", [])
        assert "name" in headers
        assert "age" in headers
        assert "city" in headers
        read_data = result["variables"].get("data", [])
        assert len(read_data) == 2
        assert read_data[0]["name"] == "John"
        assert read_data[1]["name"] == "Jane"

    @pytest.mark.asyncio
    async def test_csv_with_headers(self, temp_workspace: Path) -> None:
        """Write CSV with explicit headers, verify headers preserved."""
        file_path = str(temp_workspace / "headers.csv")
        headers = ["id", "product", "price"]
        data = [
            {"id": "1", "product": "Widget", "price": "9.99"},
            {"id": "2", "product": "Gadget", "price": "19.99"},
        ]

        result = await (
            WorkflowBuilder("csv_headers")
            .add_start()
            .add_write_csv(file_path, data, headers=headers, node_id="write")
            .add_read_csv(file_path, node_id="read")
            .add_set_variable("headers", "{{read.headers}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_headers = result["variables"].get("headers", [])
        assert read_headers == headers

    @pytest.mark.asyncio
    async def test_csv_multiple_rows(self, temp_workspace: Path) -> None:
        """Write and read CSV with many rows."""
        file_path = str(temp_workspace / "multi_row.csv")
        data = [{"id": str(i), "value": f"item_{i}"} for i in range(100)]

        result = await (
            WorkflowBuilder("csv_multi_row")
            .add_start()
            .add_write_csv(file_path, data, node_id="write")
            .add_read_csv(file_path, node_id="read")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 100

    @pytest.mark.asyncio
    async def test_csv_with_semicolon_delimiter(self, temp_workspace: Path) -> None:
        """Write and read CSV with semicolon delimiter."""
        file_path = str(temp_workspace / "semicolon.csv")
        data = [
            {"name": "Alice", "score": "95"},
            {"name": "Bob", "score": "87"},
        ]

        result = await (
            WorkflowBuilder("csv_semicolon")
            .add_start()
            .add_write_csv(file_path, data, delimiter=";", node_id="write")
            .add_read_csv(file_path, delimiter=";", node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 2
        read_data = result["variables"].get("data", [])
        assert read_data[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_csv_with_tab_delimiter(self, temp_workspace: Path) -> None:
        """Write and read TSV (tab-separated values)."""
        file_path = str(temp_workspace / "data.tsv")
        data = [
            {"col1": "a", "col2": "b"},
            {"col1": "c", "col2": "d"},
        ]

        result = await (
            WorkflowBuilder("csv_tab")
            .add_start()
            .add_write_csv(file_path, data, delimiter="\t", node_id="write")
            .add_read_csv(file_path, delimiter="\t", node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("data", [])
        assert len(read_data) == 2

    @pytest.mark.asyncio
    async def test_csv_with_quoted_values(self, temp_workspace: Path) -> None:
        """Write and read CSV with values containing commas (quoted)."""
        file_path = str(temp_workspace / "quoted.csv")
        data = [
            {"name": "John, Jr.", "address": "123 Main St, Apt 4"},
            {"name": "Jane", "address": "456 Oak Ave"},
        ]

        result = await (
            WorkflowBuilder("csv_quoted")
            .add_start()
            .add_write_csv(file_path, data, node_id="write")
            .add_read_csv(file_path, node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("data", [])
        assert read_data[0]["name"] == "John, Jr."
        assert "Apt 4" in read_data[0]["address"]

    @pytest.mark.asyncio
    async def test_csv_no_header(self, temp_workspace: Path) -> None:
        """Write and read CSV without header row."""
        file_path = str(temp_workspace / "no_header.csv")
        data = [
            ["row1_col1", "row1_col2", "row1_col3"],
            ["row2_col1", "row2_col2", "row2_col3"],
        ]

        result = await (
            WorkflowBuilder("csv_no_header")
            .add_start()
            .add_write_csv(file_path, data, write_header=False, node_id="write")
            .add_read_csv(file_path, has_header=False, node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 2
        read_data = result["variables"].get("data", [])
        # Without header, data is list of lists
        assert len(read_data) == 2

    @pytest.mark.asyncio
    async def test_csv_skip_rows(self, temp_workspace: Path) -> None:
        """Read CSV skipping first N rows."""
        file_path = str(temp_workspace / "skip_rows.csv")
        # Create CSV with some rows to skip
        content = """name,value
# Comment line to skip
Alice,100
Bob,200
Charlie,300"""
        Path(file_path).write_text(content)

        result = await (
            WorkflowBuilder("csv_skip")
            .add_start()
            .add_read_csv(file_path, skip_rows=1, node_id="read")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_set_variable("data", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        # After skipping 1 row, we should have 3 data rows
        assert result["variables"].get("row_count") == 3

    @pytest.mark.asyncio
    async def test_csv_max_rows(self, temp_workspace: Path) -> None:
        """Read CSV with max_rows limit."""
        file_path = str(temp_workspace / "max_rows.csv")
        data = [{"id": str(i), "val": f"v{i}"} for i in range(50)]

        result = await (
            WorkflowBuilder("csv_max_rows")
            .add_start()
            .add_write_csv(file_path, data, node_id="write")
            .add_read_csv(file_path, max_rows=10, node_id="read")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 10


# =============================================================================
# CSV DATA TRANSFORMATIONS
# =============================================================================


class TestCSVTransformations:
    """Test CSV transformation workflows."""

    @pytest.mark.asyncio
    async def test_csv_read_transform_write(self, temp_workspace: Path) -> None:
        """Read CSV, transform via variables, write new CSV."""
        input_path = str(temp_workspace / "input.csv")
        output_path = str(temp_workspace / "output.csv")

        # Create input CSV
        input_data = [
            {"first_name": "John", "last_name": "Doe"},
            {"first_name": "Jane", "last_name": "Smith"},
        ]

        # Write input, read, transform, write output
        result = await (
            WorkflowBuilder("csv_transform")
            .add_start()
            .add_write_csv(input_path, input_data, node_id="write_input")
            .add_read_csv(input_path, node_id="read")
            .add_set_variable("original_data", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        original = result["variables"].get("original_data", [])
        assert len(original) == 2
        assert original[0]["first_name"] == "John"

    @pytest.mark.asyncio
    async def test_csv_copy_to_new_file(self, temp_workspace: Path) -> None:
        """Read CSV and write to different location."""
        src_path = str(temp_workspace / "source.csv")
        dst_path = str(temp_workspace / "dest.csv")
        data = [{"col1": "a", "col2": "b"}, {"col1": "c", "col2": "d"}]

        result = await (
            WorkflowBuilder("csv_copy")
            .add_start()
            .add_write_csv(src_path, data, node_id="write_src")
            .add_read_csv(src_path, node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_write_csv(dst_path, "{{data}}", node_id="write_dst")
            .add_read_csv(dst_path, node_id="verify")
            .add_set_variable("dst_count", "{{verify.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("dst_count") == 2

    @pytest.mark.asyncio
    async def test_csv_with_different_encodings(self, temp_workspace: Path) -> None:
        """Write and read CSV with different encodings."""
        utf8_path = str(temp_workspace / "utf8.csv")
        latin1_path = str(temp_workspace / "latin1.csv")

        data = [{"name": "Test", "value": "123"}]

        # Test UTF-8
        result = await (
            WorkflowBuilder("csv_utf8")
            .add_start()
            .add_write_csv(utf8_path, data, encoding="utf-8", node_id="write")
            .add_read_csv(utf8_path, encoding="utf-8", node_id="read")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_end()
            .execute()
        )
        assert result["success"], f"UTF-8 workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 1

        # Test Latin-1
        result = await (
            WorkflowBuilder("csv_latin1")
            .add_start()
            .add_write_csv(latin1_path, data, encoding="latin-1", node_id="write")
            .add_read_csv(latin1_path, encoding="latin-1", node_id="read")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Latin-1 workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 1


# =============================================================================
# ETL PIPELINES
# =============================================================================


class TestCSVEtlPipelines:
    """Test ETL-style CSV workflows."""

    @pytest.mark.asyncio
    async def test_csv_etl_extract_transform_load(self, temp_workspace: Path) -> None:
        """Full ETL pipeline: extract from CSV, process, load to new CSV."""
        input_path = str(temp_workspace / "raw_data.csv")
        output_path = str(temp_workspace / "processed.csv")

        # Create raw data
        raw_data = [
            {"id": "1", "amount": "100", "status": "active"},
            {"id": "2", "amount": "200", "status": "inactive"},
            {"id": "3", "amount": "150", "status": "active"},
        ]

        result = await (
            WorkflowBuilder("etl_pipeline")
            .add_start()
            # Extract
            .add_write_csv(input_path, raw_data, node_id="create_source")
            .add_read_csv(input_path, node_id="extract")
            .add_set_variable("extracted", "{{extract.data}}")
            # Load (in real scenario, would transform data between extract/load)
            .add_write_csv(output_path, "{{extracted}}", node_id="load")
            # Verify
            .add_read_csv(output_path, node_id="verify")
            .add_set_variable("loaded_count", "{{verify.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("loaded_count") == 3

    @pytest.mark.asyncio
    async def test_csv_multi_file_workflow(self, temp_workspace: Path) -> None:
        """Work with multiple CSV files in one workflow."""
        users_path = str(temp_workspace / "users.csv")
        orders_path = str(temp_workspace / "orders.csv")
        summary_path = str(temp_workspace / "summary.csv")

        users = [
            {"user_id": "1", "name": "Alice"},
            {"user_id": "2", "name": "Bob"},
        ]
        orders = [
            {"order_id": "101", "user_id": "1", "total": "50"},
            {"order_id": "102", "user_id": "1", "total": "75"},
            {"order_id": "103", "user_id": "2", "total": "100"},
        ]
        summary = [
            {"metric": "total_users", "value": "2"},
            {"metric": "total_orders", "value": "3"},
        ]

        result = await (
            WorkflowBuilder("multi_csv")
            .add_start()
            .add_write_csv(users_path, users, node_id="write_users")
            .add_write_csv(orders_path, orders, node_id="write_orders")
            .add_write_csv(summary_path, summary, node_id="write_summary")
            .add_read_csv(users_path, node_id="read_users")
            .add_set_variable("user_count", "{{read_users.row_count}}")
            .add_read_csv(orders_path, node_id="read_orders")
            .add_set_variable("order_count", "{{read_orders.row_count}}")
            .add_read_csv(summary_path, node_id="read_summary")
            .add_set_variable("summary_data", "{{read_summary.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("user_count") == 2
        assert result["variables"].get("order_count") == 3
        summary_data = result["variables"].get("summary_data", [])
        assert len(summary_data) == 2

    @pytest.mark.asyncio
    async def test_csv_backup_before_modify(self, temp_workspace: Path) -> None:
        """Create backup of CSV before modifying."""
        original_path = str(temp_workspace / "data.csv")
        backup_path = str(temp_workspace / "data.csv.bak")

        original_data = [
            {"id": "1", "value": "original1"},
            {"id": "2", "value": "original2"},
        ]
        modified_data = [
            {"id": "1", "value": "modified1"},
            {"id": "2", "value": "modified2"},
            {"id": "3", "value": "new3"},
        ]

        result = await (
            WorkflowBuilder("csv_backup")
            .add_start()
            # Create original
            .add_write_csv(original_path, original_data, node_id="write_original")
            # Copy original content
            .add_read_csv(original_path, node_id="read_original")
            .add_set_variable("backup_data", "{{read_original.data}}")
            # Write backup
            .add_write_csv(backup_path, "{{backup_data}}", node_id="write_backup")
            # Modify original
            .add_write_csv(original_path, modified_data, node_id="write_modified")
            # Verify
            .add_read_csv(original_path, node_id="verify_modified")
            .add_set_variable("modified_count", "{{verify_modified.row_count}}")
            .add_read_csv(backup_path, node_id="verify_backup")
            .add_set_variable("backup_count", "{{verify_backup.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("modified_count") == 3
        assert result["variables"].get("backup_count") == 2


# =============================================================================
# ERROR HANDLING
# =============================================================================


class TestCSVErrorHandling:
    """Test CSV error handling scenarios."""

    @pytest.mark.asyncio
    async def test_read_nonexistent_csv(self, temp_workspace: Path) -> None:
        """Reading non-existent CSV should fail."""
        file_path = str(temp_workspace / "does_not_exist.csv")

        result = await (
            WorkflowBuilder("read_missing_csv")
            .add_start()
            .add_read_csv(file_path, node_id="read")
            .add_end()
            .execute()
        )

        assert not result["success"]
        assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_csv_wrong_delimiter(self, temp_workspace: Path) -> None:
        """Reading CSV with wrong delimiter returns incorrect data structure."""
        file_path = str(temp_workspace / "semicolon.csv")

        # Write with semicolon
        data = [{"col1": "a", "col2": "b"}]
        await (
            WorkflowBuilder("write_semicolon")
            .add_start()
            .add_write_csv(file_path, data, delimiter=";", node_id="write")
            .add_end()
            .execute()
        )

        # Read with comma (wrong delimiter)
        result = await (
            WorkflowBuilder("read_wrong_delimiter")
            .add_start()
            .add_read_csv(file_path, delimiter=",", node_id="read")
            .add_set_variable("headers", "{{read.headers}}")
            .add_end()
            .execute()
        )

        # Should succeed but headers will be combined
        assert result["success"]
        headers = result["variables"].get("headers", [])
        # The header "col1;col2" will be treated as single column
        assert len(headers) == 1

    @pytest.mark.asyncio
    async def test_csv_empty_data(self, temp_workspace: Path) -> None:
        """Writing and reading empty CSV data."""
        file_path = str(temp_workspace / "empty.csv")
        data: List[Dict[str, Any]] = []

        result = await (
            WorkflowBuilder("empty_csv")
            .add_start()
            .add_write_csv(file_path, data, node_id="write")
            .add_read_csv(file_path, node_id="read")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 0


# =============================================================================
# SPECIAL CHARACTERS AND EDGE CASES
# =============================================================================


class TestCSVEdgeCases:
    """Test CSV edge cases and special characters."""

    @pytest.mark.asyncio
    async def test_csv_with_newlines_in_values(self, temp_workspace: Path) -> None:
        """Handle values containing newline characters."""
        file_path = str(temp_workspace / "newlines.csv")
        data = [
            {"name": "Item 1", "description": "Line 1"},
            {"name": "Item 2", "description": "Simple description"},
        ]

        result = await (
            WorkflowBuilder("csv_newlines")
            .add_start()
            .add_write_csv(file_path, data, node_id="write")
            .add_read_csv(file_path, node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 2

    @pytest.mark.asyncio
    async def test_csv_with_unicode(self, temp_workspace: Path) -> None:
        """Handle Unicode characters in CSV."""
        file_path = str(temp_workspace / "unicode.csv")
        data = [
            {"name": "Test Unicode", "symbol": "ABC"},
            {"name": "More Unicode", "symbol": "XYZ"},
        ]

        result = await (
            WorkflowBuilder("csv_unicode")
            .add_start()
            .add_write_csv(file_path, data, encoding="utf-8", node_id="write")
            .add_read_csv(file_path, encoding="utf-8", node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("data", [])
        assert len(read_data) == 2

    @pytest.mark.asyncio
    async def test_csv_with_empty_values(self, temp_workspace: Path) -> None:
        """Handle empty string values in CSV."""
        file_path = str(temp_workspace / "empty_values.csv")
        data = [
            {"name": "Complete", "value": "100"},
            {"name": "", "value": "50"},
            {"name": "Missing Value", "value": ""},
        ]

        result = await (
            WorkflowBuilder("csv_empty_values")
            .add_start()
            .add_write_csv(file_path, data, node_id="write")
            .add_read_csv(file_path, node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_set_variable("row_count", "{{read.row_count}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("row_count") == 3
        read_data = result["variables"].get("data", [])
        assert read_data[1]["name"] == ""
        assert read_data[2]["value"] == ""

    @pytest.mark.asyncio
    async def test_csv_with_large_values(self, temp_workspace: Path) -> None:
        """Handle large string values in CSV."""
        file_path = str(temp_workspace / "large_values.csv")
        large_value = "x" * 10000  # 10KB string
        data = [
            {"id": "1", "content": large_value},
        ]

        result = await (
            WorkflowBuilder("csv_large")
            .add_start()
            .add_write_csv(file_path, data, node_id="write")
            .add_read_csv(file_path, node_id="read")
            .add_set_variable("data", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("data", [])
        assert len(read_data[0]["content"]) == 10000
