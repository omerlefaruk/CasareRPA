-- CasareRPA Fleet Management Schema for Supabase
-- Combined migration from: 001_workflows.sql, 002_robots_orchestration.sql,
--                          003_robot_api_keys.sql, 004_robot_logs.sql
--
-- Run this in Supabase SQL Editor or via CLI:
--   supabase db push
--
-- Prerequisites:
--   1. Enable realtime for required tables (see README.md)
--   2. Configure RLS policies after running this migration

-- =============================================================================
-- PART 1: CORE FUNCTIONS
-- =============================================================================

-- Trigger function for updating updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- PART 2: WORKFLOWS TABLE
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

-- Workflow indexes
CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_workflows_search ON workflows USING GIN(search_vector);

-- Updated_at trigger
DROP TRIGGER IF EXISTS update_workflows_updated_at ON workflows;
CREATE TRIGGER update_workflows_updated_at
BEFORE UPDATE ON workflows
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- PART 3: ROBOTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS robots (
    robot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'offline',
    environment VARCHAR(255) DEFAULT 'default',

    -- Capabilities and configuration (JSONB for flexibility)
    capabilities JSONB DEFAULT '[]'::JSONB,
    tags JSONB DEFAULT '[]'::JSONB,
    metrics JSONB DEFAULT '{}'::JSONB,

    -- Concurrency settings
    max_concurrent_jobs INTEGER DEFAULT 1,
    current_job_ids JSONB DEFAULT '[]'::JSONB,

    -- Workflow assignments (denormalized for quick lookup)
    assigned_workflows JSONB DEFAULT '[]'::JSONB,

    -- Heartbeat and timing
    last_heartbeat TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT robots_hostname_unique UNIQUE (hostname),
    CONSTRAINT robots_valid_status CHECK (status IN (
        'offline', 'online', 'busy', 'error', 'maintenance'
    )),
    CONSTRAINT robots_valid_max_concurrent CHECK (max_concurrent_jobs >= 0)
);

-- Robot indexes
CREATE INDEX IF NOT EXISTS idx_robots_status ON robots(status);
CREATE INDEX IF NOT EXISTS idx_robots_hostname ON robots(hostname);
CREATE INDEX IF NOT EXISTS idx_robots_environment ON robots(environment);
CREATE INDEX IF NOT EXISTS idx_robots_last_heartbeat ON robots(last_heartbeat DESC);
CREATE INDEX IF NOT EXISTS idx_robots_capabilities ON robots USING GIN(capabilities);
CREATE INDEX IF NOT EXISTS idx_robots_tags ON robots USING GIN(tags);

-- Updated_at trigger
DROP TRIGGER IF EXISTS update_robots_updated_at ON robots;
CREATE TRIGGER update_robots_updated_at
BEFORE UPDATE ON robots
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- PART 4: JOBS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    robot_uuid UUID REFERENCES robots(robot_id) ON DELETE SET NULL,

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    robot_id VARCHAR(255),  -- Legacy string ID (kept for compatibility)

    -- Execution settings
    priority INTEGER DEFAULT 10,
    execution_mode VARCHAR(20) DEFAULT 'lan',

    -- Job payload and metadata
    payload JSONB DEFAULT '{}'::JSONB,
    workflow_name VARCHAR(255),
    progress INTEGER DEFAULT 0,
    current_node VARCHAR(255) DEFAULT '',
    duration_ms INTEGER DEFAULT 0,
    logs TEXT DEFAULT '',

    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    claimed_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    scheduled_time TIMESTAMPTZ,
    timeout_seconds INTEGER DEFAULT 3600,

    -- Results
    result JSONB,
    error TEXT,

    -- Retry handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Audit
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'queued', 'claimed', 'running',
        'completed', 'failed', 'cancelled', 'timeout'
    )),
    CONSTRAINT valid_execution_mode CHECK (execution_mode IN ('lan', 'internet')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 0 AND 20),
    CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
);

-- Job indexes
CREATE INDEX IF NOT EXISTS idx_jobs_workflow_id ON jobs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_robot_id ON jobs(robot_id);
CREATE INDEX IF NOT EXISTS idx_jobs_robot_uuid ON jobs(robot_uuid);
CREATE INDEX IF NOT EXISTS idx_jobs_execution_mode ON jobs(execution_mode);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority, created_at);

-- Queue polling index (most important for performance)
CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(status, execution_mode, priority, created_at)
WHERE status = 'queued';


-- =============================================================================
-- PART 5: ROBOT API KEYS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS robot_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    robot_id UUID NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,

    -- API key hash (SHA-256 of raw key)
    -- Raw key format: crpa_<base64url_token> (shown once at creation)
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

-- API key indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_hash_active
    ON robot_api_keys(api_key_hash)
    WHERE is_revoked = FALSE;

CREATE INDEX IF NOT EXISTS idx_api_keys_robot
    ON robot_api_keys(robot_id);

CREATE INDEX IF NOT EXISTS idx_api_keys_expires
    ON robot_api_keys(expires_at)
    WHERE expires_at IS NOT NULL AND is_revoked = FALSE;

CREATE INDEX IF NOT EXISTS idx_api_keys_created_at
    ON robot_api_keys(created_at DESC);

-- Updated_at trigger
DROP TRIGGER IF EXISTS update_robot_api_keys_updated_at ON robot_api_keys;
CREATE TRIGGER update_robot_api_keys_updated_at
BEFORE UPDATE ON robot_api_keys
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- PART 6: ROBOT LOGS TABLE (Partitioned)
-- =============================================================================

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

-- Robot logs indexes
CREATE INDEX IF NOT EXISTS idx_robot_logs_robot_time
    ON robot_logs(robot_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_robot_logs_tenant_time
    ON robot_logs(tenant_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_robot_logs_level
    ON robot_logs(level, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_robot_logs_message_search
    ON robot_logs USING GIN (to_tsvector('english', message));

CREATE INDEX IF NOT EXISTS idx_robot_logs_source
    ON robot_logs(source, timestamp DESC)
    WHERE source IS NOT NULL;


-- =============================================================================
-- PART 7: SUPPORTING TABLES
-- =============================================================================

-- Schedules table
CREATE TABLE IF NOT EXISTS schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    schedule_name VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    run_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS idx_schedules_workflow_id ON schedules(workflow_id);
CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run_at) WHERE enabled = TRUE;

DROP TRIGGER IF EXISTS update_schedules_updated_at ON schedules;
CREATE TRIGGER update_schedules_updated_at
BEFORE UPDATE ON schedules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- Workflow versions table (history tracking)
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

CREATE INDEX IF NOT EXISTS idx_workflow_versions_workflow_id ON workflow_versions(workflow_id, version_number DESC);


-- Workflow robot assignments table
CREATE TABLE IF NOT EXISTS workflow_robot_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    robot_id UUID NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,
    is_default BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    notes TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT workflow_robot_unique UNIQUE (workflow_id, robot_id),
    CONSTRAINT valid_priority CHECK (priority >= 0)
);

CREATE INDEX IF NOT EXISTS idx_workflow_assignments_workflow ON workflow_robot_assignments(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_assignments_robot ON workflow_robot_assignments(robot_id);
CREATE INDEX IF NOT EXISTS idx_workflow_assignments_default ON workflow_robot_assignments(workflow_id) WHERE is_default = TRUE;

DROP TRIGGER IF EXISTS update_workflow_assignments_updated_at ON workflow_robot_assignments;
CREATE TRIGGER update_workflow_assignments_updated_at
BEFORE UPDATE ON workflow_robot_assignments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- Node robot overrides table
CREATE TABLE IF NOT EXISTS node_robot_overrides (
    override_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,
    robot_id UUID REFERENCES robots(robot_id) ON DELETE CASCADE,
    required_capabilities JSONB DEFAULT '[]'::JSONB,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT node_override_unique UNIQUE (workflow_id, node_id),
    CONSTRAINT override_has_target CHECK (
        robot_id IS NOT NULL OR jsonb_array_length(required_capabilities) > 0
    )
);

CREATE INDEX IF NOT EXISTS idx_node_overrides_workflow ON node_robot_overrides(workflow_id);
CREATE INDEX IF NOT EXISTS idx_node_overrides_robot ON node_robot_overrides(robot_id);
CREATE INDEX IF NOT EXISTS idx_node_overrides_active ON node_robot_overrides(workflow_id) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_node_overrides_capabilities ON node_robot_overrides USING GIN(required_capabilities);

DROP TRIGGER IF EXISTS update_node_overrides_updated_at ON node_robot_overrides;
CREATE TRIGGER update_node_overrides_updated_at
BEFORE UPDATE ON node_robot_overrides
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- Robot heartbeats table (historical tracking)
CREATE TABLE IF NOT EXISTS robot_heartbeats (
    heartbeat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    robot_id UUID NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    current_jobs INTEGER DEFAULT 0,
    metrics JSONB DEFAULT '{}'::JSONB,
    ip_address INET,
    latency_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_heartbeats_robot_time ON robot_heartbeats(robot_id, timestamp DESC);


-- API key audit log table
CREATE TABLE IF NOT EXISTS robot_api_key_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID NOT NULL REFERENCES robot_api_keys(id) ON DELETE CASCADE,
    robot_id UUID NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_time TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent VARCHAR(500),
    endpoint VARCHAR(255),
    details JSONB DEFAULT '{}'::JSONB,
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'auth_success', 'auth_failure', 'created', 'revoked', 'expired', 'rotated'
    ))
);

CREATE INDEX IF NOT EXISTS idx_api_key_audit_key ON robot_api_key_audit(api_key_id, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_api_key_audit_robot ON robot_api_key_audit(robot_id, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_api_key_audit_failures ON robot_api_key_audit(event_time DESC) WHERE event_type = 'auth_failure';


-- Robot logs cleanup history table
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

CREATE INDEX IF NOT EXISTS idx_cleanup_history_time ON robot_logs_cleanup_history(cleanup_time DESC);


-- =============================================================================
-- PART 8: HELPER FUNCTIONS
-- =============================================================================

-- Validate API key hash function
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


-- Update API key last_used function
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


-- Create robot logs partition function
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


-- Drop old robot logs partitions function (retention enforcement)
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


-- Ensure robot logs partitions exist function
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


-- Query robot logs function
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
    level_order := ARRAY['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];
    SELECT array_position(level_order, p_min_level) INTO min_level_idx;
    IF min_level_idx IS NULL THEN
        min_level_idx := 2;
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


-- Get robot logs stats function
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


-- =============================================================================
-- PART 9: VIEWS
-- =============================================================================

-- Workflow statistics view
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


-- Queue statistics view
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


-- Robot statistics view
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


-- Workflow assignment stats view
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


-- Active API keys view
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


-- API key statistics view
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


-- Robot logs statistics view (last 24 hours)
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


-- Robot logs daily summary view
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


-- =============================================================================
-- PART 10: INITIAL SETUP
-- =============================================================================

-- Create initial partitions for robot_logs (current month + 2 months ahead)
SELECT * FROM ensure_robot_logs_partitions(2);


-- =============================================================================
-- PART 11: ROW LEVEL SECURITY (RLS)
-- =============================================================================
-- NOTE: Enable RLS in Supabase Dashboard or uncomment these lines

-- Enable RLS on tables
-- ALTER TABLE robots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE robot_api_keys ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE robot_logs ENABLE ROW LEVEL SECURITY;

-- Example RLS policies (customize based on your auth model):

-- Robots: Service role has full access
-- CREATE POLICY "Service role full access" ON robots
--     FOR ALL
--     USING (auth.role() = 'service_role');

-- Jobs: Service role has full access
-- CREATE POLICY "Service role full access" ON jobs
--     FOR ALL
--     USING (auth.role() = 'service_role');

-- Robot logs: Filter by tenant_id
-- CREATE POLICY "Tenant isolation" ON robot_logs
--     FOR ALL
--     USING (tenant_id = auth.uid());


-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================
-- Next steps:
-- 1. Enable realtime for: robots, jobs (see README.md)
-- 2. Configure RLS policies above based on your auth model
-- 3. Set up Edge Functions for cleanup and notifications (optional)
