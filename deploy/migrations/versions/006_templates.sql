-- Migration: 006_templates
-- Description: Workflow templates with versioning, reviews, and marketplace support
-- Consolidated from:
--   - src/casare_rpa/infrastructure/database/migrations/014_workflow_templates.sql
--   - src/casare_rpa/infrastructure/database/migrations/017_workflow_templates.sql
-- Created: 2024-12-03

-- =============================================================================
-- WORKFLOW TEMPLATES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS workflow_templates (
    id VARCHAR(50) PRIMARY KEY,

    -- Metadata
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category VARCHAR(50) NOT NULL DEFAULT 'general'
        CHECK (category IN (
            'web_scraping', 'data_entry', 'report_generation', 'api_integration',
            'file_operations', 'email_processing', 'database_operations',
            'desktop_automation', 'pdf_processing', 'excel_automation',
            'general', 'custom'
        )),
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    author VARCHAR(255) NOT NULL DEFAULT '',
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'intermediate'
        CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    estimated_duration VARCHAR(100),
    requirements JSONB NOT NULL DEFAULT '[]'::jsonb,
    icon VARCHAR(100) NOT NULL DEFAULT '',
    preview_image VARCHAR(500) NOT NULL DEFAULT '',

    -- Template Definition
    parameters JSONB NOT NULL DEFAULT '[]'::jsonb,
    workflow_definition JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Source
    is_builtin BOOLEAN NOT NULL DEFAULT FALSE,
    source VARCHAR(50) NOT NULL DEFAULT 'user',
    marketplace_id VARCHAR(100),

    -- Statistics
    total_uses INTEGER NOT NULL DEFAULT 0 CHECK (total_uses >= 0),
    successful_instantiations INTEGER NOT NULL DEFAULT 0 CHECK (successful_instantiations >= 0),
    failed_instantiations INTEGER NOT NULL DEFAULT 0 CHECK (failed_instantiations >= 0),
    last_used_at TIMESTAMPTZ,
    average_rating NUMERIC(3, 2) CHECK (average_rating IS NULL OR (average_rating >= 1 AND average_rating <= 5)),
    rating_count INTEGER NOT NULL DEFAULT 0 CHECK (rating_count >= 0),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_templates_category ON workflow_templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_name ON workflow_templates(name);
CREATE INDEX IF NOT EXISTS idx_templates_builtin ON workflow_templates(is_builtin);
CREATE INDEX IF NOT EXISTS idx_templates_source ON workflow_templates(source);
CREATE INDEX IF NOT EXISTS idx_templates_tags ON workflow_templates USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_templates_uses ON workflow_templates(total_uses DESC);
CREATE INDEX IF NOT EXISTS idx_templates_rating ON workflow_templates(average_rating DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_templates_created ON workflow_templates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_templates_fulltext ON workflow_templates
    USING GIN (to_tsvector('english', name || ' ' || description));

-- =============================================================================
-- TEMPLATE VERSIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS template_versions (
    id BIGSERIAL PRIMARY KEY,
    template_id VARCHAR(50) NOT NULL REFERENCES workflow_templates(id) ON DELETE CASCADE,

    version VARCHAR(20) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    change_summary TEXT NOT NULL DEFAULT '',
    breaking_changes BOOLEAN NOT NULL DEFAULT FALSE,

    workflow_definition JSONB NOT NULL,
    parameters JSONB NOT NULL DEFAULT '[]'::jsonb,

    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'published', 'deprecated', 'archived')),
    published_at TIMESTAMPTZ,
    published_by VARCHAR(100),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (template_id, version)
);

CREATE INDEX IF NOT EXISTS idx_template_versions_template ON template_versions(template_id);
CREATE INDEX IF NOT EXISTS idx_template_versions_status ON template_versions(status);
CREATE INDEX IF NOT EXISTS idx_template_versions_published ON template_versions(published_at DESC);

-- =============================================================================
-- TEMPLATE REVIEWS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS template_reviews (
    id BIGSERIAL PRIMARY KEY,
    template_id VARCHAR(50) NOT NULL REFERENCES workflow_templates(id) ON DELETE CASCADE,

    rating SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200) NOT NULL DEFAULT '',
    review_text TEXT NOT NULL DEFAULT '',

    reviewer_id VARCHAR(100),
    reviewer_name VARCHAR(200) NOT NULL DEFAULT 'Anonymous',

    verified_use BOOLEAN NOT NULL DEFAULT FALSE,
    template_version VARCHAR(20),

    helpful_count INTEGER NOT NULL DEFAULT 0 CHECK (helpful_count >= 0),
    not_helpful_count INTEGER NOT NULL DEFAULT 0 CHECK (not_helpful_count >= 0),

    status VARCHAR(20) NOT NULL DEFAULT 'published'
        CHECK (status IN ('pending', 'published', 'hidden', 'removed')),
    moderated_at TIMESTAMPTZ,
    moderated_by VARCHAR(100),
    moderation_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (template_id, reviewer_id)
);

CREATE INDEX IF NOT EXISTS idx_template_reviews_template ON template_reviews(template_id);
CREATE INDEX IF NOT EXISTS idx_template_reviews_rating ON template_reviews(rating);
CREATE INDEX IF NOT EXISTS idx_template_reviews_status ON template_reviews(status);
CREATE INDEX IF NOT EXISTS idx_template_reviews_created ON template_reviews(created_at DESC);

-- =============================================================================
-- TEMPLATE USAGE LOG
-- =============================================================================
CREATE TABLE IF NOT EXISTS template_usage_log (
    id BIGSERIAL PRIMARY KEY,
    template_id VARCHAR(50) NOT NULL,
    template_version VARCHAR(20),

    action VARCHAR(50) NOT NULL
        CHECK (action IN ('view', 'instantiate', 'download', 'clone', 'rate', 'review')),

    user_id VARCHAR(100),
    session_id VARCHAR(100),
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    source VARCHAR(50),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_log_template ON template_usage_log(template_id);
CREATE INDEX IF NOT EXISTS idx_usage_log_action ON template_usage_log(action);
CREATE INDEX IF NOT EXISTS idx_usage_log_created ON template_usage_log(created_at DESC);

-- =============================================================================
-- TEMPLATE COLLECTIONS
-- =============================================================================
CREATE TABLE IF NOT EXISTS template_collections (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    icon VARCHAR(100) NOT NULL DEFAULT '',

    collection_type VARCHAR(50) NOT NULL DEFAULT 'custom'
        CHECK (collection_type IN ('featured', 'category', 'curated', 'custom', 'user')),

    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    owner_id VARCHAR(100),
    display_order INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collections_type ON template_collections(collection_type);
CREATE INDEX IF NOT EXISTS idx_collections_public ON template_collections(is_public);

CREATE TABLE IF NOT EXISTS template_collection_items (
    id BIGSERIAL PRIMARY KEY,
    collection_id VARCHAR(50) NOT NULL REFERENCES template_collections(id) ON DELETE CASCADE,
    template_id VARCHAR(50) NOT NULL,

    display_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (collection_id, template_id)
);

CREATE INDEX IF NOT EXISTS idx_collection_items_collection ON template_collection_items(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_items_template ON template_collection_items(template_id);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to record template usage
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

-- Function to submit a review
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
    IF p_rating < 1 OR p_rating > 5 THEN
        RAISE EXCEPTION 'Rating must be between 1 and 5';
    END IF;

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

    SELECT AVG(rating), COUNT(*)
    INTO v_new_avg, v_new_count
    FROM template_reviews
    WHERE template_id = p_template_id AND status = 'published';

    UPDATE workflow_templates
    SET
        average_rating = v_new_avg,
        rating_count = v_new_count
    WHERE id = p_template_id;

    RETURN v_review_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- Function to search templates
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

-- =============================================================================
-- VIEWS
-- =============================================================================

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

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger for template modified_at
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

-- =============================================================================
-- INITIAL DATA
-- =============================================================================
INSERT INTO template_collections (id, name, description, icon, collection_type, display_order)
VALUES
    ('col_featured', 'Featured Templates', 'Hand-picked templates to get you started', 'star', 'featured', 1),
    ('col_beginner', 'Beginner Friendly', 'Simple templates for those new to RPA', 'graduation-cap', 'curated', 2),
    ('col_web', 'Web Automation', 'Templates for web scraping and browser automation', 'globe', 'category', 3),
    ('col_data', 'Data Processing', 'Templates for ETL, data transformation', 'database', 'category', 4),
    ('col_office', 'Office Automation', 'Templates for Excel, PDF, documents', 'file-text', 'category', 5)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE workflow_templates IS 'Workflow templates for rapid workflow creation';
COMMENT ON TABLE template_versions IS 'Version history for workflow templates';
COMMENT ON TABLE template_reviews IS 'User reviews and ratings for templates';
COMMENT ON TABLE template_usage_log IS 'Detailed usage log for template analytics';
COMMENT ON TABLE template_collections IS 'Collections for grouping templates';
COMMENT ON FUNCTION search_templates IS 'Search templates with full-text search';
