-- Migration: 002_job_queue
-- Description: Job queue with PgQueuer support, visibility timeout, and crash recovery
-- Consolidated from:
--   - src/casare_rpa/infrastructure/queue/migrations/001_create_job_queue.sql
--   - deploy/supabase/migrations/002_job_queue_and_robots_fix.sql
-- Created: 2024-12-03

-- =============================================================================
-- JOB QUEUE TABLE (Extended)
-- =============================================================================
-- This table provides high-performance job claiming with SKIP LOCKED
CREATE TABLE IF NOT EXISTS job_queue (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Workflow information
    workflow_id VARCHAR(255) NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_json TEXT NOT NULL,

    -- Job priority (higher = more important)
    -- 0=LOW, 1=NORMAL, 2=HIGH, 3=CRITICAL
    priority INTEGER DEFAULT 1 CHECK (priority >= 0 AND priority <= 20),

    -- Job status: pending, running, completed, failed, cancelled
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,

    -- Robot assignment
    robot_id VARCHAR(255),

    -- Environment for job routing
    environment VARCHAR(100) DEFAULT 'default' NOT NULL,

    -- Visibility timeout: job becomes visible again after this timestamp
    visible_after TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Error handling
    error_message TEXT,

    -- Result data
    result JSONB DEFAULT '{}'::jsonb,

    -- Retry configuration
    retry_count INTEGER DEFAULT 0 NOT NULL,
    max_retries INTEGER DEFAULT 3 NOT NULL,

    -- Input variables for workflow execution
    variables JSONB DEFAULT '{}'::jsonb,

    -- Optional metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_job_queue_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_retry_count CHECK (retry_count >= 0)
);

-- =============================================================================
-- INDEXES FOR JOB QUEUE
-- =============================================================================

-- Critical index for high-throughput job acquisition with SKIP LOCKED
CREATE INDEX IF NOT EXISTS idx_job_queue_claiming
    ON job_queue (status, visible_after, priority DESC, created_at ASC)
    WHERE status = 'pending';

-- Index for querying jobs by robot
CREATE INDEX IF NOT EXISTS idx_job_queue_robot
    ON job_queue (robot_id, status)
    WHERE robot_id IS NOT NULL;

-- Index for querying jobs by environment
CREATE INDEX IF NOT EXISTS idx_job_queue_environment
    ON job_queue (environment, status);

-- Index for querying jobs by workflow
CREATE INDEX IF NOT EXISTS idx_job_queue_workflow
    ON job_queue (workflow_id, status);

-- Index for visibility timeout recovery
CREATE INDEX IF NOT EXISTS idx_job_queue_visibility_timeout
    ON job_queue (visible_after, status)
    WHERE status = 'running';

-- Index for completed jobs (for history/reporting)
CREATE INDEX IF NOT EXISTS idx_job_queue_completed
    ON job_queue (completed_at DESC)
    WHERE status IN ('completed', 'failed');

-- =============================================================================
-- JOB CLAIMING FUNCTIONS
-- =============================================================================

-- Function to atomically claim jobs with SKIP LOCKED
CREATE OR REPLACE FUNCTION claim_jobs(
    p_environment VARCHAR(100),
    p_robot_id VARCHAR(255),
    p_batch_size INTEGER,
    p_visibility_timeout_seconds INTEGER
)
RETURNS SETOF job_queue AS $$
BEGIN
    RETURN QUERY
    WITH claimed AS (
        SELECT id
        FROM job_queue
        WHERE status = 'pending'
          AND visible_after <= NOW()
          AND (environment = p_environment OR environment = 'default' OR p_environment = 'default')
        ORDER BY priority DESC, created_at ASC
        LIMIT p_batch_size
        FOR UPDATE SKIP LOCKED
    )
    UPDATE job_queue jq
    SET status = 'running',
        robot_id = p_robot_id,
        started_at = NOW(),
        visible_after = NOW() + (p_visibility_timeout_seconds || ' seconds')::INTERVAL
    FROM claimed
    WHERE jq.id = claimed.id
    RETURNING jq.*;
END;
$$ LANGUAGE plpgsql;

-- Function to extend job lease (heartbeat)
CREATE OR REPLACE FUNCTION extend_job_lease(
    p_job_id UUID,
    p_robot_id VARCHAR(255),
    p_extension_seconds INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE job_queue
    SET visible_after = NOW() + (p_extension_seconds || ' seconds')::INTERVAL
    WHERE id = p_job_id
      AND status = 'running'
      AND robot_id = p_robot_id;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Function to recover timed-out jobs
CREATE OR REPLACE FUNCTION recover_timed_out_jobs()
RETURNS TABLE(job_id UUID, new_status VARCHAR(50)) AS $$
BEGIN
    RETURN QUERY
    UPDATE job_queue
    SET status = CASE
            WHEN retry_count < max_retries THEN 'pending'
            ELSE 'failed'
        END,
        robot_id = NULL,
        error_message = COALESCE(error_message, '') || ' [Visibility timeout exceeded]',
        retry_count = retry_count + 1,
        visible_after = NOW(),
        completed_at = CASE
            WHEN retry_count >= max_retries THEN NOW()
            ELSE NULL
        END
    WHERE status = 'running'
      AND visible_after < NOW()
    RETURNING id, status;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- JOB QUEUE STATISTICS VIEW
-- =============================================================================
CREATE OR REPLACE VIEW job_queue_stats AS
SELECT
    environment,
    status,
    COUNT(*) AS job_count,
    AVG(priority)::NUMERIC(3,1) AS avg_priority,
    MIN(created_at) AS oldest_job,
    MAX(created_at) AS newest_job,
    COUNT(*) FILTER (WHERE visible_after < NOW() AND status = 'running') AS timed_out_count
FROM job_queue
GROUP BY environment, status
ORDER BY environment, status;

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE job_queue IS 'Distributed job queue for RPA workflow execution';
COMMENT ON COLUMN job_queue.visible_after IS 'Jobs become visible for claiming after this timestamp. Used for visibility timeout and crash recovery.';
COMMENT ON COLUMN job_queue.priority IS 'Job priority (0=LOW, 1=NORMAL, 2=HIGH, 3=CRITICAL). Higher priority jobs are processed first.';
COMMENT ON COLUMN job_queue.environment IS 'Target execution environment. Robots only claim jobs matching their environment.';
COMMENT ON INDEX idx_job_queue_claiming IS 'Critical index for high-throughput job claiming with SKIP LOCKED.';
COMMENT ON FUNCTION claim_jobs IS 'Atomically claim pending jobs for a robot';
COMMENT ON FUNCTION extend_job_lease IS 'Extend the visibility timeout for a running job';
COMMENT ON FUNCTION recover_timed_out_jobs IS 'Recover jobs that have exceeded their visibility timeout';
