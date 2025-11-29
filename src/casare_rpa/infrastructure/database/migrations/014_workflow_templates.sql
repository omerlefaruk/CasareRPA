-- Migration: 014_workflow_templates
-- Description: Create workflow_templates table for template library system
-- Created: 2024-11-28

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Workflow Templates table stores reusable workflow patterns
-- Features:
-- - Parameterized templates with configurable variables
-- - Category-based organization
-- - Usage statistics and ratings
-- - Support for built-in and user-created templates
-- - Marketplace integration (future)

CREATE TABLE IF NOT EXISTS workflow_templates (
    -- Primary key: unique template identifier (tmpl_xxxx format)
    id VARCHAR(50) PRIMARY KEY,

    -- =========================================================================
    -- Metadata
    -- =========================================================================

    -- Template name (human-readable)
    name VARCHAR(255) NOT NULL,

    -- Template description
    description TEXT NOT NULL DEFAULT '',

    -- Template category for organization
    category VARCHAR(50) NOT NULL DEFAULT 'general'
        CHECK (category IN (
            'web_scraping',
            'data_entry',
            'report_generation',
            'api_integration',
            'file_operations',
            'email_processing',
            'database_operations',
            'desktop_automation',
            'pdf_processing',
            'excel_automation',
            'general',
            'custom'
        )),

    -- Semantic version (e.g., "1.0.0")
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

    -- Template author
    author VARCHAR(255) NOT NULL DEFAULT '',

    -- Tags for search/filtering (stored as JSON array)
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Difficulty level
    difficulty VARCHAR(20) NOT NULL DEFAULT 'intermediate'
        CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),

    -- Estimated execution duration (human-readable, e.g., "2-5 minutes")
    estimated_duration VARCHAR(100),

    -- Requirements/dependencies (stored as JSON array)
    requirements JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Icon identifier for UI
    icon VARCHAR(100) NOT NULL DEFAULT '',

    -- Preview image path/URL
    preview_image VARCHAR(500) NOT NULL DEFAULT '',

    -- =========================================================================
    -- Template Definition
    -- =========================================================================

    -- Configurable parameters (JSON array of parameter definitions)
    -- Each parameter: {name, display_name, description, param_type, default_value, required, constraints, group, order}
    parameters JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- The workflow definition with placeholders (full workflow JSON)
    -- Placeholders use {{parameter_name}} syntax
    workflow_definition JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- =========================================================================
    -- Source and Origin
    -- =========================================================================

    -- Whether this is a built-in system template (cannot be modified/deleted)
    is_builtin BOOLEAN NOT NULL DEFAULT FALSE,

    -- Template source: 'builtin', 'user', 'imported', 'marketplace'
    source VARCHAR(50) NOT NULL DEFAULT 'user',

    -- Marketplace identifier for marketplace templates
    marketplace_id VARCHAR(100),

    -- =========================================================================
    -- Usage Statistics
    -- =========================================================================

    -- Total number of times this template has been instantiated
    total_uses INTEGER NOT NULL DEFAULT 0 CHECK (total_uses >= 0),

    -- Successful instantiations
    successful_instantiations INTEGER NOT NULL DEFAULT 0 CHECK (successful_instantiations >= 0),

    -- Failed instantiations
    failed_instantiations INTEGER NOT NULL DEFAULT 0 CHECK (failed_instantiations >= 0),

    -- Last time the template was used
    last_used_at TIMESTAMPTZ,

    -- Average rating (1-5 scale)
    average_rating NUMERIC(3, 2) CHECK (average_rating IS NULL OR (average_rating >= 1 AND average_rating <= 5)),

    -- Number of ratings received
    rating_count INTEGER NOT NULL DEFAULT 0 CHECK (rating_count >= 0),

    -- =========================================================================
    -- Timestamps
    -- =========================================================================

    -- When the template was created
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- When the template was last modified
    modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Index for category-based queries
CREATE INDEX IF NOT EXISTS idx_templates_category ON workflow_templates(category);

-- Index for name search
CREATE INDEX IF NOT EXISTS idx_templates_name ON workflow_templates(name);

-- Index for built-in filter
CREATE INDEX IF NOT EXISTS idx_templates_builtin ON workflow_templates(is_builtin);

-- Index for source filter
CREATE INDEX IF NOT EXISTS idx_templates_source ON workflow_templates(source);

-- GIN index for tags search
CREATE INDEX IF NOT EXISTS idx_templates_tags ON workflow_templates USING GIN (tags);

-- Index for popularity sorting (by total uses)
CREATE INDEX IF NOT EXISTS idx_templates_uses ON workflow_templates(total_uses DESC);

-- Index for rating sorting
CREATE INDEX IF NOT EXISTS idx_templates_rating ON workflow_templates(average_rating DESC NULLS LAST);

-- Index for recent templates
CREATE INDEX IF NOT EXISTS idx_templates_created ON workflow_templates(created_at DESC);

-- Index for recently used templates
CREATE INDEX IF NOT EXISTS idx_templates_last_used ON workflow_templates(last_used_at DESC NULLS LAST);

-- Composite index for category + name search
CREATE INDEX IF NOT EXISTS idx_templates_category_name ON workflow_templates(category, name);

-- Full-text search index for name and description
CREATE INDEX IF NOT EXISTS idx_templates_fulltext ON workflow_templates
    USING GIN (to_tsvector('english', name || ' ' || description));

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE workflow_templates IS 'Workflow templates for rapid workflow creation';
COMMENT ON COLUMN workflow_templates.id IS 'Unique template identifier (tmpl_xxxx format)';
COMMENT ON COLUMN workflow_templates.parameters IS 'JSON array of configurable parameter definitions';
COMMENT ON COLUMN workflow_templates.workflow_definition IS 'Workflow JSON with {{placeholder}} syntax for parameters';
COMMENT ON COLUMN workflow_templates.is_builtin IS 'Built-in templates cannot be modified or deleted';
COMMENT ON COLUMN workflow_templates.marketplace_id IS 'Identifier for templates from the marketplace';

-- ============================================================================
-- Template Ratings Table (for detailed rating history)
-- ============================================================================

CREATE TABLE IF NOT EXISTS template_ratings (
    id BIGSERIAL PRIMARY KEY,

    -- Reference to template
    template_id VARCHAR(50) NOT NULL REFERENCES workflow_templates(id) ON DELETE CASCADE,

    -- Rating value (1-5)
    rating SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),

    -- Optional feedback/comment
    comment TEXT,

    -- User identifier (if authenticated)
    user_id VARCHAR(100),

    -- When the rating was submitted
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate ratings from same user
    UNIQUE (template_id, user_id)
);

-- Index for template-based queries
CREATE INDEX IF NOT EXISTS idx_ratings_template ON template_ratings(template_id);

-- Index for user ratings
CREATE INDEX IF NOT EXISTS idx_ratings_user ON template_ratings(user_id) WHERE user_id IS NOT NULL;

COMMENT ON TABLE template_ratings IS 'Individual ratings for workflow templates';

-- ============================================================================
-- Views
-- ============================================================================

-- View for template summary with calculated fields
CREATE OR REPLACE VIEW template_summary AS
SELECT
    t.id,
    t.name,
    t.description,
    t.category,
    t.version,
    t.author,
    t.tags,
    t.difficulty,
    t.is_builtin,
    t.source,
    t.total_uses,
    t.average_rating,
    t.rating_count,
    t.created_at,
    t.modified_at,
    t.last_used_at,
    jsonb_array_length(t.parameters) as parameter_count,
    CASE
        WHEN t.total_uses = 0 THEN NULL
        ELSE ROUND((t.successful_instantiations::NUMERIC / t.total_uses) * 100, 2)
    END as success_rate
FROM workflow_templates t
ORDER BY t.total_uses DESC, t.average_rating DESC NULLS LAST;

COMMENT ON VIEW template_summary IS 'Summary view of workflow templates with calculated metrics';

-- View for category statistics
CREATE OR REPLACE VIEW template_category_stats AS
SELECT
    category,
    COUNT(*) as template_count,
    SUM(total_uses) as total_uses,
    AVG(average_rating) FILTER (WHERE average_rating IS NOT NULL) as avg_rating,
    SUM(CASE WHEN is_builtin THEN 1 ELSE 0 END) as builtin_count,
    SUM(CASE WHEN NOT is_builtin THEN 1 ELSE 0 END) as user_count
FROM workflow_templates
GROUP BY category
ORDER BY template_count DESC;

COMMENT ON VIEW template_category_stats IS 'Statistics grouped by template category';

-- ============================================================================
-- Functions
-- ============================================================================

-- Function to record template usage
CREATE OR REPLACE FUNCTION record_template_use(
    p_template_id VARCHAR(50),
    p_success BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    UPDATE workflow_templates
    SET
        total_uses = total_uses + 1,
        successful_instantiations = successful_instantiations + CASE WHEN p_success THEN 1 ELSE 0 END,
        failed_instantiations = failed_instantiations + CASE WHEN p_success THEN 0 ELSE 1 END,
        last_used_at = NOW()
    WHERE id = p_template_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION record_template_use IS 'Record a template instantiation attempt';

-- Function to add a rating to a template
CREATE OR REPLACE FUNCTION rate_template(
    p_template_id VARCHAR(50),
    p_rating SMALLINT,
    p_user_id VARCHAR(100) DEFAULT NULL,
    p_comment TEXT DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    v_old_avg NUMERIC(3,2);
    v_old_count INTEGER;
    v_new_avg NUMERIC(3,2);
BEGIN
    -- Validate rating
    IF p_rating < 1 OR p_rating > 5 THEN
        RAISE EXCEPTION 'Rating must be between 1 and 5';
    END IF;

    -- Insert or update rating
    INSERT INTO template_ratings (template_id, rating, user_id, comment)
    VALUES (p_template_id, p_rating, p_user_id, p_comment)
    ON CONFLICT (template_id, user_id)
    DO UPDATE SET
        rating = p_rating,
        comment = p_comment,
        created_at = NOW();

    -- Recalculate average rating
    SELECT AVG(rating), COUNT(*)
    INTO v_new_avg, v_old_count
    FROM template_ratings
    WHERE template_id = p_template_id;

    -- Update template statistics
    UPDATE workflow_templates
    SET
        average_rating = v_new_avg,
        rating_count = v_old_count
    WHERE id = p_template_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION rate_template IS 'Add or update a rating for a template';

-- Function to search templates with full-text search
CREATE OR REPLACE FUNCTION search_templates(
    p_query TEXT,
    p_category VARCHAR(50) DEFAULT NULL,
    p_is_builtin BOOLEAN DEFAULT NULL,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id VARCHAR(50),
    name VARCHAR(255),
    description TEXT,
    category VARCHAR(50),
    tags JSONB,
    difficulty VARCHAR(20),
    is_builtin BOOLEAN,
    total_uses INTEGER,
    average_rating NUMERIC(3,2),
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.name,
        t.description,
        t.category,
        t.tags,
        t.difficulty,
        t.is_builtin,
        t.total_uses,
        t.average_rating,
        ts_rank(to_tsvector('english', t.name || ' ' || t.description), plainto_tsquery('english', p_query)) as rank
    FROM workflow_templates t
    WHERE
        (p_query IS NULL OR p_query = '' OR
         to_tsvector('english', t.name || ' ' || t.description) @@ plainto_tsquery('english', p_query))
        AND (p_category IS NULL OR t.category = p_category)
        AND (p_is_builtin IS NULL OR t.is_builtin = p_is_builtin)
    ORDER BY
        rank DESC,
        t.total_uses DESC,
        t.average_rating DESC NULLS LAST
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION search_templates IS 'Search templates with full-text search and filtering';

-- Function to get popular templates
CREATE OR REPLACE FUNCTION get_popular_templates(
    p_category VARCHAR(50) DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id VARCHAR(50),
    name VARCHAR(255),
    category VARCHAR(50),
    total_uses INTEGER,
    average_rating NUMERIC(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.name,
        t.category,
        t.total_uses,
        t.average_rating
    FROM workflow_templates t
    WHERE p_category IS NULL OR t.category = p_category
    ORDER BY t.total_uses DESC, t.average_rating DESC NULLS LAST
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_popular_templates IS 'Get most popular templates by usage';

-- ============================================================================
-- Trigger to update modified_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_template_modified_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_template_modified ON workflow_templates;
CREATE TRIGGER trigger_template_modified
    BEFORE UPDATE ON workflow_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_template_modified_at();


-- ============================================================================
-- DOWN MIGRATION (in separate file: 014_workflow_templates_down.sql)
-- ============================================================================
