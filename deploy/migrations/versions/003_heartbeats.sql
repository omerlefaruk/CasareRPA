-- Migration: 003_heartbeats
-- Description: Robot heartbeat tracking for monitoring and analytics
-- Consolidated from:
--   - src/casare_rpa/infrastructure/database/migrations/011_heartbeats_table.sql
--   - src/casare_rpa/infrastructure/persistence/migrations/002_robots_orchestration.sql (partial)
-- Created: 2024-12-03

-- =============================================================================
-- ROBOT HEARTBEATS TABLE
-- =============================================================================
-- Stores heartbeat history for monitoring and analytics
CREATE TABLE IF NOT EXISTS robot_heartbeats (
    heartbeat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    robot_id UUID NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Status at heartbeat time
    status VARCHAR(50) NOT NULL,
    current_jobs INTEGER DEFAULT 0,

    -- Metrics snapshot (CPU, memory, disk, etc.)
    metrics JSONB DEFAULT '{}'::JSONB,

    -- Connection info
    ip_address INET,
    latency_ms INTEGER
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Index for time-series queries
CREATE INDEX IF NOT EXISTS idx_heartbeats_robot_time
    ON robot_heartbeats(robot_id, timestamp DESC);

-- Index for finding recent heartbeats
CREATE INDEX IF NOT EXISTS idx_heartbeats_timestamp
    ON robot_heartbeats(timestamp DESC);

-- Index for status-based queries
CREATE INDEX IF NOT EXISTS idx_heartbeats_status
    ON robot_heartbeats(status, timestamp DESC);

-- Partial index for recent data (last 24 hours)
-- Note: Use a scheduled job to clean up old heartbeats
CREATE INDEX IF NOT EXISTS idx_heartbeats_recent
    ON robot_heartbeats(robot_id, timestamp DESC)
    WHERE timestamp > NOW() - INTERVAL '24 hours';

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to record a heartbeat
CREATE OR REPLACE FUNCTION record_robot_heartbeat(
    p_robot_id UUID,
    p_status VARCHAR(50),
    p_current_jobs INTEGER DEFAULT 0,
    p_metrics JSONB DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_latency_ms INTEGER DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_heartbeat_id UUID;
BEGIN
    -- Insert heartbeat record
    INSERT INTO robot_heartbeats (
        robot_id, status, current_jobs, metrics, ip_address, latency_ms
    ) VALUES (
        p_robot_id, p_status, p_current_jobs, COALESCE(p_metrics, '{}'), p_ip_address, p_latency_ms
    )
    RETURNING heartbeat_id INTO v_heartbeat_id;

    -- Update robot's last_heartbeat and last_seen
    UPDATE robots
    SET
        last_heartbeat = NOW(),
        last_seen = NOW(),
        status = p_status,
        metrics = COALESCE(p_metrics, metrics)
    WHERE robot_id = p_robot_id;

    RETURN v_heartbeat_id;
END;
$$ LANGUAGE plpgsql;

-- Function to check robot health (stale heartbeats)
CREATE OR REPLACE FUNCTION check_robot_health(
    p_stale_threshold_seconds INTEGER DEFAULT 60
)
RETURNS TABLE (
    robot_id UUID,
    robot_name VARCHAR(255),
    last_heartbeat TIMESTAMPTZ,
    seconds_since_heartbeat NUMERIC,
    current_status VARCHAR(50),
    is_stale BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.robot_id,
        r.name AS robot_name,
        r.last_heartbeat,
        EXTRACT(EPOCH FROM (NOW() - r.last_heartbeat))::NUMERIC AS seconds_since_heartbeat,
        r.status AS current_status,
        EXTRACT(EPOCH FROM (NOW() - r.last_heartbeat)) > p_stale_threshold_seconds AS is_stale
    FROM robots r
    WHERE r.status != 'offline'
    ORDER BY r.last_heartbeat ASC NULLS FIRST;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to mark stale robots as offline
CREATE OR REPLACE FUNCTION mark_stale_robots_offline(
    p_stale_threshold_seconds INTEGER DEFAULT 120
)
RETURNS TABLE (
    robot_id UUID,
    robot_name VARCHAR(255),
    old_status VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    UPDATE robots r
    SET
        status = 'offline',
        updated_at = NOW()
    WHERE r.status IN ('online', 'busy')
      AND (
          r.last_heartbeat IS NULL
          OR EXTRACT(EPOCH FROM (NOW() - r.last_heartbeat)) > p_stale_threshold_seconds
      )
    RETURNING r.robot_id, r.name, r.status;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old heartbeats
CREATE OR REPLACE FUNCTION cleanup_old_heartbeats(
    p_retention_hours INTEGER DEFAULT 24
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM robot_heartbeats
    WHERE timestamp < NOW() - (p_retention_hours || ' hours')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View for latest heartbeat per robot
CREATE OR REPLACE VIEW robot_latest_heartbeat AS
SELECT DISTINCT ON (robot_id)
    h.heartbeat_id,
    h.robot_id,
    r.name AS robot_name,
    h.timestamp,
    h.status,
    h.current_jobs,
    h.metrics,
    h.ip_address,
    h.latency_ms,
    EXTRACT(EPOCH FROM (NOW() - h.timestamp))::INTEGER AS seconds_ago
FROM robot_heartbeats h
JOIN robots r ON h.robot_id = r.robot_id
ORDER BY h.robot_id, h.timestamp DESC;

-- View for heartbeat statistics
CREATE OR REPLACE VIEW robot_heartbeat_stats AS
SELECT
    r.robot_id,
    r.name AS robot_name,
    COUNT(h.heartbeat_id) AS heartbeat_count_24h,
    AVG(h.latency_ms)::INTEGER AS avg_latency_ms,
    MAX(h.timestamp) AS last_heartbeat,
    MIN(h.timestamp) AS first_heartbeat_24h,
    COUNT(DISTINCT h.status) AS status_changes
FROM robots r
LEFT JOIN robot_heartbeats h ON r.robot_id = h.robot_id
    AND h.timestamp > NOW() - INTERVAL '24 hours'
GROUP BY r.robot_id, r.name;

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE robot_heartbeats IS 'Heartbeat history for robot monitoring and analytics';
COMMENT ON COLUMN robot_heartbeats.metrics IS 'System metrics snapshot (CPU, memory, disk, etc.)';
COMMENT ON FUNCTION record_robot_heartbeat IS 'Record a heartbeat and update robot status';
COMMENT ON FUNCTION check_robot_health IS 'Check for stale robot heartbeats';
COMMENT ON FUNCTION mark_stale_robots_offline IS 'Mark robots with stale heartbeats as offline';
COMMENT ON FUNCTION cleanup_old_heartbeats IS 'Remove old heartbeat records beyond retention period';
