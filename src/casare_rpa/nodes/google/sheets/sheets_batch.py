"""
CasareRPA - Google Sheets Batch Operation Nodes

Nodes for efficient batch operations on spreadsheets:
- SheetsBatchUpdateNode: Multiple value updates in one request
- SheetsBatchGetNode: Read multiple ranges in one request
- SheetsBatchClearNode: Clear multiple ranges in one request
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from loguru import logger

from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_sheets_client import (
    GoogleSheetsClient,
)
from casare_rpa.nodes.google.google_base import SheetsBaseNode


class SheetsBatchUpdateNode(SheetsBaseNode):
    """
    Update multiple ranges in a single API call.

    This is more efficient than multiple single updates as it reduces
    API calls and quota usage.

    Inputs:
        - spreadsheet_id: Target spreadsheet ID
        - updates: List of update objects with structure:
            [
                {"range": "Sheet1!A1:B2", "values": [["A1", "B1"], ["A2", "B2"]]},
                {"range": "Sheet1!D1:E2", "values": [["D1", "E1"], ["D2", "E2"]]}
            ]
        - value_input_option: How to interpret input ("USER_ENTERED" or "RAW")

    Outputs:
        - success: Whether operation succeeded
        - result: Batch update response with updated cells info
        - total_updated_cells: Total number of cells updated
        - total_updated_rows: Total number of rows updated
    """

    # @category: google
    # @requires: none
    # @ports: updates, value_input_option -> total_updated_cells, total_updated_rows

    NODE_NAME = "Batch Update Values"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Batch Update Values", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("updates", PortType.INPUT, DataType.LIST, required=True)
        self.add_input_port(
            "value_input_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("total_updated_cells", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("total_updated_rows", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Execute batch update of multiple ranges."""
        spreadsheet_id = self._get_spreadsheet_id(context)
        if not spreadsheet_id:
            self._set_error_outputs("Spreadsheet ID is required")
            return {
                "success": False,
                "error": "Spreadsheet ID is required",
                "next_nodes": [],
            }

        # Get updates data
        updates = self.get_parameter("updates")
        if isinstance(updates, str):
            if hasattr(context, "resolve_value"):
                updates = context.resolve_value(updates)
            # Try to parse as JSON if string
            if isinstance(updates, str):
                try:
                    updates = json.loads(updates)
                except json.JSONDecodeError as e:
                    self._set_error_outputs(f"Invalid JSON in updates: {e}")
                    return {
                        "success": False,
                        "error": f"Invalid JSON in updates: {e}",
                        "next_nodes": [],
                    }

        if not updates or not isinstance(updates, list):
            self._set_error_outputs("Updates must be a non-empty list")
            return {
                "success": False,
                "error": "Updates must be a non-empty list",
                "next_nodes": [],
            }

        value_input_option = self.get_parameter("value_input_option", "USER_ENTERED")
        if hasattr(context, "resolve_value"):
            value_input_option = context.resolve_value(value_input_option)

        # Validate and transform updates format
        data: List[Dict[str, Any]] = []
        for update in updates:
            if not isinstance(update, dict):
                self._set_error_outputs(
                    "Each update must be an object with 'range' and 'values'"
                )
                return {
                    "success": False,
                    "error": "Each update must be an object with 'range' and 'values'",
                    "next_nodes": [],
                }

            range_notation = update.get("range")
            values = update.get("values")

            if not range_notation or values is None:
                self._set_error_outputs(
                    "Each update must have 'range' and 'values' keys"
                )
                return {
                    "success": False,
                    "error": "Each update must have 'range' and 'values' keys",
                    "next_nodes": [],
                }

            data.append({"range": range_notation, "values": values})

        # Execute batch update
        result = await client.batch_update_values(
            spreadsheet_id=spreadsheet_id,
            data=data,
            value_input_option=value_input_option,
        )

        # Extract statistics from response
        total_cells = result.get("totalUpdatedCells", 0)
        total_rows = result.get("totalUpdatedRows", 0)

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("total_updated_cells", total_cells)
        self.set_output_value("total_updated_rows", total_rows)
        self.set_output_value(
            "result",
            {
                "spreadsheet_id": result.get("spreadsheetId", spreadsheet_id),
                "total_updated_cells": total_cells,
                "total_updated_rows": total_rows,
                "total_updated_columns": result.get("totalUpdatedColumns", 0),
                "total_updated_sheets": result.get("totalUpdatedSheets", 0),
                "responses": result.get("responses", []),
            },
        )

        logger.info(
            f"Batch updated {len(data)} ranges in {spreadsheet_id}: "
            f"{total_cells} cells, {total_rows} rows"
        )

        return {
            "success": True,
            "data": {
                "ranges_updated": len(data),
                "total_cells": total_cells,
                "total_rows": total_rows,
            },
            "next_nodes": ["exec_out"],
        }


class SheetsBatchGetNode(SheetsBaseNode):
    """
    Read multiple ranges in a single API call.

    This is more efficient than multiple single reads as it reduces
    API calls and quota usage.

    Inputs:
        - spreadsheet_id: Target spreadsheet ID
        - ranges: List of A1 notation ranges to read
            ["Sheet1!A1:B10", "Sheet1!D1:E10", "Sheet2!A1:C5"]
        - value_render_option: How to render values
            ("FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA")

    Outputs:
        - success: Whether operation succeeded
        - result: Dictionary mapping range to values
        - values: List of value arrays (in order of ranges)
        - ranges_count: Number of ranges read
    """

    # @category: google
    # @requires: none
    # @ports: ranges, value_render_option -> values, ranges_count

    NODE_NAME = "Batch Get Values"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Batch Get Values", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("ranges", PortType.INPUT, DataType.LIST, required=True)
        self.add_input_port(
            "value_render_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("values", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("ranges_count", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Execute batch read of multiple ranges."""
        spreadsheet_id = self._get_spreadsheet_id(context)
        if not spreadsheet_id:
            self._set_error_outputs("Spreadsheet ID is required")
            return {
                "success": False,
                "error": "Spreadsheet ID is required",
                "next_nodes": [],
            }

        # Get ranges
        ranges = self.get_parameter("ranges")
        if isinstance(ranges, str):
            if hasattr(context, "resolve_value"):
                ranges = context.resolve_value(ranges)
            # Try to parse as JSON if string
            if isinstance(ranges, str):
                try:
                    ranges = json.loads(ranges)
                except json.JSONDecodeError as e:
                    self._set_error_outputs(f"Invalid JSON in ranges: {e}")
                    return {
                        "success": False,
                        "error": f"Invalid JSON in ranges: {e}",
                        "next_nodes": [],
                    }

        if not ranges or not isinstance(ranges, list):
            self._set_error_outputs("Ranges must be a non-empty list")
            return {
                "success": False,
                "error": "Ranges must be a non-empty list",
                "next_nodes": [],
            }

        value_render_option = self.get_parameter(
            "value_render_option", "FORMATTED_VALUE"
        )
        if hasattr(context, "resolve_value"):
            value_render_option = context.resolve_value(value_render_option)

        # Execute batch get
        result = await client.batch_get_values(
            spreadsheet_id=spreadsheet_id,
            ranges=ranges,
            value_render_option=value_render_option,
        )

        # Convert to ordered list of values matching input ranges
        values_list = [result.get(r, []) for r in ranges]

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("values", values_list)
        self.set_output_value("ranges_count", len(ranges))
        self.set_output_value("result", result)

        logger.info(f"Batch read {len(ranges)} ranges from {spreadsheet_id}")

        return {
            "success": True,
            "data": {"ranges_count": len(ranges), "ranges": ranges},
            "next_nodes": ["exec_out"],
        }


class SheetsBatchClearNode(SheetsBaseNode):
    """
    Clear multiple ranges in a single API call.

    This is more efficient than multiple single clears as it reduces
    API calls and quota usage.

    Inputs:
        - spreadsheet_id: Target spreadsheet ID
        - ranges: List of A1 notation ranges to clear
            ["Sheet1!A1:B10", "Sheet1!D1:E10", "Sheet2!A1:C5"]

    Outputs:
        - success: Whether operation succeeded
        - result: Batch clear response
        - cleared_ranges: List of ranges that were cleared
    """

    # @category: google
    # @requires: none
    # @ports: ranges -> cleared_ranges

    NODE_NAME = "Batch Clear Values"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Batch Clear Values", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("ranges", PortType.INPUT, DataType.LIST, required=True)

        self._define_common_output_ports()
        self.add_output_port("cleared_ranges", PortType.OUTPUT, DataType.LIST)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Execute batch clear of multiple ranges."""
        spreadsheet_id = self._get_spreadsheet_id(context)
        if not spreadsheet_id:
            self._set_error_outputs("Spreadsheet ID is required")
            return {
                "success": False,
                "error": "Spreadsheet ID is required",
                "next_nodes": [],
            }

        # Get ranges
        ranges = self.get_parameter("ranges")
        if isinstance(ranges, str):
            if hasattr(context, "resolve_value"):
                ranges = context.resolve_value(ranges)
            # Try to parse as JSON if string
            if isinstance(ranges, str):
                try:
                    ranges = json.loads(ranges)
                except json.JSONDecodeError as e:
                    self._set_error_outputs(f"Invalid JSON in ranges: {e}")
                    return {
                        "success": False,
                        "error": f"Invalid JSON in ranges: {e}",
                        "next_nodes": [],
                    }

        if not ranges or not isinstance(ranges, list):
            self._set_error_outputs("Ranges must be a non-empty list")
            return {
                "success": False,
                "error": "Ranges must be a non-empty list",
                "next_nodes": [],
            }

        # Execute batch clear
        result = await client.batch_clear_values(
            spreadsheet_id=spreadsheet_id,
            ranges=ranges,
        )

        # Extract cleared ranges from response
        cleared_ranges = result.get("clearedRanges", ranges)

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("cleared_ranges", cleared_ranges)
        self.set_output_value(
            "result",
            {
                "spreadsheet_id": result.get("spreadsheetId", spreadsheet_id),
                "cleared_ranges": cleared_ranges,
            },
        )

        logger.info(f"Batch cleared {len(ranges)} ranges from {spreadsheet_id}")

        return {
            "success": True,
            "data": {"cleared_count": len(ranges), "ranges": cleared_ranges},
            "next_nodes": ["exec_out"],
        }


__all__ = [
    "SheetsBatchUpdateNode",
    "SheetsBatchGetNode",
    "SheetsBatchClearNode",
]
