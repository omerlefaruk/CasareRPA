"""
Stdout/Stderr capture for UI display.

Captures print() statements and subprocess output during workflow execution
and forwards them to the Terminal tab.
"""

from __future__ import annotations

import atexit
import sys
import io
import threading
from typing import Callable, Optional, TextIO
from contextlib import contextmanager


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
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize output capture.

        Args:
            stdout_callback: Called with each line of stdout
            stderr_callback: Called with each line of stderr
        """
        self._stdout_callback = stdout_callback
        self._stderr_callback = stderr_callback
        self._original_stdout: Optional[TextIO] = None
        self._original_stderr: Optional[TextIO] = None
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

    def __enter__(self) -> "OutputCapture":
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
        callback: Optional[Callable[[str], None]] = None,
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
    def errors(self) -> Optional[str]:
        """Get error handling."""
        return getattr(self._original, "errors", None)


# Global capture instance (set by presentation layer)
_global_capture: Optional[OutputCapture] = None


def _cleanup_on_exit() -> None:
    """Cleanup handler registered with atexit to restore streams on exit."""
    global _global_capture
    with _global_lock:
        if _global_capture:
            _global_capture.stop()
            _global_capture = None


# Register cleanup handler
atexit.register(_cleanup_on_exit)


def set_output_callbacks(
    stdout_callback: Optional[Callable[[str], None]] = None,
    stderr_callback: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Set global stdout/stderr callbacks (thread-safe).

    Called by ExecutionController to wire output to Terminal tab.

    Args:
        stdout_callback: Called with each line of stdout
        stderr_callback: Called with each line of stderr
    """
    global _global_capture

    with _global_lock:
        # Stop existing capture
        if _global_capture:
            _global_capture.stop()

        # Create and start new capture
        _global_capture = OutputCapture(stdout_callback, stderr_callback)
        _global_capture.start()


def remove_output_callbacks() -> None:
    """Remove global output callbacks and restore original streams (thread-safe)."""
    global _global_capture

    with _global_lock:
        if _global_capture:
            _global_capture.stop()
            _global_capture = None


@contextmanager
def capture_output(
    stdout_callback: Optional[Callable[[str], None]] = None,
    stderr_callback: Optional[Callable[[str], None]] = None,
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
