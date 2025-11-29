-- Migration: 015_schedule_enhancements
-- Description: Advanced scheduling features - business calendars, SLA, dependencies, rate limits
-- Created: 2024-11-28

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Business Calendars Table
-- Stores calendar configurations for business hours, holidays, and blackouts
CREATE TABLE IF NOT EXISTS business_calendars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    timezone TEXT NOT NULL DEFAULT 'UTC',

    -- Working hours configuration (JSON structure per day of week)
    -- Example: {"MONDAY": {"start": "09:00", "end": "17:00", "enabled": true}, ...}
    working_hours JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Flags for flexibility
    allow_weekends BOOLEAN NOT NULL DEFAULT FALSE,
    allow_outside_hours BOOLEAN NOT NULL DEFAULT FALSE,

    -- Holidays (array of holiday definitions)
    -- Example: [{"name": "New Year", "type": "fixed", "month": 1, "day": 1}, ...]
    holidays JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Custom non-working dates (array of ISO date strings)
    custom_dates JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Organization/tenant isolation
    organization_id UUID,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    updated_at TIMESTAMPTZ,
    updated_by TEXT,

    CONSTRAINT calendars_name_org_unique UNIQUE (name, organization_id)
);

-- Index for calendar lookups by organization
CREATE INDEX IF NOT EXISTS idx_calendars_org ON business_calendars(organization_id);

-- Index for timezone-based queries
CREATE INDEX IF NOT EXISTS idx_calendars_timezone ON business_calendars(timezone);

COMMENT ON TABLE business_calendars IS 'Business calendar configurations for scheduling';


-- Blackout Periods Table
-- Stores scheduled maintenance windows and scheduling blackouts
CREATE TABLE IF NOT EXISTS blackout_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_id UUID REFERENCES business_calendars(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    reason TEXT DEFAULT '',

    -- Period boundaries (timezone-aware)
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,

    -- Recurrence
    recurring BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_pattern TEXT, -- 'yearly', 'monthly', 'weekly', or cron expression

    -- Scope - which workflows are affected (empty array = all)
    affected_workflows TEXT[] DEFAULT '{}',

    -- Status
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,

    CONSTRAINT blackout_time_check CHECK (end_time > start_time)
);

-- Index for finding active blackouts
CREATE INDEX IF NOT EXISTS idx_blackouts_active ON blackout_periods(start_time, end_time)
    WHERE enabled = TRUE;

-- Index for calendar lookups
CREATE INDEX IF NOT EXISTS idx_blackouts_calendar ON blackout_periods(calendar_id);

COMMENT ON TABLE blackout_periods IS 'Scheduled blackout periods when scheduling is blocked';


-- Advanced Schedules Table
-- Extends base schedules with enterprise features
CREATE TABLE IF NOT EXISTS advanced_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic identification
    name TEXT NOT NULL,
    description TEXT DEFAULT '',

    -- Workflow reference
    workflow_id UUID NOT NULL,
    workflow_name TEXT NOT NULL DEFAULT '',

    -- Schedule type and expression
    schedule_type TEXT NOT NULL DEFAULT 'cron',
    -- Type values: 'cron', 'interval', 'event', 'dependency', 'one_time'

    cron_expression TEXT,
    interval_seconds INTEGER DEFAULT 0,
    run_at TIMESTAMPTZ, -- For one-time schedules

    -- Timezone handling
    timezone TEXT NOT NULL DEFAULT 'UTC',

    -- Business calendar integration
    calendar_id UUID REFERENCES business_calendars(id) ON DELETE SET NULL,
    respect_business_hours BOOLEAN NOT NULL DEFAULT FALSE,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'active',
    -- Status values: 'active', 'paused', 'disabled', 'completed', 'error'
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Execution assignment
    priority INTEGER NOT NULL DEFAULT 1 CHECK (priority >= 0 AND priority <= 3),
    robot_id UUID, -- Specific robot assignment (NULL = any available)
    environment TEXT DEFAULT 'default',

    -- Variables to pass to workflow
    variables JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Tags for categorization
    tags TEXT[] DEFAULT '{}',

    -- Additional metadata
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Execution statistics
    last_run TIMESTAMPTZ,
    next_run TIMESTAMPTZ,
    run_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,

    -- Organization/tenant isolation
    organization_id UUID,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    updated_at TIMESTAMPTZ,
    updated_by TEXT
);

-- Index for schedule type queries
CREATE INDEX IF NOT EXISTS idx_schedules_type ON advanced_schedules(schedule_type);

-- Index for active schedules
CREATE INDEX IF NOT EXISTS idx_schedules_active ON advanced_schedules(status, enabled)
    WHERE enabled = TRUE AND status = 'active';

-- Index for next run calculations
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON advanced_schedules(next_run)
    WHERE enabled = TRUE AND next_run IS NOT NULL;

-- Index for workflow lookups
CREATE INDEX IF NOT EXISTS idx_schedules_workflow ON advanced_schedules(workflow_id);

-- Index for organization queries
CREATE INDEX IF NOT EXISTS idx_schedules_org ON advanced_schedules(organization_id);

-- Index for tags (GIN for array contains queries)
CREATE INDEX IF NOT EXISTS idx_schedules_tags ON advanced_schedules USING GIN(tags);

-- Index for priority-based ordering
CREATE INDEX IF NOT EXISTS idx_schedules_priority ON advanced_schedules(priority DESC, next_run);

COMMENT ON TABLE advanced_schedules IS 'Advanced workflow schedules with enterprise features';


-- SLA Configurations Table
-- Stores SLA rules for schedules
CREATE TABLE IF NOT EXISTS schedule_sla_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- Duration limits (in seconds)
    max_duration_seconds INTEGER,
    max_start_delay_seconds INTEGER DEFAULT 300,

    -- Success rate thresholds (percentage 0-100)
    success_rate_threshold NUMERIC(5,2) NOT NULL DEFAULT 95.00,

    -- Failure tolerance
    consecutive_failure_limit INTEGER NOT NULL DEFAULT 3,

    -- Alert configuration (JSON with notification settings)
    alert_config JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Current SLA status
    current_status TEXT NOT NULL DEFAULT 'ok',
    -- Status values: 'ok', 'warning', 'breached', 'unknown'
    last_status_change TIMESTAMPTZ,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    CONSTRAINT sla_schedule_unique UNIQUE (schedule_id)
);

-- Index for SLA status queries
CREATE INDEX IF NOT EXISTS idx_sla_status ON schedule_sla_configs(current_status)
    WHERE current_status IN ('warning', 'breached');

COMMENT ON TABLE schedule_sla_configs IS 'SLA configurations for schedule monitoring';


-- Rate Limit Configurations Table
-- Stores sliding window rate limits for schedules
CREATE TABLE IF NOT EXISTS schedule_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- Rate limit parameters
    max_executions INTEGER NOT NULL DEFAULT 10,
    window_seconds INTEGER NOT NULL DEFAULT 3600,

    -- Overflow behavior
    queue_overflow BOOLEAN NOT NULL DEFAULT TRUE,

    -- Current window tracking
    current_window_start TIMESTAMPTZ,
    current_execution_count INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT rate_limit_schedule_unique UNIQUE (schedule_id),
    CONSTRAINT rate_limit_max_check CHECK (max_executions > 0),
    CONSTRAINT rate_limit_window_check CHECK (window_seconds > 0)
);

COMMENT ON TABLE schedule_rate_limits IS 'Sliding window rate limits for schedules';


-- Schedule Dependencies Table
-- Stores DAG dependencies between schedules
CREATE TABLE IF NOT EXISTS schedule_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The dependent schedule (child)
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- The dependency (parent that must complete first)
    depends_on_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- Dependency configuration
    wait_for_all BOOLEAN NOT NULL DEFAULT TRUE, -- Wait for all deps or just this one
    require_success BOOLEAN NOT NULL DEFAULT TRUE, -- Only trigger on successful completion
    timeout_seconds INTEGER NOT NULL DEFAULT 3600,

    -- Priority order if multiple dependencies
    priority_order INTEGER NOT NULL DEFAULT 0,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT deps_no_self_reference CHECK (schedule_id != depends_on_id),
    CONSTRAINT deps_unique UNIQUE (schedule_id, depends_on_id)
);

-- Index for finding dependencies of a schedule
CREATE INDEX IF NOT EXISTS idx_deps_schedule ON schedule_dependencies(schedule_id);

-- Index for finding dependents of a schedule
CREATE INDEX IF NOT EXISTS idx_deps_depends_on ON schedule_dependencies(depends_on_id);

COMMENT ON TABLE schedule_dependencies IS 'DAG dependencies between schedules';


-- Conditional Execution Configs Table
-- Stores conditional execution rules
CREATE TABLE IF NOT EXISTS schedule_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- Condition expression (evaluated at runtime)
    condition_expression TEXT,

    -- Condition type for built-in checks
    condition_type TEXT, -- 'sql_query', 'http_check', 'file_exists', 'custom'

    -- Condition parameters (JSON based on type)
    condition_params JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Retry behavior
    retry_on_fail BOOLEAN NOT NULL DEFAULT FALSE,
    retry_interval_seconds INTEGER NOT NULL DEFAULT 60,
    max_retries INTEGER NOT NULL DEFAULT 5,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    CONSTRAINT conditions_schedule_unique UNIQUE (schedule_id)
);

COMMENT ON TABLE schedule_conditions IS 'Conditional execution rules for schedules';


-- Catch-up Configurations Table
-- Stores catch-up behavior for missed runs
CREATE TABLE IF NOT EXISTS schedule_catchup_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- Catch-up enabled
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Limits
    max_catchup_runs INTEGER NOT NULL DEFAULT 5,
    catchup_window_hours INTEGER NOT NULL DEFAULT 24,

    -- Execution behavior
    run_sequentially BOOLEAN NOT NULL DEFAULT TRUE,

    -- Tracking
    last_catchup_at TIMESTAMPTZ,
    catchup_runs_executed INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT catchup_schedule_unique UNIQUE (schedule_id),
    CONSTRAINT catchup_max_check CHECK (max_catchup_runs > 0),
    CONSTRAINT catchup_window_check CHECK (catchup_window_hours > 0)
);

COMMENT ON TABLE schedule_catchup_configs IS 'Catch-up configurations for missed schedule runs';


-- Event Triggers Table
-- Stores event-driven trigger configurations
CREATE TABLE IF NOT EXISTS schedule_event_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- Event definition
    event_type TEXT NOT NULL,
    -- Types: 'file_arrival', 'webhook', 'database_change', 'queue_message', 'workflow_completed', 'custom'

    event_source TEXT NOT NULL, -- Path, endpoint, table name, etc.

    -- Event filtering (JSON query spec)
    event_filter JSONB,

    -- Debouncing
    debounce_seconds INTEGER NOT NULL DEFAULT 0,
    last_triggered_at TIMESTAMPTZ,

    -- Batching
    batch_events BOOLEAN NOT NULL DEFAULT FALSE,
    batch_window_seconds INTEGER NOT NULL DEFAULT 60,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    CONSTRAINT event_schedule_unique UNIQUE (schedule_id)
);

-- Index for event type lookups
CREATE INDEX IF NOT EXISTS idx_event_triggers_type ON schedule_event_triggers(event_type, event_source);

COMMENT ON TABLE schedule_event_triggers IS 'Event-driven trigger configurations';


-- Schedule Execution History Table
-- Tracks execution metrics for SLA monitoring
CREATE TABLE IF NOT EXISTS schedule_execution_history (
    id BIGSERIAL PRIMARY KEY,
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- Execution tracking
    execution_id UUID NOT NULL DEFAULT gen_random_uuid(),

    -- Timing
    scheduled_time TIMESTAMPTZ,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,

    -- Calculated metrics (in milliseconds)
    duration_ms INTEGER,
    start_delay_ms INTEGER,

    -- Result
    success BOOLEAN,
    error_message TEXT,

    -- Execution context
    robot_id UUID,
    job_id UUID,
    catch_up BOOLEAN NOT NULL DEFAULT FALSE,

    -- Partition key for time-based partitioning (if needed later)
    partition_date DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Index for schedule execution lookups
CREATE INDEX IF NOT EXISTS idx_exec_history_schedule ON schedule_execution_history(schedule_id, started_at DESC);

-- Index for execution ID lookups
CREATE INDEX IF NOT EXISTS idx_exec_history_exec_id ON schedule_execution_history(execution_id);

-- Index for success rate calculations
CREATE INDEX IF NOT EXISTS idx_exec_history_success ON schedule_execution_history(schedule_id, success, started_at DESC);

-- Index for partition pruning
CREATE INDEX IF NOT EXISTS idx_exec_history_partition ON schedule_execution_history(partition_date);

-- Partial index for recent failures
CREATE INDEX IF NOT EXISTS idx_exec_history_failures ON schedule_execution_history(schedule_id, started_at DESC)
    WHERE success = FALSE;

COMMENT ON TABLE schedule_execution_history IS 'Execution history for schedule SLA monitoring';


-- Dependency Completion Tracking Table
-- Tracks completion status for dependency resolution
CREATE TABLE IF NOT EXISTS dependency_completions (
    id BIGSERIAL PRIMARY KEY,
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    success BOOLEAN NOT NULL,

    -- Optional result data
    result_data JSONB,

    -- TTL for cleanup
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '24 hours'
);

-- Index for dependency lookups
CREATE INDEX IF NOT EXISTS idx_dep_completions_schedule ON dependency_completions(schedule_id, completed_at DESC);

-- Index for cleanup
CREATE INDEX IF NOT EXISTS idx_dep_completions_expires ON dependency_completions(expires_at);

COMMENT ON TABLE dependency_completions IS 'Tracks schedule completions for dependency resolution';


-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for schedule status overview
CREATE OR REPLACE VIEW schedule_status_overview AS
SELECT
    s.id,
    s.name,
    s.workflow_name,
    s.schedule_type,
    s.status,
    s.enabled,
    s.priority,
    s.next_run,
    s.last_run,
    s.run_count,
    s.success_count,
    s.failure_count,
    s.consecutive_failures,
    CASE
        WHEN s.run_count = 0 THEN 100.0
        ELSE ROUND((s.success_count::numeric / s.run_count) * 100, 2)
    END as success_rate,
    sla.current_status as sla_status,
    sla.success_rate_threshold as sla_threshold,
    rl.max_executions as rate_limit_max,
    rl.window_seconds as rate_limit_window,
    bc.name as calendar_name,
    s.organization_id
FROM advanced_schedules s
LEFT JOIN schedule_sla_configs sla ON s.id = sla.schedule_id
LEFT JOIN schedule_rate_limits rl ON s.id = rl.schedule_id
LEFT JOIN business_calendars bc ON s.calendar_id = bc.id;

COMMENT ON VIEW schedule_status_overview IS 'Comprehensive view of schedule status and configurations';


-- View for SLA breaches
CREATE OR REPLACE VIEW sla_breaches AS
SELECT
    s.id as schedule_id,
    s.name as schedule_name,
    s.workflow_name,
    sla.current_status as sla_status,
    sla.success_rate_threshold,
    CASE
        WHEN s.run_count = 0 THEN 100.0
        ELSE ROUND((s.success_count::numeric / s.run_count) * 100, 2)
    END as actual_success_rate,
    s.consecutive_failures,
    sla.consecutive_failure_limit,
    sla.last_status_change,
    s.organization_id
FROM advanced_schedules s
JOIN schedule_sla_configs sla ON s.id = sla.schedule_id
WHERE sla.current_status IN ('warning', 'breached');

COMMENT ON VIEW sla_breaches IS 'View of schedules with SLA issues';


-- View for dependency graph
CREATE OR REPLACE VIEW dependency_graph AS
SELECT
    s.id as schedule_id,
    s.name as schedule_name,
    d.depends_on_id,
    parent.name as depends_on_name,
    d.wait_for_all,
    d.require_success,
    d.timeout_seconds,
    d.priority_order
FROM advanced_schedules s
JOIN schedule_dependencies d ON s.id = d.schedule_id
JOIN advanced_schedules parent ON d.depends_on_id = parent.id
ORDER BY s.id, d.priority_order;

COMMENT ON VIEW dependency_graph IS 'View of schedule dependency relationships';


-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to check if a schedule can execute (business hours check)
CREATE OR REPLACE FUNCTION can_schedule_execute(
    p_schedule_id UUID,
    p_check_time TIMESTAMPTZ DEFAULT NOW()
) RETURNS TABLE (
    can_execute BOOLEAN,
    reason TEXT
) AS $$
DECLARE
    v_schedule RECORD;
    v_calendar RECORD;
    v_blackout RECORD;
    v_day_name TEXT;
    v_check_time_local TIME;
    v_working_hours JSONB;
BEGIN
    -- Get schedule
    SELECT * INTO v_schedule FROM advanced_schedules WHERE id = p_schedule_id;
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Schedule not found';
        RETURN;
    END IF;

    -- Check if enabled
    IF NOT v_schedule.enabled THEN
        RETURN QUERY SELECT FALSE, 'Schedule is disabled';
        RETURN;
    END IF;

    -- Check if paused
    IF v_schedule.status = 'paused' THEN
        RETURN QUERY SELECT FALSE, 'Schedule is paused';
        RETURN;
    END IF;

    -- If not respecting business hours, allow execution
    IF NOT v_schedule.respect_business_hours OR v_schedule.calendar_id IS NULL THEN
        RETURN QUERY SELECT TRUE, NULL::TEXT;
        RETURN;
    END IF;

    -- Get calendar
    SELECT * INTO v_calendar FROM business_calendars WHERE id = v_schedule.calendar_id;
    IF NOT FOUND THEN
        RETURN QUERY SELECT TRUE, NULL::TEXT; -- No calendar = allow
        RETURN;
    END IF;

    -- Check blackouts
    FOR v_blackout IN
        SELECT * FROM blackout_periods
        WHERE calendar_id = v_calendar.id
        AND enabled = TRUE
        AND p_check_time BETWEEN start_time AND end_time
    LOOP
        IF array_length(v_blackout.affected_workflows, 1) IS NULL
           OR v_schedule.workflow_id::TEXT = ANY(v_blackout.affected_workflows) THEN
            RETURN QUERY SELECT FALSE, 'Blackout period: ' || v_blackout.name;
            RETURN;
        END IF;
    END LOOP;

    -- Check working hours
    v_check_time_local := (p_check_time AT TIME ZONE v_calendar.timezone)::TIME;
    v_day_name := UPPER(TO_CHAR(p_check_time AT TIME ZONE v_calendar.timezone, 'DAY'));
    v_day_name := TRIM(v_day_name);

    v_working_hours := v_calendar.working_hours -> v_day_name;

    IF v_working_hours IS NULL THEN
        -- No working hours defined for this day
        IF NOT v_calendar.allow_weekends AND EXTRACT(DOW FROM p_check_time AT TIME ZONE v_calendar.timezone) IN (0, 6) THEN
            RETURN QUERY SELECT FALSE, 'Weekend execution not allowed';
            RETURN;
        END IF;
    ELSE
        IF NOT (v_working_hours ->> 'enabled')::BOOLEAN THEN
            RETURN QUERY SELECT FALSE, 'Day ' || v_day_name || ' is not a working day';
            RETURN;
        END IF;

        IF NOT v_calendar.allow_outside_hours THEN
            IF v_check_time_local < (v_working_hours ->> 'start')::TIME
               OR v_check_time_local > (v_working_hours ->> 'end')::TIME THEN
                RETURN QUERY SELECT FALSE, 'Outside working hours';
                RETURN;
            END IF;
        END IF;
    END IF;

    RETURN QUERY SELECT TRUE, NULL::TEXT;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION can_schedule_execute IS 'Check if a schedule can execute at a given time';


-- Function to update SLA status
CREATE OR REPLACE FUNCTION update_sla_status(p_schedule_id UUID) RETURNS TEXT AS $$
DECLARE
    v_schedule RECORD;
    v_sla RECORD;
    v_success_rate NUMERIC;
    v_new_status TEXT;
    v_old_status TEXT;
BEGIN
    -- Get schedule and SLA config
    SELECT * INTO v_schedule FROM advanced_schedules WHERE id = p_schedule_id;
    SELECT * INTO v_sla FROM schedule_sla_configs WHERE schedule_id = p_schedule_id;

    IF v_sla IS NULL THEN
        RETURN 'unknown';
    END IF;

    v_old_status := v_sla.current_status;

    -- Calculate success rate
    IF v_schedule.run_count = 0 THEN
        v_success_rate := 100.0;
    ELSE
        v_success_rate := (v_schedule.success_count::numeric / v_schedule.run_count) * 100;
    END IF;

    -- Determine new status
    IF v_schedule.consecutive_failures >= v_sla.consecutive_failure_limit THEN
        v_new_status := 'breached';
    ELSIF v_success_rate < v_sla.success_rate_threshold - 5 THEN
        v_new_status := 'breached';
    ELSIF v_success_rate < v_sla.success_rate_threshold THEN
        v_new_status := 'warning';
    ELSE
        v_new_status := 'ok';
    END IF;

    -- Update if changed
    IF v_new_status != v_old_status THEN
        UPDATE schedule_sla_configs
        SET current_status = v_new_status,
            last_status_change = NOW(),
            updated_at = NOW()
        WHERE schedule_id = p_schedule_id;
    END IF;

    RETURN v_new_status;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_sla_status IS 'Update SLA status based on execution history';


-- Function to record schedule execution
CREATE OR REPLACE FUNCTION record_schedule_execution(
    p_schedule_id UUID,
    p_success BOOLEAN,
    p_started_at TIMESTAMPTZ,
    p_completed_at TIMESTAMPTZ,
    p_scheduled_time TIMESTAMPTZ DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_robot_id UUID DEFAULT NULL,
    p_job_id UUID DEFAULT NULL,
    p_catch_up BOOLEAN DEFAULT FALSE
) RETURNS BIGINT AS $$
DECLARE
    v_execution_id BIGINT;
    v_duration_ms INTEGER;
    v_start_delay_ms INTEGER;
BEGIN
    -- Calculate metrics
    v_duration_ms := EXTRACT(EPOCH FROM (p_completed_at - p_started_at)) * 1000;

    IF p_scheduled_time IS NOT NULL THEN
        v_start_delay_ms := GREATEST(0, EXTRACT(EPOCH FROM (p_started_at - p_scheduled_time)) * 1000);
    ELSE
        v_start_delay_ms := 0;
    END IF;

    -- Insert execution record
    INSERT INTO schedule_execution_history (
        schedule_id, scheduled_time, started_at, completed_at,
        duration_ms, start_delay_ms, success, error_message,
        robot_id, job_id, catch_up
    ) VALUES (
        p_schedule_id, p_scheduled_time, p_started_at, p_completed_at,
        v_duration_ms, v_start_delay_ms, p_success, p_error_message,
        p_robot_id, p_job_id, p_catch_up
    ) RETURNING id INTO v_execution_id;

    -- Update schedule statistics
    UPDATE advanced_schedules SET
        last_run = p_completed_at,
        run_count = run_count + 1,
        success_count = CASE WHEN p_success THEN success_count + 1 ELSE success_count END,
        failure_count = CASE WHEN NOT p_success THEN failure_count + 1 ELSE failure_count END,
        consecutive_failures = CASE
            WHEN p_success THEN 0
            ELSE consecutive_failures + 1
        END,
        updated_at = NOW()
    WHERE id = p_schedule_id;

    -- Update SLA status
    PERFORM update_sla_status(p_schedule_id);

    -- Record completion for dependencies
    INSERT INTO dependency_completions (schedule_id, success, result_data)
    VALUES (p_schedule_id, p_success,
            jsonb_build_object('duration_ms', v_duration_ms, 'job_id', p_job_id));

    RETURN v_execution_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_schedule_execution IS 'Record a schedule execution and update statistics';


-- Function to cleanup old data
CREATE OR REPLACE FUNCTION cleanup_schedule_history(p_retention_days INTEGER DEFAULT 90) RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER := 0;
    v_cutoff TIMESTAMPTZ;
BEGIN
    v_cutoff := NOW() - (p_retention_days || ' days')::INTERVAL;

    -- Cleanup execution history
    DELETE FROM schedule_execution_history
    WHERE started_at < v_cutoff;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    -- Cleanup expired dependency completions
    DELETE FROM dependency_completions
    WHERE expires_at < NOW();

    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_schedule_history IS 'Cleanup old schedule execution history';


-- Function to check for dependency cycles
CREATE OR REPLACE FUNCTION check_dependency_cycle(
    p_schedule_id UUID,
    p_depends_on_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_has_cycle BOOLEAN := FALSE;
BEGIN
    -- Check if adding this dependency would create a cycle
    WITH RECURSIVE dep_chain AS (
        -- Start from the potential parent
        SELECT p_depends_on_id as schedule_id, 1 as depth

        UNION ALL

        -- Follow dependencies
        SELECT d.depends_on_id, dc.depth + 1
        FROM schedule_dependencies d
        JOIN dep_chain dc ON d.schedule_id = dc.schedule_id
        WHERE dc.depth < 100 -- Prevent infinite loops
    )
    SELECT EXISTS (
        SELECT 1 FROM dep_chain WHERE schedule_id = p_schedule_id
    ) INTO v_has_cycle;

    RETURN v_has_cycle;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION check_dependency_cycle IS 'Check if adding a dependency would create a cycle';


-- Trigger to prevent dependency cycles
CREATE OR REPLACE FUNCTION prevent_dependency_cycle() RETURNS TRIGGER AS $$
BEGIN
    IF check_dependency_cycle(NEW.schedule_id, NEW.depends_on_id) THEN
        RAISE EXCEPTION 'Adding this dependency would create a cycle';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_dependency_cycle ON schedule_dependencies;
CREATE TRIGGER trg_prevent_dependency_cycle
    BEFORE INSERT OR UPDATE ON schedule_dependencies
    FOR EACH ROW
    EXECUTE FUNCTION prevent_dependency_cycle();


-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_schedules_org_status ON advanced_schedules(organization_id, status, enabled);
CREATE INDEX IF NOT EXISTS idx_schedules_workflow_active ON advanced_schedules(workflow_id, enabled) WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_exec_history_recent ON schedule_execution_history(schedule_id, started_at DESC)
    WHERE started_at > NOW() - INTERVAL '7 days';


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN advanced_schedules.schedule_type IS 'Type: cron, interval, event, dependency, one_time';
COMMENT ON COLUMN advanced_schedules.status IS 'Status: active, paused, disabled, completed, error';
COMMENT ON COLUMN advanced_schedules.priority IS 'Priority 0-3 (0=low, 3=critical)';
COMMENT ON COLUMN schedule_sla_configs.current_status IS 'SLA status: ok, warning, breached, unknown';
COMMENT ON COLUMN schedule_event_triggers.event_type IS 'Event type: file_arrival, webhook, database_change, queue_message, workflow_completed, custom';
