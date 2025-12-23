"""
Canvas telemetry helpers for startup timing and runtime event logging.

Provides structured log lines that can be parsed from log files.
"""

from __future__ import annotations

import json
import time
from typing import Any

from loguru import logger

IMPORT_START = time.perf_counter()


def _log_structured(prefix: str, payload: dict[str, Any], level: str) -> None:
    message = f"{prefix} {json.dumps(payload, separators=(',', ':'), default=str)}"
    log_fn = getattr(logger, level, logger.info)
    log_fn(message)


class StartupTimer:
    """
    Tracks Canvas startup phases and emits structured timing logs.

    Each call to mark() logs elapsed time from the timer start and from the last
    mark, enabling phase-by-phase analysis.
    """

    def __init__(self, name: str = "canvas_startup", start_time: float | None = None) -> None:
        self._name = name
        self._start_time = start_time if start_time is not None else time.perf_counter()
        self._last_time = self._start_time

    def mark(self, phase: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        now = time.perf_counter()
        payload: dict[str, Any] = {
            "event": self._name,
            "phase": phase,
            "elapsed_ms": round((now - self._start_time) * 1000.0, 2),
            "since_last_ms": round((now - self._last_time) * 1000.0, 2),
        }
        if details:
            payload["details"] = details
        _log_structured("STARTUP_TIMING", payload, level="info")
        self._last_time = now
        return payload


def log_canvas_event(event: str, **fields: Any) -> None:
    """
    Emit a structured runtime event log for Canvas operations.

    Use for low-frequency events like serialize/deserialize, undo/redo,
    connection changes, and culling decisions.
    """
    payload: dict[str, Any] = {"event": event, "ts_ms": int(time.time() * 1000)}
    if fields:
        payload.update(fields)
    _log_structured("CANVAS_EVENT", payload, level="debug")
