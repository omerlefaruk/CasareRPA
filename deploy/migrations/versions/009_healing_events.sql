-- Migration: 009_healing_events
-- Description: Self-healing selector telemetry for UI element reliability tracking
-- Consolidated from:
--   - src/casare_rpa/infrastructure/database/migrations/019_healing_events.sql
-- Created: 2024-12-03

-- =============================================================================
-- HEALING EVENTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS healing_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event identification
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Selector information
    selector TEXT NOT NULL,
    healed_selector TEXT,
    page_url TEXT NOT NULL,

    -- Outcome
    success BOOLEAN NOT NULL,
    tier_used VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 1.0,

    -- Performance
    healing_time_ms FLOAT NOT NULL DEFAULT 0.0,

    -- Context
    tiers_attempted TEXT[] DEFAULT '{}',
    error_message TEXT,

    -- Workflow context
    workflow_id UUID,
    job_id UUID,
    node_id VARCHAR(255),
    robot_id VARCHAR(255),

    -- Constraints
    CONSTRAINT valid_tier CHECK (tier_used IN (
        'original', 'heuristic', 'anchor', 'cv', 'failed'
    )),
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Time-based queries (analytics dashboards)
CREATE INDEX IF NOT EXISTS idx_healing_events_timestamp
    ON healing_events (timestamp DESC);

-- Selector-based lookups (finding problematic selectors)
CREATE INDEX IF NOT EXISTS idx_healing_events_selector
    ON healing_events (selector);

-- Success rate analysis
CREATE INDEX IF NOT EXISTS idx_healing_events_success
    ON healing_events (success, timestamp);

-- Tier analysis
CREATE INDEX IF NOT EXISTS idx_healing_events_tier
    ON healing_events (tier_used, success);

-- Workflow correlation
CREATE INDEX IF NOT EXISTS idx_healing_events_workflow
    ON healing_events (workflow_id)
    WHERE workflow_id IS NOT NULL;

-- Robot-specific analysis
CREATE INDEX IF NOT EXISTS idx_healing_events_robot
    ON healing_events (robot_id)
    WHERE robot_id IS NOT NULL;

-- Compound index for analytics queries
CREATE INDEX IF NOT EXISTS idx_healing_events_analytics
    ON healing_events (timestamp, selector, tier_used, success);

-- =============================================================================
-- SELECTOR STATISTICS MATERIALIZED VIEW
-- =============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS selector_healing_stats AS
SELECT
    selector,
    COUNT(*) as total_uses,
    COUNT(*) FILTER (WHERE tier_used = 'original') as original_successes,
    COUNT(*) FILTER (WHERE success = true AND tier_used != 'original') as healed_successes,
    COUNT(*) FILTER (WHERE success = false) as failures,
    ROUND(
        COUNT(*) FILTER (WHERE success = true) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) as success_rate,
    ROUND(
        AVG(healing_time_ms) FILTER (WHERE tier_used != 'original'),
        2
    ) as avg_healing_time_ms,
    MAX(timestamp) as last_used,
    jsonb_build_object(
        'original', COUNT(*) FILTER (WHERE tier_used = 'original'),
        'heuristic', COUNT(*) FILTER (WHERE tier_used = 'heuristic'),
        'anchor', COUNT(*) FILTER (WHERE tier_used = 'anchor'),
        'cv', COUNT(*) FILTER (WHERE tier_used = 'cv'),
        'failed', COUNT(*) FILTER (WHERE tier_used = 'failed')
    ) as tier_breakdown
FROM healing_events
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY selector
HAVING COUNT(*) >= 3;

-- Index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_selector_healing_stats_selector
    ON selector_healing_stats (selector);

CREATE INDEX IF NOT EXISTS idx_selector_healing_stats_success_rate
    ON selector_healing_stats (success_rate);

-- =============================================================================
-- DAILY AGGREGATES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS healing_daily_stats (
    date DATE PRIMARY KEY,
    total_attempts INTEGER NOT NULL DEFAULT 0,
    original_successes INTEGER NOT NULL DEFAULT 0,
    healed_successes INTEGER NOT NULL DEFAULT 0,
    failures INTEGER NOT NULL DEFAULT 0,
    avg_healing_time_ms FLOAT DEFAULT 0.0,
    tier_breakdown JSONB DEFAULT '{}',
    unique_selectors INTEGER DEFAULT 0,
    problematic_selectors INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_healing_daily_stats_date
    ON healing_daily_stats (date DESC);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to aggregate daily stats
CREATE OR REPLACE FUNCTION aggregate_healing_daily_stats(target_date DATE)
RETURNS void AS $$
BEGIN
    INSERT INTO healing_daily_stats (
        date,
        total_attempts,
        original_successes,
        healed_successes,
        failures,
        avg_healing_time_ms,
        tier_breakdown,
        unique_selectors,
        problematic_selectors
    )
    SELECT
        target_date,
        COUNT(*),
        COUNT(*) FILTER (WHERE tier_used = 'original'),
        COUNT(*) FILTER (WHERE success = true AND tier_used != 'original'),
        COUNT(*) FILTER (WHERE success = false),
        COALESCE(AVG(healing_time_ms) FILTER (WHERE tier_used != 'original'), 0.0),
        jsonb_build_object(
            'original', COUNT(*) FILTER (WHERE tier_used = 'original'),
            'heuristic', COUNT(*) FILTER (WHERE tier_used = 'heuristic'),
            'anchor', COUNT(*) FILTER (WHERE tier_used = 'anchor'),
            'cv', COUNT(*) FILTER (WHERE tier_used = 'cv'),
            'failed', COUNT(*) FILTER (WHERE tier_used = 'failed')
        ),
        COUNT(DISTINCT selector),
        COUNT(DISTINCT selector) FILTER (
            WHERE success = false OR tier_used NOT IN ('original', 'heuristic')
        )
    FROM healing_events
    WHERE timestamp::date = target_date
    ON CONFLICT (date) DO UPDATE SET
        total_attempts = EXCLUDED.total_attempts,
        original_successes = EXCLUDED.original_successes,
        healed_successes = EXCLUDED.healed_successes,
        failures = EXCLUDED.failures,
        avg_healing_time_ms = EXCLUDED.avg_healing_time_ms,
        tier_breakdown = EXCLUDED.tier_breakdown,
        unique_selectors = EXCLUDED.unique_selectors,
        problematic_selectors = EXCLUDED.problematic_selectors;
END;
$$ LANGUAGE plpgsql;

-- Function to insert healing event
CREATE OR REPLACE FUNCTION insert_healing_event(
    p_selector TEXT,
    p_page_url TEXT,
    p_success BOOLEAN,
    p_tier_used VARCHAR(50),
    p_healing_time_ms FLOAT,
    p_healed_selector TEXT DEFAULT NULL,
    p_confidence FLOAT DEFAULT 1.0,
    p_tiers_attempted TEXT[] DEFAULT '{}',
    p_error_message TEXT DEFAULT NULL,
    p_workflow_id UUID DEFAULT NULL,
    p_job_id UUID DEFAULT NULL,
    p_node_id VARCHAR(255) DEFAULT NULL,
    p_robot_id VARCHAR(255) DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO healing_events (
        selector, page_url, success, tier_used, healing_time_ms,
        healed_selector, confidence, tiers_attempted, error_message,
        workflow_id, job_id, node_id, robot_id
    )
    VALUES (
        p_selector, p_page_url, p_success, p_tier_used, p_healing_time_ms,
        p_healed_selector, p_confidence, p_tiers_attempted, p_error_message,
        p_workflow_id, p_job_id, p_node_id, p_robot_id
    )
    RETURNING id INTO event_id;

    RETURN event_id;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old events
CREATE OR REPLACE FUNCTION cleanup_old_healing_events(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM healing_events
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View for problematic selectors
CREATE OR REPLACE VIEW healing_problematic_selectors AS
SELECT
    selector,
    COUNT(*) AS total_attempts,
    COUNT(*) FILTER (WHERE success = false) AS failure_count,
    ROUND(COUNT(*) FILTER (WHERE success = false) * 100.0 / COUNT(*), 2) AS failure_rate,
    MAX(timestamp) AS last_failure,
    array_agg(DISTINCT tier_used) AS tiers_used,
    array_agg(DISTINCT page_url) AS affected_pages
FROM healing_events
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY selector
HAVING COUNT(*) FILTER (WHERE success = false) > 0
ORDER BY failure_rate DESC, failure_count DESC
LIMIT 100;

-- View for healing performance by tier
CREATE OR REPLACE VIEW healing_tier_performance AS
SELECT
    tier_used,
    COUNT(*) AS total_attempts,
    COUNT(*) FILTER (WHERE success = true) AS successful,
    ROUND(AVG(healing_time_ms), 2) AS avg_time_ms,
    ROUND(AVG(confidence) FILTER (WHERE success = true), 3) AS avg_confidence,
    MIN(timestamp) AS first_seen,
    MAX(timestamp) AS last_seen
FROM healing_events
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY tier_used
ORDER BY tier_used;

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE healing_events IS
    'Self-healing selector telemetry events for tracking UI element reliability';
COMMENT ON COLUMN healing_events.tier_used IS
    'Healing tier that succeeded: original (no healing needed), heuristic, anchor, cv, failed';
COMMENT ON COLUMN healing_events.healing_time_ms IS
    'Time spent attempting to heal the selector in milliseconds';
COMMENT ON COLUMN healing_events.confidence IS
    'Confidence score of the healed selector (0.0-1.0)';
COMMENT ON MATERIALIZED VIEW selector_healing_stats IS
    'Pre-aggregated selector statistics. Refresh with: REFRESH MATERIALIZED VIEW CONCURRENTLY selector_healing_stats;';
COMMENT ON FUNCTION aggregate_healing_daily_stats IS
    'Aggregates healing events into daily statistics. Call daily via scheduler.';
COMMENT ON FUNCTION insert_healing_event IS
    'Helper function to insert a healing event with proper validation.';
COMMENT ON FUNCTION cleanup_old_healing_events IS
    'Removes healing events older than retention period. Default: 90 days.';
