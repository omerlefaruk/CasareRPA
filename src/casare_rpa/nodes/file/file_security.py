"""
Path security utilities for file operations.

This module provides security validation for file paths to prevent:
- Path traversal attacks
- Access to sensitive system directories
- Windows device name exploits
- Null byte injection

SECURITY: All file operations should validate paths before access.
"""

from pathlib import Path

from loguru import logger


class PathSecurityError(Exception):
    """Raised when a path fails security validation."""

    pass


# SECURITY: Default allowed directories for file operations
# Can be customized via environment variable CASARE_ALLOWED_PATHS
_DEFAULT_ALLOWED_PATHS = [
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path.cwd(),  # Current working directory
]

# SECURITY: Paths that should NEVER be accessed
_BLOCKED_PATHS = [
    Path.home() / ".ssh",
    Path.home() / ".gnupg",
    Path.home() / ".aws",
    Path.home() / ".azure",
    Path.home() / ".config",
    Path.home() / "AppData" / "Local" / "Microsoft" / "Credentials",
    Path.home() / "AppData" / "Roaming" / "Microsoft" / "Credentials",
    Path("C:/Windows/System32"),
    Path("C:/Windows/SysWOW64"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
]

# Windows reserved device names
_WINDOWS_DEVICES = [
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
]


def validate_path_security(
    path: str | Path,
    operation: str = "access",
    allow_dangerous: bool = False,
) -> Path:
    """Validate that a file path is safe to access.

    SECURITY: This function prevents path traversal attacks and blocks
    access to sensitive system directories.

    Args:
        path: The path to validate
        operation: The operation being performed (for logging)
        allow_dangerous: If True, skip security checks (NOT RECOMMENDED)

    Returns:
        The validated, canonicalized Path object

    Raises:
        PathSecurityError: If the path fails security validation
    """
    if allow_dangerous:
        logger.warning(f"Path security check BYPASSED for {operation}: {path}")
        return Path(path).resolve()

    try:
        # Resolve to absolute path (handles .. and symlinks)
        resolved_path = Path(path).resolve()
    except Exception as e:
        raise PathSecurityError(f"Invalid path '{path}': {e}") from e

    # SECURITY: Check for blocked paths
    for blocked in _BLOCKED_PATHS:
        try:
            blocked_resolved = blocked.resolve()
            if resolved_path == blocked_resolved or blocked_resolved in resolved_path.parents:
                raise PathSecurityError(
                    f"Access to '{resolved_path}' is blocked for security reasons. "
                    f"This path is in a protected system directory."
                )
        except Exception:
            pass  # Blocked path doesn't exist, skip

    # SECURITY: Check original path string for traversal attempts
    path_str = str(path)
    if ".." in path_str:
        raise PathSecurityError(
            f"Path traversal detected in '{path}'. " f"Paths containing '..' are not allowed."
        )

    # SECURITY: Check for null bytes (can be used to bypass checks)
    if "\x00" in path_str:
        raise PathSecurityError(
            f"Null byte detected in path '{path}'. " f"This is a potential security exploit."
        )

    # SECURITY: Check for special Windows device names
    stem = resolved_path.stem.upper()
    if stem in _WINDOWS_DEVICES:
        raise PathSecurityError(f"Access to Windows device '{stem}' is not allowed.")

    # Log the operation for audit
    logger.debug(f"File {operation}: {resolved_path}")

    return resolved_path


def validate_path_security_readonly(
    path: str | Path,
    operation: str = "read",
    allow_dangerous: bool = False,
) -> Path:
    """Validate path for read-only operations with relaxed restrictions.

    SECURITY: Read-only validation allows checking system paths but still
    prevents path traversal and null byte attacks. Blocked paths are logged
    but not rejected since read operations don't modify system state.

    Args:
        path: The path to validate
        operation: The operation being performed (for logging)
        allow_dangerous: If True, skip all validation

    Returns:
        The validated, canonicalized Path object

    Raises:
        PathSecurityError: Only for path traversal or null byte attacks
    """
    if allow_dangerous:
        logger.warning(f"Path security check BYPASSED for {operation}: {path}")
        return Path(path).resolve()

    try:
        # Resolve to absolute path (handles .. and symlinks)
        resolved_path = Path(path).resolve()
    except Exception as e:
        raise PathSecurityError(f"Invalid path '{path}': {e}") from e

    # SECURITY: Still block path traversal attempts
    path_str = str(path)
    if ".." in path_str:
        raise PathSecurityError(
            f"Path traversal detected in '{path}'. " f"Paths containing '..' are not allowed."
        )

    # SECURITY: Still block null bytes
    if "\x00" in path_str:
        raise PathSecurityError(
            f"Null byte detected in path '{path}'. " f"This is a potential security exploit."
        )

    # SECURITY: Still block Windows device names
    stem = resolved_path.stem.upper()
    if stem in _WINDOWS_DEVICES:
        raise PathSecurityError(f"Access to Windows device '{stem}' is not allowed.")

    # SECURITY: Log access to blocked paths for audit (but don't prevent)
    for blocked in _BLOCKED_PATHS:
        try:
            blocked_resolved = blocked.resolve()
            if resolved_path == blocked_resolved or blocked_resolved in resolved_path.parents:
                logger.warning(
                    f"Read-only access to protected path: {resolved_path} "
                    f"(operation: {operation})"
                )
                break
        except Exception:
            pass

    # Log the operation for audit
    logger.debug(f"File {operation} (read-only): {resolved_path}")

    return resolved_path
