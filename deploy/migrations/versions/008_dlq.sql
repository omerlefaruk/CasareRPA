-- Migration: 008_dlq
-- Description: Dead letter queue for failed jobs
-- Consolidated from:
--   - src/casare_rpa/infrastructure/database/migrations/012_dlq_table.sql
-- Created: 2024-12-03

-- =============================================================================
-- DEAD LETTER QUEUE TABLE
-- =============================================================================
-- Stores jobs that have exhausted their retries for later analysis and reprocessing
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Original job information
    original_job_id UUID NOT NULL,
    workflow_id UUID,
    workflow_name VARCHAR(255),
    workflow_json TEXT,

    -- Failure context
    failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    failure_reason TEXT NOT NULL,
    failure_count INTEGER NOT NULL DEFAULT 1,
    last_error TEXT,
    error_details JSONB DEFAULT '{}'::jsonb,

    -- Original job data
    original_payload JSONB DEFAULT '{}'::jsonb,
    original_variables JSONB DEFAULT '{}'::jsonb,
    original_metadata JSONB DEFAULT '{}'::jsonb,

    -- Execution context
    robot_id VARCHAR(255),
    environment VARCHAR(100),
    priority INTEGER,

    -- Reprocessing status
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'reviewing', 'requeued', 'discarded', 'resolved')),
    reprocessed_at TIMESTAMPTZ,
    reprocessed_by VARCHAR(255),
    reprocess_job_id UUID,
    resolution_notes TEXT,

    -- Categorization for analysis
    error_category VARCHAR(100),
    tags TEXT[] DEFAULT '{}',

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Index for finding unprocessed items
CREATE INDEX IF NOT EXISTS idx_dlq_status ON dead_letter_queue(status)
    WHERE status IN ('pending', 'reviewing');

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_dlq_failed_at ON dead_letter_queue(failed_at DESC);

-- Index for workflow-based analysis
CREATE INDEX IF NOT EXISTS idx_dlq_workflow ON dead_letter_queue(workflow_id);

-- Index for error category analysis
CREATE INDEX IF NOT EXISTS idx_dlq_error_category ON dead_letter_queue(error_category)
    WHERE error_category IS NOT NULL;

-- Index for original job lookups
CREATE INDEX IF NOT EXISTS idx_dlq_original_job ON dead_letter_queue(original_job_id);

-- Index for robot-based analysis
CREATE INDEX IF NOT EXISTS idx_dlq_robot ON dead_letter_queue(robot_id)
    WHERE robot_id IS NOT NULL;

-- GIN index for tag-based queries
CREATE INDEX IF NOT EXISTS idx_dlq_tags ON dead_letter_queue USING GIN(tags);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to move a failed job to DLQ
CREATE OR REPLACE FUNCTION move_to_dlq(
    p_job_id UUID,
    p_failure_reason TEXT,
    p_last_error TEXT DEFAULT NULL,
    p_error_details JSONB DEFAULT NULL,
    p_error_category VARCHAR(100) DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_dlq_id UUID;
    v_job RECORD;
BEGIN
    -- Get original job data from job_queue
    SELECT * INTO v_job FROM job_queue WHERE id = p_job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Job % not found', p_job_id;
    END IF;

    -- Insert into DLQ
    INSERT INTO dead_letter_queue (
        original_job_id,
        workflow_id,
        workflow_name,
        workflow_json,
        failure_reason,
        failure_count,
        last_error,
        error_details,
        original_payload,
        original_variables,
        original_metadata,
        robot_id,
        environment,
        priority,
        error_category
    ) VALUES (
        p_job_id,
        v_job.workflow_id::UUID,
        v_job.workflow_name,
        v_job.workflow_json,
        p_failure_reason,
        v_job.retry_count + 1,
        COALESCE(p_last_error, v_job.error_message),
        COALESCE(p_error_details, '{}'::jsonb),
        v_job.metadata,
        v_job.variables,
        v_job.metadata,
        v_job.robot_id,
        v_job.environment,
        v_job.priority,
        p_error_category
    )
    RETURNING id INTO v_dlq_id;

    -- Update original job status to 'failed'
    UPDATE job_queue
    SET
        status = 'failed',
        error_message = p_failure_reason,
        completed_at = NOW()
    WHERE id = p_job_id;

    RETURN v_dlq_id;
END;
$$ LANGUAGE plpgsql;

-- Function to requeue a DLQ item
CREATE OR REPLACE FUNCTION requeue_from_dlq(
    p_dlq_id UUID,
    p_requeued_by VARCHAR(255) DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_dlq_item RECORD;
    v_new_job_id UUID;
BEGIN
    -- Get DLQ item
    SELECT * INTO v_dlq_item FROM dead_letter_queue WHERE id = p_dlq_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'DLQ item % not found', p_dlq_id;
    END IF;

    IF v_dlq_item.status NOT IN ('pending', 'reviewing') THEN
        RAISE EXCEPTION 'DLQ item % cannot be requeued (status: %)', p_dlq_id, v_dlq_item.status;
    END IF;

    -- Create new job
    INSERT INTO job_queue (
        workflow_id,
        workflow_name,
        workflow_json,
        priority,
        environment,
        variables,
        metadata,
        status
    ) VALUES (
        v_dlq_item.workflow_id::VARCHAR,
        v_dlq_item.workflow_name,
        v_dlq_item.workflow_json,
        v_dlq_item.priority,
        COALESCE(v_dlq_item.environment, 'default'),
        v_dlq_item.original_variables,
        jsonb_build_object(
            'requeued_from_dlq', p_dlq_id,
            'original_job_id', v_dlq_item.original_job_id,
            'requeue_notes', p_notes
        ) || COALESCE(v_dlq_item.original_metadata, '{}'::jsonb),
        'pending'
    )
    RETURNING id INTO v_new_job_id;

    -- Update DLQ item
    UPDATE dead_letter_queue
    SET
        status = 'requeued',
        reprocessed_at = NOW(),
        reprocessed_by = p_requeued_by,
        reprocess_job_id = v_new_job_id,
        resolution_notes = p_notes,
        updated_at = NOW()
    WHERE id = p_dlq_id;

    RETURN v_new_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to discard a DLQ item
CREATE OR REPLACE FUNCTION discard_dlq_item(
    p_dlq_id UUID,
    p_discarded_by VARCHAR(255) DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE dead_letter_queue
    SET
        status = 'discarded',
        reprocessed_at = NOW(),
        reprocessed_by = p_discarded_by,
        resolution_notes = p_notes,
        updated_at = NOW()
    WHERE id = p_dlq_id
    AND status IN ('pending', 'reviewing');

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to get DLQ statistics
CREATE OR REPLACE FUNCTION get_dlq_stats()
RETURNS TABLE (
    total_items BIGINT,
    pending_items BIGINT,
    reviewing_items BIGINT,
    requeued_items BIGINT,
    discarded_items BIGINT,
    resolved_items BIGINT,
    items_last_24h BIGINT,
    items_last_7d BIGINT,
    top_error_categories JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT AS total_items,
        COUNT(*) FILTER (WHERE d.status = 'pending')::BIGINT AS pending_items,
        COUNT(*) FILTER (WHERE d.status = 'reviewing')::BIGINT AS reviewing_items,
        COUNT(*) FILTER (WHERE d.status = 'requeued')::BIGINT AS requeued_items,
        COUNT(*) FILTER (WHERE d.status = 'discarded')::BIGINT AS discarded_items,
        COUNT(*) FILTER (WHERE d.status = 'resolved')::BIGINT AS resolved_items,
        COUNT(*) FILTER (WHERE d.failed_at > NOW() - INTERVAL '24 hours')::BIGINT AS items_last_24h,
        COUNT(*) FILTER (WHERE d.failed_at > NOW() - INTERVAL '7 days')::BIGINT AS items_last_7d,
        (
            SELECT jsonb_agg(jsonb_build_object('category', category, 'count', cnt))
            FROM (
                SELECT error_category AS category, COUNT(*) AS cnt
                FROM dead_letter_queue
                WHERE error_category IS NOT NULL
                AND status = 'pending'
                GROUP BY error_category
                ORDER BY cnt DESC
                LIMIT 5
            ) sub
        ) AS top_error_categories
    FROM dead_letter_queue d;
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View for DLQ analysis
CREATE OR REPLACE VIEW dlq_analysis AS
SELECT
    workflow_id,
    workflow_name,
    error_category,
    COUNT(*) AS failure_count,
    MIN(failed_at) AS first_failure,
    MAX(failed_at) AS last_failure,
    AVG(failure_count)::NUMERIC(5,2) AS avg_retries_before_dlq,
    array_agg(DISTINCT robot_id) FILTER (WHERE robot_id IS NOT NULL) AS affected_robots
FROM dead_letter_queue
WHERE status = 'pending'
GROUP BY workflow_id, workflow_name, error_category
ORDER BY failure_count DESC;

-- View for recent failures
CREATE OR REPLACE VIEW dlq_recent_failures AS
SELECT
    id,
    original_job_id,
    workflow_name,
    failure_reason,
    last_error,
    error_category,
    robot_id,
    failed_at,
    status,
    failure_count
FROM dead_letter_queue
WHERE failed_at > NOW() - INTERVAL '7 days'
ORDER BY failed_at DESC;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_dlq_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_dlq_updated_at ON dead_letter_queue;
CREATE TRIGGER trigger_dlq_updated_at
    BEFORE UPDATE ON dead_letter_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_dlq_updated_at();

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE dead_letter_queue IS 'Storage for failed jobs that exhausted retries';
COMMENT ON COLUMN dead_letter_queue.status IS 'pending: awaiting review, reviewing: being analyzed, requeued: sent back to queue, discarded: manually dismissed, resolved: auto-resolved';
COMMENT ON FUNCTION move_to_dlq IS 'Move a failed job to the dead letter queue';
COMMENT ON FUNCTION requeue_from_dlq IS 'Requeue a DLQ item back to the job queue';
COMMENT ON FUNCTION get_dlq_stats IS 'Get DLQ statistics for monitoring';
