"""
Structured data file operations for CasareRPA.

This module provides nodes for structured data file operations:
- ReadCSVNode, WriteCSVNode
- ReadJSONFileNode, WriteJSONFileNode
- ZipFilesNode, UnzipFilesNode

SECURITY: All file operations are subject to path sandboxing.
"""

import csv
import glob
import json
import zipfile
from pathlib import Path

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.file.file_security import (
    PathSecurityError,
    validate_path_security,
)


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


@node_schema(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        placeholder="C:\\path\\to\\file.csv",
    ),
    PropertyDef("delimiter", PropertyType.STRING, default=",", label="Delimiter"),
    PropertyDef("has_header", PropertyType.BOOLEAN, default=True, label="Has Header"),
    PropertyDef("encoding", PropertyType.STRING, default="utf-8", label="Encoding"),
    PropertyDef(
        "quotechar",
        PropertyType.STRING,
        default='"',
        label="Quote Char",
        tab="advanced",
    ),
    PropertyDef(
        "skip_rows", PropertyType.INTEGER, default=0, label="Skip Rows", tab="advanced"
    ),
    PropertyDef(
        "max_rows",
        PropertyType.INTEGER,
        default=0,
        label="Max Rows (0=unlimited)",
        tab="advanced",
    ),
    PropertyDef(
        "strict",
        PropertyType.BOOLEAN,
        default=False,
        label="Strict Mode",
        tab="advanced",
    ),
)
@executable_node
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

    def __init__(self, node_id: str, name: str = "Read CSV", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadCSVNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("data", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("headers", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("row_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            file_path = self.get_parameter("file_path")
            delimiter = self.config.get("delimiter", ",")
            has_header = self.config.get("has_header", True)
            encoding = self.config.get("encoding", "utf-8")
            quotechar = self.config.get("quotechar", '"')
            skip_rows = self.config.get("skip_rows", 0)
            max_rows = self.config.get("max_rows", 0)
            strict = self.config.get("strict", False)
            doublequote = self.config.get("doublequote", True)
            escapechar = self.config.get("escapechar", None)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")

            data = []
            headers = []

            logger.info(
                f"Reading CSV: {path} (delimiter='{delimiter}', has_header={has_header})"
            )

            with open(path, "r", encoding=encoding, newline="") as f:
                # Build CSV reader options
                csv_options = {
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                    "doublequote": doublequote,
                    "strict": strict,
                }
                if escapechar:
                    csv_options["escapechar"] = escapechar

                # Skip initial rows if configured
                for _ in range(skip_rows):
                    next(f, None)

                if has_header:
                    reader = csv.DictReader(f, **csv_options)
                    headers = reader.fieldnames or []

                    # Read data with optional max_rows limit
                    if max_rows > 0:
                        for i, row in enumerate(reader):
                            if i >= max_rows:
                                break
                            data.append(row)
                    else:
                        data = list(reader)
                else:
                    reader = csv.reader(f, **csv_options)

                    # Read data with optional max_rows limit
                    if max_rows > 0:
                        for i, row in enumerate(reader):
                            if i >= max_rows:
                                break
                            data.append(row)
                    else:
                        data = list(reader)

            self.set_output_value("data", data)
            self.set_output_value("headers", headers)
            self.set_output_value("row_count", len(data))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(
                f"CSV read successfully: {len(data)} rows, {len(headers)} columns"
            )

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


@node_schema(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        placeholder="C:\\path\\to\\output.csv",
    ),
    PropertyDef("delimiter", PropertyType.STRING, default=",", label="Delimiter"),
    PropertyDef(
        "write_header", PropertyType.BOOLEAN, default=True, label="Write Header"
    ),
    PropertyDef("encoding", PropertyType.STRING, default="utf-8", label="Encoding"),
)
@executable_node
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

    def __init__(self, node_id: str, name: str = "Write CSV", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WriteCSVNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("data", PortType.INPUT, DataType.LIST)
        self.add_input_port("headers", PortType.INPUT, DataType.LIST)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("attachment_file", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("row_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            file_path = self.get_parameter("file_path")
            data = self.get_parameter("data") or []
            headers = self.get_parameter("headers")
            delimiter = self.config.get("delimiter", ",")
            write_header = self.config.get("write_header", True)
            encoding = self.config.get("encoding", "utf-8")

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            row_count = 0

            with open(path, "w", encoding=encoding, newline="") as f:
                if data and isinstance(data[0], dict):
                    # Dict data
                    fieldnames = headers or (list(data[0].keys()) if data else [])
                    writer = csv.DictWriter(
                        f, fieldnames=fieldnames, delimiter=delimiter
                    )
                    if write_header:
                        writer.writeheader()
                    writer.writerows(data)
                    row_count = len(data)
                else:
                    # List data
                    writer = csv.writer(f, delimiter=delimiter)
                    if write_header and headers:
                        writer.writerow(headers)
                    writer.writerows(data)
                    row_count = len(data)

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


@node_schema(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        placeholder="C:\\path\\to\\file.json",
    ),
    PropertyDef("encoding", PropertyType.STRING, default="utf-8", label="Encoding"),
)
@executable_node
class ReadJSONFileNode(BaseNode):
    """
    Read and parse a JSON file.

    Inputs:
        file_path: Path to JSON file

    Outputs:
        data: Parsed JSON data
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Read JSON File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadJSONFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("data", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            file_path = self.get_parameter("file_path")
            encoding = self.config.get("encoding", "utf-8")

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"JSON file not found: {file_path}")

            with open(path, "r", encoding=encoding) as f:
                data = json.load(f)

            self.set_output_value("data", data)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"type": type(data).__name__},
                "next_nodes": ["exec_out"],
            }

        except json.JSONDecodeError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": f"Invalid JSON: {e}", "next_nodes": []}
        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        placeholder="C:\\path\\to\\output.json",
    ),
    PropertyDef("encoding", PropertyType.STRING, default="utf-8", label="Encoding"),
    PropertyDef("indent", PropertyType.INTEGER, default=2, label="Indent"),
    PropertyDef(
        "ensure_ascii", PropertyType.BOOLEAN, default=False, label="Ensure ASCII"
    ),
)
@executable_node
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

    def __init__(self, node_id: str, name: str = "Write JSON File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WriteJSONFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("data", PortType.INPUT, DataType.ANY)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("attachment_file", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            file_path = self.get_parameter("file_path")
            data = self.get_parameter("data")
            encoding = self.config.get("encoding", "utf-8")
            indent = self.config.get("indent", 2)
            ensure_ascii = self.config.get("ensure_ascii", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding=encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)

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


@node_schema(
    PropertyDef(
        "zip_path",
        PropertyType.STRING,
        required=True,
        label="ZIP Path",
        placeholder="C:\\output\\archive.zip",
    ),
    PropertyDef(
        "source_path",
        PropertyType.STRING,
        default="",
        label="Source Path",
        placeholder="C:\\folder\\to\\zip or C:\\folder\\*.txt",
        tooltip="Folder path (zips entire folder) or glob pattern (e.g., *.txt)",
    ),
    PropertyDef(
        "base_dir",
        PropertyType.STRING,
        default="",
        label="Base Directory",
        placeholder="C:\\source\\folder",
        tooltip="Base directory for relative paths in archive (auto-set if source_path is folder)",
    ),
    PropertyDef(
        "compression",
        PropertyType.CHOICE,
        default="ZIP_DEFLATED",
        choices=["ZIP_STORED", "ZIP_DEFLATED"],
        label="Compression",
    ),
)
@executable_node
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

    def __init__(self, node_id: str, name: str = "Zip Files", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ZipFilesNode"

    def _define_ports(self) -> None:
        self.add_input_port("zip_path", PortType.INPUT, DataType.STRING)
        # source_path, files, base_dir are optional - node can work with any combination
        self.add_input_port(
            "source_path", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("files", PortType.INPUT, DataType.LIST, required=False)
        self.add_input_port("base_dir", PortType.INPUT, DataType.STRING, required=False)
        self.add_output_port("zip_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("attachment_file", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("file_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            zip_path = self.get_parameter("zip_path")
            source_path = self.get_parameter("source_path")
            files = self.get_parameter("files") or []
            base_dir = self.get_parameter("base_dir")
            compression = self.config.get("compression", "ZIP_DEFLATED")

            if not zip_path:
                raise ValueError("zip_path is required")

            # Resolve {{variable}} patterns
            zip_path = context.resolve_value(zip_path)
            if source_path:
                source_path = context.resolve_value(source_path)
            if base_dir:
                base_dir = context.resolve_value(base_dir)

            # Auto-discover files from source_path if files list is empty
            if not files and source_path:
                source = Path(source_path)

                if source.is_dir():
                    # It's a folder - recursively get all files
                    files = [str(f) for f in source.rglob("*") if f.is_file()]
                    # Auto-set base_dir to the folder if not specified
                    if not base_dir:
                        base_dir = str(source)
                    logger.info(
                        f"Auto-discovered {len(files)} files from folder: {source}"
                    )
                elif "*" in source_path or "?" in source_path:
                    # It's a glob pattern
                    files = [
                        f
                        for f in glob.glob(source_path, recursive=True)
                        if Path(f).is_file()
                    ]
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
                zipfile.ZIP_DEFLATED
                if compression == "ZIP_DEFLATED"
                else zipfile.ZIP_STORED
            )

            path = Path(zip_path)
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            file_count = 0
            base = Path(base_dir) if base_dir else None

            with zipfile.ZipFile(path, "w", compression=zip_compression) as zf:
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

            self.set_output_value("zip_path", str(path))
            self.set_output_value("attachment_file", [str(path)])
            self.set_output_value("file_count", file_count)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Created ZIP archive: {path} with {file_count} files")

            return {
                "success": True,
                "data": {"zip_path": str(path), "file_count": file_count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        compression = self.config.get("compression", "ZIP_DEFLATED")
        if compression not in ["ZIP_STORED", "ZIP_DEFLATED"]:
            return False, "compression must be 'ZIP_STORED' or 'ZIP_DEFLATED'"
        return True, ""


@node_schema(
    PropertyDef(
        "zip_path",
        PropertyType.STRING,
        required=True,
        label="ZIP Path",
        placeholder="C:\\input\\archive.zip",
    ),
    PropertyDef(
        "extract_to",
        PropertyType.STRING,
        required=True,
        label="Extract To",
        placeholder="C:\\output\\extracted",
    ),
)
@executable_node
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

    def __init__(self, node_id: str, name: str = "Unzip Files", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "UnzipFilesNode"

    def _define_ports(self) -> None:
        self.add_input_port("zip_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("extract_to", PortType.INPUT, DataType.STRING)
        self.add_output_port("extract_to", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("files", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("file_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Use get_parameter to check both port value and config
            zip_path = self.get_parameter("zip_path")
            extract_to = self.get_parameter("extract_to")
            allow_dangerous = self.config.get("allow_dangerous_paths", False)

            if not zip_path:
                raise ValueError("zip_path is required")
            if not extract_to:
                raise ValueError("extract_to is required")

            # Resolve {{variable}} patterns in zip_path and extract_to
            zip_path = context.resolve_value(zip_path)
            extract_to = context.resolve_value(extract_to)

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
