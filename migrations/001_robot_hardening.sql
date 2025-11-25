-- Migration: Robot Hardening (Phase 8B)
-- Description: Add columns for job locking, progress reporting, and cancellation
-- Date: 2024-01-15

-- ============================================================================
-- ROBOTS TABLE UPDATES
-- ============================================================================

-- Add version and metrics columns to robots table
ALTER TABLE robots ADD COLUMN IF NOT EXISTS version TEXT DEFAULT '1.0.0';
ALTER TABLE robots ADD COLUMN IF NOT EXISTS metrics JSONB DEFAULT '{}';
ALTER TABLE robots ADD COLUMN IF NOT EXISTS capabilities JSONB DEFAULT '[]';
ALTER TABLE robots ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- Add index for robot status queries
CREATE INDEX IF NOT EXISTS idx_robots_status ON robots(status);
CREATE INDEX IF NOT EXISTS idx_robots_last_seen ON robots(last_seen);

-- ============================================================================
-- JOBS TABLE UPDATES
-- ============================================================================

-- Add job locking columns
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS claimed_by UUID REFERENCES robots(id);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS lock_heartbeat TIMESTAMPTZ;

-- Add cancellation support
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS cancel_requested BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS cancel_reason TEXT;

-- Add progress reporting
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS progress JSONB DEFAULT '{}';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Add error tracking
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS error TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS error_details JSONB;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Add priority for job ordering
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;

-- Add indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_robot_id ON jobs(robot_id);
CREATE INDEX IF NOT EXISTS idx_jobs_claimed_by ON jobs(claimed_by);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority DESC, created_at ASC);

-- Composite index for pending job queries
CREATE INDEX IF NOT EXISTS idx_jobs_pending_unclaimed
ON jobs(robot_id, status, claimed_by)
WHERE status = 'pending' AND claimed_by IS NULL;

-- ============================================================================
-- JOB HISTORY TABLE (for audit trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    robot_id UUID REFERENCES robots(id),
    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_history_job_id ON job_history(job_id);
CREATE INDEX IF NOT EXISTS idx_job_history_created_at ON job_history(created_at);

-- ============================================================================
-- ROBOT METRICS TABLE (for time-series metrics)
-- ============================================================================

CREATE TABLE IF NOT EXISTS robot_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    robot_id UUID NOT NULL REFERENCES robots(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL,
    metric_value JSONB NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_robot_metrics_robot_id ON robot_metrics(robot_id);
CREATE INDEX IF NOT EXISTS idx_robot_metrics_recorded_at ON robot_metrics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_robot_metrics_type ON robot_metrics(metric_type);

-- Composite index for metric queries
CREATE INDEX IF NOT EXISTS idx_robot_metrics_robot_type_time
ON robot_metrics(robot_id, metric_type, recorded_at DESC);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to claim a job atomically
CREATE OR REPLACE FUNCTION claim_job(
    p_job_id UUID,
    p_robot_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_claimed BOOLEAN;
BEGIN
    UPDATE jobs
    SET
        claimed_by = p_robot_id,
        claimed_at = NOW(),
        status = 'running'
    WHERE
        id = p_job_id
        AND status = 'pending'
        AND claimed_by IS NULL
    RETURNING TRUE INTO v_claimed;

    RETURN COALESCE(v_claimed, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Function to release a job (for retry or failure)
CREATE OR REPLACE FUNCTION release_job(
    p_job_id UUID,
    p_robot_id UUID,
    p_new_status TEXT DEFAULT 'pending'
) RETURNS BOOLEAN AS $$
DECLARE
    v_released BOOLEAN;
BEGIN
    UPDATE jobs
    SET
        claimed_by = NULL,
        claimed_at = NULL,
        status = p_new_status
    WHERE
        id = p_job_id
        AND claimed_by = p_robot_id
    RETURNING TRUE INTO v_released;

    RETURN COALESCE(v_released, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Function to clean up stale job locks
CREATE OR REPLACE FUNCTION cleanup_stale_locks(
    p_timeout_minutes INTEGER DEFAULT 5
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE jobs
    SET
        claimed_by = NULL,
        claimed_at = NULL,
        status = 'pending'
    WHERE
        status = 'running'
        AND claimed_by IS NOT NULL
        AND lock_heartbeat < NOW() - (p_timeout_minutes || ' minutes')::INTERVAL
    RETURNING COUNT(*) INTO v_count;

    RETURN COALESCE(v_count, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to record job event
CREATE OR REPLACE FUNCTION record_job_event(
    p_job_id UUID,
    p_robot_id UUID,
    p_event_type TEXT,
    p_event_data JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    INSERT INTO job_history (job_id, robot_id, event_type, event_data)
    VALUES (p_job_id, p_robot_id, p_event_type, p_event_data)
    RETURNING id INTO v_event_id;

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to automatically record job status changes
CREATE OR REPLACE FUNCTION trigger_job_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        PERFORM record_job_event(
            NEW.id,
            NEW.claimed_by,
            'status_changed',
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS job_status_change_trigger ON jobs;
CREATE TRIGGER job_status_change_trigger
    AFTER UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION trigger_job_status_change();

-- ============================================================================
-- ROW LEVEL SECURITY (Optional - enable if using Supabase auth)
-- ============================================================================

-- Enable RLS on tables
-- ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE robots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE job_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE robot_metrics ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- REALTIME SUBSCRIPTIONS
-- ============================================================================

-- Enable realtime for jobs table (for progress updates)
-- Run this in Supabase dashboard or via SQL:
-- ALTER PUBLICATION supabase_realtime ADD TABLE jobs;

-- ============================================================================
-- CLEANUP OLD DATA (scheduled job)
-- ============================================================================

-- Function to clean up old metrics (call periodically)
CREATE OR REPLACE FUNCTION cleanup_old_metrics(
    p_days INTEGER DEFAULT 7
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    DELETE FROM robot_metrics
    WHERE recorded_at < NOW() - (p_days || ' days')::INTERVAL;
    GET DIAGNOSTICS v_count = ROW_COUNT;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old job history
CREATE OR REPLACE FUNCTION cleanup_old_history(
    p_days INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    DELETE FROM job_history
    WHERE created_at < NOW() - (p_days || ' days')::INTERVAL;
    GET DIAGNOSTICS v_count = ROW_COUNT;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;
