"""
Node preloader for improved startup performance.

This module provides background preloading of commonly used node categories
to reduce lag when users first access those nodes.

Preloading Strategy:
- Preload is triggered after the main window is visible
- Uses a background thread to avoid blocking the UI
- Loads node categories in priority order (most commonly used first)
- Silent failure - preload errors don't affect application startup
"""

import threading
import time

from loguru import logger

# Node names to preload (commonly used individual nodes)
PRELOAD_NODES: list[str] = [
    # Basic
    "StartNode",
    "EndNode",
    # Control flow
    "IfNode",
    "ForLoopStartNode",
    "ForLoopEndNode",
    # Variables
    "SetVariableNode",
    "GetVariableNode",
    # Browser
    "LaunchBrowserNode",
    "ClickElementNode",
    "TypeTextNode",
    "GoToURLNode",
    # Wait
    "WaitNode",
    "WaitForElementNode",
    # File
    "ReadFileNode",
    "WriteFileNode",
]

_preload_thread: threading.Thread | None = None
_preload_started: bool = False
_preload_complete: bool = False


def _preload_worker() -> None:
    """
    Background worker that preloads node modules.

    Loads node categories and individual nodes in priority order.
    Logs progress for debugging startup performance.
    """
    global _preload_complete

    start_time = time.perf_counter()
    loaded_count = 0
    failed_count = 0

    try:
        # Import lazily to avoid circular imports
        from casare_rpa import nodes

        # Preload individual nodes (fastest, most commonly used)
        for node_name in PRELOAD_NODES:
            try:
                getattr(nodes, node_name, None)
                loaded_count += 1
            except Exception as e:
                logger.trace(f"Preload skipped {node_name}: {e}")
                failed_count += 1

        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Node preload complete: {loaded_count} loaded, "
            f"{failed_count} skipped in {elapsed:.1f}ms"
        )

    except Exception as e:
        logger.warning(f"Node preload failed: {e}")
    finally:
        _preload_complete = True


def start_node_preload() -> None:
    """
    Start background node preloading.

    This function is safe to call multiple times - it will only
    start preloading once. Call this after the main window is visible.

    The preload runs in a daemon thread so it will be automatically
    terminated if the application exits.
    """
    global _preload_thread, _preload_started

    if _preload_started:
        return

    _preload_started = True
    logger.debug("Starting background node preload...")

    _preload_thread = threading.Thread(
        target=_preload_worker,
        name="NodePreloader",
        daemon=True,
    )
    _preload_thread.start()


def is_preload_complete() -> bool:
    """
    Check if preloading has completed.

    Returns:
        True if preloading is done (or was never started), False otherwise.
    """
    return _preload_complete or not _preload_started


def wait_for_preload(timeout: float = 5.0) -> bool:
    """
    Wait for preloading to complete.

    Args:
        timeout: Maximum time to wait in seconds.

    Returns:
        True if preloading completed, False if timeout occurred.
    """
    if not _preload_started or _preload_thread is None:
        return True

    _preload_thread.join(timeout=timeout)
    return not _preload_thread.is_alive()
