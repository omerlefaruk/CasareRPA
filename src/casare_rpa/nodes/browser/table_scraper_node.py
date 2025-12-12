"""
Table Scraper Node - Extract structured data from HTML tables.

Provides functionality to scrape HTML table content and convert it
to various formats (list of dicts, list of lists, CSV string).

All nodes extend BrowserBaseNode for consistent patterns:
- Page access from context
- Selector normalization
- Retry logic
- Screenshot on failure
"""

import csv
import io
from typing import Any, Dict, List, Union

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    BROWSER_TIMEOUT,
)
from casare_rpa.config import DEFAULT_NODE_TIMEOUT
from casare_rpa.utils import safe_int
from casare_rpa.utils.resilience import retry_operation


# JavaScript code for table extraction - kept separate for readability
TABLE_EXTRACTION_JS = """
(params) => {
    const table = document.querySelector(params.selector);
    if (!table) {
        return {error: "Table not found with selector: " + params.selector};
    }

    const rows = Array.from(table.querySelectorAll("tr"));
    let headers = [];
    const data = [];
    let headerRowIndex = -1;

    // Find header row (first row with th elements or first row)
    for (let i = 0; i < rows.length; i++) {
        const thElements = rows[i].querySelectorAll("th");
        if (thElements.length > 0) {
            headers = Array.from(thElements).map(th => th.innerText.trim());
            headerRowIndex = i;
            break;
        }
    }

    // If no th elements found, use first row as headers if include_headers is true
    if (headers.length === 0 && params.includeHeaders && rows.length > 0) {
        const firstRowCells = rows[0].querySelectorAll("td");
        if (firstRowCells.length > 0) {
            headers = Array.from(firstRowCells).map(td => td.innerText.trim());
            headerRowIndex = 0;
        }
    }

    // Extract data rows
    let rowsProcessed = 0;
    let rowsSkipped = 0;

    for (let i = 0; i < rows.length; i++) {
        // Skip header row
        if (i === headerRowIndex) continue;

        // Skip specified number of rows
        if (rowsSkipped < params.skipRows) {
            rowsSkipped++;
            continue;
        }

        // Check max rows limit
        if (params.maxRows > 0 && rowsProcessed >= params.maxRows) break;

        const cells = rows[i].querySelectorAll("td");
        if (cells.length === 0) continue;

        const rowData = Array.from(cells).map(cell => cell.innerText.trim());

        // Skip empty rows
        if (rowData.every(cell => cell === "")) continue;

        data.push(rowData);
        rowsProcessed++;
    }

    return {
        headers: headers,
        data: data,
        rowCount: data.length,
        columnCount: headers.length || (data.length > 0 ? data[0].length : 0)
    };
}
"""


@node(category="browser")
@properties(
    PropertyDef(
        "table_selector",
        PropertyType.SELECTOR,
        default="table",
        required=True,
        label="Table Selector",
        tooltip="CSS or XPath selector for the table element",
        placeholder="table, .data-table, #results-table",
    ),
    PropertyDef(
        "include_headers",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Headers",
        tooltip="Include table headers in output (for list_of_dicts) or as first row (for list_of_lists)",
    ),
    PropertyDef(
        "output_format",
        PropertyType.CHOICE,
        default="list_of_dicts",
        choices=["list_of_dicts", "list_of_lists", "csv_string"],
        label="Output Format",
        tooltip="Format for output data: list_of_dicts (rows as dictionaries), list_of_lists (rows as arrays), csv_string (CSV text)",
    ),
    PropertyDef(
        "skip_rows",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Skip Rows",
        tooltip="Number of data rows to skip after the header",
        tab="advanced",
    ),
    PropertyDef(
        "max_rows",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Max Rows (0=all)",
        tooltip="Maximum number of rows to extract (0 = unlimited)",
        tab="advanced",
    ),
    PropertyDef(
        "output_variable",
        PropertyType.STRING,
        default="table_data",
        label="Output Variable",
        tooltip="Name of variable to store the extracted data",
    ),
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
)
class TableScraperNode(BrowserBaseNode):
    """
    Table Scraper Node - extracts structured data from HTML tables.

    Finds a table element and extracts its rows and cells into
    structured data formats.

    Config (via @properties):
        table_selector: CSS or XPath selector for the table
        include_headers: Whether to include headers in output
        output_format: Output format (list_of_dicts, list_of_lists, csv_string)
        skip_rows: Number of data rows to skip
        max_rows: Maximum rows to extract (0 = all)
        output_variable: Variable name for result
        timeout: Timeout in milliseconds
        retry_count: Retry attempts
        retry_interval: Delay between retries
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for screenshot

    Inputs:
        page: Browser page instance
        table_selector: Table selector override

    Outputs:
        data: Extracted table data
        row_count: Number of rows extracted
        headers: Table headers (if found)
    """

    # @category: browser
    # @requires: none
    # @ports: table_selector -> data, row_count, headers

    def __init__(
        self,
        node_id: str,
        name: str = "Table Scraper",
        **kwargs: Any,
    ) -> None:
        """Initialize table scraper node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "TableScraperNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_input_port()
        self.add_input_port("table_selector", DataType.STRING, required=False)
        self.add_output_port("data", DataType.ANY)
        self.add_output_port("row_count", DataType.INTEGER)
        self.add_output_port("headers", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute table extraction."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)

            # Get selector - from input port or config
            selector = self.get_input_value("table_selector")
            if not selector:
                selector = self.get_parameter("table_selector", "table")
            selector = context.resolve_value(selector)

            # Get extraction parameters
            include_headers = self.get_parameter("include_headers", True)
            output_format = self.get_parameter("output_format", "list_of_dicts")
            skip_rows = safe_int(self.get_parameter("skip_rows", 0), 0)
            max_rows = safe_int(self.get_parameter("max_rows", 0), 0)
            output_variable = self.get_parameter("output_variable", "table_data")
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )

            logger.info(f"Extracting table data from: {selector}")

            async def perform_extraction() -> Dict[str, Any]:
                """Execute table extraction via JavaScript."""
                # Wait for table element to be present
                await page.wait_for_selector(
                    selector, timeout=timeout, state="attached"
                )

                # Extract table data via JavaScript
                raw_data = await page.evaluate(
                    TABLE_EXTRACTION_JS,
                    {
                        "selector": selector,
                        "includeHeaders": include_headers,
                        "skipRows": skip_rows,
                        "maxRows": max_rows,
                    },
                )

                if "error" in raw_data:
                    raise ValueError(raw_data["error"])

                return raw_data

            result = await retry_operation(
                perform_extraction,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name=f"extract table from {selector}",
            )

            if result.success:
                raw_data = result.value
                headers = raw_data.get("headers", [])
                rows = raw_data.get("data", [])
                row_count = raw_data.get("rowCount", 0)
                column_count = raw_data.get("columnCount", 0)

                # Format output according to requested format
                formatted_data = self._format_output(
                    headers, rows, output_format, include_headers
                )

                # Store in context variable
                context.set_variable(output_variable, formatted_data)

                # Set output port values
                self.set_output_value("data", formatted_data)
                self.set_output_value("row_count", row_count)
                self.set_output_value("headers", headers)

                logger.info(
                    f"Extracted {row_count} rows, {column_count} columns from table"
                )

                return self.success_result(
                    {
                        "row_count": row_count,
                        "column_count": column_count,
                        "headers": headers,
                        "output_format": output_format,
                        "variable": output_variable,
                        "attempts": result.attempts,
                    }
                )

            await self.screenshot_on_failure(page, "table_scraper_fail")
            raise result.last_error or RuntimeError("Table extraction failed")

        except Exception as e:
            logger.error(f"Table scraping failed: {e}")
            return self.error_result(e)

    def _format_output(
        self,
        headers: List[str],
        rows: List[List[str]],
        output_format: str,
        include_headers: bool,
    ) -> Union[List[Dict[str, str]], List[List[str]], str]:
        """
        Format extracted table data according to requested format.

        Args:
            headers: List of column headers
            rows: List of row data (each row is a list of cell values)
            output_format: One of "list_of_dicts", "list_of_lists", "csv_string"
            include_headers: Whether to include headers in output

        Returns:
            Formatted data in requested format
        """
        if output_format == "list_of_dicts":
            # Convert rows to list of dictionaries using headers as keys
            if headers:
                return [dict(zip(headers, row)) for row in rows]
            else:
                # If no headers, use column indices as keys
                return [
                    {f"col_{i}": cell for i, cell in enumerate(row)} for row in rows
                ]

        elif output_format == "list_of_lists":
            # Return as list of lists, optionally with headers as first row
            if include_headers and headers:
                return [headers] + rows
            return rows

        elif output_format == "csv_string":
            # Convert to CSV string
            output = io.StringIO()
            writer = csv.writer(output)

            if include_headers and headers:
                writer.writerow(headers)

            writer.writerows(rows)
            return output.getvalue()

        else:
            # Default to list of lists
            logger.warning(
                f"Unknown output format '{output_format}', using list_of_lists"
            )
            return rows

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        table_selector = self.config.get("table_selector", "")
        if not table_selector:
            return False, "Table selector is required"

        output_format = self.config.get("output_format", "list_of_dicts")
        valid_formats = ["list_of_dicts", "list_of_lists", "csv_string"]
        if output_format not in valid_formats:
            return False, f"Invalid output format. Must be one of: {valid_formats}"

        return True, ""
