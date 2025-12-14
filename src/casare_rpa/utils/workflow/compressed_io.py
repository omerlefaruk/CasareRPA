"""
Compressed Workflow I/O Utilities.

PERFORMANCE: Large workflows can be several MB in JSON format.
Compression reduces file size by 60-90% and can actually speed up
I/O on slower storage (time to compress < time to write extra bytes).

Supports:
- .json: Uncompressed JSON (default, human-readable)
- .json.gz: Gzip compressed JSON (60-70% smaller)
- .json.zst: Zstandard compressed JSON (70-90% smaller, fastest)

Usage:
    from casare_rpa.utils.workflow.compressed_io import save_workflow, load_workflow

    # Save (auto-detects format from extension)
    save_workflow(workflow_data, Path("workflow.json.gz"))

    # Load (auto-detects format from extension)
    workflow_data = load_workflow(Path("workflow.json.gz"))

    # Streaming load for large files (>1MB)
    workflow_data = load_workflow_streaming(Path("large_workflow.json.zst"))
"""

import gzip
import mmap
from pathlib import Path
from typing import Any, Dict, Optional

import orjson
from loguru import logger

# Try to import zstandard for best compression (optional dependency)
try:
    import zstandard as zstd

    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

# Threshold for using streaming/mmap (1MB)
LARGE_FILE_THRESHOLD = 1024 * 1024


def save_workflow(
    data: Dict[str, Any],
    path: Path,
    compression_level: int = 6,
    pretty: bool = True,
) -> None:
    """
    Save workflow data to file with optional compression.

    PERFORMANCE: Compression is recommended for workflows > 100KB.
    Gzip provides good compression with wide compatibility.
    Zstandard provides best compression and speed if available.

    Args:
        data: Workflow data dictionary
        path: Output file path (extension determines format)
        compression_level: Compression level (1-9 for gzip, 1-22 for zstd)
        pretty: Whether to use pretty formatting (ignored for compressed)
    """
    # Determine format from extension
    suffix = "".join(path.suffixes).lower()

    # Serialize with orjson
    options = (
        orjson.OPT_INDENT_2 if pretty and not suffix.endswith((".gz", ".zst")) else 0
    )
    json_bytes = orjson.dumps(data, option=options)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    if suffix.endswith(".json.zst"):
        if not ZSTD_AVAILABLE:
            logger.warning("Zstandard not available, falling back to gzip")
            path = path.with_suffix(".json.gz")
            suffix = ".json.gz"
        else:
            # Zstandard compression (best)
            cctx = zstd.ZstdCompressor(level=compression_level)
            compressed = cctx.compress(json_bytes)
            path.write_bytes(compressed)
            logger.debug(
                f"Saved compressed workflow ({len(compressed)/1024:.1f}KB, "
                f"{len(compressed)/len(json_bytes)*100:.0f}% of original)"
            )
            return

    if suffix.endswith(".json.gz"):
        # Gzip compression
        compressed = gzip.compress(json_bytes, compresslevel=compression_level)
        path.write_bytes(compressed)
        logger.debug(
            f"Saved gzip workflow ({len(compressed)/1024:.1f}KB, "
            f"{len(compressed)/len(json_bytes)*100:.0f}% of original)"
        )
        return

    # Uncompressed JSON
    path.write_bytes(json_bytes)
    logger.debug(f"Saved workflow ({len(json_bytes)/1024:.1f}KB)")


def load_workflow(
    path: Path, use_streaming: Optional[bool] = None
) -> Optional[Dict[str, Any]]:
    """
    Load workflow data from file with automatic decompression.

    PERFORMANCE: Automatically uses streaming for files > 1MB unless
    explicitly disabled. Streaming reduces peak memory usage.

    Args:
        path: Input file path (extension determines format)
        use_streaming: Force streaming on/off. None = auto (>1MB uses streaming)

    Returns:
        Workflow data dictionary, or None on error
    """
    if not path.exists():
        logger.error(f"Workflow file not found: {path}")
        return None

    # Auto-detect streaming based on file size
    file_size = path.stat().st_size
    if use_streaming is None:
        use_streaming = file_size > LARGE_FILE_THRESHOLD

    if use_streaming:
        return load_workflow_streaming(path)

    suffix = "".join(path.suffixes).lower()

    try:
        if suffix.endswith(".json.zst"):
            if not ZSTD_AVAILABLE:
                logger.error("Zstandard not available, cannot load .zst file")
                return None
            # Zstandard decompression
            dctx = zstd.ZstdDecompressor()
            compressed = path.read_bytes()
            json_bytes = dctx.decompress(compressed)
            return orjson.loads(json_bytes)

        if suffix.endswith(".json.gz"):
            # Gzip decompression
            compressed = path.read_bytes()
            json_bytes = gzip.decompress(compressed)
            return orjson.loads(json_bytes)

        # Uncompressed JSON
        return orjson.loads(path.read_bytes())

    except Exception as e:
        logger.error(f"Failed to load workflow: {e}")
        return None


def get_compression_stats(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get compression statistics for workflow data.

    Useful for deciding whether to use compression.

    Args:
        data: Workflow data dictionary

    Returns:
        Dictionary with size statistics
    """
    json_bytes = orjson.dumps(data)
    original_size = len(json_bytes)

    stats = {
        "original_bytes": original_size,
        "original_kb": original_size / 1024,
    }

    # Gzip compression
    gzip_bytes = gzip.compress(json_bytes, compresslevel=6)
    stats["gzip_bytes"] = len(gzip_bytes)
    stats["gzip_ratio"] = len(gzip_bytes) / original_size

    # Zstandard compression (if available)
    if ZSTD_AVAILABLE:
        cctx = zstd.ZstdCompressor(level=6)
        zstd_bytes = cctx.compress(json_bytes)
        stats["zstd_bytes"] = len(zstd_bytes)
        stats["zstd_ratio"] = len(zstd_bytes) / original_size

    return stats


def load_workflow_streaming(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load workflow data using streaming decompression.

    PERFORMANCE: Optimized for large files (>1MB).
    - Uses streaming decompression for zstd files
    - Uses memory mapping for large uncompressed JSON files
    - Falls back to regular loading for small files

    Args:
        path: Input file path (extension determines format)

    Returns:
        Workflow data dictionary, or None on error
    """
    if not path.exists():
        logger.error(f"Workflow file not found: {path}")
        return None

    suffix = "".join(path.suffixes).lower()
    file_size = path.stat().st_size

    try:
        if suffix.endswith(".json.zst"):
            if not ZSTD_AVAILABLE:
                logger.error("Zstandard not available, cannot load .zst file")
                return None
            return _load_zstd_streaming(path)

        if suffix.endswith(".json.gz"):
            return _load_gzip_streaming(path)

        # Uncompressed JSON - use mmap for large files
        if file_size > LARGE_FILE_THRESHOLD:
            return _load_json_mmap(path)

        # Small files - regular load
        return orjson.loads(path.read_bytes())

    except Exception as e:
        logger.error(f"Failed to load workflow (streaming): {e}")
        return None


def _load_zstd_streaming(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load zstd-compressed workflow using streaming decompression.

    Uses zstd streaming API to decompress in chunks, reducing peak memory.

    Args:
        path: Path to .json.zst file

    Returns:
        Parsed workflow data
    """
    dctx = zstd.ZstdDecompressor()
    chunks: list[bytes] = []

    with open(path, "rb") as fh:
        with dctx.stream_reader(fh) as reader:
            while True:
                chunk = reader.read(65536)  # 64KB chunks
                if not chunk:
                    break
                chunks.append(chunk)

    json_bytes = b"".join(chunks)
    logger.debug(f"Streaming decompressed {path.name}: {len(json_bytes)/1024:.1f}KB")
    return orjson.loads(json_bytes)


def _load_gzip_streaming(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load gzip-compressed workflow using streaming decompression.

    Args:
        path: Path to .json.gz file

    Returns:
        Parsed workflow data
    """
    chunks: list[bytes] = []

    with gzip.open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)  # 64KB chunks
            if not chunk:
                break
            chunks.append(chunk)

    json_bytes = b"".join(chunks)
    logger.debug(f"Streaming decompressed {path.name}: {len(json_bytes)/1024:.1f}KB")
    return orjson.loads(json_bytes)


def _load_json_mmap(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load large uncompressed JSON using memory mapping.

    Memory mapping allows the OS to handle paging efficiently,
    reducing memory pressure for very large files.

    Args:
        path: Path to .json file

    Returns:
        Parsed workflow data
    """
    file_size = path.stat().st_size

    with open(path, "rb") as fh:
        # Create read-only memory map
        with mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            logger.debug(f"Memory-mapped {path.name}: {file_size/1024:.1f}KB")
            return orjson.loads(mm[:])
