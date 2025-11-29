-- CasareRPA Job Queue Schema Migration
-- Version: 001
-- Description: Create job_queue table for distributed job processing
--
-- This schema supports:
-- - SKIP LOCKED for high-concurrency job claiming
-- - Visibility timeout for crash recovery
-- - Priority-based job ordering
-- - Environment-based job routing
-- - Automatic retry with exponential backoff

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main job queue table
CREATE TABLE IF NOT EXISTS job_queue (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

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

    -- Environment for job routing (e.g., 'production', 'staging', 'default')
    environment VARCHAR(100) DEFAULT 'default' NOT NULL,

    -- Visibility timeout: job becomes visible again after this timestamp
    -- Used for crash recovery and lease management
    visible_after TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Error handling
    error_message TEXT,

    -- Result data (stored as JSONB for efficient querying)
    result JSONB DEFAULT '{}'::jsonb,

    -- Retry configuration
    retry_count INTEGER DEFAULT 0 NOT NULL,
    max_retries INTEGER DEFAULT 3 NOT NULL,

    -- Input variables for workflow execution
    variables JSONB DEFAULT '{}'::jsonb,

    -- Optional metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_retry_count CHECK (retry_count >= 0)
);

-- Index for efficient job claiming with SKIP LOCKED
-- This is the critical index for high-throughput job acquisition
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

-- Index for visibility timeout recovery (finding timed-out jobs)
CREATE INDEX IF NOT EXISTS idx_job_queue_visibility_timeout
    ON job_queue (visible_after, status)
    WHERE status = 'running';

-- Index for completed jobs (for history/reporting)
CREATE INDEX IF NOT EXISTS idx_job_queue_completed
    ON job_queue (completed_at DESC)
    WHERE status IN ('completed', 'failed');

-- Function to update visibility timeout and return claimed jobs
-- This provides atomic claim-and-update in a single query
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
-- Called periodically by a background process
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

-- Add comments for documentation
COMMENT ON TABLE job_queue IS 'Distributed job queue for RPA workflow execution';
COMMENT ON COLUMN job_queue.visible_after IS 'Jobs become visible for claiming after this timestamp. Used for visibility timeout and crash recovery.';
COMMENT ON COLUMN job_queue.priority IS 'Job priority (0=LOW, 1=NORMAL, 2=HIGH, 3=CRITICAL). Higher priority jobs are processed first.';
COMMENT ON COLUMN job_queue.environment IS 'Target execution environment. Robots only claim jobs matching their environment.';
COMMENT ON INDEX idx_job_queue_claiming IS 'Critical index for high-throughput job claiming with SKIP LOCKED.';
