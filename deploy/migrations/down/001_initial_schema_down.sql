-- Migration Rollback: 001_initial_schema
-- Description: Drop core tables - robots, workflows, users

-- Drop views first (they depend on tables)
DROP VIEW IF EXISTS workflow_assignment_stats CASCADE;
DROP VIEW IF EXISTS robot_stats CASCADE;
DROP VIEW IF EXISTS queue_stats CASCADE;
DROP VIEW IF EXISTS workflow_stats CASCADE;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS node_robot_overrides CASCADE;
DROP TABLE IF EXISTS workflow_robot_assignments CASCADE;
DROP TABLE IF EXISTS workflow_versions CASCADE;
DROP TABLE IF EXISTS schedules CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS robots CASCADE;
DROP TABLE IF EXISTS workflows CASCADE;

-- Drop the utility function (only if no other migrations use it)
-- Note: Keep this function as other migrations may depend on it
-- DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
