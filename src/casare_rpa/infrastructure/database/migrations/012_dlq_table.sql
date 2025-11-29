-- Migration: 012_dlq_table
-- Description: Create pgqueuer_dlq (Dead Letter Queue) for failed job tracking
-- Created: 2024-11-28

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Dead Letter Queue stores jobs that have permanently failed after all retries
-- Used for:
-- - Post-mortem analysis of failures
-- - Manual retry after fixing issues
-- - Failure pattern detection
-- - Audit trail of workflow failures

CREATE TABLE IF NOT EXISTS pgqueuer_dlq (
    -- Auto-incrementing primary key
    id BIGSERIAL PRIMARY KEY,

    -- Original job ID from pgqueuer
    job_id UUID NOT NULL,

    -- Workflow identifier (file path or unique ID)
    workflow_id TEXT NOT NULL,

    -- Human-readable workflow name for easier identification
    workflow_name TEXT NOT NULL,

    -- Input variables that were passed to the workflow
    variables JSONB,

    -- Error message or stack trace from final failure
    error TEXT NOT NULL,

    -- Number of retry attempts before moving to DLQ
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),

    -- Timestamp when the job was moved to DLQ
    failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Optional: robot that was executing when failure occurred
    robot_id TEXT,

    -- Optional: last node that was executing (for debugging)
    last_node TEXT,

    -- Optional: flag for manual review/acknowledgment
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,

    -- Optional: notes from manual review
    notes TEXT
);

-- Index for workflow-based queries (find all failures for a workflow)
CREATE INDEX IF NOT EXISTS idx_dlq_workflow ON pgqueuer_dlq(workflow_id);

-- Index for time-based queries (recent failures)
CREATE INDEX IF NOT EXISTS idx_dlq_failed_at ON pgqueuer_dlq(failed_at DESC);

-- Index for finding unacknowledged failures
CREATE INDEX IF NOT EXISTS idx_dlq_unacknowledged ON pgqueuer_dlq(acknowledged)
    WHERE acknowledged = FALSE;

-- Index for job_id lookups (checking if a job is in DLQ)
CREATE INDEX IF NOT EXISTS idx_dlq_job_id ON pgqueuer_dlq(job_id);

-- Composite index for workflow + time queries
CREATE INDEX IF NOT EXISTS idx_dlq_workflow_time ON pgqueuer_dlq(workflow_id, failed_at DESC);

-- Add comments for documentation
COMMENT ON TABLE pgqueuer_dlq IS 'Dead Letter Queue for permanently failed workflow jobs';
COMMENT ON COLUMN pgqueuer_dlq.job_id IS 'Original UUID from pgqueuer job table';
COMMENT ON COLUMN pgqueuer_dlq.workflow_id IS 'Workflow file path or unique identifier';
COMMENT ON COLUMN pgqueuer_dlq.variables IS 'Input variables passed to the workflow at execution time';
COMMENT ON COLUMN pgqueuer_dlq.error IS 'Final error message or stack trace';
COMMENT ON COLUMN pgqueuer_dlq.retry_count IS 'Number of retry attempts before failure';
COMMENT ON COLUMN pgqueuer_dlq.acknowledged IS 'Whether failure has been reviewed by operator';


-- ============================================================================
-- Optional: Create view for unacknowledged failures summary
-- ============================================================================

CREATE OR REPLACE VIEW dlq_summary AS
SELECT
    workflow_id,
    workflow_name,
    COUNT(*) as failure_count,
    MIN(failed_at) as first_failure,
    MAX(failed_at) as last_failure,
    SUM(CASE WHEN acknowledged THEN 0 ELSE 1 END) as unacknowledged_count
FROM pgqueuer_dlq
GROUP BY workflow_id, workflow_name
ORDER BY last_failure DESC;

COMMENT ON VIEW dlq_summary IS 'Summary of DLQ failures grouped by workflow';


-- ============================================================================
-- Optional: Function to move failed job to DLQ
-- ============================================================================

CREATE OR REPLACE FUNCTION move_to_dlq(
    p_job_id UUID,
    p_workflow_id TEXT,
    p_workflow_name TEXT,
    p_variables JSONB,
    p_error TEXT,
    p_retry_count INTEGER,
    p_robot_id TEXT DEFAULT NULL,
    p_last_node TEXT DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    new_id BIGINT;
BEGIN
    INSERT INTO pgqueuer_dlq (
        job_id, workflow_id, workflow_name, variables,
        error, retry_count, robot_id, last_node
    ) VALUES (
        p_job_id, p_workflow_id, p_workflow_name, p_variables,
        p_error, p_retry_count, p_robot_id, p_last_node
    )
    RETURNING id INTO new_id;

    RETURN new_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION move_to_dlq IS 'Insert a failed job into the Dead Letter Queue';


-- ============================================================================
-- Optional: Function to retry a DLQ entry (returns the entry for re-queueing)
-- ============================================================================

CREATE OR REPLACE FUNCTION retry_dlq_entry(p_dlq_id BIGINT)
RETURNS TABLE (
    job_id UUID,
    workflow_id TEXT,
    workflow_name TEXT,
    variables JSONB
) AS $$
BEGIN
    -- Mark as acknowledged before retry
    UPDATE pgqueuer_dlq
    SET acknowledged = TRUE,
        notes = COALESCE(notes, '') || E'\nRetried at ' || NOW()::TEXT
    WHERE id = p_dlq_id;

    -- Return the entry data for re-queueing
    RETURN QUERY
    SELECT d.job_id, d.workflow_id, d.workflow_name, d.variables
    FROM pgqueuer_dlq d
    WHERE d.id = p_dlq_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION retry_dlq_entry IS 'Mark DLQ entry as acknowledged and return data for re-queueing';


-- ============================================================================
-- DOWN MIGRATION (in separate file: 012_dlq_table_down.sql)
-- ============================================================================
