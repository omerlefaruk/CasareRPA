"""
Merkle Tree Audit Logging System.

Provides tamper-proof audit logging using Merkle trees:
- Each log entry is hashed and chained to previous entries
- Periodic Merkle root calculation for integrity verification
- Inclusion proofs for specific entries
- Chain verification to detect tampering

Compliant with:
- SOC 2 Type II audit requirements
- GDPR Article 30 (records of processing activities)
- HIPAA audit trail requirements
"""

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

# =============================================================================
# ENUMS
# =============================================================================


class AuditAction(str, Enum):
    """Auditable actions in the system."""

    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"

    # Workflow operations
    WORKFLOW_CREATE = "workflow.create"
    WORKFLOW_UPDATE = "workflow.update"
    WORKFLOW_DELETE = "workflow.delete"
    WORKFLOW_EXECUTE = "workflow.execute"
    WORKFLOW_PUBLISH = "workflow.publish"

    # Execution operations
    EXECUTION_START = "execution.start"
    EXECUTION_COMPLETE = "execution.complete"
    EXECUTION_FAIL = "execution.fail"
    EXECUTION_CANCEL = "execution.cancel"
    EXECUTION_RETRY = "execution.retry"

    # Robot operations
    ROBOT_REGISTER = "robot.register"
    ROBOT_DEREGISTER = "robot.deregister"
    ROBOT_UPDATE = "robot.update"

    # Credential operations
    CREDENTIAL_CREATE = "credential.create"
    CREDENTIAL_UPDATE = "credential.update"
    CREDENTIAL_DELETE = "credential.delete"
    CREDENTIAL_ACCESS = "credential.access"

    # User management
    USER_INVITE = "user.invite"
    USER_REMOVE = "user.remove"
    USER_ROLE_CHANGE = "user.role_change"

    # Tenant operations
    TENANT_SETTINGS_CHANGE = "tenant.settings_change"
    TENANT_BILLING_UPDATE = "tenant.billing_update"

    # API key operations
    API_KEY_CREATE = "apikey.create"
    API_KEY_REVOKE = "apikey.revoke"

    # System events
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    AUDIT_EXPORT = "audit.export"


class ResourceType(str, Enum):
    """Resource types for audit entries."""

    WORKFLOW = "workflow"
    EXECUTION = "execution"
    ROBOT = "robot"
    USER = "user"
    CREDENTIAL = "credential"
    TENANT = "tenant"
    API_KEY = "apikey"
    SYSTEM = "system"


# =============================================================================
# DATA MODELS
# =============================================================================


class AuditEntry(BaseModel):
    """A single audit log entry with hash chain."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    action: AuditAction
    actor_id: UUID
    actor_type: str = "user"  # user, robot, system
    resource_type: ResourceType
    resource_id: UUID | None = None
    tenant_id: UUID | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None

    # Hash chain fields
    entry_hash: bytes = b""
    previous_hash: bytes = b""

    class Config:
        json_encoders = {
            bytes: lambda v: v.hex() if v else "",
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class MerkleProof(BaseModel):
    """Merkle inclusion proof for an audit entry."""

    entry_id: UUID
    entry_hash: str
    merkle_root: str
    proof_path: list[tuple[str, str]]  # (hash, position: 'left' or 'right')
    tree_size: int
    verified: bool = False


class ChainVerificationResult(BaseModel):
    """Result of hash chain verification."""

    is_valid: bool
    start_id: int
    end_id: int
    entries_verified: int
    first_invalid_id: int | None = None
    error_message: str | None = None


# =============================================================================
# MERKLE TREE SERVICE
# =============================================================================


class MerkleAuditService:
    """
    Service for managing tamper-proof audit logs using Merkle trees.

    Features:
    - Hash chain linking entries sequentially
    - Merkle tree construction for efficient verification
    - Inclusion proof generation
    - Chain integrity verification
    """

    # Genesis hash for first entry (32 bytes of zeros)
    GENESIS_HASH = b"\x00" * 32

    def __init__(self, db_pool=None):
        """
        Initialize the Merkle Audit Service.

        Args:
            db_pool: Database connection pool (asyncpg) for persistence.
                     If None, operates in memory-only mode.
        """
        self._db_pool = db_pool
        self._memory_entries: list[AuditEntry] = []
        self._last_hash = self.GENESIS_HASH

    def compute_entry_hash(self, entry: AuditEntry) -> bytes:
        """
        Compute SHA-256 hash of an audit entry.

        The hash includes all critical fields to ensure integrity:
        - timestamp, action, actor, resource, details

        Args:
            entry: Audit entry to hash

        Returns:
            32-byte SHA-256 hash
        """
        # Canonical representation for hashing
        data = {
            "id": str(entry.id),
            "timestamp": entry.timestamp.isoformat(),
            "action": entry.action.value,
            "actor_id": str(entry.actor_id),
            "actor_type": entry.actor_type,
            "resource_type": entry.resource_type.value,
            "resource_id": str(entry.resource_id) if entry.resource_id else None,
            "tenant_id": str(entry.tenant_id) if entry.tenant_id else None,
            "details": entry.details,
            "previous_hash": entry.previous_hash.hex(),
        }

        # Serialize deterministically
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(json_str.encode("utf-8")).digest()

    async def append_entry(self, entry: AuditEntry) -> AuditEntry:
        """
        Append a new audit entry to the log with hash chain.

        Args:
            entry: Audit entry (without hash fields)

        Returns:
            Entry with computed hashes
        """
        # Get the last hash (chain link)
        previous_hash = await self._get_last_hash()
        entry.previous_hash = previous_hash

        # Compute this entry's hash
        entry.entry_hash = self.compute_entry_hash(entry)

        # Persist to database or memory
        if self._db_pool:
            await self._persist_entry(entry)
        else:
            self._memory_entries.append(entry)
            self._last_hash = entry.entry_hash

        logger.debug(
            f"Audit entry appended: action={entry.action.value} "
            f"hash={entry.entry_hash.hex()[:16]}..."
        )

        return entry

    async def _get_last_hash(self) -> bytes:
        """Get the hash of the last entry in the chain."""
        if self._db_pool:
            async with self._db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT entry_hash FROM audit_log
                    ORDER BY id DESC LIMIT 1
                    """
                )
                if row:
                    return bytes(row["entry_hash"])
                return self.GENESIS_HASH
        else:
            if self._memory_entries:
                return self._memory_entries[-1].entry_hash
            return self.GENESIS_HASH

    async def _persist_entry(self, entry: AuditEntry) -> None:
        """Persist entry to database."""
        if not self._db_pool:
            return

        async with self._db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log (
                    id, timestamp, action, actor_id, actor_type,
                    resource_type, resource_id, tenant_id, details,
                    ip_address, user_agent, entry_hash, previous_hash
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                entry.id,
                entry.timestamp,
                entry.action.value,
                entry.actor_id,
                entry.actor_type,
                entry.resource_type.value,
                entry.resource_id,
                entry.tenant_id,
                json.dumps(entry.details),
                entry.ip_address,
                entry.user_agent,
                entry.entry_hash,
                entry.previous_hash,
            )

    async def verify_chain(
        self,
        start_id: int | None = None,
        end_id: int | None = None,
    ) -> ChainVerificationResult:
        """
        Verify the integrity of the hash chain.

        Args:
            start_id: Starting entry ID (default: first entry)
            end_id: Ending entry ID (default: last entry)

        Returns:
            Verification result with validity status
        """
        entries = await self._get_entries_range(start_id, end_id)

        if not entries:
            return ChainVerificationResult(
                is_valid=True,
                start_id=start_id or 0,
                end_id=end_id or 0,
                entries_verified=0,
            )

        # Verify each entry's hash and chain link
        expected_previous = self.GENESIS_HASH if start_id is None else None

        for i, entry in enumerate(entries):
            # Recompute hash and compare
            computed_hash = self.compute_entry_hash(entry)

            if computed_hash != entry.entry_hash:
                logger.error(
                    f"Hash mismatch at entry {entry.id}: "
                    f"stored={entry.entry_hash.hex()[:16]} "
                    f"computed={computed_hash.hex()[:16]}"
                )
                return ChainVerificationResult(
                    is_valid=False,
                    start_id=start_id or 0,
                    end_id=end_id or len(entries) - 1,
                    entries_verified=i,
                    first_invalid_id=i,
                    error_message=f"Hash mismatch at entry {entry.id}",
                )

            # Verify chain link
            if expected_previous is not None and entry.previous_hash != expected_previous:
                logger.error(
                    f"Chain break at entry {entry.id}: "
                    f"expected_prev={expected_previous.hex()[:16]} "
                    f"actual_prev={entry.previous_hash.hex()[:16]}"
                )
                return ChainVerificationResult(
                    is_valid=False,
                    start_id=start_id or 0,
                    end_id=end_id or len(entries) - 1,
                    entries_verified=i,
                    first_invalid_id=i,
                    error_message=f"Chain link broken at entry {entry.id}",
                )

            expected_previous = entry.entry_hash

        return ChainVerificationResult(
            is_valid=True,
            start_id=start_id or 0,
            end_id=end_id or len(entries) - 1,
            entries_verified=len(entries),
        )

    async def _get_entries_range(
        self,
        start_id: int | None,
        end_id: int | None,
    ) -> list[AuditEntry]:
        """Get entries in a range for verification."""
        if self._db_pool:
            async with self._db_pool.acquire() as conn:
                query = "SELECT * FROM audit_log"
                conditions = []
                params = []

                if start_id is not None:
                    conditions.append(f"id >= ${len(params) + 1}")
                    params.append(start_id)
                if end_id is not None:
                    conditions.append(f"id <= ${len(params) + 1}")
                    params.append(end_id)

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY id ASC"

                rows = await conn.fetch(query, *params)
                return [self._row_to_entry(row) for row in rows]
        else:
            entries = self._memory_entries
            if start_id is not None:
                entries = [e for e in entries if int(str(e.id)[:8], 16) >= start_id]
            if end_id is not None:
                entries = [e for e in entries if int(str(e.id)[:8], 16) <= end_id]
            return entries

    def _row_to_entry(self, row) -> AuditEntry:
        """Convert database row to AuditEntry."""
        return AuditEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            action=AuditAction(row["action"]),
            actor_id=row["actor_id"],
            actor_type=row["actor_type"],
            resource_type=ResourceType(row["resource_type"]),
            resource_id=row["resource_id"],
            tenant_id=row["tenant_id"],
            details=json.loads(row["details"]) if row["details"] else {},
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            entry_hash=bytes(row["entry_hash"]),
            previous_hash=bytes(row["previous_hash"]),
        )

    def build_merkle_tree(self, entry_hashes: list[bytes]) -> bytes:
        """
        Build a Merkle tree from entry hashes and return the root.

        Args:
            entry_hashes: List of entry hashes (leaves)

        Returns:
            Merkle root hash (32 bytes)
        """
        if not entry_hashes:
            return self.GENESIS_HASH

        # Copy to avoid modifying input
        level = list(entry_hashes)

        # Build tree bottom-up
        while len(level) > 1:
            next_level = []

            # Process pairs
            for i in range(0, len(level), 2):
                left = level[i]
                # If odd number, duplicate last hash
                right = level[i + 1] if i + 1 < len(level) else left

                # Combine and hash
                combined = left + right
                parent = hashlib.sha256(combined).digest()
                next_level.append(parent)

            level = next_level

        return level[0]

    async def compute_merkle_root(
        self,
        start_id: int | None = None,
        end_id: int | None = None,
    ) -> bytes:
        """
        Compute Merkle root for a range of entries.

        Args:
            start_id: Starting entry ID
            end_id: Ending entry ID

        Returns:
            Merkle root hash
        """
        entries = await self._get_entries_range(start_id, end_id)
        hashes = [e.entry_hash for e in entries]
        return self.build_merkle_tree(hashes)

    def generate_merkle_proof(
        self,
        entry_hash: bytes,
        all_hashes: list[bytes],
    ) -> list[tuple[bytes, str]]:
        """
        Generate Merkle inclusion proof for an entry.

        Args:
            entry_hash: Hash of the entry to prove
            all_hashes: All entry hashes in the tree

        Returns:
            List of (sibling_hash, position) tuples forming the proof path
        """
        if entry_hash not in all_hashes:
            return []

        proof = []
        level = list(all_hashes)
        index = level.index(entry_hash)

        while len(level) > 1:
            next_level = []

            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left

                # If our target is at this position, record sibling
                if i == index:
                    proof.append((right, "right"))
                elif i + 1 == index:
                    proof.append((left, "left"))

                parent = hashlib.sha256(left + right).digest()
                next_level.append(parent)

            # Update index for next level
            index = index // 2
            level = next_level

        return proof

    def verify_merkle_proof(
        self,
        entry_hash: bytes,
        merkle_root: bytes,
        proof: list[tuple[bytes, str]],
    ) -> bool:
        """
        Verify a Merkle inclusion proof.

        Args:
            entry_hash: Hash of the entry to verify
            merkle_root: Expected Merkle root
            proof: Proof path from generate_merkle_proof

        Returns:
            True if proof is valid
        """
        current = entry_hash

        for sibling_hash, position in proof:
            if position == "left":
                combined = sibling_hash + current
            else:
                combined = current + sibling_hash

            current = hashlib.sha256(combined).digest()

        return current == merkle_root

    async def export_audit_log(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        include_proof: bool = True,
    ) -> dict[str, Any]:
        """
        Export audit log with optional Merkle proofs for compliance.

        Args:
            start_date: Filter start date
            end_date: Filter end date
            include_proof: Include Merkle root and verification info

        Returns:
            Export data with entries and optional verification info
        """
        entries = await self._get_entries_range(None, None)

        # Filter by date if specified
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]

        export_data = {
            "export_timestamp": datetime.now(UTC).isoformat(),
            "entry_count": len(entries),
            "entries": [
                {
                    "id": str(e.id),
                    "timestamp": e.timestamp.isoformat(),
                    "action": e.action.value,
                    "actor_id": str(e.actor_id),
                    "resource_type": e.resource_type.value,
                    "resource_id": str(e.resource_id) if e.resource_id else None,
                    "details": e.details,
                    "entry_hash": e.entry_hash.hex(),
                }
                for e in entries
            ],
        }

        if include_proof and entries:
            hashes = [e.entry_hash for e in entries]
            merkle_root = self.build_merkle_tree(hashes)
            export_data["merkle_root"] = merkle_root.hex()
            export_data["verification"] = {
                "algorithm": "sha256",
                "chain_type": "sequential_hash_chain",
                "merkle_tree_type": "binary_merkle_tree",
            }

        return export_data


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


# Global service instance
_audit_service: MerkleAuditService | None = None


def get_audit_service(db_pool=None) -> MerkleAuditService:
    """Get or create the global audit service instance."""
    global _audit_service
    if _audit_service is None:
        _audit_service = MerkleAuditService(db_pool)
    return _audit_service


async def log_audit_event(
    action: AuditAction,
    actor_id: UUID,
    resource_type: ResourceType,
    resource_id: UUID | None = None,
    tenant_id: UUID | None = None,
    details: dict[str, Any] | None = None,
    actor_type: str = "user",
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditEntry:
    """
    Convenience function to log an audit event.

    Args:
        action: The action being audited
        actor_id: ID of the actor (user, robot, system)
        resource_type: Type of resource affected
        resource_id: ID of the specific resource
        tenant_id: Tenant context
        details: Additional details
        actor_type: Type of actor (user, robot, system)
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        The created audit entry with hash chain
    """
    service = get_audit_service()

    entry = AuditEntry(
        action=action,
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_id=tenant_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return await service.append_entry(entry)
