-- Migration: 004_schedules
-- Description: Advanced workflow schedules with business calendars, SLA, dependencies, and rate limits
-- Consolidated from:
--   - src/casare_rpa/infrastructure/database/migrations/015_schedule_enhancements.sql
-- Created: 2024-12-03

-- =============================================================================
-- BUSINESS CALENDARS TABLE
-- =============================================================================
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
    holidays JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Custom non-working dates
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_calendars_org ON business_calendars(organization_id);
CREATE INDEX IF NOT EXISTS idx_calendars_timezone ON business_calendars(timezone);

-- =============================================================================
-- BLACKOUT PERIODS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS blackout_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_id UUID REFERENCES business_calendars(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    reason TEXT DEFAULT '',

    -- Period boundaries
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,

    -- Recurrence
    recurring BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_pattern TEXT,

    -- Scope
    affected_workflows TEXT[] DEFAULT '{}',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,

    CONSTRAINT blackout_time_check CHECK (end_time > start_time)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_blackouts_active ON blackout_periods(start_time, end_time)
    WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_blackouts_calendar ON blackout_periods(calendar_id);

-- =============================================================================
-- ADVANCED SCHEDULES TABLE
-- =============================================================================
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
    cron_expression TEXT,
    interval_seconds INTEGER DEFAULT 0,
    run_at TIMESTAMPTZ,

    -- Timezone handling
    timezone TEXT NOT NULL DEFAULT 'UTC',

    -- Business calendar integration
    calendar_id UUID REFERENCES business_calendars(id) ON DELETE SET NULL,
    respect_business_hours BOOLEAN NOT NULL DEFAULT FALSE,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'active',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Execution assignment
    priority INTEGER NOT NULL DEFAULT 1 CHECK (priority >= 0 AND priority <= 3),
    robot_id UUID,
    environment TEXT DEFAULT 'default',

    -- Variables to pass to workflow
    variables JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Tags for categorization
    tags TEXT[] DEFAULT '{}',
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_schedules_type ON advanced_schedules(schedule_type);
CREATE INDEX IF NOT EXISTS idx_schedules_active ON advanced_schedules(status, enabled)
    WHERE enabled = TRUE AND status = 'active';
CREATE INDEX IF NOT EXISTS idx_schedules_next_run_adv ON advanced_schedules(next_run)
    WHERE enabled = TRUE AND next_run IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_schedules_workflow_adv ON advanced_schedules(workflow_id);
CREATE INDEX IF NOT EXISTS idx_schedules_org ON advanced_schedules(organization_id);
CREATE INDEX IF NOT EXISTS idx_schedules_tags ON advanced_schedules USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_schedules_priority_adv ON advanced_schedules(priority DESC, next_run);

-- =============================================================================
-- SLA CONFIGURATIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS schedule_sla_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- Duration limits (in seconds)
    max_duration_seconds INTEGER,
    max_start_delay_seconds INTEGER DEFAULT 300,

    -- Success rate thresholds
    success_rate_threshold NUMERIC(5,2) NOT NULL DEFAULT 95.00,

    -- Failure tolerance
    consecutive_failure_limit INTEGER NOT NULL DEFAULT 3,

    -- Alert configuration
    alert_config JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Current SLA status
    current_status TEXT NOT NULL DEFAULT 'ok',
    last_status_change TIMESTAMPTZ,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    CONSTRAINT sla_schedule_unique UNIQUE (schedule_id)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_sla_status ON schedule_sla_configs(current_status)
    WHERE current_status IN ('warning', 'breached');

-- =============================================================================
-- RATE LIMIT CONFIGURATIONS TABLE
-- =============================================================================
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

-- =============================================================================
-- SCHEDULE DEPENDENCIES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS schedule_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,
    depends_on_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    -- Dependency configuration
    wait_for_all BOOLEAN NOT NULL DEFAULT TRUE,
    require_success BOOLEAN NOT NULL DEFAULT TRUE,
    timeout_seconds INTEGER NOT NULL DEFAULT 3600,

    -- Priority order
    priority_order INTEGER NOT NULL DEFAULT 0,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT deps_no_self_reference CHECK (schedule_id != depends_on_id),
    CONSTRAINT deps_unique UNIQUE (schedule_id, depends_on_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_deps_schedule ON schedule_dependencies(schedule_id);
CREATE INDEX IF NOT EXISTS idx_deps_depends_on ON schedule_dependencies(depends_on_id);

-- =============================================================================
-- SCHEDULE EXECUTION HISTORY TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS schedule_execution_history (
    id BIGSERIAL PRIMARY KEY,
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,
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

    -- Partition key
    partition_date DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_exec_history_schedule ON schedule_execution_history(schedule_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_exec_history_exec_id ON schedule_execution_history(execution_id);
CREATE INDEX IF NOT EXISTS idx_exec_history_success ON schedule_execution_history(schedule_id, success, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_exec_history_partition ON schedule_execution_history(partition_date);
CREATE INDEX IF NOT EXISTS idx_exec_history_failures ON schedule_execution_history(schedule_id, started_at DESC)
    WHERE success = FALSE;

-- =============================================================================
-- DEPENDENCY COMPLETION TRACKING
-- =============================================================================
CREATE TABLE IF NOT EXISTS dependency_completions (
    id BIGSERIAL PRIMARY KEY,
    schedule_id UUID NOT NULL REFERENCES advanced_schedules(id) ON DELETE CASCADE,

    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    success BOOLEAN NOT NULL,

    result_data JSONB,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '24 hours'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_dep_completions_schedule ON dependency_completions(schedule_id, completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_dep_completions_expires ON dependency_completions(expires_at);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to check if a schedule can execute
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

    -- If not respecting business hours, allow
    IF NOT v_schedule.respect_business_hours OR v_schedule.calendar_id IS NULL THEN
        RETURN QUERY SELECT TRUE, NULL::TEXT;
        RETURN;
    END IF;

    -- Check blackouts
    FOR v_blackout IN
        SELECT * FROM blackout_periods
        WHERE calendar_id = v_schedule.calendar_id
        AND enabled = TRUE
        AND p_check_time BETWEEN start_time AND end_time
    LOOP
        IF array_length(v_blackout.affected_workflows, 1) IS NULL
           OR v_schedule.workflow_id::TEXT = ANY(v_blackout.affected_workflows) THEN
            RETURN QUERY SELECT FALSE, 'Blackout period: ' || v_blackout.name;
            RETURN;
        END IF;
    END LOOP;

    RETURN QUERY SELECT TRUE, NULL::TEXT;
END;
$$ LANGUAGE plpgsql STABLE;

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

    -- Record completion for dependencies
    INSERT INTO dependency_completions (schedule_id, success, result_data)
    VALUES (p_schedule_id, p_success,
            jsonb_build_object('duration_ms', v_duration_ms, 'job_id', p_job_id));

    RETURN v_execution_id;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old schedule history
CREATE OR REPLACE FUNCTION cleanup_schedule_history(p_retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER := 0;
    v_cutoff TIMESTAMPTZ;
BEGIN
    v_cutoff := NOW() - (p_retention_days || ' days')::INTERVAL;

    DELETE FROM schedule_execution_history
    WHERE started_at < v_cutoff;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    DELETE FROM dependency_completions
    WHERE expires_at < NOW();

    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Schedule status overview
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
    bc.name as calendar_name,
    s.organization_id
FROM advanced_schedules s
LEFT JOIN schedule_sla_configs sla ON s.id = sla.schedule_id
LEFT JOIN business_calendars bc ON s.calendar_id = bc.id;

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE business_calendars IS 'Business calendar configurations for scheduling';
COMMENT ON TABLE blackout_periods IS 'Scheduled blackout periods when scheduling is blocked';
COMMENT ON TABLE advanced_schedules IS 'Advanced workflow schedules with enterprise features';
COMMENT ON TABLE schedule_sla_configs IS 'SLA configurations for schedule monitoring';
COMMENT ON TABLE schedule_rate_limits IS 'Sliding window rate limits for schedules';
COMMENT ON TABLE schedule_dependencies IS 'DAG dependencies between schedules';
COMMENT ON TABLE schedule_execution_history IS 'Execution history for schedule SLA monitoring';
