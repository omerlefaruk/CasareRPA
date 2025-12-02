-- Migration 002: Robot Orchestration Tables
-- Creates/updates tables for robot management, job orchestration, and workflow assignments
-- Aligns with domain entities: Robot, Job, RobotAssignment, NodeRobotOverride

-- =========================
-- Robots Table
-- =========================
-- Stores registered robot agents with their capabilities and status
CREATE TABLE IF NOT EXISTS robots (
    robot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'offline',
    environment VARCHAR(255) DEFAULT 'default',

    -- Capabilities and configuration (JSONB for flexibility)
    capabilities JSONB DEFAULT '[]'::JSONB,  -- Array of RobotCapability strings
    tags JSONB DEFAULT '[]'::JSONB,          -- Custom tags for filtering
    metrics JSONB DEFAULT '{}'::JSONB,       -- Runtime metrics (CPU, memory, etc.)

    -- Concurrency settings
    max_concurrent_jobs INTEGER DEFAULT 1,
    current_job_ids JSONB DEFAULT '[]'::JSONB,  -- Array of job UUIDs currently executing

    -- Workflow assignments (denormalized for quick lookup)
    assigned_workflows JSONB DEFAULT '[]'::JSONB,  -- Array of workflow UUIDs

    -- Heartbeat and timing
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT robots_hostname_unique UNIQUE (hostname),
    CONSTRAINT robots_valid_status CHECK (status IN (
        'offline', 'online', 'busy', 'error', 'maintenance'
    )),
    CONSTRAINT robots_valid_max_concurrent CHECK (max_concurrent_jobs >= 0)
);

-- Indexes for robots
CREATE INDEX IF NOT EXISTS idx_robots_status ON robots(status);
CREATE INDEX IF NOT EXISTS idx_robots_hostname ON robots(hostname);
CREATE INDEX IF NOT EXISTS idx_robots_environment ON robots(environment);
CREATE INDEX IF NOT EXISTS idx_robots_last_heartbeat ON robots(last_heartbeat DESC);
CREATE INDEX IF NOT EXISTS idx_robots_capabilities ON robots USING GIN(capabilities);
CREATE INDEX IF NOT EXISTS idx_robots_tags ON robots USING GIN(tags);

-- Trigger for robots updated_at
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_robots_updated_at'
    ) THEN
        CREATE TRIGGER update_robots_updated_at
        BEFORE UPDATE ON robots
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;


-- =========================
-- Enhanced Jobs Table
-- =========================
-- Note: This adds columns to the existing jobs table from migration 001
-- If jobs table already has these columns, these ALTERs will be no-ops

-- Add robot reference as foreign key
DO $$
BEGIN
    -- Add robot_uuid column if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'robot_uuid'
    ) THEN
        ALTER TABLE jobs ADD COLUMN robot_uuid UUID REFERENCES robots(robot_id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_jobs_robot_uuid ON jobs(robot_uuid);
    END IF;

    -- Add payload column for job input data
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'payload'
    ) THEN
        ALTER TABLE jobs ADD COLUMN payload JSONB DEFAULT '{}'::JSONB;
    END IF;

    -- Add workflow_name for denormalized access
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'workflow_name'
    ) THEN
        ALTER TABLE jobs ADD COLUMN workflow_name VARCHAR(255);
    END IF;

    -- Add progress tracking
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'progress'
    ) THEN
        ALTER TABLE jobs ADD COLUMN progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100);
    END IF;

    -- Add current_node tracking
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'current_node'
    ) THEN
        ALTER TABLE jobs ADD COLUMN current_node VARCHAR(255) DEFAULT '';
    END IF;

    -- Add duration tracking
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'duration_ms'
    ) THEN
        ALTER TABLE jobs ADD COLUMN duration_ms INTEGER DEFAULT 0;
    END IF;

    -- Add logs storage
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'logs'
    ) THEN
        ALTER TABLE jobs ADD COLUMN logs TEXT DEFAULT '';
    END IF;

    -- Add scheduled_time for future execution
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'scheduled_time'
    ) THEN
        ALTER TABLE jobs ADD COLUMN scheduled_time TIMESTAMP WITH TIME ZONE;
    END IF;

    -- Add timeout_seconds per job
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'timeout_seconds'
    ) THEN
        ALTER TABLE jobs ADD COLUMN timeout_seconds INTEGER DEFAULT 3600;
    END IF;

    -- Add created_by for audit
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs' AND column_name = 'created_by'
    ) THEN
        ALTER TABLE jobs ADD COLUMN created_by VARCHAR(255);
    END IF;
END $$;


-- =========================
-- Workflow Robot Assignments Table
-- =========================
-- Maps workflows to their default robots
CREATE TABLE IF NOT EXISTS workflow_robot_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    robot_id UUID NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,

    -- Assignment configuration
    is_default BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    notes TEXT,

    -- Audit fields
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT workflow_robot_unique UNIQUE (workflow_id, robot_id),
    CONSTRAINT valid_priority CHECK (priority >= 0)
);

-- Indexes for workflow_robot_assignments
CREATE INDEX IF NOT EXISTS idx_workflow_assignments_workflow ON workflow_robot_assignments(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_assignments_robot ON workflow_robot_assignments(robot_id);
CREATE INDEX IF NOT EXISTS idx_workflow_assignments_default ON workflow_robot_assignments(workflow_id)
    WHERE is_default = TRUE;

-- Trigger for updated_at
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_workflow_assignments_updated_at'
    ) THEN
        CREATE TRIGGER update_workflow_assignments_updated_at
        BEFORE UPDATE ON workflow_robot_assignments
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;


-- =========================
-- Node Robot Overrides Table
-- =========================
-- Allows specific nodes to target different robots than the workflow default
CREATE TABLE IF NOT EXISTS node_robot_overrides (
    override_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,

    -- Target robot (NULL means use capability matching)
    robot_id UUID REFERENCES robots(robot_id) ON DELETE CASCADE,

    -- Capability-based routing (when robot_id is NULL)
    required_capabilities JSONB DEFAULT '[]'::JSONB,

    -- Override metadata
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit fields
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT node_override_unique UNIQUE (workflow_id, node_id),
    CONSTRAINT override_has_target CHECK (
        robot_id IS NOT NULL OR jsonb_array_length(required_capabilities) > 0
    )
);

-- Indexes for node_robot_overrides
CREATE INDEX IF NOT EXISTS idx_node_overrides_workflow ON node_robot_overrides(workflow_id);
CREATE INDEX IF NOT EXISTS idx_node_overrides_robot ON node_robot_overrides(robot_id);
CREATE INDEX IF NOT EXISTS idx_node_overrides_active ON node_robot_overrides(workflow_id)
    WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_node_overrides_capabilities ON node_robot_overrides USING GIN(required_capabilities);

-- Trigger for updated_at
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_node_overrides_updated_at'
    ) THEN
        CREATE TRIGGER update_node_overrides_updated_at
        BEFORE UPDATE ON node_robot_overrides
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;


-- =========================
-- Robot Heartbeats Table (Optional: for historical tracking)
-- =========================
-- Stores heartbeat history for monitoring and analytics
CREATE TABLE IF NOT EXISTS robot_heartbeats (
    heartbeat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    robot_id UUID NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Status at heartbeat time
    status VARCHAR(50) NOT NULL,
    current_jobs INTEGER DEFAULT 0,

    -- Metrics snapshot
    metrics JSONB DEFAULT '{}'::JSONB,

    -- Connection info
    ip_address INET,
    latency_ms INTEGER
);

-- Index for time-series queries
CREATE INDEX IF NOT EXISTS idx_heartbeats_robot_time ON robot_heartbeats(robot_id, timestamp DESC);

-- Partition by time for efficient cleanup (optional, requires PG 10+)
-- CREATE INDEX IF NOT EXISTS idx_heartbeats_timestamp ON robot_heartbeats(timestamp);


-- =========================
-- Statistics Views
-- =========================

-- Robot utilization statistics
CREATE OR REPLACE VIEW robot_stats AS
SELECT
    r.robot_id,
    r.name AS robot_name,
    r.hostname,
    r.status,
    r.environment,
    r.max_concurrent_jobs,
    jsonb_array_length(r.current_job_ids) AS current_jobs,
    CASE
        WHEN r.max_concurrent_jobs = 0 THEN 0
        ELSE ROUND(jsonb_array_length(r.current_job_ids)::NUMERIC / r.max_concurrent_jobs * 100, 2)
    END AS utilization_percent,
    r.last_heartbeat,
    COUNT(j.job_id) AS total_jobs_run,
    COUNT(CASE WHEN j.status = 'completed' THEN 1 END) AS completed_jobs,
    COUNT(CASE WHEN j.status = 'failed' THEN 1 END) AS failed_jobs,
    AVG(j.duration_ms)::INTEGER AS avg_duration_ms
FROM robots r
LEFT JOIN jobs j ON r.robot_id = j.robot_uuid
GROUP BY r.robot_id, r.name, r.hostname, r.status, r.environment,
         r.max_concurrent_jobs, r.current_job_ids, r.last_heartbeat;

-- Workflow assignment summary
CREATE OR REPLACE VIEW workflow_assignment_stats AS
SELECT
    w.workflow_id,
    w.workflow_name,
    COUNT(DISTINCT wra.robot_id) AS assigned_robot_count,
    array_agg(DISTINCT r.name) FILTER (WHERE r.name IS NOT NULL) AS assigned_robot_names,
    COUNT(DISTINCT nro.node_id) AS node_override_count
FROM workflows w
LEFT JOIN workflow_robot_assignments wra ON w.workflow_id = wra.workflow_id
LEFT JOIN robots r ON wra.robot_id = r.robot_id
LEFT JOIN node_robot_overrides nro ON w.workflow_id = nro.workflow_id AND nro.is_active = TRUE
GROUP BY w.workflow_id, w.workflow_name;


-- =========================
-- Grant Permissions
-- =========================
GRANT SELECT, INSERT, UPDATE, DELETE ON robots TO casare_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON workflow_robot_assignments TO casare_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON node_robot_overrides TO casare_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON robot_heartbeats TO casare_user;
GRANT SELECT ON robot_stats TO casare_user;
GRANT SELECT ON workflow_assignment_stats TO casare_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO casare_user;
