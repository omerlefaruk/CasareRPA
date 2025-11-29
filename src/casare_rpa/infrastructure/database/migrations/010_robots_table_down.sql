-- Migration: 010_robots_table (DOWN)
-- Description: Remove robots table and related indexes
-- Created: 2024-11-28

-- ============================================================================
-- DOWN MIGRATION
-- ============================================================================

-- Drop indexes first (some may cascade, but explicit is safer)
DROP INDEX IF EXISTS idx_robots_capabilities;
DROP INDEX IF EXISTS idx_robots_idle;
DROP INDEX IF EXISTS idx_robots_last_seen;
DROP INDEX IF EXISTS idx_robots_status;

-- Drop the robots table
DROP TABLE IF EXISTS robots CASCADE;
