-- Migration: 005_rbac_tenancy
-- Description: Multi-tenancy and RBAC schema with Row-Level Security
-- Consolidated from:
--   - src/casare_rpa/infrastructure/database/migrations/016_rbac_tenancy.sql
-- Created: 2024-12-03

-- =============================================================================
-- TENANT MANAGEMENT
-- =============================================================================

-- Tenants table (organizations/companies)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

    -- Subscription
    subscription_tier TEXT NOT NULL DEFAULT 'free' CHECK (subscription_tier IN ('free', 'starter', 'professional', 'enterprise')),
    subscription_expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_subscription ON tenants(subscription_tier);

-- =============================================================================
-- WORKSPACES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,

    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    settings JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,

    UNIQUE(tenant_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_workspaces_tenant ON workspaces(tenant_id);

-- =============================================================================
-- USERS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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

-- =============================================================================
-- TENANT MEMBERSHIP
-- =============================================================================
CREATE TABLE IF NOT EXISTS tenant_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    role_id UUID NOT NULL,

    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'invited', 'suspended')),
    invited_at TIMESTAMPTZ,
    invited_by UUID REFERENCES users(id),
    joined_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_members_tenant ON tenant_members(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_members_user ON tenant_members(user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_members_role ON tenant_members(role_id);

-- =============================================================================
-- ROLES AND PERMISSIONS
-- =============================================================================
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,

    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    priority INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_roles_tenant ON roles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_roles_system ON roles(is_system);

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,

    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(resource, action)
);

CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);
CREATE INDEX IF NOT EXISTS idx_permissions_category ON permissions(category);

CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,

    conditions JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON role_permissions(permission_id);

-- =============================================================================
-- API KEY MANAGEMENT
-- =============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    name TEXT NOT NULL,
    description TEXT,
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL,

    role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    scopes TEXT[] NOT NULL DEFAULT '{}',

    allowed_ips TEXT[],
    allowed_origins TEXT[],
    rate_limit_per_minute INTEGER,

    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'expired')),
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    use_count BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_status ON api_keys(status);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Get current tenant from session
CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '')::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Get current user from session
CREATE OR REPLACE FUNCTION current_app_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Set tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id UUID, p_user_id UUID DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', p_tenant_id::TEXT, FALSE);
    IF p_user_id IS NOT NULL THEN
        PERFORM set_config('app.current_user_id', p_user_id::TEXT, FALSE);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Check tenant quota
CREATE OR REPLACE FUNCTION check_tenant_quota(p_tenant_id UUID, p_resource_type TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    tenant_record RECORD;
BEGIN
    SELECT * INTO tenant_record FROM tenants WHERE id = p_tenant_id;

    IF NOT FOUND OR tenant_record.status != 'active' THEN
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

-- Check if user has permission
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

-- =============================================================================
-- DEFAULT SYSTEM ROLES AND PERMISSIONS
-- =============================================================================

-- Insert system permissions
INSERT INTO permissions (name, display_name, description, resource, action, category) VALUES
    ('workflow.create', 'Create Workflows', 'Create new workflows', 'workflow', 'create', 'workflows'),
    ('workflow.read', 'View Workflows', 'View workflow definitions', 'workflow', 'read', 'workflows'),
    ('workflow.update', 'Edit Workflows', 'Modify workflow definitions', 'workflow', 'update', 'workflows'),
    ('workflow.delete', 'Delete Workflows', 'Delete workflows', 'workflow', 'delete', 'workflows'),
    ('workflow.execute', 'Execute Workflows', 'Run workflow executions', 'workflow', 'execute', 'workflows'),
    ('execution.read', 'View Executions', 'View execution history', 'execution', 'read', 'executions'),
    ('execution.cancel', 'Cancel Executions', 'Cancel running executions', 'execution', 'cancel', 'executions'),
    ('robot.create', 'Create Robots', 'Register new robots', 'robot', 'create', 'robots'),
    ('robot.read', 'View Robots', 'View robot status', 'robot', 'read', 'robots'),
    ('robot.update', 'Manage Robots', 'Update robot configuration', 'robot', 'update', 'robots'),
    ('robot.delete', 'Delete Robots', 'Remove robots', 'robot', 'delete', 'robots'),
    ('user.read', 'View Users', 'View user profiles', 'user', 'read', 'users'),
    ('user.invite', 'Invite Users', 'Invite new team members', 'user', 'invite', 'users'),
    ('tenant.settings', 'Tenant Settings', 'Manage tenant configuration', 'tenant', 'settings', 'admin')
ON CONFLICT (name) DO NOTHING;

-- Insert system roles
INSERT INTO roles (id, tenant_id, name, display_name, description, is_system, priority) VALUES
    ('00000000-0000-0000-0000-000000000001', NULL, 'admin', 'Administrator', 'Full system access', TRUE, 100),
    ('00000000-0000-0000-0000-000000000002', NULL, 'developer', 'Developer', 'Create and edit workflows', TRUE, 75),
    ('00000000-0000-0000-0000-000000000003', NULL, 'operator', 'Operator', 'Execute workflows', TRUE, 50),
    ('00000000-0000-0000-0000-000000000004', NULL, 'viewer', 'Viewer', 'Read-only access', TRUE, 25)
ON CONFLICT DO NOTHING;

-- Assign all permissions to Admin role
INSERT INTO role_permissions (role_id, permission_id)
SELECT '00000000-0000-0000-0000-000000000001'::UUID, p.id
FROM permissions p
ON CONFLICT DO NOTHING;

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE tenants IS 'Multi-tenant organizations with resource quotas';
COMMENT ON TABLE workspaces IS 'Workspaces/teams within a tenant';
COMMENT ON TABLE users IS 'User accounts (can belong to multiple tenants)';
COMMENT ON TABLE roles IS 'System and custom roles for RBAC';
COMMENT ON TABLE permissions IS 'Granular permissions for resources and actions';
COMMENT ON TABLE api_keys IS 'API keys for programmatic access';
COMMENT ON FUNCTION current_tenant_id IS 'Get current tenant ID from session context';
COMMENT ON FUNCTION set_tenant_context IS 'Set tenant context for RLS policies';
