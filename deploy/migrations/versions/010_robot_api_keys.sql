-- Migration: 010_robot_api_keys
-- Description: Robot API key authentication and audit logging
-- Consolidated from:
--   - src/casare_rpa/infrastructure/persistence/migrations/003_robot_api_keys.sql
-- Created: 2024-12-03

-- =============================================================================
-- ROBOT API KEYS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS robot_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    robot_id UUID NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,

    -- API key hash (SHA-256 of the raw key)
    api_key_hash VARCHAR(64) NOT NULL,

    -- Key metadata
    name VARCHAR(255),
    description TEXT,

    -- Lifecycle tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    last_used_ip INET,

    -- Revocation
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,
    revoked_by VARCHAR(255),
    revoke_reason TEXT,

    -- Audit
    created_by VARCHAR(255),

    -- Constraints
    CONSTRAINT robot_api_keys_hash_unique UNIQUE (api_key_hash)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Index for looking up key by hash (primary authentication lookup)
CREATE INDEX IF NOT EXISTS idx_api_keys_hash_active
    ON robot_api_keys(api_key_hash)
    WHERE is_revoked = FALSE;

-- Index for listing keys by robot
CREATE INDEX IF NOT EXISTS idx_api_keys_robot
    ON robot_api_keys(robot_id);

-- Index for finding expired keys
CREATE INDEX IF NOT EXISTS idx_api_keys_expires
    ON robot_api_keys(expires_at)
    WHERE expires_at IS NOT NULL AND is_revoked = FALSE;

-- Index for audit queries
CREATE INDEX IF NOT EXISTS idx_api_keys_created_at
    ON robot_api_keys(created_at DESC);

-- =============================================================================
-- API KEY AUDIT LOG TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS robot_api_key_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID NOT NULL REFERENCES robot_api_keys(id) ON DELETE CASCADE,
    robot_id UUID NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,

    -- Event details
    event_type VARCHAR(50) NOT NULL,
    event_time TIMESTAMPTZ DEFAULT NOW(),

    -- Request context
    ip_address INET,
    user_agent VARCHAR(500),
    endpoint VARCHAR(255),

    -- Additional details
    details JSONB DEFAULT '{}'::JSONB,

    -- Constraints
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'auth_success', 'auth_failure', 'created', 'revoked', 'expired', 'rotated'
    ))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_api_key_audit_key
    ON robot_api_key_audit(api_key_id, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_api_key_audit_robot
    ON robot_api_key_audit(robot_id, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_api_key_audit_failures
    ON robot_api_key_audit(event_time DESC)
    WHERE event_type = 'auth_failure';

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to validate an API key hash
CREATE OR REPLACE FUNCTION validate_api_key_hash(key_hash VARCHAR(64))
RETURNS TABLE (
    robot_id UUID,
    key_id UUID,
    is_valid BOOLEAN,
    reason VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        k.robot_id,
        k.id AS key_id,
        CASE
            WHEN k.id IS NULL THEN FALSE
            WHEN k.is_revoked THEN FALSE
            WHEN k.expires_at IS NOT NULL AND k.expires_at < NOW() THEN FALSE
            ELSE TRUE
        END AS is_valid,
        CASE
            WHEN k.id IS NULL THEN 'not_found'::VARCHAR(50)
            WHEN k.is_revoked THEN 'revoked'::VARCHAR(50)
            WHEN k.expires_at IS NOT NULL AND k.expires_at < NOW() THEN 'expired'::VARCHAR(50)
            ELSE 'valid'::VARCHAR(50)
        END AS reason
    FROM robot_api_keys k
    WHERE k.api_key_hash = key_hash
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to update last_used timestamp
CREATE OR REPLACE FUNCTION update_api_key_last_used(
    key_hash VARCHAR(64),
    client_ip INET DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE robot_api_keys
    SET
        last_used_at = NOW(),
        last_used_ip = COALESCE(client_ip, last_used_ip)
    WHERE api_key_hash = key_hash
    AND is_revoked = FALSE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active API keys with robot info
CREATE OR REPLACE VIEW robot_api_keys_active AS
SELECT
    k.id AS key_id,
    k.robot_id,
    r.name AS robot_name,
    r.hostname AS robot_hostname,
    k.name AS key_name,
    k.created_at,
    k.expires_at,
    k.last_used_at,
    k.last_used_ip,
    k.created_by,
    CASE
        WHEN k.expires_at IS NOT NULL AND k.expires_at < NOW() THEN 'expired'
        WHEN k.is_revoked THEN 'revoked'
        ELSE 'active'
    END AS status,
    EXTRACT(EPOCH FROM (NOW() - k.last_used_at)) / 86400 AS days_since_last_use
FROM robot_api_keys k
JOIN robots r ON k.robot_id = r.robot_id
WHERE k.is_revoked = FALSE
ORDER BY k.created_at DESC;

-- API key usage statistics
CREATE OR REPLACE VIEW robot_api_key_stats AS
SELECT
    k.robot_id,
    r.name AS robot_name,
    COUNT(k.id) AS total_keys,
    COUNT(CASE WHEN k.is_revoked = FALSE AND (k.expires_at IS NULL OR k.expires_at > NOW()) THEN 1 END) AS active_keys,
    COUNT(CASE WHEN k.is_revoked = TRUE THEN 1 END) AS revoked_keys,
    COUNT(CASE WHEN k.expires_at IS NOT NULL AND k.expires_at < NOW() THEN 1 END) AS expired_keys,
    MAX(k.last_used_at) AS last_key_used_at,
    MIN(k.created_at) AS first_key_created_at
FROM robot_api_keys k
JOIN robots r ON k.robot_id = r.robot_id
GROUP BY k.robot_id, r.name
ORDER BY r.name;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger for updated_at
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_robot_api_keys_updated_at'
    ) THEN
        CREATE TRIGGER update_robot_api_keys_updated_at
        BEFORE UPDATE ON robot_api_keys
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE robot_api_keys IS 'Hashed API keys for robot authentication';
COMMENT ON TABLE robot_api_key_audit IS 'Audit log for API key usage';
COMMENT ON FUNCTION validate_api_key_hash IS 'Validate an API key hash and return status';
COMMENT ON FUNCTION update_api_key_last_used IS 'Update last_used timestamp on successful auth';
