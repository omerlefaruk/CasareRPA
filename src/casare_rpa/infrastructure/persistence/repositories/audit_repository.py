"""
CasareRPA - Audit Repository Module.

Provides persistent SQLite storage for audit events with:
- Efficient indexing for common queries
- Hash chain for tamper detection
- Configurable retention policy
- Export capabilities (CSV, JSON)
- Aggregate statistics

The repository uses SQLite for local development and can be extended
to PostgreSQL for production deployments.
"""

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import aiosqlite
from loguru import logger

from casare_rpa.infrastructure.security.vault_client import (
    AuditEvent,
    AuditEventType,
)


class AuditRepository:
    """
    Repository for persistent audit event storage.

    Uses SQLite for efficient local storage with async operations.
    Implements hash chain verification for tamper detection.

    Usage:
        repo = AuditRepository()
        await repo.initialize()

        # Log event
        event = AuditEvent(event_type=AuditEventType.SECRET_READ, path="/secrets/api")
        await repo.log_event(event)

        # Query events
        events = await repo.get_events(event_type="secret_read", limit=100)

        # Get statistics
        stats = await repo.get_event_counts(group_by="event_type", period="day")

        await repo.close()
    """

    DEFAULT_DB_PATH = ".casare/audit/audit.db"
    DEFAULT_RETENTION_DAYS = 90

    def __init__(
        self,
        db_path: str | None = None,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ) -> None:
        """
        Initialize the audit repository.

        Args:
            db_path: Path to SQLite database file
            retention_days: Number of days to retain audit events
        """
        self._db_path = db_path or self.DEFAULT_DB_PATH
        self._retention_days = retention_days
        self._connection: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()
        self._last_hash: str | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the database connection and schema.

        Creates the database file and tables if they don't exist.
        """
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            # Ensure directory exists
            db_dir = Path(self._db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

            # Connect to database
            self._connection = await aiosqlite.connect(self._db_path)
            self._connection.row_factory = aiosqlite.Row

            # Create schema
            await self._create_schema()

            # Load last hash for chain continuity
            self._last_hash = await self._get_last_hash()

            self._initialized = True
            logger.info(f"Audit repository initialized: {self._db_path}")

    async def _create_schema(self) -> None:
        """Create database schema if not exists."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        await self._connection.executescript("""
            -- Audit events table
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                resource TEXT,
                workflow_id TEXT,
                robot_id TEXT,
                user_id TEXT,
                success INTEGER NOT NULL DEFAULT 1,
                error_message TEXT,
                client_ip TEXT,
                metadata TEXT,
                hash_chain TEXT NOT NULL
            );

            -- Indexes for common queries
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_events(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_type
                ON audit_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_resource
                ON audit_events(resource);
            CREATE INDEX IF NOT EXISTS idx_audit_workflow
                ON audit_events(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_audit_robot
                ON audit_events(robot_id);
            CREATE INDEX IF NOT EXISTS idx_audit_user
                ON audit_events(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_success
                ON audit_events(success);

            -- Cleanup tracking table
            CREATE TABLE IF NOT EXISTS audit_cleanup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cleanup_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                events_deleted INTEGER NOT NULL DEFAULT 0,
                retention_days INTEGER NOT NULL,
                duration_ms INTEGER,
                status TEXT NOT NULL DEFAULT 'completed',
                error_message TEXT
            );

            -- Integrity check table
            CREATE TABLE IF NOT EXISTS audit_integrity_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                events_checked INTEGER NOT NULL DEFAULT 0,
                chain_valid INTEGER NOT NULL DEFAULT 1,
                first_invalid_id TEXT,
                error_message TEXT
            );
        """)
        await self._connection.commit()

    async def _get_last_hash(self) -> str | None:
        """Get the last hash chain value for continuity."""
        if not self._connection:
            return None

        cursor = await self._connection.execute(
            "SELECT hash_chain FROM audit_events ORDER BY timestamp DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        return row["hash_chain"] if row else None

    def _calculate_hash_chain(self, event: AuditEvent, previous_hash: str | None) -> str:
        """
        Calculate hash chain value for tamper detection.

        The hash chain links each event to its predecessor, making it
        impossible to modify or delete events without breaking the chain.

        Args:
            event: Audit event to hash
            previous_hash: Hash of the previous event

        Returns:
            SHA-256 hash of the chain
        """
        prev = previous_hash or "genesis"
        timestamp_str = event.timestamp.isoformat()
        data = f"{prev}:{event.event_id}:{timestamp_str}:{event.event_type.value}"
        return hashlib.sha256(data.encode()).hexdigest()

    async def log_event(self, event: AuditEvent) -> str:
        """
        Log an audit event to persistent storage.

        Args:
            event: AuditEvent to store

        Returns:
            The event ID
        """
        if not self._initialized:
            await self.initialize()

        async with self._lock:
            # Calculate hash chain
            hash_chain = self._calculate_hash_chain(event, self._last_hash)

            # Serialize metadata
            metadata_json = json.dumps(event.metadata) if event.metadata else None

            # Insert event
            await self._connection.execute(
                """
                INSERT INTO audit_events (
                    id, event_type, timestamp, resource, workflow_id,
                    robot_id, user_id, success, error_message, client_ip,
                    metadata, hash_chain
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    event.path,
                    event.workflow_id,
                    event.robot_id,
                    event.user_id,
                    1 if event.success else 0,
                    event.error_message,
                    event.client_ip,
                    metadata_json,
                    hash_chain,
                ),
            )
            await self._connection.commit()

            # Update last hash
            self._last_hash = hash_chain

            logger.debug(f"Audit event logged: {event.event_id} ({event.event_type.value})")
            return event.event_id

    async def log_events_batch(self, events: list[AuditEvent]) -> int:
        """
        Log multiple audit events in a batch.

        Args:
            events: List of AuditEvent objects

        Returns:
            Number of events logged
        """
        if not events:
            return 0

        if not self._initialized:
            await self.initialize()

        async with self._lock:
            records = []
            current_hash = self._last_hash

            for event in events:
                hash_chain = self._calculate_hash_chain(event, current_hash)
                metadata_json = json.dumps(event.metadata) if event.metadata else None

                records.append(
                    (
                        event.event_id,
                        event.event_type.value,
                        event.timestamp.isoformat(),
                        event.path,
                        event.workflow_id,
                        event.robot_id,
                        event.user_id,
                        1 if event.success else 0,
                        event.error_message,
                        event.client_ip,
                        metadata_json,
                        hash_chain,
                    )
                )
                current_hash = hash_chain

            await self._connection.executemany(
                """
                INSERT INTO audit_events (
                    id, event_type, timestamp, resource, workflow_id,
                    robot_id, user_id, success, error_message, client_ip,
                    metadata, hash_chain
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            await self._connection.commit()

            self._last_hash = current_hash
            logger.debug(f"Logged batch of {len(events)} audit events")
            return len(events)

    async def get_events(
        self,
        event_type: str | None = None,
        resource: str | None = None,
        workflow_id: str | None = None,
        robot_id: str | None = None,
        user_id: str | None = None,
        success: bool | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """
        Query audit events with filtering.

        Args:
            event_type: Filter by event type
            resource: Filter by resource path
            workflow_id: Filter by workflow ID
            robot_id: Filter by robot ID
            user_id: Filter by user ID
            success: Filter by success status
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of matching AuditEvent objects
        """
        if not self._initialized:
            await self.initialize()

        # Build query
        conditions = []
        params = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        if resource:
            conditions.append("resource LIKE ?")
            params.append(f"%{resource}%")

        if workflow_id:
            conditions.append("workflow_id = ?")
            params.append(workflow_id)

        if robot_id:
            conditions.append("robot_id = ?")
            params.append(robot_id)

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        if success is not None:
            conditions.append("success = ?")
            params.append(1 if success else 0)

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())

        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM audit_events
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_event(dict(row)) for row in rows]

    async def get_event_by_id(self, event_id: str) -> AuditEvent | None:
        """
        Get a single audit event by ID.

        Args:
            event_id: Event identifier

        Returns:
            AuditEvent or None if not found
        """
        if not self._initialized:
            await self.initialize()

        cursor = await self._connection.execute(
            "SELECT * FROM audit_events WHERE id = ?",
            (event_id,),
        )
        row = await cursor.fetchone()

        return self._row_to_event(dict(row)) if row else None

    async def get_event_counts(
        self,
        group_by: str = "event_type",
        period: str = "day",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, int]:
        """
        Get aggregate event counts.

        Args:
            group_by: Column to group by (event_type, resource, workflow_id, etc.)
            period: Time period for aggregation (hour, day, week, month)
            start_time: Filter events after this time
            end_time: Filter events before this time

        Returns:
            Dictionary of {group_value: count}
        """
        if not self._initialized:
            await self.initialize()

        valid_columns = {
            "event_type",
            "resource",
            "workflow_id",
            "robot_id",
            "user_id",
            "success",
        }
        if group_by not in valid_columns:
            group_by = "event_type"

        # Build time filter
        conditions = []
        params = []

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT {group_by}, COUNT(*) as count
            FROM audit_events
            WHERE {where_clause}
            GROUP BY {group_by}
            ORDER BY count DESC
        """

        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()

        return {str(row[group_by]): row["count"] for row in rows}

    async def get_statistics(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get comprehensive audit statistics.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Dictionary with various statistics
        """
        if not self._initialized:
            await self.initialize()

        conditions = []
        params = []

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Total counts
        cursor = await self._connection.execute(
            f"""
            SELECT
                COUNT(*) as total_events,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                MIN(timestamp) as oldest_event,
                MAX(timestamp) as newest_event
            FROM audit_events
            WHERE {where_clause}
            """,
            params,
        )
        totals = dict(await cursor.fetchone())

        # Event type breakdown
        type_counts = await self.get_event_counts(
            group_by="event_type",
            start_time=start_time,
            end_time=end_time,
        )

        return {
            "total_events": totals["total_events"] or 0,
            "successful_events": totals["successful"] or 0,
            "failed_events": totals["failed"] or 0,
            "oldest_event": totals["oldest_event"],
            "newest_event": totals["newest_event"],
            "events_by_type": type_counts,
        }

    async def verify_integrity(self, limit: int = 1000) -> dict[str, Any]:
        """
        Verify the integrity of the audit hash chain.

        Checks that all events are properly chained and no tampering occurred.

        Args:
            limit: Maximum number of events to verify

        Returns:
            Dictionary with verification results
        """
        if not self._initialized:
            await self.initialize()

        cursor = await self._connection.execute(
            """
            SELECT id, event_type, timestamp, hash_chain
            FROM audit_events
            ORDER BY timestamp ASC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()

        if not rows:
            return {
                "valid": True,
                "events_checked": 0,
                "message": "No events to verify",
            }

        previous_hash: str | None = None
        invalid_id: str | None = None

        for row in rows:
            # Recreate expected hash
            prev = previous_hash or "genesis"
            data = f"{prev}:{row['id']}:{row['timestamp']}:{row['event_type']}"
            expected_hash = hashlib.sha256(data.encode()).hexdigest()

            if expected_hash != row["hash_chain"]:
                invalid_id = row["id"]
                break

            previous_hash = row["hash_chain"]

        # Log integrity check
        await self._connection.execute(
            """
            INSERT INTO audit_integrity_checks (
                events_checked, chain_valid, first_invalid_id
            ) VALUES (?, ?, ?)
            """,
            (len(rows), 1 if invalid_id is None else 0, invalid_id),
        )
        await self._connection.commit()

        if invalid_id:
            return {
                "valid": False,
                "events_checked": len(rows),
                "first_invalid_id": invalid_id,
                "message": f"Chain broken at event {invalid_id}",
            }

        return {
            "valid": True,
            "events_checked": len(rows),
            "message": "All events verified successfully",
        }

    async def cleanup_old_events(
        self,
        retention_days: int | None = None,
    ) -> dict[str, Any]:
        """
        Remove audit events older than retention period.

        Args:
            retention_days: Days to retain (uses default if None)

        Returns:
            Dictionary with cleanup results
        """
        if not self._initialized:
            await self.initialize()

        days = retention_days or self._retention_days
        cutoff = datetime.now(UTC) - timedelta(days=days)
        start_time = datetime.now(UTC)

        try:
            cursor = await self._connection.execute(
                "SELECT COUNT(*) as count FROM audit_events WHERE timestamp < ?",
                (cutoff.isoformat(),),
            )
            count_row = await cursor.fetchone()
            events_to_delete = count_row["count"]

            if events_to_delete > 0:
                await self._connection.execute(
                    "DELETE FROM audit_events WHERE timestamp < ?",
                    (cutoff.isoformat(),),
                )
                await self._connection.commit()

            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            # Log cleanup
            await self._connection.execute(
                """
                INSERT INTO audit_cleanup_history (
                    events_deleted, retention_days, duration_ms, status
                ) VALUES (?, ?, ?, 'completed')
                """,
                (events_to_delete, days, duration_ms),
            )
            await self._connection.commit()

            logger.info(
                f"Audit cleanup: deleted {events_to_delete} events "
                f"older than {days} days ({duration_ms}ms)"
            )

            return {
                "events_deleted": events_to_delete,
                "retention_days": days,
                "duration_ms": duration_ms,
                "status": "completed",
            }

        except Exception as e:
            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            await self._connection.execute(
                """
                INSERT INTO audit_cleanup_history (
                    retention_days, duration_ms, status, error_message
                ) VALUES (?, ?, 'failed', ?)
                """,
                (days, duration_ms, str(e)),
            )
            await self._connection.commit()

            logger.error(f"Audit cleanup failed: {e}")
            raise

    async def export_to_json(
        self,
        output_path: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """
        Export audit events to JSON file.

        Args:
            output_path: Path for output file
            start_time: Filter events after this time
            end_time: Filter events before this time

        Returns:
            Number of events exported
        """
        events = await self.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=100000,
        )

        export_data = {
            "exported_at": datetime.now(UTC).isoformat(),
            "event_count": len(events),
            "events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type.value,
                    "timestamp": e.timestamp.isoformat(),
                    "path": e.path,
                    "workflow_id": e.workflow_id,
                    "robot_id": e.robot_id,
                    "user_id": e.user_id,
                    "success": e.success,
                    "error_message": e.error_message,
                    "client_ip": e.client_ip,
                    "metadata": e.metadata,
                }
                for e in events
            ],
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(export_data, indent=2))

        logger.info(f"Exported {len(events)} audit events to {output_path}")
        return len(events)

    async def export_to_csv(
        self,
        output_path: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """
        Export audit events to CSV file.

        Args:
            output_path: Path for output file
            start_time: Filter events after this time
            end_time: Filter events before this time

        Returns:
            Number of events exported
        """
        import csv

        events = await self.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=100000,
        )

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "event_id",
                    "event_type",
                    "timestamp",
                    "path",
                    "workflow_id",
                    "robot_id",
                    "user_id",
                    "success",
                    "error_message",
                    "client_ip",
                    "metadata",
                ]
            )

            for event in events:
                writer.writerow(
                    [
                        event.event_id,
                        event.event_type.value,
                        event.timestamp.isoformat(),
                        event.path or "",
                        event.workflow_id or "",
                        event.robot_id or "",
                        event.user_id or "",
                        "true" if event.success else "false",
                        event.error_message or "",
                        event.client_ip or "",
                        json.dumps(event.metadata) if event.metadata else "",
                    ]
                )

        logger.info(f"Exported {len(events)} audit events to {output_path}")
        return len(events)

    def _row_to_event(self, row: dict[str, Any]) -> AuditEvent:
        """
        Convert database row to AuditEvent.

        Args:
            row: Database row dictionary

        Returns:
            AuditEvent object
        """
        # Parse timestamp
        timestamp_str = row.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            timestamp = datetime.now(UTC)

        # Parse metadata
        metadata_str = row.get("metadata", "")
        try:
            metadata = json.loads(metadata_str) if metadata_str else {}
        except json.JSONDecodeError:
            metadata = {}

        # Parse event type
        event_type_str = row.get("event_type", "secret_read")
        try:
            event_type = AuditEventType(event_type_str)
        except ValueError:
            event_type = AuditEventType.SECRET_READ

        return AuditEvent(
            event_id=row.get("id", ""),
            event_type=event_type,
            timestamp=timestamp,
            path=row.get("resource"),
            workflow_id=row.get("workflow_id"),
            robot_id=row.get("robot_id"),
            user_id=row.get("user_id"),
            success=bool(row.get("success", 1)),
            error_message=row.get("error_message"),
            client_ip=row.get("client_ip"),
            metadata=metadata,
        )

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._initialized = False
            logger.debug("Audit repository closed")

    async def __aenter__(self) -> "AuditRepository":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Async context manager exit."""
        await self.close()
        return False


# Global repository instance
_repository: AuditRepository | None = None


async def get_audit_repository() -> AuditRepository:
    """
    Get the global audit repository instance.

    Returns:
        Initialized AuditRepository
    """
    global _repository
    if _repository is None:
        _repository = AuditRepository()
        await _repository.initialize()
    return _repository


__all__ = [
    "AuditRepository",
    "get_audit_repository",
]
