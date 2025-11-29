-- Migration: 013_workflow_versions
-- Description: Drop workflow versioning tables
-- DOWN MIGRATION

-- Drop views first
DROP VIEW IF EXISTS migration_history;
DROP VIEW IF EXISTS active_versions_with_pins;
DROP VIEW IF EXISTS latest_workflow_versions;

-- Drop functions
DROP FUNCTION IF EXISTS create_workflow_version;
DROP FUNCTION IF EXISTS jsonb_object_keys_count;
DROP FUNCTION IF EXISTS activate_workflow_version;
DROP FUNCTION IF EXISTS get_job_workflow_version;
DROP FUNCTION IF EXISTS get_active_workflow_version;
DROP FUNCTION IF EXISTS update_job_version_pins_timestamp;

-- Drop triggers
DROP TRIGGER IF EXISTS trg_update_jvp_timestamp ON job_version_pins;

-- Drop tables (in reverse order of dependencies)
DROP TABLE IF EXISTS breaking_changes_log;
DROP TABLE IF EXISTS workflow_migrations;
DROP TABLE IF EXISTS job_version_pins;
DROP TABLE IF EXISTS workflow_versions;
