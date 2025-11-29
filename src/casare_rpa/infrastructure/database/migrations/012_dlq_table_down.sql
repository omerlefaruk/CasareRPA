-- Migration: 012_dlq_table (DOWN)
-- Description: Remove pgqueuer_dlq table and related objects
-- Created: 2024-11-28

-- ============================================================================
-- DOWN MIGRATION
-- ============================================================================

-- Drop functions first
DROP FUNCTION IF EXISTS retry_dlq_entry(BIGINT);
DROP FUNCTION IF EXISTS move_to_dlq(UUID, TEXT, TEXT, JSONB, TEXT, INTEGER, TEXT, TEXT);

-- Drop view
DROP VIEW IF EXISTS dlq_summary;

-- Drop indexes
DROP INDEX IF EXISTS idx_dlq_workflow_time;
DROP INDEX IF EXISTS idx_dlq_job_id;
DROP INDEX IF EXISTS idx_dlq_unacknowledged;
DROP INDEX IF EXISTS idx_dlq_failed_at;
DROP INDEX IF EXISTS idx_dlq_workflow;

-- Drop the DLQ table
DROP TABLE IF EXISTS pgqueuer_dlq CASCADE;
