-- Migration 001: Workflow Storage Tables
-- Creates tables for storing workflows, jobs, and schedules in PostgreSQL

-- =========================
-- Workflows Table
-- =========================
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_name VARCHAR(255) NOT NULL,
    workflow_json JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    description TEXT,
    tags VARCHAR(255)[],

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),

    -- Execution settings
    timeout_seconds INTEGER DEFAULT 3600,
    max_retries INTEGER DEFAULT 3,

    -- Indexes for full-text search
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', COALESCE(workflow_name, '') || ' ' || COALESCE(description, ''))
    ) STORED
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_workflows_search ON workflows USING GIN(search_vector);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_workflows_updated_at
BEFORE UPDATE ON workflows
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =========================
-- Jobs Table
-- =========================
CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(workflow_id) ON DELETE CASCADE,

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    robot_id VARCHAR(255),

    -- Execution settings
    priority INTEGER DEFAULT 10,
    execution_mode VARCHAR(20) DEFAULT 'lan', -- 'lan' or 'internet'

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    claimed_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Results
    result JSONB,
    error TEXT,

    -- Retry handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'queued', 'claimed', 'running',
        'completed', 'failed', 'cancelled', 'timeout'
    )),
    CONSTRAINT valid_execution_mode CHECK (execution_mode IN ('lan', 'internet')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 0 AND 20)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_workflow_id ON jobs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_robot_id ON jobs(robot_id);
CREATE INDEX IF NOT EXISTS idx_jobs_execution_mode ON jobs(execution_mode);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority, created_at);

-- Index for queue polling (most important)
CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(status, execution_mode, priority, created_at)
WHERE status = 'queued';


-- =========================
-- Schedules Table
-- =========================
CREATE TABLE IF NOT EXISTS schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(workflow_id) ON DELETE CASCADE,

    -- Schedule configuration
    schedule_name VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,

    -- Execution tracking
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    run_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::JSONB
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_schedules_workflow_id ON schedules(workflow_id);
CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run_at)
WHERE enabled = TRUE;

-- Trigger for updated_at
CREATE TRIGGER update_schedules_updated_at
BEFORE UPDATE ON schedules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =========================
-- Workflow Versions Table (for history tracking)
-- =========================
CREATE TABLE IF NOT EXISTS workflow_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    workflow_json JSONB NOT NULL,
    change_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),

    UNIQUE (workflow_id, version_number)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_workflow_versions_workflow_id ON workflow_versions(workflow_id, version_number DESC);


-- =========================
-- Statistics Views
-- =========================

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


-- =========================
-- Grant Permissions
-- =========================
-- Grant permissions to casare_user (assuming the user exists)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO casare_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO casare_user;
GRANT SELECT ON workflow_stats TO casare_user;
GRANT SELECT ON queue_stats TO casare_user;
