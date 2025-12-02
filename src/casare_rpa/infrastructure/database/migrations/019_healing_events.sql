-- Migration 019: Self-Healing Events Table
-- Creates table for tracking self-healing selector telemetry
--
-- Stores events from the healing chain (heuristic, anchor, CV tiers)
-- to enable analytics on selector stability and healing effectiveness.

-- =========================
-- Healing Events Table
-- =========================
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

    -- Workflow context (optional)
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

-- =========================
-- Indexes
-- =========================

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


-- =========================
-- Selector Statistics Materialized View
-- =========================
-- Provides pre-aggregated statistics for faster dashboard queries
-- Should be refreshed periodically (e.g., every 5 minutes)

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
    -- Tier breakdown as JSON
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


-- =========================
-- Daily Aggregates Table
-- =========================
-- For historical trend analysis

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

-- Index for date range queries
CREATE INDEX IF NOT EXISTS idx_healing_daily_stats_date
    ON healing_daily_stats (date DESC);


-- =========================
-- Function: Aggregate Daily Stats
-- =========================
-- Called by a scheduled job to populate daily statistics

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


-- =========================
-- Function: Insert Healing Event
-- =========================
-- Helper function for inserting events with automatic statistics update

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
        selector,
        page_url,
        success,
        tier_used,
        healing_time_ms,
        healed_selector,
        confidence,
        tiers_attempted,
        error_message,
        workflow_id,
        job_id,
        node_id,
        robot_id
    )
    VALUES (
        p_selector,
        p_page_url,
        p_success,
        p_tier_used,
        p_healing_time_ms,
        p_healed_selector,
        p_confidence,
        p_tiers_attempted,
        p_error_message,
        p_workflow_id,
        p_job_id,
        p_node_id,
        p_robot_id
    )
    RETURNING id INTO event_id;

    RETURN event_id;
END;
$$ LANGUAGE plpgsql;


-- =========================
-- Cleanup: Retention Policy
-- =========================
-- Function to clean up old events (call periodically)

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


-- =========================
-- Comments
-- =========================

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
