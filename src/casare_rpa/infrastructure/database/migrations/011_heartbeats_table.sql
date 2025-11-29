-- Migration: 011_heartbeats_table
-- Description: Create robot_heartbeats table for monitoring and progress tracking
-- Created: 2024-11-28

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Robot heartbeats store periodic status updates from running robots
-- Used for:
-- - Liveness detection (robot still running)
-- - Job progress monitoring
-- - Resource usage tracking (memory, CPU)
-- - Current node execution tracking for debugging

CREATE TABLE IF NOT EXISTS robot_heartbeats (
    -- Auto-incrementing primary key for efficient inserts
    id BIGSERIAL PRIMARY KEY,

    -- Reference to the robot sending the heartbeat
    robot_id TEXT NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,

    -- Job being executed (NULL if robot is idle but still sending heartbeats)
    job_id UUID,

    -- Execution progress as percentage (0-100)
    progress_percent INTEGER CHECK (progress_percent >= 0 AND progress_percent <= 100),

    -- Currently executing node identifier for debugging
    current_node TEXT,

    -- Memory usage in megabytes
    memory_mb FLOAT CHECK (memory_mb >= 0),

    -- CPU usage percentage (0-100, can exceed 100 on multi-core)
    cpu_percent FLOAT CHECK (cpu_percent >= 0),

    -- Heartbeat timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Composite index for querying recent heartbeats by robot (most common query pattern)
-- DESC on timestamp for efficient "latest heartbeat" queries
CREATE INDEX IF NOT EXISTS idx_heartbeats_robot ON robot_heartbeats(robot_id, timestamp DESC);

-- Index for job-based queries (find all heartbeats for a specific job)
CREATE INDEX IF NOT EXISTS idx_heartbeats_job ON robot_heartbeats(job_id) WHERE job_id IS NOT NULL;

-- Index for timestamp-based cleanup (removing old heartbeats)
CREATE INDEX IF NOT EXISTS idx_heartbeats_timestamp ON robot_heartbeats(timestamp);

-- Add comments for documentation
COMMENT ON TABLE robot_heartbeats IS 'Periodic status updates from robots including progress and resource usage';
COMMENT ON COLUMN robot_heartbeats.progress_percent IS 'Workflow execution progress (0-100)';
COMMENT ON COLUMN robot_heartbeats.current_node IS 'Node ID currently being executed';
COMMENT ON COLUMN robot_heartbeats.memory_mb IS 'Robot process memory usage in MB';
COMMENT ON COLUMN robot_heartbeats.cpu_percent IS 'Robot process CPU usage percentage';


-- ============================================================================
-- Optional: Create function for getting latest heartbeat per robot
-- ============================================================================

CREATE OR REPLACE FUNCTION get_latest_heartbeat(p_robot_id TEXT)
RETURNS TABLE (
    robot_id TEXT,
    job_id UUID,
    progress_percent INTEGER,
    current_node TEXT,
    memory_mb FLOAT,
    cpu_percent FLOAT,
    timestamp TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        h.robot_id,
        h.job_id,
        h.progress_percent,
        h.current_node,
        h.memory_mb,
        h.cpu_percent,
        h.timestamp
    FROM robot_heartbeats h
    WHERE h.robot_id = p_robot_id
    ORDER BY h.timestamp DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_latest_heartbeat IS 'Get the most recent heartbeat for a robot';


-- ============================================================================
-- Optional: Create function for cleaning up old heartbeats
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_old_heartbeats(retention_hours INTEGER DEFAULT 24)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM robot_heartbeats
    WHERE timestamp < NOW() - (retention_hours || ' hours')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION cleanup_old_heartbeats IS 'Remove heartbeats older than retention_hours (default 24)';


-- ============================================================================
-- DOWN MIGRATION (in separate file: 011_heartbeats_table_down.sql)
-- ============================================================================
