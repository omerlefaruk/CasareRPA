-- Migration: 014_workflow_templates_down
-- Description: Drop workflow_templates table and related objects
-- Created: 2024-11-28

-- ============================================================================
-- DOWN MIGRATION
-- ============================================================================

-- Drop triggers
DROP TRIGGER IF EXISTS trigger_template_modified ON workflow_templates;

-- Drop functions
DROP FUNCTION IF EXISTS get_popular_templates(VARCHAR(50), INTEGER);
DROP FUNCTION IF EXISTS search_templates(TEXT, VARCHAR(50), BOOLEAN, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS rate_template(VARCHAR(50), SMALLINT, VARCHAR(100), TEXT);
DROP FUNCTION IF EXISTS record_template_use(VARCHAR(50), BOOLEAN);
DROP FUNCTION IF EXISTS update_template_modified_at();

-- Drop views
DROP VIEW IF EXISTS template_category_stats;
DROP VIEW IF EXISTS template_summary;

-- Drop ratings table (references templates)
DROP TABLE IF EXISTS template_ratings;

-- Drop main table
DROP TABLE IF EXISTS workflow_templates;
