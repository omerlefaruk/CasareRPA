-- CasareRPA Unified Database Initialization Script
-- This script runs when PostgreSQL container is first created
-- Compatible with both local Docker and cloud deployments
--
-- Tables:
--   robots          - Robot fleet management
--   robot_api_keys  - API key authentication
--   jobs            - Job queue
--   job_queue       - Legacy job queue (backwards compatibility)
--   workflows       - Workflow definitions
--   schedules       - Scheduled workflow runs
--   execution_history - Execution logs
--   robot_heartbeats - Robot health monitoring
--   audit_log       - Security audit trail
--
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- ROBOTS TABLE (Unified Schema)
-- =============================================================================
CREATE TABLE IF NOT EXISTS robots (
    robot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- Legacy column alias for backwards compatibility
    id VARCHAR(255) GENERATED ALWAYS AS (robot_id::text) STORED,
    robot_name VARCHAR(255) NOT NULL,
    -- Legacy column alias
    name VARCHAR(255) GENERATED ALWAYS AS (robot_name) STORED,
    hostname VARCHAR(255),
    status VARCHAR(50) DEFAULT 'offline'
        CHECK (status IN ('online', 'offline', 'busy', 'idle', 'working', 'maintenance', 'error')),
    robot_type VARCHAR(50) DEFAULT 'browser',
    capabilities JSONB DEFAULT '[]'::jsonb,
    tags JSONB DEFAULT '[]'::jsonb,
    max_concurrent_jobs INTEGER DEFAULT 1,
    current_job_ids JSONB DEFAULT '[]'::jsonb,
    environment VARCHAR(100) DEFAULT 'production',
    last_heartbeat TIMESTAMPTZ,
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    tenant_id VARCHAR(255),

    -- Unique constraint on legacy id for backwards compatibility
    CONSTRAINT robots_legacy_id_unique UNIQUE (id)
);

CREATE INDEX IF NOT EXISTS idx_robots_status ON robots(status);
CREATE INDEX IF NOT EXISTS idx_robots_capabilities ON robots USING GIN(capabilities);
CREATE INDEX IF NOT EXISTS idx_robots_last_heartbeat ON robots(last_heartbeat);
CREATE INDEX IF NOT EXISTS idx_robots_environment ON robots(environment);
CREATE INDEX IF NOT EXISTS idx_robots_tenant_id ON robots(tenant_id) WHERE tenant_id IS NOT NULL;

-- =============================================================================
-- ROBOT API KEYS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS robot_api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    robot_id UUID REFERENCES robots(robot_id) ON DELETE CASCADE,
    api_key_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hash
    name VARCHAR(255),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    last_used_ip INET,
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,
    revoked_by VARCHAR(255),
    revoke_reason TEXT,
    created_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON robot_api_keys(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_robot ON robot_api_keys(robot_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_valid ON robot_api_keys(api_key_hash)
    WHERE is_revoked = FALSE AND (expires_at IS NULL OR expires_at > NOW());

-- =============================================================================
-- JOBS TABLE (New Schema)
-- =============================================================================
CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) NOT NULL,
    workflow_data JSONB NOT NULL,
    variables JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'pending'
        CHECK (status IN ('pending', 'assigned', 'running', 'completed', 'failed', 'cancelled', 'timeout')),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    target_robot_id UUID REFERENCES robots(robot_id),
    assigned_robot_id UUID REFERENCES robots(robot_id),
    required_capabilities JSONB DEFAULT '[]'::jsonb,
    timeout_seconds INTEGER DEFAULT 3600,
    environment VARCHAR(100) DEFAULT 'production',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Results
    result JSONB,
    error_message TEXT,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    logs JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    created_by VARCHAR(255),
    tenant_id VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_priority_created ON jobs(priority DESC, created_at ASC) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_jobs_robot ON jobs(assigned_robot_id);
CREATE INDEX IF NOT EXISTS idx_jobs_workflow ON jobs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_tenant_id ON jobs(tenant_id) WHERE tenant_id IS NOT NULL;

-- =============================================================================
-- JOB_QUEUE TABLE (Legacy - Backwards Compatibility)
-- =============================================================================
CREATE TABLE IF NOT EXISTS job_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) NOT NULL,
    workflow_json JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 5,
    environment VARCHAR(100) DEFAULT 'production',
    robot_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    result JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    tenant_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status);
CREATE INDEX IF NOT EXISTS idx_job_queue_priority_status ON job_queue(priority DESC, status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_job_queue_robot_id ON job_queue(robot_id) WHERE robot_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_job_queue_environment ON job_queue(environment);
CREATE INDEX IF NOT EXISTS idx_job_queue_tenant_id ON job_queue(tenant_id) WHERE tenant_id IS NOT NULL;

-- =============================================================================
-- WORKFLOWS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version INTEGER DEFAULT 1,
    workflow_json JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    tenant_id VARCHAR(255),
    tags TEXT[] DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name);
CREATE INDEX IF NOT EXISTS idx_workflows_tenant_id ON workflows(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING GIN(tags);

-- =============================================================================
-- SCHEDULES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_enabled BOOLEAN DEFAULT true,
    environment VARCHAR(100) DEFAULT 'production',
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run_at) WHERE is_enabled = true;
CREATE INDEX IF NOT EXISTS idx_schedules_workflow_id ON schedules(workflow_id);

-- =============================================================================
-- EXECUTION HISTORY TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS execution_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID,  -- Can reference either jobs or job_queue
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    robot_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
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
-- ROBOT HEARTBEATS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS robot_heartbeats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    robot_id UUID REFERENCES robots(robot_id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metrics JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50),
    current_jobs INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_heartbeats_robot_time ON robot_heartbeats(robot_id, timestamp DESC);

-- =============================================================================
-- AUDIT LOG TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
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
-- FUNCTIONS
-- =============================================================================

-- Claim next job (new schema)
CREATE OR REPLACE FUNCTION claim_next_job(
    p_robot_id UUID,
    p_capabilities JSONB DEFAULT '[]'::jsonb
)
RETURNS TABLE(
    job_id UUID,
    workflow_id VARCHAR(255),
    workflow_data JSONB,
    variables JSONB,
    timeout_seconds INTEGER
) AS $$
DECLARE
    v_job_id UUID;
BEGIN
    SELECT j.job_id INTO v_job_id
    FROM jobs j
    WHERE j.status = 'pending'
      AND (j.target_robot_id IS NULL OR j.target_robot_id = p_robot_id)
      AND (
          j.required_capabilities = '[]'::jsonb
          OR j.required_capabilities <@ p_capabilities
      )
    ORDER BY j.priority DESC, j.created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    IF v_job_id IS NULL THEN
        RETURN;
    END IF;

    UPDATE jobs
    SET status = 'assigned',
        assigned_robot_id = p_robot_id,
        started_at = NOW()
    WHERE jobs.job_id = v_job_id;

    RETURN QUERY
    SELECT j.job_id, j.workflow_id, j.workflow_data, j.variables, j.timeout_seconds
    FROM jobs j
    WHERE j.job_id = v_job_id;
END;
$$ LANGUAGE plpgsql;

-- Claim next job (legacy schema)
CREATE OR REPLACE FUNCTION claim_next_job_legacy(
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

-- Complete job
CREATE OR REPLACE FUNCTION complete_job(
    p_job_id UUID,
    p_success BOOLEAN,
    p_result JSONB DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE jobs
    SET status = CASE WHEN p_success THEN 'completed' ELSE 'failed' END,
        completed_at = NOW(),
        result = p_result,
        error_message = p_error_message,
        progress = 100
    WHERE job_id = p_job_id;

    UPDATE robots
    SET current_job_ids = current_job_ids - p_job_id::text
    WHERE p_job_id::text = ANY(SELECT jsonb_array_elements_text(current_job_ids));
END;
$$ LANGUAGE plpgsql;

-- Validate API key
CREATE OR REPLACE FUNCTION validate_api_key_hash(p_hash VARCHAR(64))
RETURNS TABLE(
    robot_id UUID,
    robot_name VARCHAR(255)
) AS $$
BEGIN
    RETURN QUERY
    SELECT r.robot_id, r.robot_name
    FROM robot_api_keys k
    JOIN robots r ON k.robot_id = r.robot_id
    WHERE k.api_key_hash = p_hash
      AND k.is_revoked = FALSE
      AND (k.expires_at IS NULL OR k.expires_at > NOW());
END;
$$ LANGUAGE plpgsql;

-- Update API key last used
CREATE OR REPLACE FUNCTION update_api_key_last_used(
    p_hash VARCHAR(64),
    p_ip INET DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE robot_api_keys
    SET last_used_at = NOW(),
        last_used_ip = COALESCE(p_ip, last_used_ip)
    WHERE api_key_hash = p_hash;
END;
$$ LANGUAGE plpgsql;

-- Queue statistics
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
        COUNT(*) FILTER (WHERE status IN ('running', 'assigned'))::BIGINT as running_jobs,
        COUNT(*) FILTER (WHERE status = 'completed')::BIGINT as completed_jobs,
        COUNT(*) FILTER (WHERE status = 'failed')::BIGINT as failed_jobs
    FROM jobs
    WHERE p_environment IS NULL OR environment = p_environment;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active robots view
CREATE OR REPLACE VIEW active_robots AS
SELECT
    robot_id,
    robot_name,
    hostname,
    status,
    robot_type,
    capabilities,
    tags,
    max_concurrent_jobs,
    jsonb_array_length(current_job_ids) as current_job_count,
    environment,
    last_heartbeat,
    registered_at,
    CASE
        WHEN last_heartbeat > NOW() - INTERVAL '90 seconds' THEN true
        ELSE false
    END as is_connected
FROM robots
WHERE status != 'offline'
   OR last_heartbeat > NOW() - INTERVAL '90 seconds';

-- Pending jobs view
CREATE OR REPLACE VIEW pending_jobs AS
SELECT
    job_id,
    workflow_id,
    status,
    priority,
    target_robot_id,
    required_capabilities,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at)) as wait_time_seconds
FROM jobs
WHERE status = 'pending'
ORDER BY priority DESC, created_at ASC;

-- Job statistics view
CREATE OR REPLACE VIEW job_statistics AS
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM jobs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), status
ORDER BY hour DESC;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_robots_updated_at ON robots;
CREATE TRIGGER update_robots_updated_at
    BEFORE UPDATE ON robots
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_workflows_updated_at ON workflows;
CREATE TRIGGER update_workflows_updated_at
    BEFORE UPDATE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_schedules_updated_at ON schedules;
CREATE TRIGGER update_schedules_updated_at
    BEFORE UPDATE ON schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) - Multi-Tenancy
-- =============================================================================
-- Enable RLS when using multi-tenancy (uncomment as needed):
-- ALTER TABLE robots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE job_queue ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE execution_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
--
-- Example policy:
-- CREATE POLICY tenant_isolation ON jobs
--     USING (tenant_id = current_setting('app.current_tenant')::text);

-- =============================================================================
-- SAMPLE DATA (Development Only)
-- =============================================================================
-- Uncomment for development testing:
-- INSERT INTO robots (robot_name, hostname, status, robot_type, capabilities, max_concurrent_jobs)
-- VALUES
--     ('Dev Browser Robot', 'localhost', 'offline', 'browser', '["chromium", "firefox"]', 2),
--     ('Dev Desktop Robot', 'localhost', 'offline', 'desktop', '["uiautomation", "win32"]', 1);
