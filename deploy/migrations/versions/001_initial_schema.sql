-- Migration: 001_initial_schema
-- Description: Core tables - robots, workflows, users, and base infrastructure
-- Consolidated from:
--   - deploy/supabase/migrations/001_initial_schema.sql
--   - src/casare_rpa/infrastructure/persistence/migrations/001_workflows.sql
--   - src/casare_rpa/infrastructure/persistence/migrations/002_robots_orchestration.sql
--   - src/casare_rpa/infrastructure/database/migrations/010_robots_table.sql
--   - migrations/001_robot_hardening.sql
-- Created: 2024-12-03

-- =============================================================================
-- EXTENSIONS
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- UTILITY FUNCTION: Updated timestamp trigger
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- WORKFLOWS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_name VARCHAR(255) NOT NULL,
    workflow_json JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    description TEXT,
    tags VARCHAR(255)[],

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),

    -- Execution settings
    timeout_seconds INTEGER DEFAULT 3600,
    max_retries INTEGER DEFAULT 3,

    -- Full-text search vector
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', COALESCE(workflow_name, '') || ' ' || COALESCE(description, ''))
    ) STORED
);

-- Indexes for workflows
CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_workflows_search ON workflows USING GIN(search_vector);

-- Trigger for workflows updated_at
CREATE TRIGGER update_workflows_updated_at
BEFORE UPDATE ON workflows
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROBOTS TABLE
-- =============================================================================
-- Consolidated robot definition with all features from multiple sources
CREATE TABLE IF NOT EXISTS robots (
    robot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'offline',
    environment VARCHAR(255) DEFAULT 'default',

    -- Capabilities and configuration
    capabilities JSONB DEFAULT '[]'::JSONB,
    tags JSONB DEFAULT '[]'::JSONB,
    metrics JSONB DEFAULT '{}'::JSONB,

    -- Concurrency settings
    max_concurrent_jobs INTEGER DEFAULT 1,
    current_job_ids JSONB DEFAULT '[]'::JSONB,

    -- Workflow assignments
    assigned_workflows JSONB DEFAULT '[]'::JSONB,

    -- Heartbeat and timing
    last_heartbeat TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Machine identifier (unique per machine)
    machine_id VARCHAR(255),

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
CREATE INDEX IF NOT EXISTS idx_robots_machine_id ON robots(machine_id) WHERE machine_id IS NOT NULL;

-- Trigger for robots updated_at
CREATE TRIGGER update_robots_updated_at
BEFORE UPDATE ON robots
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- JOBS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    robot_id VARCHAR(255),
    robot_uuid UUID REFERENCES robots(robot_id) ON DELETE SET NULL,

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 10,
    execution_mode VARCHAR(20) DEFAULT 'lan',

    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    claimed_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    scheduled_time TIMESTAMPTZ,

    -- Results
    result JSONB,
    error TEXT,
    payload JSONB DEFAULT '{}'::JSONB,
    workflow_name VARCHAR(255),

    -- Progress tracking
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_node VARCHAR(255) DEFAULT '',
    duration_ms INTEGER DEFAULT 0,
    logs TEXT DEFAULT '',

    -- Retry handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 3600,

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,
    created_by VARCHAR(255),

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'queued', 'claimed', 'running',
        'completed', 'failed', 'cancelled', 'timeout'
    )),
    CONSTRAINT valid_execution_mode CHECK (execution_mode IN ('lan', 'internet')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 0 AND 20)
);

-- Indexes for jobs
CREATE INDEX IF NOT EXISTS idx_jobs_workflow_id ON jobs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_robot_id ON jobs(robot_id);
CREATE INDEX IF NOT EXISTS idx_jobs_robot_uuid ON jobs(robot_uuid);
CREATE INDEX IF NOT EXISTS idx_jobs_execution_mode ON jobs(execution_mode);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(status, execution_mode, priority, created_at)
    WHERE status = 'queued';

-- =============================================================================
-- SCHEDULES TABLE (Basic)
-- =============================================================================
CREATE TABLE IF NOT EXISTS schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(workflow_id) ON DELETE CASCADE,

    -- Schedule configuration
    schedule_name VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,

    -- Execution tracking
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    run_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::JSONB
);

-- Indexes for schedules
CREATE INDEX IF NOT EXISTS idx_schedules_workflow_id ON schedules(workflow_id);
CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run_at)
    WHERE enabled = TRUE;

-- Trigger for updated_at
CREATE TRIGGER update_schedules_updated_at
BEFORE UPDATE ON schedules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- WORKFLOW VERSIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS workflow_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    workflow_json JSONB NOT NULL,
    change_description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),

    UNIQUE (workflow_id, version_number)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_workflow_versions_workflow_id
    ON workflow_versions(workflow_id, version_number DESC);

-- =============================================================================
-- WORKFLOW ROBOT ASSIGNMENTS TABLE
-- =============================================================================
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

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

-- =============================================================================
-- NODE ROBOT OVERRIDES TABLE
-- =============================================================================
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

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

-- =============================================================================
-- STATISTICS VIEWS
-- =============================================================================

-- Workflow execution statistics
CREATE OR REPLACE VIEW workflow_stats AS
SELECT
    w.workflow_id,
    w.workflow_name,
    COUNT(j.job_id) AS total_jobs,
    COUNT(CASE WHEN j.status = 'completed' THEN 1 END) AS completed_jobs,
    COUNT(CASE WHEN j.status = 'failed' THEN 1 END) AS failed_jobs,
    COUNT(CASE WHEN j.status = 'running' THEN 1 END) AS running_jobs,
    AVG(EXTRACT(EPOCH FROM (j.completed_at - j.started_at))) AS avg_duration_seconds,
    MAX(j.completed_at) AS last_run_at
FROM workflows w
LEFT JOIN jobs j ON w.workflow_id = j.workflow_id
GROUP BY w.workflow_id, w.workflow_name;

-- Job queue statistics
CREATE OR REPLACE VIEW queue_stats AS
SELECT
    execution_mode,
    COUNT(*) AS pending_count,
    AVG(priority) AS avg_priority,
    MIN(created_at) AS oldest_job,
    MAX(created_at) AS newest_job
FROM jobs
WHERE status = 'queued'
GROUP BY execution_mode;

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

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE workflows IS 'Workflow definitions for RPA automation';
COMMENT ON TABLE robots IS 'Registered robot agents for workflow execution';
COMMENT ON TABLE jobs IS 'Job queue for workflow execution tracking';
COMMENT ON TABLE schedules IS 'Scheduled workflow executions';
COMMENT ON TABLE workflow_versions IS 'Version history for workflows';
COMMENT ON TABLE workflow_robot_assignments IS 'Maps workflows to their default robots';
COMMENT ON TABLE node_robot_overrides IS 'Per-node robot targeting overrides';
