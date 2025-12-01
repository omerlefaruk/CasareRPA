-- CasareRPA Database Initialization Script
-- This script runs when PostgreSQL container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Job Queue Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS job_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) NOT NULL,
    workflow_json JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    environment VARCHAR(100) DEFAULT 'production',
    robot_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    result JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    tenant_id VARCHAR(255),

    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Indexes for efficient job claiming
CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status);
CREATE INDEX IF NOT EXISTS idx_job_queue_priority_status ON job_queue(priority DESC, status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_job_queue_robot_id ON job_queue(robot_id) WHERE robot_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_job_queue_environment ON job_queue(environment);
CREATE INDEX IF NOT EXISTS idx_job_queue_tenant_id ON job_queue(tenant_id) WHERE tenant_id IS NOT NULL;

-- =============================================================================
-- Robots Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS robots (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'idle',
    robot_type VARCHAR(50) DEFAULT 'browser',
    capabilities JSONB DEFAULT '[]'::jsonb,
    environment VARCHAR(100) DEFAULT 'production',
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    tenant_id VARCHAR(255),

    CONSTRAINT valid_robot_status CHECK (status IN ('idle', 'busy', 'offline', 'error'))
);

CREATE INDEX IF NOT EXISTS idx_robots_status ON robots(status);
CREATE INDEX IF NOT EXISTS idx_robots_environment ON robots(environment);
CREATE INDEX IF NOT EXISTS idx_robots_tenant_id ON robots(tenant_id) WHERE tenant_id IS NOT NULL;

-- =============================================================================
-- Workflows Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version INTEGER DEFAULT 1,
    workflow_json JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    tenant_id VARCHAR(255),
    tags TEXT[] DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name);
CREATE INDEX IF NOT EXISTS idx_workflows_tenant_id ON workflows(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING GIN(tags);

-- =============================================================================
-- Schedules Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_enabled BOOLEAN DEFAULT true,
    environment VARCHAR(100) DEFAULT 'production',
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tenant_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run_at) WHERE is_enabled = true;
CREATE INDEX IF NOT EXISTS idx_schedules_workflow_id ON schedules(workflow_id);

-- =============================================================================
-- Execution History Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS execution_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES job_queue(id) ON DELETE SET NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    robot_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    error_message TEXT,
    result JSONB,
    logs JSONB,
    tenant_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_execution_history_workflow ON execution_history(workflow_id);
CREATE INDEX IF NOT EXISTS idx_execution_history_robot ON execution_history(robot_id);
CREATE INDEX IF NOT EXISTS idx_execution_history_started ON execution_history(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_history_tenant ON execution_history(tenant_id) WHERE tenant_id IS NOT NULL;

-- =============================================================================
-- Audit Log Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    user_id VARCHAR(255),
    tenant_id VARCHAR(255),
    ip_address INET,
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_tenant ON audit_log(tenant_id) WHERE tenant_id IS NOT NULL;

-- =============================================================================
-- Row-Level Security (RLS) for Multi-Tenancy
-- =============================================================================
-- Enable RLS on tables (uncomment when using multi-tenancy)
-- ALTER TABLE job_queue ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE robots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE execution_history ENABLE ROW LEVEL SECURITY;

-- Example policy (tenant isolation)
-- CREATE POLICY tenant_isolation ON job_queue
--     USING (tenant_id = current_setting('app.current_tenant')::text);

-- =============================================================================
-- Utility Functions
-- =============================================================================

-- Function to claim next available job (with SKIP LOCKED for concurrency)
CREATE OR REPLACE FUNCTION claim_next_job(
    p_robot_id VARCHAR(255),
    p_robot_type VARCHAR(50),
    p_environment VARCHAR(100) DEFAULT 'production'
) RETURNS TABLE(job_id UUID, workflow_json JSONB) AS $$
BEGIN
    RETURN QUERY
    WITH claimed AS (
        SELECT jq.id, jq.workflow_json
        FROM job_queue jq
        WHERE jq.status = 'pending'
          AND jq.environment = p_environment
        ORDER BY jq.priority DESC, jq.created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    UPDATE job_queue jq
    SET status = 'running',
        robot_id = p_robot_id,
        started_at = NOW()
    FROM claimed
    WHERE jq.id = claimed.id
    RETURNING jq.id, jq.workflow_json;
END;
$$ LANGUAGE plpgsql;

-- Function to get queue statistics
CREATE OR REPLACE FUNCTION get_queue_stats(p_environment VARCHAR(100) DEFAULT NULL)
RETURNS TABLE(
    total_jobs BIGINT,
    pending_jobs BIGINT,
    running_jobs BIGINT,
    completed_jobs BIGINT,
    failed_jobs BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_jobs,
        COUNT(*) FILTER (WHERE status = 'pending')::BIGINT as pending_jobs,
        COUNT(*) FILTER (WHERE status = 'running')::BIGINT as running_jobs,
        COUNT(*) FILTER (WHERE status = 'completed')::BIGINT as completed_jobs,
        COUNT(*) FILTER (WHERE status = 'failed')::BIGINT as failed_jobs
    FROM job_queue
    WHERE p_environment IS NULL OR environment = p_environment;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to application user (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO casare_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO casare_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO casare_app;

-- =============================================================================
-- Initial Data (Optional - for development)
-- =============================================================================
-- Uncomment to insert sample data for development

-- INSERT INTO robots (id, name, robot_type, status, capabilities)
-- VALUES
--     ('robot-dev-1', 'Dev Robot 1', 'browser', 'idle', '["chromium", "firefox"]'::jsonb),
--     ('robot-dev-2', 'Dev Robot 2', 'desktop', 'idle', '["uiautomation", "win32"]'::jsonb);
