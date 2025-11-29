-- Migration: 011_heartbeats_table (DOWN)
-- Description: Remove robot_heartbeats table and related objects
-- Created: 2024-11-28

-- ============================================================================
-- DOWN MIGRATION
-- ============================================================================

-- Drop functions first
DROP FUNCTION IF EXISTS cleanup_old_heartbeats(INTEGER);
DROP FUNCTION IF EXISTS get_latest_heartbeat(TEXT);

-- Drop indexes
DROP INDEX IF EXISTS idx_heartbeats_timestamp;
DROP INDEX IF EXISTS idx_heartbeats_job;
DROP INDEX IF EXISTS idx_heartbeats_robot;

-- Drop the heartbeats table
DROP TABLE IF EXISTS robot_heartbeats CASCADE;
