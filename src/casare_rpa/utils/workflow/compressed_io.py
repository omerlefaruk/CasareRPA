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
"""

import gzip
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


def load_workflow(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load workflow data from file with automatic decompression.

    Args:
        path: Input file path (extension determines format)

    Returns:
        Workflow data dictionary, or None on error
    """
    if not path.exists():
        logger.error(f"Workflow file not found: {path}")
        return None

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
