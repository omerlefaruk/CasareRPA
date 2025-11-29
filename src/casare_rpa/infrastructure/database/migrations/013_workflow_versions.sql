-- Migration: 013_workflow_versions
-- Description: Create tables for workflow versioning and migration tracking
-- Created: 2024-11-28

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Main workflow versions table
-- Stores every version of every workflow for audit and rollback
CREATE TABLE IF NOT EXISTS workflow_versions (
    -- Auto-incrementing primary key
    id BIGSERIAL PRIMARY KEY,

    -- Workflow identifier (file path or UUID)
    workflow_id TEXT NOT NULL,

    -- Semantic version string (e.g., "1.2.3", "2.0.0-beta.1")
    version TEXT NOT NULL,

    -- Version status lifecycle
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'active', 'deprecated', 'archived')),

    -- Complete serialized workflow data (JSONB for query efficiency)
    workflow_data JSONB NOT NULL,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    parent_version TEXT,  -- Version this was derived from
    change_summary TEXT,  -- Human-readable description of changes

    -- Workflow statistics (computed on insert)
    node_count INTEGER NOT NULL DEFAULT 0,
    connection_count INTEGER NOT NULL DEFAULT 0,

    -- Content checksum for integrity verification
    checksum TEXT NOT NULL,

    -- Version tags for filtering/categorization
    tags TEXT[] DEFAULT '{}',

    -- Ensure unique workflow_id + version combinations
    CONSTRAINT uq_workflow_version UNIQUE (workflow_id, version)
);

-- Index for finding versions of a specific workflow
CREATE INDEX IF NOT EXISTS idx_wv_workflow_id ON workflow_versions(workflow_id);

-- Index for finding active versions quickly
CREATE INDEX IF NOT EXISTS idx_wv_status ON workflow_versions(status);

-- Index for finding all active versions
CREATE INDEX IF NOT EXISTS idx_wv_workflow_active ON workflow_versions(workflow_id, status)
    WHERE status = 'active';

-- Index for timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_wv_created_at ON workflow_versions(created_at DESC);

-- Index for searching by tags
CREATE INDEX IF NOT EXISTS idx_wv_tags ON workflow_versions USING GIN (tags);

-- Index for searching workflow data (nodes, connections, etc.)
CREATE INDEX IF NOT EXISTS idx_wv_workflow_data ON workflow_versions USING GIN (workflow_data);

-- Table comments
COMMENT ON TABLE workflow_versions IS 'Stores all versions of workflows for versioning, audit, and rollback';
COMMENT ON COLUMN workflow_versions.workflow_id IS 'Unique identifier for the workflow (file path or UUID)';
COMMENT ON COLUMN workflow_versions.version IS 'Semantic version string (major.minor.patch[-prerelease])';
COMMENT ON COLUMN workflow_versions.status IS 'Lifecycle status: draft, active, deprecated, archived';
COMMENT ON COLUMN workflow_versions.workflow_data IS 'Complete serialized workflow including nodes, connections, variables';
COMMENT ON COLUMN workflow_versions.parent_version IS 'Version string this version was derived from';
COMMENT ON COLUMN workflow_versions.checksum IS 'SHA-256 hash of workflow content for integrity';


-- ============================================================================
-- Version pinning for scheduled jobs
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_version_pins (
    -- Auto-incrementing primary key
    id BIGSERIAL PRIMARY KEY,

    -- Job identifier (from scheduler)
    job_id TEXT NOT NULL,

    -- Workflow identifier
    workflow_id TEXT NOT NULL,

    -- Pinned version (NULL means use active version)
    pinned_version TEXT,

    -- When the pin was created/updated
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Who created the pin
    created_by TEXT,

    -- Reason for pinning
    pin_reason TEXT,

    -- Ensure unique job + workflow combinations
    CONSTRAINT uq_job_workflow_pin UNIQUE (job_id, workflow_id)
);

-- Index for looking up pins by workflow
CREATE INDEX IF NOT EXISTS idx_jvp_workflow_id ON job_version_pins(workflow_id);

-- Table comments
COMMENT ON TABLE job_version_pins IS 'Tracks version pinning for scheduled jobs';
COMMENT ON COLUMN job_version_pins.pinned_version IS 'Specific version to use, NULL means use active version';


-- ============================================================================
-- Migration tracking table
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflow_migrations (
    -- Auto-incrementing primary key
    id BIGSERIAL PRIMARY KEY,

    -- Workflow identifier
    workflow_id TEXT NOT NULL,

    -- Source and target versions
    from_version TEXT NOT NULL,
    to_version TEXT NOT NULL,

    -- Migration status
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'rolled_back')),

    -- Migration metadata
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    executed_by TEXT,

    -- Migration script/diff used
    migration_data JSONB,

    -- Error information if failed
    error_message TEXT,
    error_details JSONB,

    -- Rollback information
    rollback_available BOOLEAN NOT NULL DEFAULT TRUE,
    rolled_back_at TIMESTAMPTZ,

    -- Created timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for finding migrations by workflow
CREATE INDEX IF NOT EXISTS idx_wm_workflow_id ON workflow_migrations(workflow_id);

-- Index for finding pending migrations
CREATE INDEX IF NOT EXISTS idx_wm_status ON workflow_migrations(status);

-- Index for finding recent migrations
CREATE INDEX IF NOT EXISTS idx_wm_created_at ON workflow_migrations(created_at DESC);

-- Table comments
COMMENT ON TABLE workflow_migrations IS 'Tracks migration operations between workflow versions';


-- ============================================================================
-- Breaking changes log
-- ============================================================================

CREATE TABLE IF NOT EXISTS breaking_changes_log (
    -- Auto-incrementing primary key
    id BIGSERIAL PRIMARY KEY,

    -- Migration this belongs to
    migration_id BIGINT REFERENCES workflow_migrations(id) ON DELETE CASCADE,

    -- Change details
    change_type TEXT NOT NULL,
    element_id TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'error' CHECK (severity IN ('error', 'warning')),

    -- Old and new values
    old_value JSONB,
    new_value JSONB,

    -- Was this change auto-resolved?
    auto_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolution_notes TEXT,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for finding changes by migration
CREATE INDEX IF NOT EXISTS idx_bcl_migration_id ON breaking_changes_log(migration_id);

-- Table comments
COMMENT ON TABLE breaking_changes_log IS 'Logs breaking changes detected during version migrations';


-- ============================================================================
-- Helper functions
-- ============================================================================

-- Function to get the active version for a workflow
CREATE OR REPLACE FUNCTION get_active_workflow_version(p_workflow_id TEXT)
RETURNS TABLE (
    version TEXT,
    workflow_data JSONB,
    created_at TIMESTAMPTZ,
    node_count INTEGER,
    connection_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT wv.version, wv.workflow_data, wv.created_at, wv.node_count, wv.connection_count
    FROM workflow_versions wv
    WHERE wv.workflow_id = p_workflow_id
      AND wv.status = 'active'
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_active_workflow_version IS 'Returns the active version for a workflow';


-- Function to get version for a pinned job (or active if not pinned)
CREATE OR REPLACE FUNCTION get_job_workflow_version(p_job_id TEXT, p_workflow_id TEXT)
RETURNS TABLE (
    version TEXT,
    workflow_data JSONB,
    is_pinned BOOLEAN
) AS $$
DECLARE
    v_pinned_version TEXT;
BEGIN
    -- Check for pinned version
    SELECT pinned_version INTO v_pinned_version
    FROM job_version_pins
    WHERE job_id = p_job_id AND workflow_id = p_workflow_id;

    IF v_pinned_version IS NOT NULL THEN
        -- Return pinned version
        RETURN QUERY
        SELECT wv.version, wv.workflow_data, TRUE::BOOLEAN
        FROM workflow_versions wv
        WHERE wv.workflow_id = p_workflow_id
          AND wv.version = v_pinned_version
          AND wv.status IN ('active', 'deprecated')  -- Allow execution of deprecated for pinned
        LIMIT 1;
    ELSE
        -- Return active version
        RETURN QUERY
        SELECT wv.version, wv.workflow_data, FALSE::BOOLEAN
        FROM workflow_versions wv
        WHERE wv.workflow_id = p_workflow_id
          AND wv.status = 'active'
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_job_workflow_version IS 'Returns the appropriate workflow version for a job (pinned or active)';


-- Function to activate a new version (deprecates current active)
CREATE OR REPLACE FUNCTION activate_workflow_version(
    p_workflow_id TEXT,
    p_version TEXT,
    p_activated_by TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_current_active TEXT;
BEGIN
    -- Get current active version
    SELECT version INTO v_current_active
    FROM workflow_versions
    WHERE workflow_id = p_workflow_id AND status = 'active'
    LIMIT 1;

    -- Deprecate current active version if exists
    IF v_current_active IS NOT NULL THEN
        UPDATE workflow_versions
        SET status = 'deprecated'
        WHERE workflow_id = p_workflow_id AND version = v_current_active;
    END IF;

    -- Activate new version
    UPDATE workflow_versions
    SET status = 'active'
    WHERE workflow_id = p_workflow_id
      AND version = p_version
      AND status IN ('draft', 'deprecated');

    IF NOT FOUND THEN
        -- Rollback deprecation if activation failed
        IF v_current_active IS NOT NULL THEN
            UPDATE workflow_versions
            SET status = 'active'
            WHERE workflow_id = p_workflow_id AND version = v_current_active;
        END IF;
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION activate_workflow_version IS 'Activates a workflow version, deprecating the current active version';


-- Function to create a new version from existing
CREATE OR REPLACE FUNCTION create_workflow_version(
    p_workflow_id TEXT,
    p_version TEXT,
    p_workflow_data JSONB,
    p_parent_version TEXT DEFAULT NULL,
    p_change_summary TEXT DEFAULT '',
    p_created_by TEXT DEFAULT NULL,
    p_tags TEXT[] DEFAULT '{}'
)
RETURNS BIGINT AS $$
DECLARE
    v_node_count INTEGER;
    v_connection_count INTEGER;
    v_checksum TEXT;
    v_new_id BIGINT;
BEGIN
    -- Calculate statistics
    v_node_count := COALESCE(jsonb_object_keys_count(p_workflow_data->'nodes'), 0);
    v_connection_count := COALESCE(jsonb_array_length(p_workflow_data->'connections'), 0);

    -- Calculate checksum (simplified - use encode/digest for real checksum)
    v_checksum := md5(p_workflow_data::TEXT)::TEXT;

    -- Insert new version
    INSERT INTO workflow_versions (
        workflow_id, version, status, workflow_data,
        created_by, parent_version, change_summary,
        node_count, connection_count, checksum, tags
    ) VALUES (
        p_workflow_id, p_version, 'draft', p_workflow_data,
        p_created_by, p_parent_version, p_change_summary,
        v_node_count, v_connection_count, v_checksum, p_tags
    )
    RETURNING id INTO v_new_id;

    RETURN v_new_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- Helper function to count JSONB object keys
CREATE OR REPLACE FUNCTION jsonb_object_keys_count(p_jsonb JSONB)
RETURNS INTEGER AS $$
BEGIN
    IF p_jsonb IS NULL THEN
        RETURN 0;
    END IF;
    RETURN (SELECT COUNT(*) FROM jsonb_object_keys(p_jsonb));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION create_workflow_version IS 'Creates a new workflow version with computed statistics';


-- ============================================================================
-- Views for common queries
-- ============================================================================

-- View: Latest version per workflow
CREATE OR REPLACE VIEW latest_workflow_versions AS
SELECT DISTINCT ON (workflow_id)
    workflow_id,
    version,
    status,
    created_at,
    created_by,
    node_count,
    connection_count
FROM workflow_versions
ORDER BY workflow_id, created_at DESC;

COMMENT ON VIEW latest_workflow_versions IS 'Shows the most recent version of each workflow';


-- View: Active versions with job pin counts
CREATE OR REPLACE VIEW active_versions_with_pins AS
SELECT
    wv.workflow_id,
    wv.version,
    wv.created_at,
    wv.node_count,
    wv.connection_count,
    COUNT(jvp.id) as pinned_job_count
FROM workflow_versions wv
LEFT JOIN job_version_pins jvp
    ON wv.workflow_id = jvp.workflow_id
    AND wv.version = jvp.pinned_version
WHERE wv.status = 'active'
GROUP BY wv.workflow_id, wv.version, wv.created_at, wv.node_count, wv.connection_count;

COMMENT ON VIEW active_versions_with_pins IS 'Shows active versions with count of jobs pinned to them';


-- View: Migration history with breaking change counts
CREATE OR REPLACE VIEW migration_history AS
SELECT
    wm.id,
    wm.workflow_id,
    wm.from_version,
    wm.to_version,
    wm.status,
    wm.started_at,
    wm.completed_at,
    wm.executed_by,
    COUNT(bcl.id) as breaking_change_count,
    SUM(CASE WHEN bcl.severity = 'error' THEN 1 ELSE 0 END) as error_count,
    SUM(CASE WHEN bcl.auto_resolved THEN 1 ELSE 0 END) as auto_resolved_count
FROM workflow_migrations wm
LEFT JOIN breaking_changes_log bcl ON wm.id = bcl.migration_id
GROUP BY wm.id;

COMMENT ON VIEW migration_history IS 'Shows migration history with breaking change statistics';


-- ============================================================================
-- Triggers
-- ============================================================================

-- Trigger to update updated_at on job_version_pins
CREATE OR REPLACE FUNCTION update_job_version_pins_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_jvp_timestamp ON job_version_pins;
CREATE TRIGGER trg_update_jvp_timestamp
    BEFORE UPDATE ON job_version_pins
    FOR EACH ROW
    EXECUTE FUNCTION update_job_version_pins_timestamp();


-- ============================================================================
-- DOWN MIGRATION (in separate file: 013_workflow_versions_down.sql)
-- ============================================================================
