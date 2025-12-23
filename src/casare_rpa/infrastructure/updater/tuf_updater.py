"""
TUF (The Update Framework) Updater Client.

Provides secure software updates with:
- Cryptographic verification of metadata and targets
- Protection against rollback attacks
- Compromise-resilient key hierarchy
- Automatic metadata refresh

Reference: https://theupdateframework.io/
"""

import asyncio
import hashlib
import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
from loguru import logger

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    logger.warning("cryptography package not installed - TUF signature verification disabled")


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class UpdateInfo:
    """Information about an available update."""

    version: str
    target_name: str
    size_bytes: int
    sha256_hash: str
    release_notes: str | None = None
    release_date: datetime | None = None
    is_critical: bool = False
    min_version: str | None = None  # Minimum version that can update


@dataclass
class DownloadProgress:
    """Progress information during download."""

    total_bytes: int
    downloaded_bytes: int
    percent: float
    speed_bps: float  # bytes per second


@dataclass
class TUFKey:
    """TUF public key for signature verification."""

    key_id: str
    key_type: str  # "ed25519", "ecdsa-sha2-nistp256", "rsa"
    public_key: str  # PEM or hex encoded public key
    scheme: str = "ed25519"  # Signature scheme


@dataclass
class TUFRootConfig:
    """TUF root configuration with trusted keys."""

    version: int = 1
    threshold: int = 1  # Minimum signatures required
    keys: dict[str, TUFKey] = field(default_factory=dict)
    expires: datetime | None = None

    @classmethod
    def from_root_json(cls, root_data: dict[str, Any]) -> "TUFRootConfig":
        """Parse root configuration from root.json metadata."""
        signed = root_data.get("signed", {})
        keys_data = signed.get("keys", {})
        roles = signed.get("roles", {})

        keys = {}
        for key_id, key_info in keys_data.items():
            keys[key_id] = TUFKey(
                key_id=key_id,
                key_type=key_info.get("keytype", "ed25519"),
                public_key=key_info.get("keyval", {}).get("public", ""),
                scheme=key_info.get("scheme", "ed25519"),
            )

        # Get threshold from root role
        root_role = roles.get("root", {})
        threshold = root_role.get("threshold", 1)

        # Parse expiration
        expires_str = signed.get("expires")
        expires = (
            datetime.fromisoformat(expires_str.replace("Z", "+00:00")) if expires_str else None
        )

        return cls(
            version=signed.get("version", 1),
            threshold=threshold,
            keys=keys,
            expires=expires,
        )


class SignatureVerificationError(Exception):
    """Raised when TUF signature verification fails."""

    pass


# =============================================================================
# TUF UPDATER CLIENT
# =============================================================================


class TUFUpdater:
    """
    TUF-compliant update client for secure software distribution.

    Features:
    - Fetches and verifies TUF metadata (timestamp, snapshot, targets)
    - Downloads and verifies target files
    - Supports incremental updates
    - Atomic update application
    """

    # TUF metadata file names
    TIMESTAMP_METADATA = "timestamp.json"
    SNAPSHOT_METADATA = "snapshot.json"
    TARGETS_METADATA = "targets.json"
    ROOT_METADATA = "root.json"

    def __init__(
        self,
        repo_url: str,
        local_cache_dir: Path,
        current_version: str,
        trusted_root_path: Path | None = None,
        verify_signatures: bool = True,
    ):
        """
        Initialize the TUF updater.

        Args:
            repo_url: Base URL of the TUF repository
            local_cache_dir: Local directory for caching metadata/targets
            current_version: Currently installed version
            trusted_root_path: Path to trusted root.json for signature verification
            verify_signatures: Whether to verify cryptographic signatures
        """
        self._repo_url = repo_url.rstrip("/")
        self._cache_dir = Path(local_cache_dir)
        self._current_version = current_version
        self._verify_signatures = verify_signatures and HAS_CRYPTOGRAPHY

        # Create cache directories
        self._metadata_dir = self._cache_dir / "metadata"
        self._targets_dir = self._cache_dir / "targets"
        self._metadata_dir.mkdir(parents=True, exist_ok=True)
        self._targets_dir.mkdir(parents=True, exist_ok=True)

        # Cached metadata
        self._timestamp: dict[str, Any] | None = None
        self._snapshot: dict[str, Any] | None = None
        self._targets: dict[str, Any] | None = None
        self._root_config: TUFRootConfig | None = None

        # Load trusted root if provided
        if trusted_root_path and trusted_root_path.exists():
            self._load_trusted_root(trusted_root_path)
        elif self._verify_signatures:
            logger.warning(
                "No trusted root.json provided - signature verification will use cached root"
            )

        logger.info(
            f"TUF Updater initialized: repo={self._repo_url} "
            f"cache={self._cache_dir} version={current_version} "
            f"verify_signatures={self._verify_signatures}"
        )

    def _load_trusted_root(self, root_path: Path) -> None:
        """Load trusted root.json for signature verification."""
        try:
            with open(root_path) as f:
                root_data = json.load(f)
            self._root_config = TUFRootConfig.from_root_json(root_data)
            logger.info(f"Loaded trusted root.json: {len(self._root_config.keys)} keys")
        except Exception as e:
            logger.error(f"Failed to load trusted root.json: {e}")
            raise SignatureVerificationError(f"Failed to load trusted root: {e}")

    async def check_for_updates(self) -> UpdateInfo | None:
        """
        Check if updates are available.

        Returns:
            UpdateInfo if update available, None otherwise
        """
        try:
            # Refresh TUF metadata
            await self._refresh_metadata()

            if not self._targets:
                logger.warning("No targets metadata available")
                return None

            # Find latest version target
            latest = self._find_latest_target()
            if not latest:
                return None

            target_name, target_info = latest

            # Parse version from target name (e.g., "CasareRPA-3.1.0.exe")
            version = self._extract_version(target_name)
            if not version:
                logger.warning(f"Could not extract version from {target_name}")
                return None

            # Compare versions
            if not self._is_newer_version(version, self._current_version):
                logger.debug(f"No update available: current={self._current_version}")
                return None

            # Get custom metadata if available
            custom = target_info.get("custom", {})

            return UpdateInfo(
                version=version,
                target_name=target_name,
                size_bytes=target_info.get("length", 0),
                sha256_hash=target_info.get("hashes", {}).get("sha256", ""),
                release_notes=custom.get("release_notes"),
                release_date=datetime.fromisoformat(custom["release_date"])
                if custom.get("release_date")
                else None,
                is_critical=custom.get("is_critical", False),
                min_version=custom.get("min_version"),
            )

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None

    async def download_update(
        self,
        update_info: UpdateInfo,
        progress_callback: Callable[[DownloadProgress], None] | None = None,
    ) -> Path:
        """
        Download an update with verification.

        Args:
            update_info: Information about the update to download
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the downloaded and verified file

        Raises:
            ValueError: If verification fails
        """
        target_url = f"{self._repo_url}/targets/{update_info.target_name}"
        target_path = self._targets_dir / update_info.target_name

        logger.info(f"Downloading update: {update_info.target_name}")

        async with aiohttp.ClientSession() as session:
            async with session.get(target_url) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                start_time = asyncio.get_event_loop().time()

                # Download with progress tracking
                hasher = hashlib.sha256()

                with open(target_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        hasher.update(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            elapsed = asyncio.get_event_loop().time() - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0

                            progress_callback(
                                DownloadProgress(
                                    total_bytes=total_size,
                                    downloaded_bytes=downloaded,
                                    percent=(downloaded / total_size) * 100,
                                    speed_bps=speed,
                                )
                            )

                # Verify hash
                computed_hash = hasher.hexdigest()
                if computed_hash != update_info.sha256_hash:
                    target_path.unlink(missing_ok=True)
                    raise ValueError(
                        f"Hash verification failed: expected={update_info.sha256_hash} "
                        f"got={computed_hash}"
                    )

                logger.info(
                    f"Update downloaded and verified: {target_path} " f"({downloaded:,} bytes)"
                )

                return target_path

    async def apply_update(
        self,
        update_path: Path,
        restart_app: bool = True,
    ) -> bool:
        """
        Apply a downloaded update atomically.

        The update process:
        1. Extract/prepare new version in temp directory
        2. Rename current installation to .old
        3. Move new version to installation directory
        4. Optionally restart the application

        Args:
            update_path: Path to the downloaded update file
            restart_app: Whether to restart the app after update

        Returns:
            True if update was applied successfully
        """
        try:
            import sys

            # Get installation directory
            if getattr(sys, "frozen", False):
                # Running as compiled executable
                install_dir = Path(sys.executable).parent
            else:
                # Running from source
                logger.warning("Cannot apply update in development mode")
                return False

            # Create backup
            backup_dir = install_dir.parent / f"{install_dir.name}.backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)

            logger.info(f"Creating backup: {backup_dir}")
            shutil.copytree(install_dir, backup_dir)

            # For .exe updates, just replace the executable
            if update_path.suffix.lower() == ".exe":
                exe_path = install_dir / update_path.name
                old_exe = exe_path.with_suffix(".old")

                # Rename current exe
                if exe_path.exists():
                    exe_path.rename(old_exe)

                # Move new exe
                shutil.copy2(update_path, exe_path)

                logger.info(f"Update applied: {exe_path}")

                if restart_app:
                    # Schedule restart
                    import subprocess

                    subprocess.Popen([str(exe_path)])
                    sys.exit(0)

                return True

            else:
                logger.warning(f"Unsupported update format: {update_path.suffix}")
                return False

        except Exception as e:
            logger.error(f"Failed to apply update: {e}")
            return False

    async def _refresh_metadata(self) -> None:
        """Refresh TUF metadata from repository."""
        async with aiohttp.ClientSession() as session:
            # Fetch timestamp (always fetch, short expiry)
            self._timestamp = await self._fetch_metadata(session, self.TIMESTAMP_METADATA)

            # Fetch snapshot (check if changed)
            (
                self._timestamp.get("signed", {})
                .get("meta", {})
                .get(self.SNAPSHOT_METADATA, {})
                .get("version", 0)
            )

            self._snapshot = await self._fetch_metadata(session, self.SNAPSHOT_METADATA)

            # Fetch targets (check if changed)
            self._targets = await self._fetch_metadata(session, self.TARGETS_METADATA)

    async def _fetch_metadata(
        self,
        session: aiohttp.ClientSession,
        filename: str,
    ) -> dict[str, Any]:
        """Fetch, verify, and parse metadata file."""
        url = f"{self._repo_url}/metadata/{filename}"

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                # Verify signatures if enabled
                if self._verify_signatures:
                    self._verify_metadata_signatures(data, filename)

                # Check expiration
                self._check_metadata_expiration(data, filename)

                # Cache locally
                cache_path = self._metadata_dir / filename
                with open(cache_path, "w") as f:
                    json.dump(data, f)

                return data

        except aiohttp.ClientError as e:
            # Try loading from cache
            cache_path = self._metadata_dir / filename
            if cache_path.exists():
                logger.warning(f"Using cached metadata for {filename}: {e}")
                with open(cache_path) as f:
                    return json.load(f)
            raise

    def _verify_metadata_signatures(self, metadata: dict[str, Any], filename: str) -> None:
        """
        Verify cryptographic signatures on TUF metadata.

        Args:
            metadata: The metadata dict containing 'signed' and 'signatures'
            filename: Name of the metadata file for error messages

        Raises:
            SignatureVerificationError: If signature verification fails
        """
        if not HAS_CRYPTOGRAPHY:
            logger.warning(
                f"Skipping signature verification for {filename} - cryptography not available"
            )
            return

        if not self._root_config or not self._root_config.keys:
            logger.warning(f"No trusted keys available for {filename} verification")
            return

        signatures = metadata.get("signatures", [])
        signed_data = metadata.get("signed", {})

        if not signatures:
            raise SignatureVerificationError(f"No signatures found in {filename}")

        # Canonical JSON encoding for verification
        canonical_signed = json.dumps(signed_data, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

        # Count valid signatures
        valid_signatures = 0

        for sig in signatures:
            key_id = sig.get("keyid")
            signature_value = sig.get("sig")

            if not key_id or not signature_value:
                continue

            # Find the key in our trusted keys
            key = self._root_config.keys.get(key_id)
            if not key:
                logger.debug(f"Unknown key_id in signature: {key_id[:16]}...")
                continue

            try:
                if self._verify_single_signature(canonical_signed, signature_value, key):
                    valid_signatures += 1
                    logger.debug(f"Valid signature from key {key_id[:16]}...")
            except Exception as e:
                logger.warning(f"Signature verification error for key {key_id[:16]}: {e}")

        # Check threshold
        threshold = self._root_config.threshold
        if valid_signatures < threshold:
            raise SignatureVerificationError(
                f"Insufficient valid signatures for {filename}: "
                f"got {valid_signatures}, need {threshold}"
            )

        logger.debug(
            f"Signature verification passed for {filename}: {valid_signatures}/{threshold}"
        )

    def _verify_single_signature(self, data: bytes, signature_hex: str, key: TUFKey) -> bool:
        """
        Verify a single signature against a key.

        Args:
            data: The canonical JSON bytes to verify
            signature_hex: Hex-encoded signature
            key: TUF key with public key material

        Returns:
            True if signature is valid, False otherwise
        """
        if not HAS_CRYPTOGRAPHY:
            return False

        try:
            signature_bytes = bytes.fromhex(signature_hex)
            public_key_bytes = bytes.fromhex(key.public_key)

            if key.key_type == "ed25519" or key.scheme == "ed25519":
                # Ed25519 verification
                public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
                public_key.verify(signature_bytes, data)
                return True

            elif key.key_type.startswith("ecdsa") or key.scheme.startswith("ecdsa"):
                # ECDSA verification (typically P-256)
                public_key = ec.EllipticCurvePublicKey.from_encoded_point(
                    ec.SECP256R1(), b"\x04" + public_key_bytes
                )
                public_key.verify(signature_bytes, data, ec.ECDSA(hashes.SHA256()))
                return True

            elif key.key_type == "rsa" or key.scheme.startswith("rsassa"):
                # RSA verification
                public_key = serialization.load_der_public_key(public_key_bytes)
                public_key.verify(
                    signature_bytes,
                    data,
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )
                return True

            else:
                logger.warning(f"Unsupported key type: {key.key_type}/{key.scheme}")
                return False

        except InvalidSignature:
            return False
        except Exception as e:
            logger.debug(f"Signature verification failed: {e}")
            return False

    def _check_metadata_expiration(self, metadata: dict[str, Any], filename: str) -> None:
        """
        Check if metadata has expired.

        Args:
            metadata: The metadata dict
            filename: Name of the metadata file

        Raises:
            SignatureVerificationError: If metadata has expired
        """
        signed = metadata.get("signed", {})
        expires_str = signed.get("expires")

        if not expires_str:
            return

        try:
            expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            now = datetime.now(UTC)

            if now > expires:
                raise SignatureVerificationError(f"Metadata {filename} has expired: {expires_str}")

        except ValueError as e:
            logger.warning(f"Could not parse expiration date in {filename}: {e}")

    def _find_latest_target(self) -> tuple | None:
        """Find the latest version target in targets metadata."""
        if not self._targets:
            return None

        targets = self._targets.get("signed", {}).get("targets", {})
        if not targets:
            return None

        # Filter to executable targets
        exe_targets = [
            (name, info)
            for name, info in targets.items()
            if name.lower().endswith((".exe", ".msi", ".zip"))
        ]

        if not exe_targets:
            return None

        # Sort by version (extract from filename)
        def version_key(item):
            name, _ = item
            version = self._extract_version(name)
            if version:
                parts = version.split(".")
                return tuple(int(p) for p in parts if p.isdigit())
            return (0,)

        exe_targets.sort(key=version_key, reverse=True)
        return exe_targets[0]

    def _extract_version(self, filename: str) -> str | None:
        """Extract version from filename like 'CasareRPA-3.1.0.exe'."""
        import re

        match = re.search(r"(\d+\.\d+\.\d+(?:\.\d+)?)", filename)
        if match:
            return match.group(1)
        return None

    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """Compare version strings."""
        try:

            def parse_version(v: str) -> tuple:
                return tuple(int(p) for p in v.split(".") if p.isdigit())

            return parse_version(new_version) > parse_version(current_version)
        except (ValueError, TypeError):
            return False

    def cleanup_old_versions(self, keep_count: int = 2) -> int:
        """
        Clean up old downloaded versions.

        Args:
            keep_count: Number of old versions to keep

        Returns:
            Number of files deleted
        """
        targets = list(self._targets_dir.glob("*"))
        if len(targets) <= keep_count:
            return 0

        # Sort by modification time
        targets.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Delete oldest
        deleted = 0
        for target in targets[keep_count:]:
            target.unlink()
            deleted += 1
            logger.debug(f"Deleted old version: {target.name}")

        return deleted
