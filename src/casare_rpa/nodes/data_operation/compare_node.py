"""
CasareRPA - Data Compare Node

Compares two datasets (lists of dicts) and reports differences.
Supports key-based matching and column-level comparison.
"""

from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


def _normalize_value(value: Any, case_sensitive: bool) -> Any:
    """Normalize value for comparison."""
    if isinstance(value, str) and not case_sensitive:
        return value.lower()
    return value


def _get_row_key(row: dict[str, Any], key_columns: list[str], case_sensitive: bool) -> tuple:
    """Extract composite key from row based on key columns."""
    key_values = []
    for col in key_columns:
        val = row.get(col)
        key_values.append(_normalize_value(val, case_sensitive))
    return tuple(key_values)


def _rows_equal(
    row_a: dict[str, Any],
    row_b: dict[str, Any],
    compare_all_columns: bool,
    key_columns: list[str],
    case_sensitive: bool,
) -> tuple[bool, list[str]]:
    """
    Compare two rows for equality.

    Returns:
        Tuple of (are_equal, list_of_different_columns)
    """
    if not compare_all_columns:
        return True, []

    different_columns = []
    all_keys = set(row_a.keys()) | set(row_b.keys())

    for key in all_keys:
        if key in key_columns:
            continue
        val_a = _normalize_value(row_a.get(key), case_sensitive)
        val_b = _normalize_value(row_b.get(key), case_sensitive)
        if val_a != val_b:
            different_columns.append(key)

    return len(different_columns) == 0, different_columns


@properties(
    PropertyDef(
        "key_columns",
        PropertyType.STRING,
        default="",
        label="Key Columns",
        tooltip="Comma-separated list of columns to use as keys for matching",
    ),
    PropertyDef(
        "compare_all_columns",
        PropertyType.BOOLEAN,
        default=True,
        label="Compare All Columns",
        tooltip="If true, compare all columns; if false, only detect presence by key",
    ),
    PropertyDef(
        "case_sensitive",
        PropertyType.BOOLEAN,
        default=True,
        label="Case Sensitive",
        tooltip="Case sensitivity for string comparison",
    ),
)
@node(category="data_operation")
class DataCompareNode(BaseNode):
    """
    Compare two datasets and report differences.

    Compares two lists of dicts (datasets A and B) and identifies:
    - Rows only in dataset A
    - Rows only in dataset B
    - Matched rows (optionally with column-level differences)
    """

    # @category: data
    # @requires: none
    # @ports: data_a, data_b, key_columns -> only_in_a, only_in_b, matched, diff_summary, has_differences

    def __init__(self, node_id: str, name: str = "Data Compare", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DataCompareNode"

    def _define_ports(self) -> None:
        # Input ports
        self.add_input_port("data_a", DataType.LIST, required=False)
        self.add_input_port("data_b", DataType.LIST, required=False)
        self.add_input_port("key_columns", DataType.STRING, required=False)

        # Output ports
        self.add_output_port("only_in_a", DataType.LIST)
        self.add_output_port("only_in_b", DataType.LIST)
        self.add_output_port("matched", DataType.LIST)
        self.add_output_port("diff_summary", DataType.DICT)
        self.add_output_port("has_differences", DataType.BOOLEAN)

    def _resolve_list_input(
        self, context: ExecutionContext, port_name: str, param_name: str
    ) -> list[dict[str, Any]]:
        """Resolve list input from port or parameter."""
        value = self.get_input_value(port_name)
        if value is not None:
            return value if isinstance(value, list) else []

        param = self.get_parameter(param_name, [])
        if isinstance(param, str) and param:
            var_name = param.strip()
            if var_name.startswith("{{") and var_name.endswith("}}"):
                var_name = var_name[2:-2].strip()
            resolved = context.get_variable(var_name)
            return resolved if isinstance(resolved, list) else []

        return param if isinstance(param, list) else []

    def _resolve_string_input(
        self,
        context: ExecutionContext,
        port_name: str,
        param_name: str,
        default: str = "",
    ) -> str:
        """Resolve string input from port or parameter."""
        value = self.get_input_value(port_name)
        if value is not None:
            return str(value)

        param = self.get_parameter(param_name, default)
        if isinstance(param, str) and param:
            var_name = param.strip()
            if var_name.startswith("{{") and var_name.endswith("}}"):
                var_name = var_name[2:-2].strip()
                resolved = context.get_variable(var_name)
                return str(resolved) if resolved is not None else default
            return param

        return str(param) if param else default

    def _resolve_bool_input(
        self, context: ExecutionContext, param_name: str, default: bool
    ) -> bool:
        """Resolve boolean input from parameter."""
        param = self.get_parameter(param_name, default)
        if isinstance(param, bool):
            return param
        if isinstance(param, str):
            var_name = param.strip()
            if var_name.startswith("{{") and var_name.endswith("}}"):
                var_name = var_name[2:-2].strip()
                resolved = context.get_variable(var_name)
                return bool(resolved) if resolved is not None else default
            return param.lower() in ("true", "1", "yes")
        return bool(param) if param is not None else default

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            # Resolve inputs
            data_a = self._resolve_list_input(context, "data_a", "data_a")
            data_b = self._resolve_list_input(context, "data_b", "data_b")
            key_columns_str = self._resolve_string_input(context, "key_columns", "key_columns", "")
            compare_all_columns = self._resolve_bool_input(context, "compare_all_columns", True)
            case_sensitive = self._resolve_bool_input(context, "case_sensitive", True)

            # Parse key columns
            key_columns = [col.strip() for col in key_columns_str.split(",") if col.strip()]

            # Validate inputs
            if not isinstance(data_a, list):
                raise ValueError("data_a must be a list")
            if not isinstance(data_b, list):
                raise ValueError("data_b must be a list")

            # Handle empty key columns - use entire row as key
            if not key_columns:
                logger.warning("No key columns specified, using row index for matching")

            # Build index for dataset B
            b_by_key: dict[tuple, list[dict[str, Any]]] = {}
            b_matched_indices: set[int] = set()

            for idx, row in enumerate(data_b):
                if not isinstance(row, dict):
                    continue
                if key_columns:
                    key = _get_row_key(row, key_columns, case_sensitive)
                else:
                    key = (idx,)
                if key not in b_by_key:
                    b_by_key[key] = []
                b_by_key[key].append((idx, row))

            # Compare datasets
            only_in_a: list[dict[str, Any]] = []
            matched: list[dict[str, Any]] = []
            modified_count = 0

            for idx_a, row_a in enumerate(data_a):
                if not isinstance(row_a, dict):
                    continue

                if key_columns:
                    key = _get_row_key(row_a, key_columns, case_sensitive)
                else:
                    key = (idx_a,)

                if key in b_by_key and b_by_key[key]:
                    # Found match - take first unmatched
                    idx_b, row_b = b_by_key[key][0]
                    b_matched_indices.add(idx_b)
                    b_by_key[key] = b_by_key[key][1:]

                    are_equal, diff_cols = _rows_equal(
                        row_a, row_b, compare_all_columns, key_columns, case_sensitive
                    )

                    match_record = {
                        "key": {col: row_a.get(col) for col in key_columns}
                        if key_columns
                        else {"index": idx_a},
                        "row_a": row_a,
                        "row_b": row_b,
                        "is_modified": not are_equal,
                        "different_columns": diff_cols,
                    }
                    matched.append(match_record)

                    if not are_equal:
                        modified_count += 1
                else:
                    only_in_a.append(row_a)

            # Collect unmatched rows from B
            only_in_b: list[dict[str, Any]] = []
            for idx, row in enumerate(data_b):
                if not isinstance(row, dict):
                    continue
                if idx not in b_matched_indices:
                    only_in_b.append(row)

            # Build summary
            diff_summary = {
                "added_count": len(only_in_b),
                "removed_count": len(only_in_a),
                "modified_count": modified_count,
                "matched_count": len(matched),
                "total_a": len([r for r in data_a if isinstance(r, dict)]),
                "total_b": len([r for r in data_b if isinstance(r, dict)]),
                "key_columns": key_columns,
            }

            has_differences = len(only_in_a) > 0 or len(only_in_b) > 0 or modified_count > 0

            # Set outputs
            self.set_output_value("only_in_a", only_in_a)
            self.set_output_value("only_in_b", only_in_b)
            self.set_output_value("matched", matched)
            self.set_output_value("diff_summary", diff_summary)
            self.set_output_value("has_differences", has_differences)

            logger.info(
                f"Data compare complete: {diff_summary['removed_count']} removed, "
                f"{diff_summary['added_count']} added, {diff_summary['modified_count']} modified"
            )

            return {
                "success": True,
                "data": {
                    "only_in_a": only_in_a,
                    "only_in_b": only_in_b,
                    "matched": matched,
                    "diff_summary": diff_summary,
                    "has_differences": has_differences,
                },
                "next_nodes": [],
            }

        except Exception as e:
            logger.error(f"Data compare failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


__all__ = ["DataCompareNode"]
