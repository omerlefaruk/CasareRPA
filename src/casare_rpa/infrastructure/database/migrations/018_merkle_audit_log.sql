-- Migration: 018_merkle_audit_log.sql
-- Description: Create Merkle tree audit logging table for tamper-proof compliance logging
-- Created: 2024-11-30

-- =============================================================================
-- AUDIT LOG TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    -- Primary key (auto-incrementing for efficient ordering)
    id BIGSERIAL PRIMARY KEY,

    -- Entry identifier (UUID for external references)
    entry_id UUID NOT NULL DEFAULT gen_random_uuid(),

    -- Timestamp of the action (stored in UTC)
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Action performed (enum values from AuditAction)
    action VARCHAR(50) NOT NULL,

    -- Actor information
    actor_id UUID NOT NULL,
    actor_type VARCHAR(20) NOT NULL DEFAULT 'user',

    -- Resource information
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,

    -- Tenant context for multi-tenancy
    tenant_id UUID,

    -- Additional details (JSONB for flexible schema)
    details JSONB DEFAULT '{}',

    -- Request context
    ip_address INET,
    user_agent TEXT,

    -- Hash chain fields for tamper detection
    entry_hash BYTEA NOT NULL,
    previous_hash BYTEA NOT NULL,

    -- Periodic Merkle root (updated in batches)
    merkle_root BYTEA,
    merkle_root_computed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT audit_log_entry_id_unique UNIQUE (entry_id),
    CONSTRAINT audit_log_hash_length CHECK (octet_length(entry_hash) = 32),
    CONSTRAINT audit_log_previous_hash_length CHECK (octet_length(previous_hash) = 32)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Primary query patterns
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log(actor_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_tenant ON audit_log(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- Hash chain verification (sequential access)
CREATE INDEX IF NOT EXISTS idx_audit_log_chain ON audit_log(id ASC);

-- Entry lookup
CREATE INDEX IF NOT EXISTS idx_audit_log_entry_id ON audit_log(entry_id);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Enable RLS for multi-tenant isolation
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view their tenant's audit logs
CREATE POLICY audit_log_tenant_isolation ON audit_log
    FOR SELECT
    USING (
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
        OR tenant_id IS NULL  -- System-level events visible to all
        OR current_setting('app.is_admin', true)::boolean = true
    );

-- Policy: Only system can insert audit logs
CREATE POLICY audit_log_insert_only_system ON audit_log
    FOR INSERT
    WITH CHECK (true);  -- Inserts handled by application layer

-- Policy: Audit logs are immutable (no updates)
CREATE POLICY audit_log_no_update ON audit_log
    FOR UPDATE
    USING (false);

-- Policy: Audit logs cannot be deleted
CREATE POLICY audit_log_no_delete ON audit_log
    FOR DELETE
    USING (false);

-- =============================================================================
-- MERKLE ROOT TRACKING TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_merkle_roots (
    id SERIAL PRIMARY KEY,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    start_entry_id BIGINT NOT NULL,
    end_entry_id BIGINT NOT NULL,
    merkle_root BYTEA NOT NULL,
    entry_count INT NOT NULL,
    verification_status VARCHAR(20) DEFAULT 'valid',

    CONSTRAINT merkle_root_hash_length CHECK (octet_length(merkle_root) = 32),
    CONSTRAINT merkle_root_range_valid CHECK (end_entry_id >= start_entry_id)
);

CREATE INDEX IF NOT EXISTS idx_merkle_roots_computed_at ON audit_merkle_roots(computed_at DESC);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to get the latest entry hash for chain continuation
CREATE OR REPLACE FUNCTION get_latest_audit_hash()
RETURNS BYTEA AS $$
DECLARE
    latest_hash BYTEA;
BEGIN
    SELECT entry_hash INTO latest_hash
    FROM audit_log
    ORDER BY id DESC
    LIMIT 1;

    -- Return genesis hash if no entries exist
    IF latest_hash IS NULL THEN
        RETURN '\x0000000000000000000000000000000000000000000000000000000000000000'::bytea;
    END IF;

    RETURN latest_hash;
END;
$$ LANGUAGE plpgsql;

-- Function to verify chain integrity between two entries
CREATE OR REPLACE FUNCTION verify_audit_chain(start_id BIGINT, end_id BIGINT)
RETURNS TABLE (
    is_valid BOOLEAN,
    entries_checked INT,
    first_invalid_id BIGINT
) AS $$
DECLARE
    expected_hash BYTEA;
    current_entry RECORD;
    count INT := 0;
BEGIN
    -- Get hash before start_id (or genesis hash)
    SELECT entry_hash INTO expected_hash
    FROM audit_log
    WHERE id = start_id - 1;

    IF expected_hash IS NULL AND start_id > 1 THEN
        RETURN QUERY SELECT false, 0, start_id;
        RETURN;
    END IF;

    -- Use genesis hash if starting from beginning
    IF expected_hash IS NULL THEN
        expected_hash := '\x0000000000000000000000000000000000000000000000000000000000000000'::bytea;
    END IF;

    -- Check each entry in range
    FOR current_entry IN
        SELECT id, previous_hash, entry_hash
        FROM audit_log
        WHERE id >= start_id AND id <= end_id
        ORDER BY id ASC
    LOOP
        count := count + 1;

        -- Verify chain link
        IF current_entry.previous_hash != expected_hash THEN
            RETURN QUERY SELECT false, count, current_entry.id;
            RETURN;
        END IF;

        expected_hash := current_entry.entry_hash;
    END LOOP;

    RETURN QUERY SELECT true, count, NULL::BIGINT;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE audit_log IS 'Tamper-proof audit log with Merkle tree hashing for compliance';
COMMENT ON COLUMN audit_log.entry_hash IS 'SHA-256 hash of entry content for integrity verification';
COMMENT ON COLUMN audit_log.previous_hash IS 'Hash of previous entry forming sequential chain';
COMMENT ON COLUMN audit_log.merkle_root IS 'Periodic Merkle root for efficient batch verification';
COMMENT ON TABLE audit_merkle_roots IS 'Historical Merkle roots for audit verification checkpoints';
