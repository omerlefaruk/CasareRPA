-- Migration: 017_workflow_templates
-- Description: Enhanced workflow templates with versioning, reviews, and marketplace support
-- Created: 2024-11-29
-- Note: This migration extends/replaces 014_workflow_templates if not applied

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- ============================================================================
-- Template Versions Table (for template versioning)
-- ============================================================================

CREATE TABLE IF NOT EXISTS template_versions (
    id BIGSERIAL PRIMARY KEY,

    -- Reference to parent template
    template_id VARCHAR(50) NOT NULL,

    -- Version information
    version VARCHAR(20) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,

    -- Version metadata
    change_summary TEXT NOT NULL DEFAULT '',
    breaking_changes BOOLEAN NOT NULL DEFAULT FALSE,

    -- Full template snapshot for this version
    workflow_definition JSONB NOT NULL,
    parameters JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Version status
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'published', 'deprecated', 'archived')),

    -- Publishing information
    published_at TIMESTAMPTZ,
    published_by VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure unique version per template
    UNIQUE (template_id, version)
);

-- Index for template version queries
CREATE INDEX IF NOT EXISTS idx_template_versions_template ON template_versions(template_id);
CREATE INDEX IF NOT EXISTS idx_template_versions_status ON template_versions(status);
CREATE INDEX IF NOT EXISTS idx_template_versions_published ON template_versions(published_at DESC);

COMMENT ON TABLE template_versions IS 'Version history for workflow templates';
COMMENT ON COLUMN template_versions.version IS 'Semantic version (e.g., 1.0.0)';
COMMENT ON COLUMN template_versions.breaking_changes IS 'Whether this version has breaking changes';

-- ============================================================================
-- Template Reviews Table (for rating and review system)
-- ============================================================================

CREATE TABLE IF NOT EXISTS template_reviews (
    id BIGSERIAL PRIMARY KEY,

    -- Reference to template
    template_id VARCHAR(50) NOT NULL,

    -- Review content
    rating SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200) NOT NULL DEFAULT '',
    review_text TEXT NOT NULL DEFAULT '',

    -- Review metadata
    reviewer_id VARCHAR(100),
    reviewer_name VARCHAR(200) NOT NULL DEFAULT 'Anonymous',

    -- Review verification
    verified_use BOOLEAN NOT NULL DEFAULT FALSE,
    template_version VARCHAR(20),

    -- Helpfulness tracking
    helpful_count INTEGER NOT NULL DEFAULT 0 CHECK (helpful_count >= 0),
    not_helpful_count INTEGER NOT NULL DEFAULT 0 CHECK (not_helpful_count >= 0),

    -- Moderation
    status VARCHAR(20) NOT NULL DEFAULT 'published'
        CHECK (status IN ('pending', 'published', 'hidden', 'removed')),
    moderated_at TIMESTAMPTZ,
    moderated_by VARCHAR(100),
    moderation_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate reviews per user per template
    UNIQUE (template_id, reviewer_id)
);

-- Indexes for review queries
CREATE INDEX IF NOT EXISTS idx_template_reviews_template ON template_reviews(template_id);
CREATE INDEX IF NOT EXISTS idx_template_reviews_rating ON template_reviews(rating);
CREATE INDEX IF NOT EXISTS idx_template_reviews_reviewer ON template_reviews(reviewer_id) WHERE reviewer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_template_reviews_status ON template_reviews(status);
CREATE INDEX IF NOT EXISTS idx_template_reviews_helpful ON template_reviews(helpful_count DESC);
CREATE INDEX IF NOT EXISTS idx_template_reviews_created ON template_reviews(created_at DESC);

COMMENT ON TABLE template_reviews IS 'User reviews and ratings for workflow templates';
COMMENT ON COLUMN template_reviews.verified_use IS 'Whether reviewer actually used the template';

-- ============================================================================
-- Template Downloads/Usage Log (for analytics)
-- ============================================================================

CREATE TABLE IF NOT EXISTS template_usage_log (
    id BIGSERIAL PRIMARY KEY,

    -- Reference to template
    template_id VARCHAR(50) NOT NULL,
    template_version VARCHAR(20),

    -- Usage information
    action VARCHAR(50) NOT NULL
        CHECK (action IN ('view', 'instantiate', 'download', 'clone', 'rate', 'review')),

    -- User/session info
    user_id VARCHAR(100),
    session_id VARCHAR(100),

    -- Result info
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,

    -- Context
    source VARCHAR(50),  -- 'library', 'search', 'recommendation', 'direct'

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_usage_log_template ON template_usage_log(template_id);
CREATE INDEX IF NOT EXISTS idx_usage_log_action ON template_usage_log(action);
CREATE INDEX IF NOT EXISTS idx_usage_log_created ON template_usage_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_log_user ON template_usage_log(user_id) WHERE user_id IS NOT NULL;

-- Partition by month for large-scale deployments (optional)
-- CREATE INDEX IF NOT EXISTS idx_usage_log_month ON template_usage_log(date_trunc('month', created_at));

COMMENT ON TABLE template_usage_log IS 'Detailed usage log for template analytics';

-- ============================================================================
-- Template Collections (for organizing templates into groups)
-- ============================================================================

CREATE TABLE IF NOT EXISTS template_collections (
    id VARCHAR(50) PRIMARY KEY,

    -- Collection metadata
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    icon VARCHAR(100) NOT NULL DEFAULT '',

    -- Collection type
    collection_type VARCHAR(50) NOT NULL DEFAULT 'custom'
        CHECK (collection_type IN ('featured', 'category', 'curated', 'custom', 'user')),

    -- Visibility
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    owner_id VARCHAR(100),

    -- Display order
    display_order INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collections_type ON template_collections(collection_type);
CREATE INDEX IF NOT EXISTS idx_collections_public ON template_collections(is_public);
CREATE INDEX IF NOT EXISTS idx_collections_order ON template_collections(display_order);

COMMENT ON TABLE template_collections IS 'Collections for grouping related templates';

-- ============================================================================
-- Template Collection Items (many-to-many relationship)
-- ============================================================================

CREATE TABLE IF NOT EXISTS template_collection_items (
    id BIGSERIAL PRIMARY KEY,

    collection_id VARCHAR(50) NOT NULL REFERENCES template_collections(id) ON DELETE CASCADE,
    template_id VARCHAR(50) NOT NULL,

    -- Item order within collection
    display_order INTEGER NOT NULL DEFAULT 0,

    -- Optional notes about why template is in collection
    notes TEXT,

    -- Timestamps
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicates
    UNIQUE (collection_id, template_id)
);

CREATE INDEX IF NOT EXISTS idx_collection_items_collection ON template_collection_items(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_items_template ON template_collection_items(template_id);

COMMENT ON TABLE template_collection_items IS 'Templates belonging to collections';

-- ============================================================================
-- Template Dependencies (for templates that require other templates)
-- ============================================================================

CREATE TABLE IF NOT EXISTS template_dependencies (
    id BIGSERIAL PRIMARY KEY,

    -- Dependent template
    template_id VARCHAR(50) NOT NULL,

    -- Required template
    depends_on_id VARCHAR(50) NOT NULL,

    -- Dependency type
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'required'
        CHECK (dependency_type IN ('required', 'optional', 'suggested')),

    -- Version constraint (semver range, e.g., ">=1.0.0")
    version_constraint VARCHAR(50),

    -- Description of why dependency exists
    reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate dependencies
    UNIQUE (template_id, depends_on_id)
);

CREATE INDEX IF NOT EXISTS idx_dependencies_template ON template_dependencies(template_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_depends_on ON template_dependencies(depends_on_id);

COMMENT ON TABLE template_dependencies IS 'Dependencies between templates';

-- ============================================================================
-- Views for Analytics
-- ============================================================================

-- Template popularity view
CREATE OR REPLACE VIEW template_popularity AS
SELECT
    t.id,
    t.name,
    t.category,
    t.total_uses,
    t.average_rating,
    t.rating_count,
    COUNT(DISTINCT r.id) as review_count,
    COUNT(DISTINCT CASE WHEN l.action = 'view' THEN l.id END) as view_count,
    COUNT(DISTINCT CASE WHEN l.action = 'instantiate' THEN l.id END) as instantiate_count,
    COUNT(DISTINCT CASE WHEN l.action = 'clone' THEN l.id END) as clone_count
FROM workflow_templates t
LEFT JOIN template_reviews r ON t.id = r.template_id AND r.status = 'published'
LEFT JOIN template_usage_log l ON t.id = l.template_id AND l.created_at > NOW() - INTERVAL '30 days'
GROUP BY t.id, t.name, t.category, t.total_uses, t.average_rating, t.rating_count
ORDER BY t.total_uses DESC, t.average_rating DESC NULLS LAST;

COMMENT ON VIEW template_popularity IS 'Template popularity metrics with recent activity';

-- Template review summary view
CREATE OR REPLACE VIEW template_review_summary AS
SELECT
    template_id,
    COUNT(*) as total_reviews,
    AVG(rating)::NUMERIC(3,2) as avg_rating,
    COUNT(CASE WHEN rating = 5 THEN 1 END) as five_star,
    COUNT(CASE WHEN rating = 4 THEN 1 END) as four_star,
    COUNT(CASE WHEN rating = 3 THEN 1 END) as three_star,
    COUNT(CASE WHEN rating = 2 THEN 1 END) as two_star,
    COUNT(CASE WHEN rating = 1 THEN 1 END) as one_star,
    SUM(helpful_count) as total_helpful,
    MAX(created_at) as latest_review
FROM template_reviews
WHERE status = 'published'
GROUP BY template_id;

COMMENT ON VIEW template_review_summary IS 'Aggregated review statistics per template';

-- ============================================================================
-- Functions
-- ============================================================================

-- Function to log template usage
CREATE OR REPLACE FUNCTION log_template_usage(
    p_template_id VARCHAR(50),
    p_action VARCHAR(50),
    p_user_id VARCHAR(100) DEFAULT NULL,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL,
    p_source VARCHAR(50) DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO template_usage_log (
        template_id, action, user_id, success, error_message, source
    ) VALUES (
        p_template_id, p_action, p_user_id, p_success, p_error_message, p_source
    );

    -- Update template statistics for instantiate/clone actions
    IF p_action IN ('instantiate', 'clone') AND p_success THEN
        UPDATE workflow_templates
        SET
            total_uses = total_uses + 1,
            successful_instantiations = successful_instantiations + 1,
            last_used_at = NOW()
        WHERE id = p_template_id;
    ELSIF p_action = 'instantiate' AND NOT p_success THEN
        UPDATE workflow_templates
        SET
            total_uses = total_uses + 1,
            failed_instantiations = failed_instantiations + 1,
            last_used_at = NOW()
        WHERE id = p_template_id;
    END IF;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION log_template_usage IS 'Log template usage and update statistics';

-- Function to add/update a review
CREATE OR REPLACE FUNCTION submit_template_review(
    p_template_id VARCHAR(50),
    p_rating SMALLINT,
    p_reviewer_id VARCHAR(100),
    p_reviewer_name VARCHAR(200) DEFAULT 'Anonymous',
    p_title VARCHAR(200) DEFAULT '',
    p_review_text TEXT DEFAULT '',
    p_template_version VARCHAR(20) DEFAULT NULL,
    p_verified_use BOOLEAN DEFAULT FALSE
)
RETURNS BIGINT AS $$
DECLARE
    v_review_id BIGINT;
    v_new_avg NUMERIC(3,2);
    v_new_count INTEGER;
BEGIN
    -- Validate rating
    IF p_rating < 1 OR p_rating > 5 THEN
        RAISE EXCEPTION 'Rating must be between 1 and 5';
    END IF;

    -- Insert or update review
    INSERT INTO template_reviews (
        template_id, rating, reviewer_id, reviewer_name, title, review_text,
        template_version, verified_use
    ) VALUES (
        p_template_id, p_rating, p_reviewer_id, p_reviewer_name, p_title, p_review_text,
        p_template_version, p_verified_use
    )
    ON CONFLICT (template_id, reviewer_id) DO UPDATE SET
        rating = p_rating,
        title = p_title,
        review_text = p_review_text,
        template_version = p_template_version,
        verified_use = p_verified_use,
        updated_at = NOW()
    RETURNING id INTO v_review_id;

    -- Recalculate average rating
    SELECT AVG(rating), COUNT(*)
    INTO v_new_avg, v_new_count
    FROM template_reviews
    WHERE template_id = p_template_id AND status = 'published';

    -- Update template statistics
    UPDATE workflow_templates
    SET
        average_rating = v_new_avg,
        rating_count = v_new_count
    WHERE id = p_template_id;

    RETURN v_review_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION submit_template_review IS 'Submit or update a template review';

-- Function to mark review as helpful/not helpful
CREATE OR REPLACE FUNCTION mark_review_helpful(
    p_review_id BIGINT,
    p_helpful BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    IF p_helpful THEN
        UPDATE template_reviews
        SET helpful_count = helpful_count + 1
        WHERE id = p_review_id;
    ELSE
        UPDATE template_reviews
        SET not_helpful_count = not_helpful_count + 1
        WHERE id = p_review_id;
    END IF;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION mark_review_helpful IS 'Mark a review as helpful or not helpful';

-- Function to publish a new template version
CREATE OR REPLACE FUNCTION publish_template_version(
    p_template_id VARCHAR(50),
    p_version VARCHAR(20),
    p_change_summary TEXT,
    p_breaking_changes BOOLEAN,
    p_workflow_definition JSONB,
    p_parameters JSONB,
    p_published_by VARCHAR(100) DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_version_id BIGINT;
    v_version_number INTEGER;
BEGIN
    -- Get next version number
    SELECT COALESCE(MAX(version_number), 0) + 1
    INTO v_version_number
    FROM template_versions
    WHERE template_id = p_template_id;

    -- Insert new version
    INSERT INTO template_versions (
        template_id, version, version_number, change_summary, breaking_changes,
        workflow_definition, parameters, status, published_at, published_by
    ) VALUES (
        p_template_id, p_version, v_version_number, p_change_summary, p_breaking_changes,
        p_workflow_definition, p_parameters, 'published', NOW(), p_published_by
    )
    RETURNING id INTO v_version_id;

    -- Update template's current version
    UPDATE workflow_templates
    SET
        version = p_version,
        workflow_definition = p_workflow_definition,
        parameters = p_parameters,
        modified_at = NOW()
    WHERE id = p_template_id;

    RETURN v_version_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

COMMENT ON FUNCTION publish_template_version IS 'Publish a new version of a template';

-- Function to get template with all related data
CREATE OR REPLACE FUNCTION get_template_full(p_template_id VARCHAR(50))
RETURNS TABLE (
    template_data JSONB,
    review_summary JSONB,
    version_history JSONB,
    collections JSONB,
    dependencies JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        -- Template data
        to_jsonb(t.*) as template_data,

        -- Review summary
        COALESCE(
            (SELECT jsonb_build_object(
                'total_reviews', COUNT(*),
                'avg_rating', AVG(rating)::NUMERIC(3,2),
                'rating_distribution', jsonb_build_object(
                    '5', COUNT(*) FILTER (WHERE rating = 5),
                    '4', COUNT(*) FILTER (WHERE rating = 4),
                    '3', COUNT(*) FILTER (WHERE rating = 3),
                    '2', COUNT(*) FILTER (WHERE rating = 2),
                    '1', COUNT(*) FILTER (WHERE rating = 1)
                )
            )
            FROM template_reviews
            WHERE template_id = p_template_id AND status = 'published'),
            '{}'::jsonb
        ) as review_summary,

        -- Version history
        COALESCE(
            (SELECT jsonb_agg(jsonb_build_object(
                'version', tv.version,
                'change_summary', tv.change_summary,
                'breaking_changes', tv.breaking_changes,
                'published_at', tv.published_at,
                'status', tv.status
            ) ORDER BY tv.version_number DESC)
            FROM template_versions tv
            WHERE tv.template_id = p_template_id),
            '[]'::jsonb
        ) as version_history,

        -- Collections
        COALESCE(
            (SELECT jsonb_agg(jsonb_build_object(
                'id', c.id,
                'name', c.name,
                'type', c.collection_type
            ))
            FROM template_collections c
            JOIN template_collection_items ci ON c.id = ci.collection_id
            WHERE ci.template_id = p_template_id),
            '[]'::jsonb
        ) as collections,

        -- Dependencies
        COALESCE(
            (SELECT jsonb_agg(jsonb_build_object(
                'depends_on_id', d.depends_on_id,
                'dependency_type', d.dependency_type,
                'version_constraint', d.version_constraint,
                'reason', d.reason
            ))
            FROM template_dependencies d
            WHERE d.template_id = p_template_id),
            '[]'::jsonb
        ) as dependencies
    FROM workflow_templates t
    WHERE t.id = p_template_id;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_template_full IS 'Get complete template data with reviews, versions, collections, and dependencies';

-- ============================================================================
-- Triggers
-- ============================================================================

-- Update timestamp trigger for reviews
CREATE OR REPLACE FUNCTION update_review_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_review_updated ON template_reviews;
CREATE TRIGGER trigger_review_updated
    BEFORE UPDATE ON template_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_review_timestamp();

-- Update timestamp trigger for collections
DROP TRIGGER IF EXISTS trigger_collection_updated ON template_collections;
CREATE TRIGGER trigger_collection_updated
    BEFORE UPDATE ON template_collections
    FOR EACH ROW
    EXECUTE FUNCTION update_review_timestamp();

-- ============================================================================
-- Initial Data: Featured Collections
-- ============================================================================

INSERT INTO template_collections (id, name, description, icon, collection_type, display_order)
VALUES
    ('col_featured', 'Featured Templates', 'Hand-picked templates to get you started', 'star', 'featured', 1),
    ('col_beginner', 'Beginner Friendly', 'Simple templates for those new to RPA', 'graduation-cap', 'curated', 2),
    ('col_web', 'Web Automation', 'Templates for web scraping and browser automation', 'globe', 'category', 3),
    ('col_data', 'Data Processing', 'Templates for ETL, data transformation, and reporting', 'database', 'category', 4),
    ('col_office', 'Office Automation', 'Templates for Excel, PDF, and document processing', 'file-text', 'category', 5)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- DOWN MIGRATION
-- ============================================================================

-- To rollback this migration, run:
-- DROP FUNCTION IF EXISTS get_template_full CASCADE;
-- DROP FUNCTION IF EXISTS publish_template_version CASCADE;
-- DROP FUNCTION IF EXISTS mark_review_helpful CASCADE;
-- DROP FUNCTION IF EXISTS submit_template_review CASCADE;
-- DROP FUNCTION IF EXISTS log_template_usage CASCADE;
-- DROP VIEW IF EXISTS template_review_summary CASCADE;
-- DROP VIEW IF EXISTS template_popularity CASCADE;
-- DROP TABLE IF EXISTS template_dependencies CASCADE;
-- DROP TABLE IF EXISTS template_collection_items CASCADE;
-- DROP TABLE IF EXISTS template_collections CASCADE;
-- DROP TABLE IF EXISTS template_usage_log CASCADE;
-- DROP TABLE IF EXISTS template_reviews CASCADE;
-- DROP TABLE IF EXISTS template_versions CASCADE;
