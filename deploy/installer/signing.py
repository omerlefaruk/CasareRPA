"""
Code Signing Utility for CasareRPA Installers.

Handles code signing for Windows executables and installers.
Supports signing via signtool.exe (Windows SDK) or osslsigncode (cross-platform).

Configuration via environment variables:
- CASARE_SIGN_CERT: Path to .pfx certificate file
- CASARE_SIGN_PASSWORD: Certificate password (or use secure prompt)
- CASARE_SIGN_TIMESTAMP: Timestamp server URL (default: http://timestamp.digicert.com)

Usage:
    from deploy.installer.signing import sign_executable, can_sign

    if can_sign():
        sign_executable("dist/CasareRPA/CasareRPA.exe")
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple


class SigningConfig(NamedTuple):
    """Code signing configuration."""

    certificate_path: Path | None
    password: str | None
    timestamp_server: str
    signtool_path: Path | None


# Common timestamp servers
TIMESTAMP_SERVERS = [
    "http://timestamp.digicert.com",
    "http://timestamp.sectigo.com",
    "http://timestamp.comodoca.com/authenticode",
    "http://tsa.starfieldtech.com",
]

# Known signtool.exe locations in Windows SDK
SIGNTOOL_SEARCH_PATHS = [
    r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
    r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22000.0\x64\signtool.exe",
    r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe",
    r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.18362.0\x64\signtool.exe",
]


def find_signtool() -> Path | None:
    """Find signtool.exe on the system."""
    # Check PATH first
    signtool = shutil.which("signtool")
    if signtool:
        return Path(signtool)

    # Check known locations
    for path in SIGNTOOL_SEARCH_PATHS:
        p = Path(path)
        if p.exists():
            return p

    return None


def get_signing_config() -> SigningConfig:
    """Get signing configuration from environment."""
    cert_path = os.environ.get("CASARE_SIGN_CERT")
    password = os.environ.get("CASARE_SIGN_PASSWORD")
    timestamp = os.environ.get("CASARE_SIGN_TIMESTAMP", TIMESTAMP_SERVERS[0])

    return SigningConfig(
        certificate_path=Path(cert_path) if cert_path else None,
        password=password,
        timestamp_server=timestamp,
        signtool_path=find_signtool(),
    )


def can_sign() -> bool:
    """Check if code signing is available and configured."""
    config = get_signing_config()

    if not config.signtool_path:
        return False

    if not config.certificate_path or not config.certificate_path.exists():
        return False

    return True


def sign_executable(
    executable_path: str | Path,
    description: str = "CasareRPA",
    config: SigningConfig | None = None,
) -> bool:
    """
    Sign a Windows executable.

    Args:
        executable_path: Path to .exe file to sign
        description: Description for the signature
        config: Signing configuration (uses environment if None)

    Returns:
        True if signing succeeded, False otherwise

    Raises:
        FileNotFoundError: If executable doesn't exist
        RuntimeError: If signtool is not available
    """
    exe_path = Path(executable_path)
    if not exe_path.exists():
        raise FileNotFoundError(f"Executable not found: {exe_path}")

    if config is None:
        config = get_signing_config()

    if not config.signtool_path:
        raise RuntimeError("signtool.exe not found. Install Windows SDK.")

    if not config.certificate_path or not config.certificate_path.exists():
        raise RuntimeError("Certificate not configured or not found.")

    # Build signtool command
    cmd = [
        str(config.signtool_path),
        "sign",
        "/f",
        str(config.certificate_path),
        "/t",
        config.timestamp_server,
        "/d",
        description,
        "/fd",
        "SHA256",
    ]

    if config.password:
        cmd.extend(["/p", config.password])

    cmd.append(str(exe_path))

    # Execute signing
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return True
        else:
            print(f"Signing failed: {result.stderr}")
            return False

    except subprocess.SubprocessError as e:
        print(f"Signing error: {e}")
        return False


def verify_signature(executable_path: str | Path) -> bool:
    """
    Verify that an executable is signed.

    Args:
        executable_path: Path to .exe file to verify

    Returns:
        True if valid signature found, False otherwise
    """
    exe_path = Path(executable_path)
    if not exe_path.exists():
        return False

    signtool = find_signtool()
    if not signtool:
        return False

    cmd = [str(signtool), "verify", "/pa", str(exe_path)]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


def sign_all_executables(dist_dir: str | Path, description: str = "CasareRPA") -> dict:
    """
    Sign all .exe files in a directory.

    Args:
        dist_dir: Distribution directory containing executables
        description: Description for signatures

    Returns:
        Dict mapping file paths to signing success status
    """
    dist_path = Path(dist_dir)
    results = {}

    if not can_sign():
        print("Code signing not configured - skipping")
        return results

    for exe_file in dist_path.rglob("*.exe"):
        # Skip uninstaller (will be signed after NSIS build)
        if exe_file.name.lower() == "uninstall.exe":
            continue

        try:
            success = sign_executable(exe_file, description)
            results[str(exe_file)] = success
            status = "OK" if success else "FAILED"
            print(f"  [{status}] {exe_file.name}")
        except Exception as e:
            results[str(exe_file)] = False
            print(f"  [ERROR] {exe_file.name}: {e}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Code signing utility")
    parser.add_argument(
        "--check", action="store_true", help="Check if signing is available"
    )
    parser.add_argument("--sign", type=str, help="Sign a specific executable")
    parser.add_argument("--verify", type=str, help="Verify signature on executable")
    parser.add_argument(
        "--sign-all", type=str, help="Sign all executables in directory"
    )
    args = parser.parse_args()

    if args.check:
        config = get_signing_config()
        print("Code Signing Configuration:")
        print(f"  signtool: {config.signtool_path or 'NOT FOUND'}")
        print(f"  certificate: {config.certificate_path or 'NOT SET'}")
        print(f"  timestamp: {config.timestamp_server}")
        print(f"  can_sign: {can_sign()}")

    elif args.sign:
        try:
            success = sign_executable(args.sign)
            print(f"Signing {'succeeded' if success else 'failed'}")
        except Exception as e:
            print(f"Error: {e}")

    elif args.verify:
        success = verify_signature(args.verify)
        print(f"Signature {'valid' if success else 'invalid or not signed'}")

    elif args.sign_all:
        results = sign_all_executables(args.sign_all)
        success_count = sum(1 for v in results.values() if v)
        print(f"\nSigned {success_count}/{len(results)} executables")

    else:
        parser.print_help()
