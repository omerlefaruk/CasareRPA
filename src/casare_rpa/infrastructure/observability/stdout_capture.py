"""
Stdout/Stderr capture for UI display.

Captures print() statements and subprocess output during workflow execution
and forwards them to the Terminal tab.
"""

from __future__ import annotations

import atexit
import sys
import threading
from collections.abc import Callable
from contextlib import contextmanager
from typing import Optional, TextIO

# Module-level lock for global state
_global_lock = threading.Lock()


class OutputCapture:
    """
    Captures stdout/stderr and forwards to a callback.

    Thread-safe wrapper that can be used as a context manager or
    installed globally for the duration of workflow execution.
    """

    def __init__(
        self,
        stdout_callback: Callable[[str], None] | None = None,
        stderr_callback: Callable[[str], None] | None = None,
    ):
        """
        Initialize output capture.

        Args:
            stdout_callback: Called with each line of stdout
            stderr_callback: Called with each line of stderr
        """
        self._stdout_callback = stdout_callback
        self._stderr_callback = stderr_callback
        self._original_stdout: TextIO | None = None
        self._original_stderr: TextIO | None = None
        self._capturing = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start capturing stdout/stderr."""
        if self._capturing:
            return

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        sys.stdout = _CallbackWriter(self._original_stdout, self._stdout_callback)
        sys.stderr = _CallbackWriter(self._original_stderr, self._stderr_callback)

        self._capturing = True

    def stop(self) -> None:
        """Stop capturing and restore original streams."""
        if not self._capturing:
            return

        if self._original_stdout:
            sys.stdout = self._original_stdout
        if self._original_stderr:
            sys.stderr = self._original_stderr

        self._original_stdout = None
        self._original_stderr = None
        self._capturing = False

    def __enter__(self) -> OutputCapture:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


class _CallbackWriter:
    """
    File-like object that writes to both original stream and callback.

    Thread-safe: Uses lock for buffer operations to handle concurrent writes.
    """

    def __init__(
        self,
        original: TextIO,
        callback: Callable[[str], None] | None = None,
    ):
        self._original = original
        self._callback = callback
        self._buffer = ""
        self._lock = threading.Lock()

    def write(self, text: str) -> int:
        """Write text to original stream and callback (thread-safe)."""
        # Always write to original
        result = self._original.write(text)

        # Buffer and send complete lines to callback
        if self._callback and text:
            with self._lock:
                self._buffer += text
                while "\n" in self._buffer:
                    line, self._buffer = self._buffer.split("\n", 1)
                    if line:  # Don't send empty lines
                        try:
                            self._callback(line)
                        except Exception as e:
                            # Log to original stderr without using captured stream
                            sys.__stderr__.write(f"Callback error: {e}\n")

        return result

    def flush(self) -> None:
        """Flush the stream (thread-safe)."""
        self._original.flush()
        # Flush remaining buffer
        with self._lock:
            if self._callback and self._buffer:
                try:
                    self._callback(self._buffer)
                except Exception as e:
                    sys.__stderr__.write(f"Callback error: {e}\n")
                self._buffer = ""

    def fileno(self) -> int:
        """Return file descriptor."""
        return self._original.fileno()

    def isatty(self) -> bool:
        """Check if stream is a TTY."""
        return self._original.isatty()

    @property
    def encoding(self) -> str:
        """Get encoding."""
        return getattr(self._original, "encoding", "utf-8")

    @property
    def errors(self) -> str | None:
        """Get error handling."""
        return getattr(self._original, "errors", None)


# Module-level capture instance with thread-safe management
_capture_instance: OutputCapture | None = None


def _cleanup_on_exit() -> None:
    """Cleanup handler registered with atexit to restore streams on exit."""
    with _global_lock:
        _local_capture = _capture_instance
        if _local_capture:
            _local_capture.stop()
            globals()["_capture_instance"] = None


# Register cleanup handler
atexit.register(_cleanup_on_exit)


def set_output_callbacks(
    stdout_callback: Callable[[str], None] | None = None,
    stderr_callback: Callable[[str], None] | None = None,
) -> None:
    """
    Set stdout/stderr callbacks (thread-safe).

    Called by ExecutionController to wire output to Terminal tab.

    Args:
        stdout_callback: Called with each line of stdout
        stderr_callback: Called with each line of stderr
    """
    with _global_lock:
        # Stop existing capture
        _local_capture = _capture_instance
        if _local_capture:
            _local_capture.stop()

        # Create and start new capture
        _new_capture = OutputCapture(stdout_callback, stderr_callback)
        _new_capture.start()
        globals()["_capture_instance"] = _new_capture


def remove_output_callbacks() -> None:
    """Remove output callbacks and restore original streams (thread-safe)."""
    with _global_lock:
        _local_capture = _capture_instance
        if _local_capture:
            _local_capture.stop()
            globals()["_capture_instance"] = None


def get_output_capture() -> OutputCapture | None:
    """
    Get the current output capture instance (if any).

    Returns:
        Current OutputCapture or None
    """
    with _global_lock:
        return _capture_instance


@contextmanager
def capture_output(
    stdout_callback: Callable[[str], None] | None = None,
    stderr_callback: Callable[[str], None] | None = None,
):
    """
    Context manager for capturing stdout/stderr.

    Usage:
        with capture_output(on_stdout, on_stderr):
            print("This goes to terminal tab")
            subprocess.run(["cmd"])

    Args:
        stdout_callback: Called with each line of stdout
        stderr_callback: Called with each line of stderr
    """
    capture = OutputCapture(stdout_callback, stderr_callback)
    try:
        capture.start()
        yield capture
    finally:
        capture.stop()
