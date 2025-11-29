-- Migration: 010_robots_table
-- Description: Create robots table for tracking registered automation robots
-- Created: 2024-11-28

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Robots table stores registered automation agents (Robot instances)
-- Each robot has capabilities (browser types, desktop access, etc.) and tracks
-- its current status and active job assignment.

CREATE TABLE IF NOT EXISTS robots (
    -- Unique robot identifier (typically machine-id + process-id or UUID)
    robot_id TEXT PRIMARY KEY,

    -- Hostname where the robot is running
    hostname TEXT NOT NULL,

    -- Robot capabilities as JSONB for flexible querying
    -- Example: {"browsers": ["chromium", "firefox"], "desktop": true, "os": "windows"}
    capabilities JSONB NOT NULL DEFAULT '{}',

    -- Current robot status with constrained values
    status TEXT NOT NULL DEFAULT 'idle'
        CHECK (status IN ('idle', 'busy', 'offline', 'failed')),

    -- Currently assigned job (NULL if idle)
    -- References pgqueuer job table when integrated
    current_job_id UUID,

    -- Timestamp when robot first registered
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Last heartbeat timestamp for liveness detection
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for efficient status filtering (finding idle robots for job assignment)
CREATE INDEX IF NOT EXISTS idx_robots_status ON robots(status);

-- Index for finding robots by last_seen (stale robot detection)
CREATE INDEX IF NOT EXISTS idx_robots_last_seen ON robots(last_seen);

-- Partial index for finding idle robots quickly (most common query)
CREATE INDEX IF NOT EXISTS idx_robots_idle ON robots(robot_id) WHERE status = 'idle';

-- GIN index for capability queries (e.g., find robots with browser=chromium)
CREATE INDEX IF NOT EXISTS idx_robots_capabilities ON robots USING GIN (capabilities);

-- Add comment for documentation
COMMENT ON TABLE robots IS 'Registered automation robots with their capabilities and current status';
COMMENT ON COLUMN robots.robot_id IS 'Unique identifier for the robot instance';
COMMENT ON COLUMN robots.capabilities IS 'JSONB capabilities: browsers, desktop access, OS, etc.';
COMMENT ON COLUMN robots.status IS 'Current status: idle, busy, offline, or failed';
COMMENT ON COLUMN robots.current_job_id IS 'UUID of currently executing job, NULL if idle';


-- ============================================================================
-- DOWN MIGRATION (in separate file: 010_robots_table_down.sql)
-- ============================================================================
