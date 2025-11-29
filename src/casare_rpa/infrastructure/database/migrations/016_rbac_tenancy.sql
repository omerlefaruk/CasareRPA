-- Migration: 016_rbac_tenancy
-- Description: Multi-tenancy and RBAC schema with Row-Level Security
-- Created: 2024-11-28

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TENANT MANAGEMENT
-- ============================================================================

-- Tenants table (organizations/companies)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,

    -- Contact info
    admin_email TEXT NOT NULL,
    billing_email TEXT,

    -- Status
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'pending', 'archived')),

    -- SSO configuration
    sso_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    sso_provider TEXT CHECK (sso_provider IN ('saml', 'oauth2', 'oidc', NULL)),
    sso_config JSONB,

    -- Resource quotas
    max_workflows INTEGER NOT NULL DEFAULT 100,
    max_robots INTEGER NOT NULL DEFAULT 10,
    max_executions_per_hour INTEGER NOT NULL DEFAULT 1000,
    max_storage_mb INTEGER NOT NULL DEFAULT 10240,
    max_team_members INTEGER NOT NULL DEFAULT 50,

    -- Usage tracking
    current_workflow_count INTEGER NOT NULL DEFAULT 0,
    current_robot_count INTEGER NOT NULL DEFAULT 0,
    current_storage_mb INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,

    -- Subscription/billing
    subscription_tier TEXT NOT NULL DEFAULT 'free' CHECK (subscription_tier IN ('free', 'starter', 'professional', 'enterprise')),
    subscription_expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_subscription ON tenants(subscription_tier);

-- Workspaces/teams within a tenant
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,

    -- Workspace settings
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    settings JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,

    UNIQUE(tenant_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_workspaces_tenant ON workspaces(tenant_id);

-- ============================================================================
-- USER MANAGEMENT
-- ============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,

    -- Authentication
    password_hash TEXT,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret TEXT,

    -- SSO link
    sso_provider TEXT,
    sso_subject TEXT,

    -- Status
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending', 'locked')),
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at TIMESTAMPTZ,
    failed_login_count INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,

    -- Preferences
    settings JSONB NOT NULL DEFAULT '{}',
    timezone TEXT DEFAULT 'UTC',
    locale TEXT DEFAULT 'en',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(sso_provider, sso_subject)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_sso ON users(sso_provider, sso_subject);

-- Tenant membership (many-to-many)
CREATE TABLE IF NOT EXISTS tenant_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Role within tenant
    role_id UUID NOT NULL,

    -- Status
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'invited', 'suspended')),
    invited_at TIMESTAMPTZ,
    invited_by UUID REFERENCES users(id),
    joined_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_members_tenant ON tenant_members(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_members_user ON tenant_members(user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_members_role ON tenant_members(role_id);

-- Workspace membership
CREATE TABLE IF NOT EXISTS workspace_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Role within workspace (can override tenant role)
    role_id UUID,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(workspace_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace ON workspace_members(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON workspace_members(user_id);

-- ============================================================================
-- ROLE-BASED ACCESS CONTROL
-- ============================================================================

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,

    -- Role identity
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,

    -- Role type
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,

    -- Hierarchy (higher = more permissions)
    priority INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- System roles have NULL tenant_id, custom roles belong to tenant
    UNIQUE(tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_roles_tenant ON roles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_roles_system ON roles(is_system);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Permission identity
    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,

    -- Resource and action
    resource TEXT NOT NULL,
    action TEXT NOT NULL,

    -- Category for UI grouping
    category TEXT NOT NULL DEFAULT 'general',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(resource, action)
);

CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);
CREATE INDEX IF NOT EXISTS idx_permissions_category ON permissions(category);

-- Role-Permission mapping
CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,

    -- Optional conditions (JSONB for complex rules)
    conditions JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON role_permissions(permission_id);

-- ============================================================================
-- API KEY MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Key identity
    name TEXT NOT NULL,
    description TEXT,
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL,

    -- Permissions
    role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    scopes TEXT[] NOT NULL DEFAULT '{}',

    -- Restrictions
    allowed_ips TEXT[],
    allowed_origins TEXT[],
    rate_limit_per_minute INTEGER,

    -- Status
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'expired')),
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    use_count BIGINT NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_status ON api_keys(status);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);

-- ============================================================================
-- AUDIT LOGGING
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Actor
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('user', 'api_key', 'system', 'robot')),
    actor_ip TEXT,
    user_agent TEXT,

    -- Action
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,

    -- Details
    old_value JSONB,
    new_value JSONB,
    metadata JSONB,

    -- Result
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,

    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Create partitions for audit logs (monthly)
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE audit_logs_2024_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE audit_logs_2024_03 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');
CREATE TABLE audit_logs_2024_04 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');
CREATE TABLE audit_logs_2024_05 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');
CREATE TABLE audit_logs_2024_06 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');
CREATE TABLE audit_logs_2024_07 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');
CREATE TABLE audit_logs_2024_08 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');
CREATE TABLE audit_logs_2024_09 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');
CREATE TABLE audit_logs_2024_10 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');
CREATE TABLE audit_logs_2024_11 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');
CREATE TABLE audit_logs_2024_12 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- ============================================================================
-- TENANT-SCOPED RESOURCES
-- ============================================================================

-- Add tenant_id to existing tables (workflows, robots, executions)
-- These ALTER statements assume the tables exist; use IF NOT EXISTS patterns

-- Workflows with tenant isolation
CREATE TABLE IF NOT EXISTS tenant_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,

    -- Workflow identity
    name TEXT NOT NULL,
    description TEXT,
    version INTEGER NOT NULL DEFAULT 1,

    -- Content
    definition JSONB NOT NULL,

    -- Status
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived', 'disabled')),

    -- Ownership
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tenant_workflows_tenant ON tenant_workflows(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_workspace ON tenant_workflows(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_status ON tenant_workflows(status);
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_created_by ON tenant_workflows(created_by);

-- Robots with tenant isolation
CREATE TABLE IF NOT EXISTS tenant_robots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Robot identity
    name TEXT NOT NULL,
    machine_id TEXT NOT NULL,

    -- Status
    status TEXT NOT NULL DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'busy', 'error', 'maintenance')),
    last_heartbeat TIMESTAMPTZ,

    -- Configuration
    max_concurrent_executions INTEGER NOT NULL DEFAULT 1,
    tags TEXT[] NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, machine_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_robots_tenant ON tenant_robots(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_robots_status ON tenant_robots(status);

-- Executions with tenant isolation
CREATE TABLE IF NOT EXISTS tenant_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    workflow_id UUID NOT NULL REFERENCES tenant_workflows(id) ON DELETE CASCADE,
    robot_id UUID REFERENCES tenant_robots(id) ON DELETE SET NULL,

    -- Execution details
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER NOT NULL DEFAULT 0,

    -- Input/Output
    input_variables JSONB,
    output_variables JSONB,

    -- Timing
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Error info
    error_message TEXT,
    error_details JSONB,

    -- Triggered by
    triggered_by UUID REFERENCES users(id) ON DELETE SET NULL,
    trigger_type TEXT NOT NULL DEFAULT 'manual' CHECK (trigger_type IN ('manual', 'scheduled', 'api', 'webhook', 'event'))
);

CREATE INDEX IF NOT EXISTS idx_tenant_executions_tenant ON tenant_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_executions_workflow ON tenant_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_tenant_executions_robot ON tenant_executions(robot_id);
CREATE INDEX IF NOT EXISTS idx_tenant_executions_status ON tenant_executions(status);
CREATE INDEX IF NOT EXISTS idx_tenant_executions_queued ON tenant_executions(queued_at DESC);

-- ============================================================================
-- ROW-LEVEL SECURITY POLICIES
-- ============================================================================

-- Enable RLS on tenant-scoped tables
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_robots ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_executions ENABLE ROW LEVEL SECURITY;

-- Create function to get current tenant from session
CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '')::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Create function to get current user from session
CREATE OR REPLACE FUNCTION current_app_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Create function to check if user has permission
CREATE OR REPLACE FUNCTION user_has_permission(p_user_id UUID, p_tenant_id UUID, p_resource TEXT, p_action TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    has_perm BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM tenant_members tm
        JOIN role_permissions rp ON rp.role_id = tm.role_id
        JOIN permissions p ON p.id = rp.permission_id
        WHERE tm.user_id = p_user_id
          AND tm.tenant_id = p_tenant_id
          AND tm.status = 'active'
          AND p.resource = p_resource
          AND p.action = p_action
    ) INTO has_perm;

    RETURN has_perm;
END;
$$ LANGUAGE plpgsql STABLE;

-- Workspaces RLS
CREATE POLICY workspaces_tenant_isolation ON workspaces
    FOR ALL
    USING (tenant_id = current_tenant_id());

-- Tenant members RLS
CREATE POLICY tenant_members_isolation ON tenant_members
    FOR ALL
    USING (tenant_id = current_tenant_id());

-- Workspace members RLS
CREATE POLICY workspace_members_isolation ON workspace_members
    FOR ALL
    USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE tenant_id = current_tenant_id()
        )
    );

-- Roles RLS (system roles visible to all, custom roles to owner tenant)
CREATE POLICY roles_visibility ON roles
    FOR SELECT
    USING (is_system = TRUE OR tenant_id = current_tenant_id() OR tenant_id IS NULL);

CREATE POLICY roles_tenant_modification ON roles
    FOR ALL
    USING (tenant_id = current_tenant_id() AND is_system = FALSE);

-- API keys RLS
CREATE POLICY api_keys_tenant_isolation ON api_keys
    FOR ALL
    USING (tenant_id = current_tenant_id());

-- Audit logs RLS
CREATE POLICY audit_logs_tenant_isolation ON audit_logs
    FOR SELECT
    USING (tenant_id = current_tenant_id());

CREATE POLICY audit_logs_insert ON audit_logs
    FOR INSERT
    WITH CHECK (tenant_id = current_tenant_id());

-- Workflows RLS
CREATE POLICY tenant_workflows_isolation ON tenant_workflows
    FOR ALL
    USING (tenant_id = current_tenant_id());

-- Robots RLS
CREATE POLICY tenant_robots_isolation ON tenant_robots
    FOR ALL
    USING (tenant_id = current_tenant_id());

-- Executions RLS
CREATE POLICY tenant_executions_isolation ON tenant_executions
    FOR ALL
    USING (tenant_id = current_tenant_id());

-- ============================================================================
-- DEFAULT SYSTEM ROLES AND PERMISSIONS
-- ============================================================================

-- Insert system permissions
INSERT INTO permissions (name, display_name, description, resource, action, category) VALUES
    -- Workflow permissions
    ('workflow.create', 'Create Workflows', 'Create new workflows', 'workflow', 'create', 'workflows'),
    ('workflow.read', 'View Workflows', 'View workflow definitions', 'workflow', 'read', 'workflows'),
    ('workflow.update', 'Edit Workflows', 'Modify workflow definitions', 'workflow', 'update', 'workflows'),
    ('workflow.delete', 'Delete Workflows', 'Delete workflows', 'workflow', 'delete', 'workflows'),
    ('workflow.execute', 'Execute Workflows', 'Run workflow executions', 'workflow', 'execute', 'workflows'),
    ('workflow.publish', 'Publish Workflows', 'Publish workflows for production', 'workflow', 'publish', 'workflows'),

    -- Execution permissions
    ('execution.read', 'View Executions', 'View execution history and logs', 'execution', 'read', 'executions'),
    ('execution.cancel', 'Cancel Executions', 'Cancel running executions', 'execution', 'cancel', 'executions'),
    ('execution.retry', 'Retry Executions', 'Retry failed executions', 'execution', 'retry', 'executions'),

    -- Robot permissions
    ('robot.create', 'Create Robots', 'Register new robots', 'robot', 'create', 'robots'),
    ('robot.read', 'View Robots', 'View robot status and details', 'robot', 'read', 'robots'),
    ('robot.update', 'Manage Robots', 'Update robot configuration', 'robot', 'update', 'robots'),
    ('robot.delete', 'Delete Robots', 'Remove robots', 'robot', 'delete', 'robots'),

    -- User/Team management permissions
    ('user.read', 'View Users', 'View user profiles', 'user', 'read', 'users'),
    ('user.invite', 'Invite Users', 'Invite new team members', 'user', 'invite', 'users'),
    ('user.update', 'Manage Users', 'Update user roles and settings', 'user', 'update', 'users'),
    ('user.remove', 'Remove Users', 'Remove users from tenant', 'user', 'remove', 'users'),

    -- Workspace permissions
    ('workspace.create', 'Create Workspaces', 'Create new workspaces', 'workspace', 'create', 'workspaces'),
    ('workspace.read', 'View Workspaces', 'View workspace details', 'workspace', 'read', 'workspaces'),
    ('workspace.update', 'Manage Workspaces', 'Update workspace settings', 'workspace', 'update', 'workspaces'),
    ('workspace.delete', 'Delete Workspaces', 'Delete workspaces', 'workspace', 'delete', 'workspaces'),

    -- Credentials/Secrets permissions
    ('credential.create', 'Create Credentials', 'Add new credentials', 'credential', 'create', 'credentials'),
    ('credential.read', 'View Credentials', 'View credential metadata', 'credential', 'read', 'credentials'),
    ('credential.update', 'Update Credentials', 'Modify credentials', 'credential', 'update', 'credentials'),
    ('credential.delete', 'Delete Credentials', 'Remove credentials', 'credential', 'delete', 'credentials'),
    ('credential.use', 'Use Credentials', 'Use credentials in workflows', 'credential', 'use', 'credentials'),

    -- API Key permissions
    ('apikey.create', 'Create API Keys', 'Generate new API keys', 'apikey', 'create', 'apikeys'),
    ('apikey.read', 'View API Keys', 'View API key metadata', 'apikey', 'read', 'apikeys'),
    ('apikey.revoke', 'Revoke API Keys', 'Revoke API keys', 'apikey', 'revoke', 'apikeys'),

    -- Audit permissions
    ('audit.read', 'View Audit Logs', 'Access audit history', 'audit', 'read', 'audit'),
    ('audit.export', 'Export Audit Logs', 'Export audit data', 'audit', 'export', 'audit'),

    -- Admin permissions
    ('tenant.settings', 'Tenant Settings', 'Manage tenant configuration', 'tenant', 'settings', 'admin'),
    ('tenant.billing', 'Billing Management', 'Manage subscription and billing', 'tenant', 'billing', 'admin'),
    ('role.manage', 'Manage Roles', 'Create and modify custom roles', 'role', 'manage', 'admin')
ON CONFLICT (name) DO NOTHING;

-- Insert system roles (NULL tenant_id = system-wide)
INSERT INTO roles (id, tenant_id, name, display_name, description, is_system, priority) VALUES
    ('00000000-0000-0000-0000-000000000001', NULL, 'admin', 'Administrator', 'Full system access', TRUE, 100),
    ('00000000-0000-0000-0000-000000000002', NULL, 'developer', 'Developer', 'Create and edit workflows, view executions', TRUE, 75),
    ('00000000-0000-0000-0000-000000000003', NULL, 'operator', 'Operator', 'Execute workflows and view results', TRUE, 50),
    ('00000000-0000-0000-0000-000000000004', NULL, 'viewer', 'Viewer', 'Read-only access', TRUE, 25)
ON CONFLICT DO NOTHING;

-- Assign all permissions to Admin role
INSERT INTO role_permissions (role_id, permission_id)
SELECT
    '00000000-0000-0000-0000-000000000001'::UUID,
    p.id
FROM permissions p
ON CONFLICT DO NOTHING;

-- Developer permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT
    '00000000-0000-0000-0000-000000000002'::UUID,
    p.id
FROM permissions p
WHERE p.name IN (
    'workflow.create', 'workflow.read', 'workflow.update', 'workflow.delete', 'workflow.execute', 'workflow.publish',
    'execution.read', 'execution.cancel', 'execution.retry',
    'robot.read',
    'credential.read', 'credential.use',
    'user.read',
    'workspace.read',
    'apikey.read'
)
ON CONFLICT DO NOTHING;

-- Operator permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT
    '00000000-0000-0000-0000-000000000003'::UUID,
    p.id
FROM permissions p
WHERE p.name IN (
    'workflow.read', 'workflow.execute',
    'execution.read', 'execution.cancel',
    'robot.read',
    'credential.use',
    'user.read',
    'workspace.read'
)
ON CONFLICT DO NOTHING;

-- Viewer permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT
    '00000000-0000-0000-0000-000000000004'::UUID,
    p.id
FROM permissions p
WHERE p.name IN (
    'workflow.read',
    'execution.read',
    'robot.read',
    'user.read',
    'workspace.read'
)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Set tenant context for RLS
CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id UUID, p_user_id UUID DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', p_tenant_id::TEXT, FALSE);
    IF p_user_id IS NOT NULL THEN
        PERFORM set_config('app.current_user_id', p_user_id::TEXT, FALSE);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Clear tenant context
CREATE OR REPLACE FUNCTION clear_tenant_context()
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', '', FALSE);
    PERFORM set_config('app.current_user_id', '', FALSE);
END;
$$ LANGUAGE plpgsql;

-- Check quota before creating resources
CREATE OR REPLACE FUNCTION check_tenant_quota(p_tenant_id UUID, p_resource_type TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    tenant_record RECORD;
BEGIN
    SELECT * INTO tenant_record FROM tenants WHERE id = p_tenant_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF tenant_record.status != 'active' THEN
        RETURN FALSE;
    END IF;

    CASE p_resource_type
        WHEN 'workflow' THEN
            RETURN tenant_record.current_workflow_count < tenant_record.max_workflows;
        WHEN 'robot' THEN
            RETURN tenant_record.current_robot_count < tenant_record.max_robots;
        ELSE
            RETURN TRUE;
    END CASE;
END;
$$ LANGUAGE plpgsql STABLE;

-- Update tenant resource counts
CREATE OR REPLACE FUNCTION update_tenant_resource_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF TG_TABLE_NAME = 'tenant_workflows' THEN
            UPDATE tenants SET current_workflow_count = current_workflow_count + 1
            WHERE id = NEW.tenant_id;
        ELSIF TG_TABLE_NAME = 'tenant_robots' THEN
            UPDATE tenants SET current_robot_count = current_robot_count + 1
            WHERE id = NEW.tenant_id;
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        IF TG_TABLE_NAME = 'tenant_workflows' THEN
            UPDATE tenants SET current_workflow_count = GREATEST(0, current_workflow_count - 1)
            WHERE id = OLD.tenant_id;
        ELSIF TG_TABLE_NAME = 'tenant_robots' THEN
            UPDATE tenants SET current_robot_count = GREATEST(0, current_robot_count - 1)
            WHERE id = OLD.tenant_id;
        END IF;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Triggers for resource counting
CREATE TRIGGER trigger_workflow_count
    AFTER INSERT OR DELETE ON tenant_workflows
    FOR EACH ROW EXECUTE FUNCTION update_tenant_resource_count();

CREATE TRIGGER trigger_robot_count
    AFTER INSERT OR DELETE ON tenant_robots
    FOR EACH ROW EXECUTE FUNCTION update_tenant_resource_count();

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_workspaces_updated_at
    BEFORE UPDATE ON workspaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_tenant_members_updated_at
    BEFORE UPDATE ON tenant_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_tenant_workflows_updated_at
    BEFORE UPDATE ON tenant_workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_tenant_robots_updated_at
    BEFORE UPDATE ON tenant_robots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE tenants IS 'Multi-tenant organizations with resource quotas';
COMMENT ON TABLE workspaces IS 'Workspaces/teams within a tenant for organizing workflows';
COMMENT ON TABLE users IS 'User accounts (can belong to multiple tenants)';
COMMENT ON TABLE tenant_members IS 'Tenant membership with role assignment';
COMMENT ON TABLE roles IS 'System and custom roles for RBAC';
COMMENT ON TABLE permissions IS 'Granular permissions for resources and actions';
COMMENT ON TABLE role_permissions IS 'Many-to-many mapping of roles to permissions';
COMMENT ON TABLE api_keys IS 'API keys for programmatic access';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail of all actions';

COMMENT ON FUNCTION current_tenant_id IS 'Get current tenant ID from session context';
COMMENT ON FUNCTION current_app_user_id IS 'Get current user ID from session context';
COMMENT ON FUNCTION set_tenant_context IS 'Set tenant context for RLS policies';
COMMENT ON FUNCTION check_tenant_quota IS 'Verify tenant has quota for resource creation';
COMMENT ON FUNCTION user_has_permission IS 'Check if user has specific permission in tenant';
