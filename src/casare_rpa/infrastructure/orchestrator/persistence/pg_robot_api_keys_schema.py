"""Database schema helpers for robot API keys.

These SQL snippets are used by both the Orchestrator API server and the
Orchestrator engine when running in DB-backed mode.

Important:
- Production deployments may exist with partial/older schemas (missing columns).
- `CREATE TABLE IF NOT EXISTS` does not backfill columns.
- Index creation can fail if it references a missing column.

To keep startup resilient, table creation, ALTERs, and index creation are split so
callers can:
1) Create tables (if missing)
2) Add missing columns (if older)
3) Create indexes (once columns exist)
"""

from __future__ import annotations

from typing import Sequence


CREATE_ROBOT_API_KEYS_TABLE_SQL = """
-- NOTE: Index creation is intentionally separated to keep startup resilient for older schemas.
CREATE TABLE IF NOT EXISTS robot_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    robot_id VARCHAR(255) NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,

    api_key_hash VARCHAR(64) NOT NULL,

    name VARCHAR(255),
    description TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    last_used_ip INET,

    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,
    revoked_by VARCHAR(255),
    revoke_reason TEXT,

    created_by VARCHAR(255),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""


CREATE_ROBOT_API_KEYS_INDEXES_SQL = """
-- Uniqueness on api_key_hash (older schemas might not have the named constraint)
CREATE UNIQUE INDEX IF NOT EXISTS robot_api_keys_hash_unique_idx
    ON robot_api_keys(api_key_hash);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash_active
    ON robot_api_keys(api_key_hash)
    WHERE is_revoked = FALSE;

CREATE INDEX IF NOT EXISTS idx_api_keys_robot
    ON robot_api_keys(robot_id);

CREATE INDEX IF NOT EXISTS idx_api_keys_expires
    ON robot_api_keys(expires_at)
    WHERE expires_at IS NOT NULL AND is_revoked = FALSE;

CREATE INDEX IF NOT EXISTS idx_api_keys_created_at
    ON robot_api_keys(created_at DESC);
"""


CREATE_ROBOT_API_KEY_AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS robot_api_key_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID NOT NULL REFERENCES robot_api_keys(id) ON DELETE CASCADE,
    robot_id VARCHAR(255) NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,

    event_type VARCHAR(50) NOT NULL,
    event_time TIMESTAMPTZ DEFAULT NOW(),

    ip_address INET,
    user_agent VARCHAR(500),
    endpoint VARCHAR(255),

    details JSONB DEFAULT '{}'::JSONB,

    CONSTRAINT valid_event_type CHECK (event_type IN (
        'auth_success', 'auth_failure', 'created', 'revoked', 'expired', 'rotated'
    ))
);

CREATE INDEX IF NOT EXISTS idx_api_key_audit_time
    ON robot_api_key_audit(event_time DESC);

CREATE INDEX IF NOT EXISTS idx_api_key_audit_robot
    ON robot_api_key_audit(robot_id);

CREATE INDEX IF NOT EXISTS idx_api_key_audit_key
    ON robot_api_key_audit(api_key_id);
"""


ROBOT_API_KEYS_COMPAT_ALTERS: Sequence[str] = (
    # Hash column name drift: older deployments use `key_hash` (text) while newer code expects `api_key_hash`.
    # We keep both optional and let callers choose the available one.
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS api_key_hash VARCHAR(64)",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS key_hash TEXT",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS description TEXT",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS last_used_ip INET",
    # Older deployments may use `is_active` instead of `is_revoked`.
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS is_revoked BOOLEAN DEFAULT FALSE",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS revoked_by VARCHAR(255)",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS revoke_reason TEXT",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS created_by VARCHAR(255)",
    "ALTER TABLE robot_api_keys ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
)


async def ensure_robot_api_key_tables(conn) -> None:
    """Best-effort ensure for robot API key tables + compatibility columns."""
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception:
        pass

    try:
        await conn.execute(CREATE_ROBOT_API_KEYS_TABLE_SQL)
    except Exception as e:
        # Some Postgres deployments don't have pgcrypto (gen_random_uuid).
        # Fall back to uuid-ossp (uuid_generate_v4) if available.
        if "gen_random_uuid" in str(e):
            try:
                await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            except Exception:
                pass
            await conn.execute(
                CREATE_ROBOT_API_KEYS_TABLE_SQL.replace(
                    "gen_random_uuid()", "uuid_generate_v4()"
                )
            )
        else:
            raise
    for stmt in ROBOT_API_KEYS_COMPAT_ALTERS:
        await conn.execute(stmt)

    # Create indexes safely based on which hash column exists.
    cols = await conn.fetch(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name='robot_api_keys'
        """
    )
    colset = {r["column_name"] for r in cols}
    hash_col = (
        "api_key_hash"
        if "api_key_hash" in colset
        else ("key_hash" if "key_hash" in colset else None)
    )

    # If both legacy and new hash columns exist, keep them in sync so existing keys remain valid.
    if "api_key_hash" in colset and "key_hash" in colset:
        await conn.execute(
            """
            UPDATE robot_api_keys
            SET api_key_hash = COALESCE(api_key_hash, key_hash),
                key_hash = COALESCE(key_hash, api_key_hash)
            WHERE api_key_hash IS NULL OR key_hash IS NULL
            """
        )

    if hash_col:
        await conn.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS robot_api_keys_hash_unique_idx ON robot_api_keys({hash_col})"
        )
        if "is_revoked" in colset:
            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_api_keys_hash_active
                    ON robot_api_keys({hash_col})
                    WHERE is_revoked = FALSE
                """
            )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_keys_robot ON robot_api_keys(robot_id)"
        )
        if "expires_at" in colset and "is_revoked" in colset:
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_keys_expires
                    ON robot_api_keys(expires_at)
                    WHERE expires_at IS NOT NULL AND is_revoked = FALSE
                """
            )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_keys_created_at ON robot_api_keys(created_at DESC)"
        )
    try:
        await conn.execute(CREATE_ROBOT_API_KEY_AUDIT_TABLE_SQL)
    except Exception as e:
        if "gen_random_uuid" in str(e):
            await conn.execute(
                CREATE_ROBOT_API_KEY_AUDIT_TABLE_SQL.replace(
                    "gen_random_uuid()", "uuid_generate_v4()"
                )
            )
        else:
            raise


__all__ = [
    "CREATE_ROBOT_API_KEYS_TABLE_SQL",
    "CREATE_ROBOT_API_KEYS_INDEXES_SQL",
    "CREATE_ROBOT_API_KEY_AUDIT_TABLE_SQL",
    "ROBOT_API_KEYS_COMPAT_ALTERS",
    "ensure_robot_api_key_tables",
]
