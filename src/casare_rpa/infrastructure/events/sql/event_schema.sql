-- ============================================================================
-- CasareRPA Event-Driven Architecture: Database Schema
-- PostgreSQL + pgmq + Supabase Realtime
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgmq;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Robots registry
CREATE TABLE IF NOT EXISTS robots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    machine_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'offline',
    capabilities JSONB DEFAULT '[]',
    last_heartbeat TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table (mirrors pgmq for queryability)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pgmq_msg_id BIGINT,
    workflow_id UUID NOT NULL,
    robot_id UUID REFERENCES robots(id),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    payload JSONB NOT NULL,
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Event log for audit/replay
CREATE TABLE IF NOT EXISTS event_log (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    channel VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    source VARCHAR(100),
    correlation_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Idempotency keys for deduplication
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key VARCHAR(255) PRIMARY KEY,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);

-- ============================================================================
-- PGMQ QUEUES
-- ============================================================================

-- Create job queues per priority
SELECT pgmq.create('jobs_high');
SELECT pgmq.create('jobs_normal');
SELECT pgmq.create('jobs_low');

-- Create event queues
SELECT pgmq.create('events_robot');
SELECT pgmq.create('events_orchestrator');
SELECT pgmq.create('events_system');

-- Dead letter queue
SELECT pgmq.create('jobs_dlq');

-- ============================================================================
-- TRIGGER FUNCTIONS
-- ============================================================================

-- Notify on job INSERT (triggers Supabase Realtime)
CREATE OR REPLACE FUNCTION notify_job_created()
RETURNS TRIGGER AS $$
DECLARE
    channel_name TEXT;
    payload JSONB;
BEGIN
    -- Build payload
    payload := jsonb_build_object(
        'event', 'job.created',
        'job_id', NEW.id,
        'workflow_id', NEW.workflow_id,
        'robot_id', NEW.robot_id,
        'priority', NEW.priority,
        'timestamp', NOW()
    );

    -- Notify robot-specific channel if assigned
    IF NEW.robot_id IS NOT NULL THEN
        channel_name := 'robot:' || NEW.robot_id::TEXT;
        PERFORM pg_notify(channel_name, payload::TEXT);
    END IF;

    -- Notify broadcast channel for unassigned jobs
    IF NEW.robot_id IS NULL THEN
        PERFORM pg_notify('jobs:available', payload::TEXT);
    END IF;

    -- Log event
    INSERT INTO event_log (event_type, channel, payload, source, correlation_id)
    VALUES ('job.created', COALESCE(channel_name, 'jobs:available'), payload, 'trigger', NEW.id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Notify on job status change
CREATE OR REPLACE FUNCTION notify_job_status_change()
RETURNS TRIGGER AS $$
DECLARE
    payload JSONB;
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        payload := jsonb_build_object(
            'event', 'job.status_changed',
            'job_id', NEW.id,
            'old_status', OLD.status,
            'new_status', NEW.status,
            'robot_id', NEW.robot_id,
            'timestamp', NOW()
        );

        -- Notify job-specific channel
        PERFORM pg_notify('job:' || NEW.id::TEXT, payload::TEXT);

        -- Notify orchestrator
        PERFORM pg_notify('orchestrator:jobs', payload::TEXT);

        -- Notify dashboard
        PERFORM pg_notify('dashboard:jobs', payload::TEXT);

        -- Log event
        INSERT INTO event_log (event_type, channel, payload, source, correlation_id)
        VALUES ('job.status_changed', 'job:' || NEW.id::TEXT, payload, 'trigger', NEW.id);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Notify on robot heartbeat
CREATE OR REPLACE FUNCTION notify_robot_heartbeat()
RETURNS TRIGGER AS $$
DECLARE
    payload JSONB;
BEGIN
    IF OLD.last_heartbeat IS DISTINCT FROM NEW.last_heartbeat THEN
        payload := jsonb_build_object(
            'event', 'robot.heartbeat',
            'robot_id', NEW.id,
            'status', NEW.status,
            'timestamp', NEW.last_heartbeat
        );

        -- Notify orchestrator health monitor
        PERFORM pg_notify('orchestrator:health', payload::TEXT);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Notify on robot status change
CREATE OR REPLACE FUNCTION notify_robot_status_change()
RETURNS TRIGGER AS $$
DECLARE
    payload JSONB;
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        payload := jsonb_build_object(
            'event', 'robot.status_changed',
            'robot_id', NEW.id,
            'old_status', OLD.status,
            'new_status', NEW.status,
            'timestamp', NOW()
        );

        -- Notify dashboard
        PERFORM pg_notify('dashboard:robots', payload::TEXT);

        -- Notify orchestrator
        PERFORM pg_notify('orchestrator:health', payload::TEXT);

        -- Log event
        INSERT INTO event_log (event_type, channel, payload, source, correlation_id)
        VALUES ('robot.status_changed', 'dashboard:robots', payload, 'trigger', NEW.id);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ATTACH TRIGGERS
-- ============================================================================

DROP TRIGGER IF EXISTS trg_job_created ON jobs;
CREATE TRIGGER trg_job_created
    AFTER INSERT ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION notify_job_created();

DROP TRIGGER IF EXISTS trg_job_status_change ON jobs;
CREATE TRIGGER trg_job_status_change
    AFTER UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION notify_job_status_change();

DROP TRIGGER IF EXISTS trg_robot_heartbeat ON robots;
CREATE TRIGGER trg_robot_heartbeat
    AFTER UPDATE ON robots
    FOR EACH ROW
    EXECUTE FUNCTION notify_robot_heartbeat();

DROP TRIGGER IF EXISTS trg_robot_status_change ON robots;
CREATE TRIGGER trg_robot_status_change
    AFTER UPDATE ON robots
    FOR EACH ROW
    EXECUTE FUNCTION notify_robot_status_change();

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_robot_id ON jobs(robot_id);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_scheduled_at ON jobs(scheduled_at) WHERE scheduled_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_robots_status ON robots(status);
CREATE INDEX IF NOT EXISTS idx_robots_last_heartbeat ON robots(last_heartbeat);
CREATE INDEX IF NOT EXISTS idx_event_log_created_at ON event_log(created_at);
CREATE INDEX IF NOT EXISTS idx_event_log_correlation_id ON event_log(correlation_id);
CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON idempotency_keys(expires_at);

-- ============================================================================
-- CLEANUP FUNCTIONS
-- ============================================================================

-- Clean expired idempotency keys
CREATE OR REPLACE FUNCTION cleanup_expired_idempotency_keys()
RETURNS void AS $$
BEGIN
    DELETE FROM idempotency_keys WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Archive old event logs
CREATE OR REPLACE FUNCTION archive_old_events(days_to_keep INTEGER DEFAULT 30)
RETURNS void AS $$
BEGIN
    DELETE FROM event_log WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;
