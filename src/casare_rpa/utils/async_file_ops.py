"""
Async File Operations for CasareRPA.

Provides non-blocking file I/O using aiofiles with fallback to asyncio.to_thread.
All file operations are async to avoid blocking the event loop.

SECURITY: All path validation must be done by caller before using these functions.
"""

import asyncio
import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger

# Lazy import aiofiles - fallback to asyncio.to_thread if unavailable
_aiofiles_available: bool | None = None


def _check_aiofiles() -> bool:
    """Check if aiofiles is available."""
    global _aiofiles_available
    if _aiofiles_available is None:
        try:
            import aiofiles  # noqa: F401

            _aiofiles_available = True
        except ImportError:
            _aiofiles_available = False
            logger.warning("aiofiles not installed, using asyncio.to_thread fallback")
    return _aiofiles_available


class AsyncFileOperations:
    """
    Async file operations utility class.

    Uses aiofiles for true async I/O when available, falls back to
    asyncio.to_thread for synchronous operations when not.

    Thread-safe and suitable for concurrent access from multiple nodes.
    """

    @staticmethod
    async def read_text(
        path: str | Path,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> str:
        """
        Read text content from a file asynchronously.

        Args:
            path: Path to the file
            encoding: Text encoding (default: utf-8)
            errors: Error handling mode (strict, ignore, replace, etc.)

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file does not exist
            UnicodeDecodeError: If encoding fails with strict mode
        """
        path = Path(path)

        if _check_aiofiles():
            import aiofiles

            async with aiofiles.open(path, encoding=encoding, errors=errors) as f:
                return await f.read()
        else:
            return await asyncio.to_thread(_sync_read_text, path, encoding, errors)

    @staticmethod
    async def write_text(
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
        errors: str = "strict",
        create_dirs: bool = True,
    ) -> int:
        """
        Write text content to a file asynchronously.

        Args:
            path: Path to the file
            content: Content to write
            encoding: Text encoding (default: utf-8)
            errors: Error handling mode
            create_dirs: Create parent directories if needed

        Returns:
            Number of characters written
        """
        path = Path(path)

        if create_dirs and path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)

        if _check_aiofiles():
            import aiofiles

            async with aiofiles.open(path, "w", encoding=encoding, errors=errors) as f:
                return await f.write(content)
        else:
            return await asyncio.to_thread(_sync_write_text, path, content, encoding, errors)

    @staticmethod
    async def append_text(
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
        errors: str = "strict",
        create_dirs: bool = True,
    ) -> int:
        """
        Append text content to a file asynchronously.

        Args:
            path: Path to the file
            content: Content to append
            encoding: Text encoding (default: utf-8)
            errors: Error handling mode
            create_dirs: Create parent directories if needed

        Returns:
            Number of characters written
        """
        path = Path(path)

        if create_dirs and path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)

        if _check_aiofiles():
            import aiofiles

            async with aiofiles.open(path, "a", encoding=encoding, errors=errors) as f:
                return await f.write(content)
        else:
            return await asyncio.to_thread(_sync_append_text, path, content, encoding, errors)

    @staticmethod
    async def read_binary(path: str | Path) -> bytes:
        """
        Read binary content from a file asynchronously.

        Args:
            path: Path to the file

        Returns:
            File contents as bytes
        """
        path = Path(path)

        if _check_aiofiles():
            import aiofiles

            async with aiofiles.open(path, "rb") as f:
                return await f.read()
        else:
            return await asyncio.to_thread(_sync_read_binary, path)

    @staticmethod
    async def write_binary(
        path: str | Path,
        content: bytes,
        create_dirs: bool = True,
    ) -> int:
        """
        Write binary content to a file asynchronously.

        Args:
            path: Path to the file
            content: Binary content to write
            create_dirs: Create parent directories if needed

        Returns:
            Number of bytes written
        """
        path = Path(path)

        if create_dirs and path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)

        if _check_aiofiles():
            import aiofiles

            async with aiofiles.open(path, "wb") as f:
                return await f.write(content)
        else:
            return await asyncio.to_thread(_sync_write_binary, path, content)

    @staticmethod
    async def read_json(
        path: str | Path,
        encoding: str = "utf-8",
    ) -> Any:
        """
        Read and parse a JSON file asynchronously.

        Args:
            path: Path to the JSON file
            encoding: Text encoding (default: utf-8)

        Returns:
            Parsed JSON data (dict, list, etc.)

        Raises:
            json.JSONDecodeError: If JSON is invalid
        """
        content = await AsyncFileOperations.read_text(path, encoding)
        # Use asyncio.to_thread for CPU-bound JSON parsing on large files
        if len(content) > 100_000:  # 100KB threshold
            return await asyncio.to_thread(json.loads, content)
        return json.loads(content)

    @staticmethod
    async def write_json(
        path: str | Path,
        data: Any,
        encoding: str = "utf-8",
        indent: int = 2,
        ensure_ascii: bool = False,
        create_dirs: bool = True,
    ) -> int:
        """
        Write data as JSON to a file asynchronously.

        Args:
            path: Path to the JSON file
            data: Data to serialize as JSON
            encoding: Text encoding (default: utf-8)
            indent: Indentation level (default: 2)
            ensure_ascii: Escape non-ASCII characters (default: False)
            create_dirs: Create parent directories if needed

        Returns:
            Number of characters written
        """
        # Use asyncio.to_thread for CPU-bound JSON serialization on complex data
        content = await asyncio.to_thread(
            json.dumps, data, indent=indent, ensure_ascii=ensure_ascii
        )
        return await AsyncFileOperations.write_text(
            path, content, encoding, create_dirs=create_dirs
        )

    @staticmethod
    async def read_csv(
        path: str | Path,
        encoding: str = "utf-8",
        delimiter: str = ",",
        has_header: bool = True,
        skip_rows: int = 0,
        max_rows: int = 0,
        quotechar: str = '"',
        strict: bool = False,
    ) -> tuple[list[dict[str, str] | list[str]], list[str]]:
        """
        Read and parse a CSV file asynchronously.

        Args:
            path: Path to the CSV file
            encoding: Text encoding (default: utf-8)
            delimiter: Field delimiter (default: ,)
            has_header: Whether first row is header (default: True)
            skip_rows: Number of rows to skip at start (default: 0)
            max_rows: Maximum rows to read, 0=unlimited (default: 0)
            quotechar: Quote character (default: ")
            strict: Strict parsing mode (default: False)

        Returns:
            Tuple of (data, headers):
            - data: List of dicts (if has_header) or lists
            - headers: List of column headers (empty if no header)
        """
        content = await AsyncFileOperations.read_text(path, encoding)

        # CPU-bound CSV parsing in thread pool
        return await asyncio.to_thread(
            _parse_csv,
            content,
            delimiter,
            has_header,
            skip_rows,
            max_rows,
            quotechar,
            strict,
        )

    @staticmethod
    async def write_csv(
        path: str | Path,
        data: list[dict[str, Any] | list[Any]],
        headers: list[str] | None = None,
        encoding: str = "utf-8",
        delimiter: str = ",",
        write_header: bool = True,
        create_dirs: bool = True,
    ) -> int:
        """
        Write data to a CSV file asynchronously.

        Args:
            path: Path to the CSV file
            data: List of dicts or lists to write
            headers: Column headers (auto-detected from dicts if not provided)
            encoding: Text encoding (default: utf-8)
            delimiter: Field delimiter (default: ,)
            write_header: Whether to write header row (default: True)
            create_dirs: Create parent directories if needed

        Returns:
            Number of rows written
        """
        # CPU-bound CSV formatting in thread pool
        content = await asyncio.to_thread(_format_csv, data, headers, delimiter, write_header)
        await AsyncFileOperations.write_text(path, content, encoding, create_dirs=create_dirs)
        return len(data)


# =============================================================================
# Synchronous Helper Functions (for asyncio.to_thread fallback)
# =============================================================================


def _sync_read_text(path: Path, encoding: str, errors: str) -> str:
    """Synchronous text file read."""
    with open(path, encoding=encoding, errors=errors) as f:
        return f.read()


def _sync_write_text(path: Path, content: str, encoding: str, errors: str) -> int:
    """Synchronous text file write."""
    with open(path, "w", encoding=encoding, errors=errors) as f:
        return f.write(content)


def _sync_append_text(path: Path, content: str, encoding: str, errors: str) -> int:
    """Synchronous text file append."""
    with open(path, "a", encoding=encoding, errors=errors) as f:
        return f.write(content)


def _sync_read_binary(path: Path) -> bytes:
    """Synchronous binary file read."""
    with open(path, "rb") as f:
        return f.read()


def _sync_write_binary(path: Path, content: bytes) -> int:
    """Synchronous binary file write."""
    with open(path, "wb") as f:
        return f.write(content)


def _parse_csv(
    content: str,
    delimiter: str,
    has_header: bool,
    skip_rows: int,
    max_rows: int,
    quotechar: str,
    strict: bool,
) -> tuple[list[dict[str, str] | list[str]], list[str]]:
    """Parse CSV content (CPU-bound, run in thread pool)."""
    data: list[dict[str, str] | list[str]] = []
    headers: list[str] = []

    string_io = StringIO(content)

    # Skip initial rows
    for _ in range(skip_rows):
        next(string_io, None)

    csv_options = {
        "delimiter": delimiter,
        "quotechar": quotechar,
        "strict": strict,
    }

    if has_header:
        reader = csv.DictReader(string_io, **csv_options)
        headers = reader.fieldnames or []

        if max_rows > 0:
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                data.append(row)
        else:
            data = list(reader)
    else:
        reader = csv.reader(string_io, **csv_options)

        if max_rows > 0:
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                data.append(row)
        else:
            data = list(reader)

    return data, headers


def _format_csv(
    data: list[dict[str, Any] | list[Any]],
    headers: list[str] | None,
    delimiter: str,
    write_header: bool,
) -> str:
    """Format data as CSV content (CPU-bound, run in thread pool)."""
    output = StringIO()

    if data and isinstance(data[0], dict):
        # Dict data
        fieldnames = headers or (list(data[0].keys()) if data else [])
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
        if write_header:
            writer.writeheader()
        writer.writerows(data)
    else:
        # List data
        writer = csv.writer(output, delimiter=delimiter)
        if write_header and headers:
            writer.writerow(headers)
        writer.writerows(data)

    return output.getvalue()
