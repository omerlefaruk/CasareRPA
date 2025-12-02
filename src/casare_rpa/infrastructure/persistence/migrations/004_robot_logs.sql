-- Migration 004: Robot Logs with 30-Day Retention
-- Real-time log streaming from robots to orchestrator with automatic cleanup.
-- Uses native partitioning for efficient retention management.

-- =========================
-- Robot Logs Table (Partitioned)
-- =========================
-- Stores log entries from robots, partitioned by timestamp for efficient retention
CREATE TABLE IF NOT EXISTS robot_logs (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    robot_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(255),
    extra JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Primary key includes timestamp for partitioning
    PRIMARY KEY (id, timestamp),

    -- Valid log levels
    CONSTRAINT valid_log_level CHECK (level IN (
        'TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    ))
) PARTITION BY RANGE (timestamp);

-- =========================
-- Create Initial Partitions
-- =========================
-- Create partitions for current month and next 2 months
-- Partitions are named robot_logs_YYYY_MM
DO $$
DECLARE
    current_date DATE := CURRENT_DATE;
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
    i INT;
BEGIN
    FOR i IN 0..2 LOOP
        start_date := DATE_TRUNC('month', current_date + (i || ' months')::INTERVAL);
        end_date := start_date + '1 month'::INTERVAL;
        partition_name := 'robot_logs_' || TO_CHAR(start_date, 'YYYY_MM');

        IF NOT EXISTS (
            SELECT 1 FROM pg_class WHERE relname = partition_name
        ) THEN
            EXECUTE FORMAT(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF robot_logs
                FOR VALUES FROM (%L) TO (%L)',
                partition_name,
                start_date,
                end_date
            );
            RAISE NOTICE 'Created partition: %', partition_name;
        END IF;
    END LOOP;
END $$;

-- =========================
-- Indexes for Efficient Queries
-- =========================
-- Index for querying by robot and time (most common query)
CREATE INDEX IF NOT EXISTS idx_robot_logs_robot_time
    ON robot_logs(robot_id, timestamp DESC);

-- Index for querying by tenant and time (admin queries)
CREATE INDEX IF NOT EXISTS idx_robot_logs_tenant_time
    ON robot_logs(tenant_id, timestamp DESC);

-- Index for filtering by level
CREATE INDEX IF NOT EXISTS idx_robot_logs_level
    ON robot_logs(level, timestamp DESC);

-- Index for full-text search on message (optional, can be slow)
CREATE INDEX IF NOT EXISTS idx_robot_logs_message_search
    ON robot_logs USING GIN (to_tsvector('english', message));

-- Index for source filtering
CREATE INDEX IF NOT EXISTS idx_robot_logs_source
    ON robot_logs(source, timestamp DESC)
    WHERE source IS NOT NULL;

-- =========================
-- Partition Management Functions
-- =========================

-- Function to create future partitions (run periodically)
CREATE OR REPLACE FUNCTION create_robot_logs_partition(target_date DATE)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := DATE_TRUNC('month', target_date);
    end_date := start_date + '1 month'::INTERVAL;
    partition_name := 'robot_logs_' || TO_CHAR(start_date, 'YYYY_MM');

    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE FORMAT(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF robot_logs
            FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            start_date,
            end_date
        );
        RETURN 'Created: ' || partition_name;
    END IF;

    RETURN 'Exists: ' || partition_name;
END;
$$ LANGUAGE plpgsql;

-- Function to drop old partitions (enforces retention policy)
CREATE OR REPLACE FUNCTION drop_old_robot_logs_partitions(retention_days INT DEFAULT 30)
RETURNS TABLE (partition_name TEXT, action TEXT) AS $$
DECLARE
    cutoff_date DATE;
    rec RECORD;
BEGIN
    cutoff_date := CURRENT_DATE - (retention_days || ' days')::INTERVAL;

    FOR rec IN
        SELECT c.relname AS name,
               TO_DATE(SUBSTRING(c.relname FROM 'robot_logs_(\d{4}_\d{2})'), 'YYYY_MM') AS partition_date
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname LIKE 'robot_logs_%'
        AND c.relname != 'robot_logs'
        AND c.relkind = 'r'
        AND n.nspname = 'public'
    LOOP
        IF rec.partition_date + '1 month'::INTERVAL < cutoff_date THEN
            EXECUTE FORMAT('DROP TABLE IF EXISTS %I', rec.name);
            partition_name := rec.name;
            action := 'DROPPED';
            RETURN NEXT;
        END IF;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function to ensure future partitions exist
CREATE OR REPLACE FUNCTION ensure_robot_logs_partitions(months_ahead INT DEFAULT 2)
RETURNS TABLE (partition_name TEXT, status TEXT) AS $$
DECLARE
    i INT;
    target_date DATE;
    result TEXT;
BEGIN
    FOR i IN 0..months_ahead LOOP
        target_date := CURRENT_DATE + (i || ' months')::INTERVAL;
        SELECT create_robot_logs_partition(target_date) INTO result;
        partition_name := 'robot_logs_' || TO_CHAR(DATE_TRUNC('month', target_date), 'YYYY_MM');
        status := result;
        RETURN NEXT;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =========================
-- Log Statistics View
-- =========================
CREATE OR REPLACE VIEW robot_logs_stats AS
SELECT
    tenant_id,
    robot_id,
    level,
    DATE_TRUNC('hour', timestamp) AS hour,
    COUNT(*) AS log_count,
    MIN(timestamp) AS first_log,
    MAX(timestamp) AS last_log
FROM robot_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY tenant_id, robot_id, level, DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC, log_count DESC;

-- Daily log summary view
CREATE OR REPLACE VIEW robot_logs_daily_summary AS
SELECT
    tenant_id,
    robot_id,
    DATE(timestamp) AS log_date,
    COUNT(*) AS total_logs,
    COUNT(CASE WHEN level = 'ERROR' THEN 1 END) AS error_count,
    COUNT(CASE WHEN level = 'WARNING' THEN 1 END) AS warning_count,
    COUNT(CASE WHEN level = 'CRITICAL' THEN 1 END) AS critical_count,
    pg_size_pretty(SUM(LENGTH(message))::BIGINT) AS estimated_size
FROM robot_logs
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY tenant_id, robot_id, DATE(timestamp)
ORDER BY log_date DESC;

-- =========================
-- Log Query Helper Functions
-- =========================

-- Function to query logs with filtering
CREATE OR REPLACE FUNCTION query_robot_logs(
    p_tenant_id UUID,
    p_robot_id UUID DEFAULT NULL,
    p_start_time TIMESTAMPTZ DEFAULT NULL,
    p_end_time TIMESTAMPTZ DEFAULT NULL,
    p_min_level VARCHAR(10) DEFAULT 'DEBUG',
    p_source VARCHAR(255) DEFAULT NULL,
    p_search_text TEXT DEFAULT NULL,
    p_limit INT DEFAULT 100,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    robot_id UUID,
    tenant_id UUID,
    timestamp TIMESTAMPTZ,
    level VARCHAR(10),
    message TEXT,
    source VARCHAR(255),
    extra JSONB
) AS $$
DECLARE
    level_order VARCHAR(10)[];
    min_level_idx INT;
BEGIN
    -- Define level ordering
    level_order := ARRAY['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];

    -- Find minimum level index
    SELECT array_position(level_order, p_min_level) INTO min_level_idx;
    IF min_level_idx IS NULL THEN
        min_level_idx := 2; -- Default to DEBUG
    END IF;

    RETURN QUERY
    SELECT
        l.id,
        l.robot_id,
        l.tenant_id,
        l.timestamp,
        l.level,
        l.message,
        l.source,
        l.extra
    FROM robot_logs l
    WHERE l.tenant_id = p_tenant_id
    AND (p_robot_id IS NULL OR l.robot_id = p_robot_id)
    AND (p_start_time IS NULL OR l.timestamp >= p_start_time)
    AND (p_end_time IS NULL OR l.timestamp <= p_end_time)
    AND array_position(level_order, l.level) >= min_level_idx
    AND (p_source IS NULL OR l.source = p_source)
    AND (p_search_text IS NULL OR l.message ILIKE '%' || p_search_text || '%')
    ORDER BY l.timestamp DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Function to get log statistics
CREATE OR REPLACE FUNCTION get_robot_logs_stats(
    p_tenant_id UUID,
    p_robot_id UUID DEFAULT NULL
)
RETURNS TABLE (
    total_count BIGINT,
    trace_count BIGINT,
    debug_count BIGINT,
    info_count BIGINT,
    warning_count BIGINT,
    error_count BIGINT,
    critical_count BIGINT,
    oldest_log TIMESTAMPTZ,
    newest_log TIMESTAMPTZ,
    storage_bytes BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT AS total_count,
        COUNT(CASE WHEN l.level = 'TRACE' THEN 1 END)::BIGINT AS trace_count,
        COUNT(CASE WHEN l.level = 'DEBUG' THEN 1 END)::BIGINT AS debug_count,
        COUNT(CASE WHEN l.level = 'INFO' THEN 1 END)::BIGINT AS info_count,
        COUNT(CASE WHEN l.level = 'WARNING' THEN 1 END)::BIGINT AS warning_count,
        COUNT(CASE WHEN l.level = 'ERROR' THEN 1 END)::BIGINT AS error_count,
        COUNT(CASE WHEN l.level = 'CRITICAL' THEN 1 END)::BIGINT AS critical_count,
        MIN(l.timestamp) AS oldest_log,
        MAX(l.timestamp) AS newest_log,
        COALESCE(SUM(LENGTH(l.message))::BIGINT, 0) AS storage_bytes
    FROM robot_logs l
    WHERE l.tenant_id = p_tenant_id
    AND (p_robot_id IS NULL OR l.robot_id = p_robot_id);
END;
$$ LANGUAGE plpgsql;

-- =========================
-- Cleanup Tracking Table
-- =========================
-- Track retention cleanup jobs for auditing
CREATE TABLE IF NOT EXISTS robot_logs_cleanup_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cleanup_time TIMESTAMPTZ DEFAULT NOW(),
    partitions_dropped TEXT[],
    rows_deleted BIGINT DEFAULT 0,
    retention_days INT NOT NULL,
    duration_ms INT,
    status VARCHAR(20) DEFAULT 'completed',
    error_message TEXT
);

-- Index for querying cleanup history
CREATE INDEX IF NOT EXISTS idx_cleanup_history_time
    ON robot_logs_cleanup_history(cleanup_time DESC);

-- =========================
-- Grant Permissions
-- =========================
GRANT SELECT, INSERT ON robot_logs TO casare_user;
GRANT SELECT ON robot_logs_stats TO casare_user;
GRANT SELECT ON robot_logs_daily_summary TO casare_user;
GRANT SELECT, INSERT, UPDATE ON robot_logs_cleanup_history TO casare_user;
GRANT EXECUTE ON FUNCTION create_robot_logs_partition TO casare_user;
GRANT EXECUTE ON FUNCTION drop_old_robot_logs_partitions TO casare_user;
GRANT EXECUTE ON FUNCTION ensure_robot_logs_partitions TO casare_user;
GRANT EXECUTE ON FUNCTION query_robot_logs TO casare_user;
GRANT EXECUTE ON FUNCTION get_robot_logs_stats TO casare_user;

-- =========================
-- Initial Setup
-- =========================
-- Ensure partitions exist for next 2 months
SELECT * FROM ensure_robot_logs_partitions(2);
