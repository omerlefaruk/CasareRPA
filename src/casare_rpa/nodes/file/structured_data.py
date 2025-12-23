"""
Structured data file operations for CasareRPA.

This module provides nodes for structured data file operations:
- ReadCSVNode, WriteCSVNode
- ReadJSONFileNode, WriteJSONFileNode
- ZipFilesNode, UnzipFilesNode

SECURITY: All file operations are subject to path sandboxing.
NOTE: File I/O uses AsyncFileOperations for non-blocking operations.
"""

import glob
import os
import zipfile
from pathlib import Path

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.file.file_security import (
    PathSecurityError,
    validate_path_security,
)
from casare_rpa.nodes.file.property_constants import (
    CSV_DELIMITER,
    CSV_HAS_HEADER,
    CSV_MAX_ROWS,
    CSV_QUOTECHAR,
    CSV_SKIP_ROWS,
    CSV_STRICT,
    CSV_WRITE_HEADER,
    FILE_ENCODING,
    FILE_PATH_INPUT,
    FILE_PATH_OUTPUT,
    JSON_ENSURE_ASCII,
    JSON_INDENT,
    ZIP_BASE_DIR,
    ZIP_COMPRESSION,
    ZIP_EXTRACT_TO,
    ZIP_PATH,
    ZIP_SOURCE_PATH,
)
from casare_rpa.utils.async_file_ops import AsyncFileOperations


def validate_zip_entry(zip_path: str, entry_name: str) -> Path:
    """Validate a zip entry name to prevent Zip Slip attacks.

    SECURITY: Prevents path traversal via malicious zip entries.

    Args:
        zip_path: The path where files will be extracted
        entry_name: The name of the entry in the zip file

    Returns:
        The validated target path

    Raises:
        PathSecurityError: If the entry would escape the target directory
    """
    target_dir = Path(zip_path).resolve()
    target_path = (target_dir / entry_name).resolve()

    # SECURITY: Ensure the target path is within the target directory
    if not str(target_path).startswith(str(target_dir)):
        raise PathSecurityError(
            f"Zip Slip attack detected! Entry '{entry_name}' would extract "
            f"outside the target directory. This is a security vulnerability."
        )

    return target_path


@properties(
    FILE_PATH_INPUT,
    CSV_DELIMITER,
    CSV_HAS_HEADER,
    FILE_ENCODING,
    CSV_QUOTECHAR,
    CSV_SKIP_ROWS,
    CSV_MAX_ROWS,
    CSV_STRICT,
)
@node(category="file")
class ReadCSVNode(BaseNode):
    """
    Read and parse a CSV file.

    Inputs:
        file_path: Path to CSV file

    Outputs:
        data: List of rows (dicts if has_header, else lists)
        headers: Column headers (if has_header)
        row_count: Number of rows
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path -> data, headers, row_count, success

    def __init__(self, node_id: str, name: str = "Read CSV", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadCSVNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING, required=False)
        self.add_output_port("data", DataType.LIST)
        self.add_output_port("headers", DataType.LIST)
        self.add_output_port("row_count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            file_path = self.get_parameter("file_path")
            delimiter = self.get_parameter("delimiter", ",")
            has_header = self.get_parameter("has_header", True)
            encoding = self.get_parameter("encoding", "utf-8")
            quotechar = self.get_parameter("quotechar", '"')
            skip_rows = self.get_parameter("skip_rows", 0)
            max_rows = self.get_parameter("max_rows", 0)
            strict = self.get_parameter("strict", False)
            self.get_parameter("doublequote", True)
            self.get_parameter("escapechar", None)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables in file_path
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path before access
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)
            path = validate_path_security(file_path, "read", allow_dangerous)

            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")

            data = []
            headers = []

            logger.info(f"Reading CSV: {path} (delimiter='{delimiter}', has_header={has_header})")

            # Use async file operations for non-blocking I/O
            data, headers = await AsyncFileOperations.read_csv(
                path,
                encoding=encoding,
                delimiter=delimiter,
                has_header=has_header,
                skip_rows=skip_rows,
                max_rows=max_rows,
                quotechar=quotechar,
                strict=strict,
            )

            self.set_output_value("data", data)
            self.set_output_value("headers", headers)
            self.set_output_value("row_count", len(data))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"CSV read successfully: {len(data)} rows, {len(headers)} columns")

            return {
                "success": True,
                "data": {"row_count": len(data), "headers": headers},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    FILE_PATH_OUTPUT,
    CSV_DELIMITER,
    CSV_WRITE_HEADER,
    FILE_ENCODING,
)
@node(category="file")
class WriteCSVNode(BaseNode):
    """
    Write data to a CSV file.

    Inputs:
        file_path: Path to write
        data: List of rows (dicts or lists)
        headers: Column headers (optional if data is dicts)

    Outputs:
        file_path: Written file path
        row_count: Number of rows written
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path, data, headers -> file_path, attachment_file, row_count, success

    def __init__(self, node_id: str, name: str = "Write CSV", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WriteCSVNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING, required=False)
        self.add_input_port("data", DataType.LIST, required=False)
        self.add_input_port("headers", DataType.LIST, required=False)
        self.add_output_port("file_path", DataType.STRING)
        self.add_output_port("attachment_file", DataType.LIST)
        self.add_output_port("row_count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            file_path = self.get_parameter("file_path")
            data = self.get_parameter("data") or []
            headers = self.get_parameter("headers")
            delimiter = self.get_parameter("delimiter", ",")
            write_header = self.get_parameter("write_header", True)
            encoding = self.get_parameter("encoding", "utf-8")

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables
            file_path = os.path.expandvars(file_path)
            data = data or []
            headers = headers if headers else None

            # SECURITY: Validate path before access
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)
            path = validate_path_security(file_path, "write", allow_dangerous)

            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Use async file operations for non-blocking I/O
            row_count = await AsyncFileOperations.write_csv(
                path,
                data,
                headers=headers,
                encoding=encoding,
                delimiter=delimiter,
                write_header=write_header,
                create_dirs=True,
            )

            self.set_output_value("file_path", str(path))
            self.set_output_value("attachment_file", [str(path)])
            self.set_output_value("row_count", row_count)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"file_path": str(path), "row_count": row_count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    FILE_PATH_INPUT,
    FILE_ENCODING,
)
@node(category="file")
class ReadJSONFileNode(BaseNode):
    """
    Read and parse a JSON file.

    Inputs:
        file_path: Path to JSON file

    Outputs:
        data: Parsed JSON data
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path -> data, success

    def __init__(self, node_id: str, name: str = "Read JSON File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadJSONFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING, required=False)
        self.add_output_port("data", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            file_path = self.get_parameter("file_path")
            encoding = self.get_parameter("encoding", "utf-8")

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables in file_path
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path before access
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)
            path = validate_path_security(file_path, "read", allow_dangerous)

            if not path.exists():
                raise FileNotFoundError(f"JSON file not found: {file_path}")

            # Use async file operations for non-blocking I/O
            data = await AsyncFileOperations.read_json(path, encoding=encoding)

            self.set_output_value("data", data)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"type": type(data).__name__},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            # Check for JSON decode error
            import json

            if isinstance(e, json.JSONDecodeError) or (
                hasattr(e, "__cause__") and isinstance(e.__cause__, json.JSONDecodeError)
            ):
                return {
                    "success": False,
                    "error": f"Invalid JSON: {e}",
                    "next_nodes": [],
                }
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    FILE_PATH_OUTPUT,
    FILE_ENCODING,
    JSON_INDENT,
    JSON_ENSURE_ASCII,
)
@node(category="file")
class WriteJSONFileNode(BaseNode):
    """
    Write data to a JSON file.

    Inputs:
        file_path: Path to write
        data: Data to serialize as JSON

    Outputs:
        file_path: Written file path
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path, data -> file_path, attachment_file, success

    def __init__(self, node_id: str, name: str = "Write JSON File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WriteJSONFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING, required=False)
        self.add_input_port("data", DataType.ANY, required=False)
        self.add_output_port("file_path", DataType.STRING)
        self.add_output_port("attachment_file", DataType.LIST)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            file_path = self.get_parameter("file_path")
            data = self.get_parameter("data")
            encoding = self.get_parameter("encoding", "utf-8")
            indent = self.get_parameter("indent", 2)
            ensure_ascii = self.get_parameter("ensure_ascii", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables in file_path and data
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path before access
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)
            path = validate_path_security(file_path, "write", allow_dangerous)

            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Use async file operations for non-blocking I/O
            await AsyncFileOperations.write_json(
                path,
                data,
                encoding=encoding,
                indent=indent,
                ensure_ascii=ensure_ascii,
                create_dirs=True,
            )

            self.set_output_value("file_path", str(path))
            self.set_output_value("attachment_file", [str(path)])
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"file_path": str(path)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    ZIP_PATH,
    ZIP_SOURCE_PATH,
    ZIP_BASE_DIR,
    ZIP_COMPRESSION,
)
@node(category="file")
class ZipFilesNode(BaseNode):
    """
    Create a ZIP archive from files.

    Supports three modes of operation:
    1. Folder mode: Set source_path to a folder path (e.g., C:\\myFolder)
       - Recursively zips all files in the folder
       - Preserves folder structure in archive

    2. Glob mode: Set source_path to a glob pattern (e.g., C:\\folder\\*.txt)
       - Zips all files matching the pattern
       - Supports recursive patterns (e.g., **/*.txt)

    3. File list mode: Connect a list of file paths to the 'files' input port
       - For programmatic file selection

    Inputs:
        zip_path: Path for the ZIP file to create
        source_path: Folder path or glob pattern (auto-discovers files)
        files: List of file paths to include (optional if source_path provided)
        base_dir: Base directory for relative paths (auto-set if source_path is folder)

    Outputs:
        zip_path: Created ZIP file path
        file_count: Number of files added
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: zip_path, source_path, files, base_dir -> zip_path, attachment_file, file_count, success

    def __init__(self, node_id: str, name: str = "Zip Files", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ZipFilesNode"

    def _define_ports(self) -> None:
        self.add_input_port("zip_path", DataType.STRING, required=False)
        # source_path, files, base_dir are optional - node can work with any combination
        self.add_input_port("source_path", DataType.STRING, required=False)
        self.add_input_port("files", DataType.LIST, required=False)
        self.add_input_port("base_dir", DataType.STRING, required=False)
        self.add_output_port("zip_path", DataType.STRING)
        self.add_output_port("attachment_file", DataType.LIST)
        self.add_output_port("file_count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            zip_path = self.get_parameter("zip_path")
            source_path = self.get_parameter("source_path")
            files = self.get_parameter("files") or []
            base_dir = self.get_parameter("base_dir")
            compression = self.get_parameter("compression", "ZIP_DEFLATED")

            if not zip_path:
                raise ValueError("zip_path is required")

            # Resolve {{variable}} patterns and environment variables
            zip_path = os.path.expandvars(zip_path)
            if source_path:
                source_path = os.path.expandvars(source_path)
            if base_dir:
                base_dir = os.path.expandvars(base_dir)

            # SECURITY: Validate output zip path before access
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)
            zip_validated_path = validate_path_security(zip_path, "write", allow_dangerous)

            # Auto-discover files from source_path if files list is empty
            if not files and source_path:
                source = Path(source_path)

                if source.is_dir():
                    # It's a folder - recursively get all files
                    files = [str(f) for f in source.rglob("*") if f.is_file()]
                    # Auto-set base_dir to the folder if not specified
                    if not base_dir:
                        base_dir = str(source)
                    logger.info(f"Auto-discovered {len(files)} files from folder: {source}")
                elif "*" in source_path or "?" in source_path:
                    # It's a glob pattern
                    files = [f for f in glob.glob(source_path, recursive=True) if Path(f).is_file()]
                    # For glob patterns, use parent of the pattern as base_dir if not specified
                    if not base_dir:
                        # Find the first non-glob part of the path
                        parts = Path(source_path).parts
                        non_glob_parts = []
                        for part in parts:
                            if "*" in part or "?" in part:
                                break
                            non_glob_parts.append(part)
                        if non_glob_parts:
                            base_dir = str(Path(*non_glob_parts))
                    logger.info(
                        f"Auto-discovered {len(files)} files from glob pattern: {source_path}"
                    )
                elif source.is_file():
                    # Single file
                    files = [str(source)]
                    logger.info(f"Using single file: {source}")
                else:
                    raise ValueError(f"source_path not found: {source_path}")

            if not files:
                raise ValueError(
                    "No files to zip. Provide either 'source_path' (folder or glob pattern) "
                    "or connect a 'files' list input."
                )

            zip_compression = (
                zipfile.ZIP_DEFLATED if compression == "ZIP_DEFLATED" else zipfile.ZIP_STORED
            )

            # Use the security-validated path
            if zip_validated_path.parent:
                zip_validated_path.parent.mkdir(parents=True, exist_ok=True)

            file_count = 0
            base = Path(base_dir) if base_dir else None

            with zipfile.ZipFile(zip_validated_path, "w", compression=zip_compression) as zf:
                for file_path in files:
                    fp = Path(file_path)
                    if not fp.exists():
                        continue

                    if base and fp.is_relative_to(base):
                        arcname = str(fp.relative_to(base))
                    else:
                        arcname = fp.name

                    zf.write(fp, arcname)
                    file_count += 1

            self.set_output_value("zip_path", str(zip_validated_path))
            self.set_output_value("attachment_file", [str(zip_validated_path)])
            self.set_output_value("file_count", file_count)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Created ZIP archive: {zip_validated_path} with {file_count} files")

            return {
                "success": True,
                "data": {"zip_path": str(zip_validated_path), "file_count": file_count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        compression = self.get_parameter("compression", "ZIP_DEFLATED")
        if compression not in ["ZIP_STORED", "ZIP_DEFLATED"]:
            return False, "compression must be 'ZIP_STORED' or 'ZIP_DEFLATED'"
        return True, ""


@properties(
    ZIP_PATH,
    ZIP_EXTRACT_TO,
)
@node(category="file")
class UnzipFilesNode(BaseNode):
    """
    Extract files from a ZIP archive.

    Inputs:
        zip_path: Path to ZIP file
        extract_to: Directory to extract to

    Outputs:
        extract_to: Extraction directory
        files: List of extracted file paths
        file_count: Number of files extracted
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: zip_path, extract_to -> extract_to, files, file_count, success

    def __init__(self, node_id: str, name: str = "Unzip Files", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "UnzipFilesNode"

    def _define_ports(self) -> None:
        self.add_input_port("zip_path", DataType.STRING, required=False)
        self.add_input_port("extract_to", DataType.STRING, required=False)
        self.add_output_port("extract_to", DataType.STRING)
        self.add_output_port("files", DataType.LIST)
        self.add_output_port("file_count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            zip_path = self.get_parameter("zip_path")
            extract_to = self.get_parameter("extract_to")
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not zip_path:
                raise ValueError("zip_path is required")
            if not extract_to:
                raise ValueError("extract_to is required")

            # Resolve {{variable}} patterns and environment variables in zip_path and extract_to
            zip_path = os.path.expandvars(zip_path)
            extract_to = os.path.expandvars(extract_to)

            # SECURITY: Validate paths
            zip_file = validate_path_security(zip_path, "read", allow_dangerous)
            dest = validate_path_security(extract_to, "write", allow_dangerous)

            if not zip_file.exists():
                raise FileNotFoundError(f"ZIP file not found: {zip_path}")

            dest.mkdir(parents=True, exist_ok=True)

            extracted_files = []

            with zipfile.ZipFile(zip_file, "r") as zf:
                # SECURITY: Do NOT use extractall() - vulnerable to Zip Slip!
                # Instead, validate each entry and extract manually
                for member in zf.namelist():
                    # SECURITY: Validate entry path to prevent Zip Slip
                    target_path = validate_zip_entry(str(dest), member)

                    # Extract the file safely
                    if member.endswith("/"):
                        # Directory entry
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        # File entry - ensure parent directory exists
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with (
                            zf.open(member) as source,
                            open(target_path, "wb") as target,
                        ):
                            target.write(source.read())

                    extracted_files.append(str(target_path))

            logger.info(f"Extracted {len(extracted_files)} files to {dest}")

            self.set_output_value("extract_to", str(dest))
            self.set_output_value("files", extracted_files)
            self.set_output_value("file_count", len(extracted_files))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"extract_to": str(dest), "file_count": len(extracted_files)},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in UnzipFilesNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
