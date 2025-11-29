#!/usr/bin/env bash
# =============================================================================
# CasareRPA Production Deployment Script
# =============================================================================
#
# This script automates the deployment of CasareRPA components:
# - PostgreSQL database initialization
# - Orchestrator service deployment
# - Robot agent deployment
# - Monitoring stack setup
#
# Usage:
#   ./deploy.sh [command] [options]
#
# Commands:
#   init          Initialize environment (first-time setup)
#   deploy        Deploy all services
#   deploy-db     Deploy database only
#   deploy-orch   Deploy orchestrator only
#   deploy-robot  Deploy robot agents
#   deploy-mon    Deploy monitoring stack
#   status        Show service status
#   logs          Show service logs
#   backup        Create database backup
#   restore       Restore from backup
#   upgrade       Upgrade to new version
#   rollback      Rollback to previous version
#   health        Check system health
#   clean         Clean up resources
#
# Options:
#   -e, --env FILE        Environment file (default: .env.production)
#   -c, --config FILE     Docker compose file (default: docker-compose.production.yml)
#   -n, --dry-run         Show what would be done without executing
#   -v, --verbose         Enable verbose output
#   -h, --help            Show this help message
#
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="${PROJECT_ROOT}/deploy"
BACKUP_DIR="${PROJECT_ROOT}/backups"
LOG_DIR="${PROJECT_ROOT}/logs"

# Default values
ENV_FILE="${PROJECT_ROOT}/.env.production"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.production.yml"
DRY_RUN=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

die() {
    log_error "$1"
    exit 1
}

run_cmd() {
    local cmd="$*"
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would execute: $cmd"
    else
        log_debug "Executing: $cmd"
        eval "$cmd"
    fi
}

check_requirements() {
    log_info "Checking requirements..."

    local missing=()

    command -v docker >/dev/null 2>&1 || missing+=("docker")
    command -v docker-compose >/dev/null 2>&1 || command -v "docker compose" >/dev/null 2>&1 || missing+=("docker-compose")
    command -v openssl >/dev/null 2>&1 || missing+=("openssl")

    if [[ ${#missing[@]} -gt 0 ]]; then
        die "Missing required tools: ${missing[*]}"
    fi

    # Check Docker daemon
    docker info >/dev/null 2>&1 || die "Docker daemon is not running"

    log_success "All requirements satisfied"
}

load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        log_info "Loading environment from $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
    else
        log_warn "Environment file not found: $ENV_FILE"
    fi
}

docker_compose() {
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose -f "$COMPOSE_FILE" "$@"
    else
        docker compose -f "$COMPOSE_FILE" "$@"
    fi
}

wait_for_service() {
    local service="$1"
    local max_attempts="${2:-30}"
    local attempt=1

    log_info "Waiting for $service to be healthy..."

    while [[ $attempt -le $max_attempts ]]; do
        if docker_compose ps "$service" | grep -q "healthy"; then
            log_success "$service is healthy"
            return 0
        fi
        log_debug "Attempt $attempt/$max_attempts: $service not ready yet"
        sleep 2
        ((attempt++))
    done

    die "$service failed to become healthy after $max_attempts attempts"
}

# =============================================================================
# Init Command
# =============================================================================

cmd_init() {
    log_info "Initializing CasareRPA deployment environment..."

    # Create directories
    mkdir -p "$DEPLOY_DIR" "$BACKUP_DIR" "$LOG_DIR"
    mkdir -p "${PROJECT_ROOT}/config/postgres/init"
    mkdir -p "${PROJECT_ROOT}/config/otel"
    mkdir -p "${PROJECT_ROOT}/config/prometheus"
    mkdir -p "${PROJECT_ROOT}/config/grafana/dashboards"
    mkdir -p "${PROJECT_ROOT}/config/grafana/datasources"
    mkdir -p "${PROJECT_ROOT}/config/nginx/conf.d"
    mkdir -p "${PROJECT_ROOT}/config/nginx/ssl"

    # Generate environment file if not exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_info "Generating environment file..."
        cat > "$ENV_FILE" << 'EOF'
# =============================================================================
# CasareRPA Production Environment
# =============================================================================

# Environment
ENVIRONMENT=production
CASARE_VERSION=3.0.0

# PostgreSQL
POSTGRES_USER=casare
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
POSTGRES_DB=casare_rpa
POSTGRES_PORT=5432
POSTGRES_SSL_ENABLED=true

# PgBouncer
PGBOUNCER_PORT=6432

# Orchestrator
ORCHESTRATOR_PORT=8080
ORCHESTRATOR_REPLICAS=1
API_WORKERS=4
API_RATE_LIMIT=100

# Robot
ROBOT_REPLICAS=2
ROBOT_BATCH_SIZE=1
ROBOT_POLL_INTERVAL=2.0
ROBOT_MAX_CONCURRENT=1

# Authentication
JWT_SECRET=CHANGE_ME_32_BYTE_SECRET_KEY_HERE

# Supabase (Optional)
SUPABASE_ENABLED=false
SUPABASE_URL=
SUPABASE_KEY=

# HashiCorp Vault (Optional)
VAULT_ADDR=
VAULT_TOKEN=
VAULT_ROLE_ID=
VAULT_SECRET_ID=

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=CHANGE_ME_GRAFANA_PASSWORD
GRAFANA_ROOT_URL=http://localhost:3000
GRAFANA_PORT=3000

# Jaeger
JAEGER_UI_PORT=16686

# Prometheus
PROMETHEUS_PORT=9090

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
        log_warn "Generated $ENV_FILE - Please update with production values!"
    fi

    # Create PostgreSQL init script
    cat > "${PROJECT_ROOT}/config/postgres/init/01-init.sql" << 'EOF'
-- CasareRPA Database Initialization

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Job Queue Table
CREATE TABLE IF NOT EXISTS job_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_json TEXT NOT NULL,
    priority INTEGER DEFAULT 1 CHECK (priority >= 0 AND priority <= 100),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    robot_id VARCHAR(255),
    environment VARCHAR(100) DEFAULT 'production',
    visible_after TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    result JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    variables JSONB DEFAULT '{}',
    correlation_id UUID,
    parent_job_id UUID REFERENCES job_queue(id),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for job claiming
CREATE INDEX IF NOT EXISTS idx_job_queue_claiming ON job_queue (status, visible_after, priority DESC)
    WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_job_queue_robot ON job_queue (robot_id, status)
    WHERE status = 'running';
CREATE INDEX IF NOT EXISTS idx_job_queue_workflow ON job_queue (workflow_id);
CREATE INDEX IF NOT EXISTS idx_job_queue_correlation ON job_queue (correlation_id)
    WHERE correlation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_job_queue_created ON job_queue (created_at DESC);

-- Robot Heartbeats Table
CREATE TABLE IF NOT EXISTS robot_heartbeats (
    robot_id VARCHAR(255) PRIMARY KEY,
    robot_name VARCHAR(255),
    environment VARCHAR(100) DEFAULT 'production',
    status VARCHAR(50) DEFAULT 'online',
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    current_job_id UUID REFERENCES job_queue(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_robot_heartbeats_status ON robot_heartbeats (status, last_heartbeat);

-- Workflow Definitions Table
CREATE TABLE IF NOT EXISTS workflow_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    workflow_json TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    UNIQUE (name, version)
);

CREATE INDEX IF NOT EXISTS idx_workflow_definitions_active ON workflow_definitions (is_active, name);

-- Schedule Definitions Table
CREATE TABLE IF NOT EXISTS schedule_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflow_definitions(id),
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(100) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT true,
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    environment VARCHAR(100) DEFAULT 'production',
    variables JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_schedule_definitions_next_run ON schedule_definitions (is_active, next_run_at);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    actor VARCHAR(255),
    actor_ip INET,
    details JSONB DEFAULT '{}',
    trace_id VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log (entity_type, entity_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for workflow_definitions
DROP TRIGGER IF EXISTS update_workflow_definitions_updated_at ON workflow_definitions;
CREATE TRIGGER update_workflow_definitions_updated_at
    BEFORE UPDATE ON workflow_definitions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grants (adjust as needed)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO casare_app;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO casare_app;
EOF

    # Create PostgreSQL config
    cat > "${PROJECT_ROOT}/config/postgres/postgresql.conf" << 'EOF'
# PostgreSQL Production Configuration

# Connection Settings
listen_addresses = '*'
port = 5432
max_connections = 200

# Memory Settings
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 32MB

# Write-Ahead Logging
wal_level = replica
max_wal_senders = 5
wal_keep_size = 1GB
hot_standby = on

# Checkpointing
checkpoint_completion_target = 0.9
checkpoint_timeout = 10min
max_wal_size = 2GB
min_wal_size = 512MB

# Query Tuning
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'ddl'
log_min_duration_statement = 1000
EOF

    # Create pg_hba.conf
    cat > "${PROJECT_ROOT}/config/postgres/pg_hba.conf" << 'EOF'
# PostgreSQL Client Authentication Configuration

# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
host    all             all             0.0.0.0/0               scram-sha-256
host    replication     all             0.0.0.0/0               scram-sha-256
EOF

    # Create OTel Collector config
    cat > "${PROJECT_ROOT}/config/otel/otel-collector-config.yaml" << 'EOF'
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

  memory_limiter:
    check_interval: 1s
    limit_mib: 1000
    spike_limit_mib: 200

  attributes:
    actions:
      - key: environment
        value: production
        action: upsert

exporters:
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true

  prometheus:
    endpoint: "0.0.0.0:8888"
    namespace: casare_rpa

  logging:
    loglevel: info

extensions:
  health_check:
    endpoint: 0.0.0.0:13133

service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, attributes]
      exporters: [otlp/jaeger, logging]

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]

    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [logging]
EOF

    # Create Prometheus config
    cat > "${PROJECT_ROOT}/config/prometheus/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - /etc/prometheus/alerts.yml

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8888']

  - job_name: 'casare-orchestrator'
    static_configs:
      - targets: ['orchestrator:8080']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-primary:5432']
EOF

    # Create Prometheus alerts
    cat > "${PROJECT_ROOT}/config/prometheus/alerts.yml" << 'EOF'
groups:
  - name: casare_rpa
    rules:
      - alert: HighQueueDepth
        expr: casare_rpa_queue_depth > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High job queue depth"
          description: "Job queue depth is {{ $value }} jobs"

      - alert: RobotOffline
        expr: time() - casare_rpa_robot_last_heartbeat > 120
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Robot offline"
          description: "Robot {{ $labels.robot_id }} has not sent heartbeat"

      - alert: HighErrorRate
        expr: rate(casare_rpa_error_count[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate"
          description: "Error rate is {{ $value }} errors/second"

      - alert: JobExecutionTimeout
        expr: casare_rpa_job_duration_seconds > 3600
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Job execution timeout"
          description: "Job {{ $labels.job_id }} running for > 1 hour"
EOF

    # Create Grafana datasources
    cat > "${PROJECT_ROOT}/config/grafana/datasources/datasources.yaml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
EOF

    # Generate SSL certificates for development
    if [[ ! -f "${PROJECT_ROOT}/config/nginx/ssl/server.crt" ]]; then
        log_info "Generating self-signed SSL certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "${PROJECT_ROOT}/config/nginx/ssl/server.key" \
            -out "${PROJECT_ROOT}/config/nginx/ssl/server.crt" \
            -subj "/CN=localhost" 2>/dev/null
        log_warn "Generated self-signed certificates - Replace with proper certs for production!"
    fi

    # Create nginx config
    cat > "${PROJECT_ROOT}/config/nginx/nginx.conf" << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;

    include /etc/nginx/conf.d/*.conf;
}
EOF

    cat > "${PROJECT_ROOT}/config/nginx/conf.d/default.conf" << 'EOF'
upstream orchestrator {
    server orchestrator:8080;
}

upstream grafana {
    server grafana:3000;
}

server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://orchestrator/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://orchestrator/health;
    }

    # Grafana
    location /grafana/ {
        proxy_pass http://grafana/;
        proxy_set_header Host $host;
    }
}
EOF

    log_success "Environment initialized successfully!"
    log_info "Next steps:"
    log_info "  1. Edit $ENV_FILE with production values"
    log_info "  2. Run: ./deploy.sh deploy"
}

# =============================================================================
# Deploy Commands
# =============================================================================

cmd_deploy() {
    log_info "Deploying CasareRPA stack..."

    check_requirements
    load_env

    # Validate environment
    [[ -z "${POSTGRES_PASSWORD:-}" ]] && die "POSTGRES_PASSWORD is required"
    [[ -z "${JWT_SECRET:-}" ]] && die "JWT_SECRET is required"
    [[ -z "${GRAFANA_ADMIN_PASSWORD:-}" ]] && die "GRAFANA_ADMIN_PASSWORD is required"

    # Pull latest images
    log_info "Pulling latest images..."
    run_cmd "docker_compose pull"

    # Start services in order
    cmd_deploy_db
    cmd_deploy_orch
    cmd_deploy_robot
    cmd_deploy_mon

    log_success "CasareRPA stack deployed successfully!"
    cmd_status
}

cmd_deploy_db() {
    log_info "Deploying database..."

    run_cmd "docker_compose up -d postgres-primary pgbouncer"
    wait_for_service "postgres-primary"
    wait_for_service "pgbouncer"

    log_success "Database deployed"
}

cmd_deploy_orch() {
    log_info "Deploying orchestrator..."

    run_cmd "docker_compose up -d orchestrator"
    wait_for_service "orchestrator"

    log_success "Orchestrator deployed"
}

cmd_deploy_robot() {
    log_info "Deploying robot agents..."

    run_cmd "docker_compose up -d robot"

    log_success "Robot agents deployed"
}

cmd_deploy_mon() {
    log_info "Deploying monitoring stack..."

    run_cmd "docker_compose up -d otel-collector jaeger prometheus grafana nginx"
    wait_for_service "prometheus"
    wait_for_service "grafana"

    log_success "Monitoring stack deployed"
}

# =============================================================================
# Status Command
# =============================================================================

cmd_status() {
    log_info "Service Status:"
    echo ""
    docker_compose ps
    echo ""

    log_info "Service URLs:"
    echo "  Orchestrator API: https://localhost/api/"
    echo "  Grafana:          https://localhost/grafana/"
    echo "  Jaeger UI:        http://localhost:${JAEGER_UI_PORT:-16686}"
    echo "  Prometheus:       http://localhost:${PROMETHEUS_PORT:-9090}"
}

# =============================================================================
# Logs Command
# =============================================================================

cmd_logs() {
    local service="${1:-}"

    if [[ -n "$service" ]]; then
        docker_compose logs -f "$service"
    else
        docker_compose logs -f
    fi
}

# =============================================================================
# Backup Command
# =============================================================================

cmd_backup() {
    local backup_name="casare_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_file="${BACKUP_DIR}/${backup_name}.sql.gz"

    log_info "Creating database backup..."

    mkdir -p "$BACKUP_DIR"

    docker_compose exec -T postgres-primary pg_dump -U "${POSTGRES_USER:-casare}" "${POSTGRES_DB:-casare_rpa}" | gzip > "$backup_file"

    log_success "Backup created: $backup_file"

    # Cleanup old backups (keep last 30)
    log_info "Cleaning up old backups..."
    ls -t "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm -f
}

# =============================================================================
# Restore Command
# =============================================================================

cmd_restore() {
    local backup_file="${1:-}"

    if [[ -z "$backup_file" ]]; then
        log_info "Available backups:"
        ls -lt "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | head -10
        die "Usage: deploy.sh restore <backup_file>"
    fi

    [[ -f "$backup_file" ]] || die "Backup file not found: $backup_file"

    log_warn "This will REPLACE the current database. Are you sure? (yes/no)"
    read -r confirm
    [[ "$confirm" == "yes" ]] || die "Restore cancelled"

    log_info "Restoring from backup..."

    gunzip -c "$backup_file" | docker_compose exec -T postgres-primary psql -U "${POSTGRES_USER:-casare}" "${POSTGRES_DB:-casare_rpa}"

    log_success "Database restored from $backup_file"
}

# =============================================================================
# Upgrade Command
# =============================================================================

cmd_upgrade() {
    local new_version="${1:-}"

    [[ -n "$new_version" ]] || die "Usage: deploy.sh upgrade <version>"

    log_info "Upgrading to version $new_version..."

    # Create backup first
    cmd_backup

    # Update version in env file
    sed -i "s/CASARE_VERSION=.*/CASARE_VERSION=$new_version/" "$ENV_FILE"

    # Pull new images
    log_info "Pulling new images..."
    run_cmd "docker_compose pull"

    # Rolling update
    log_info "Performing rolling update..."
    run_cmd "docker_compose up -d --no-deps orchestrator"
    wait_for_service "orchestrator"

    run_cmd "docker_compose up -d --no-deps robot"

    log_success "Upgrade to $new_version complete"
}

# =============================================================================
# Rollback Command
# =============================================================================

cmd_rollback() {
    local backup_file="${1:-}"

    if [[ -z "$backup_file" ]]; then
        log_info "Latest backups:"
        ls -lt "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | head -5
        die "Usage: deploy.sh rollback <backup_file>"
    fi

    log_info "Rolling back..."

    cmd_restore "$backup_file"

    log_success "Rollback complete"
}

# =============================================================================
# Health Command
# =============================================================================

cmd_health() {
    log_info "Checking system health..."
    echo ""

    # Check each service
    local services=("postgres-primary" "pgbouncer" "orchestrator" "otel-collector" "prometheus" "grafana")

    for service in "${services[@]}"; do
        if docker_compose ps "$service" 2>/dev/null | grep -q "healthy\|running"; then
            echo -e "  ${GREEN}[OK]${NC} $service"
        else
            echo -e "  ${RED}[FAIL]${NC} $service"
        fi
    done

    echo ""

    # Check API health
    log_info "API Health Check:"
    curl -sf http://localhost:8080/health 2>/dev/null | head -c 200 || echo "API not responding"
    echo ""
}

# =============================================================================
# Clean Command
# =============================================================================

cmd_clean() {
    log_warn "This will stop and remove all containers, networks, and volumes."
    log_warn "Data will be PERMANENTLY DELETED. Are you sure? (yes/no)"
    read -r confirm
    [[ "$confirm" == "yes" ]] || die "Clean cancelled"

    log_info "Stopping and removing all resources..."

    run_cmd "docker_compose down -v --remove-orphans"

    log_success "Cleanup complete"
}

# =============================================================================
# Help
# =============================================================================

show_help() {
    head -50 "$0" | tail -n +2 | sed 's/^# //' | sed 's/^#//'
}

# =============================================================================
# Main
# =============================================================================

main() {
    # Parse options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            -c|--config)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done

    local command="${1:-help}"
    shift || true

    case "$command" in
        init)
            cmd_init "$@"
            ;;
        deploy)
            cmd_deploy "$@"
            ;;
        deploy-db)
            load_env
            cmd_deploy_db "$@"
            ;;
        deploy-orch)
            load_env
            cmd_deploy_orch "$@"
            ;;
        deploy-robot)
            load_env
            cmd_deploy_robot "$@"
            ;;
        deploy-mon)
            load_env
            cmd_deploy_mon "$@"
            ;;
        status)
            load_env
            cmd_status "$@"
            ;;
        logs)
            load_env
            cmd_logs "$@"
            ;;
        backup)
            load_env
            cmd_backup "$@"
            ;;
        restore)
            load_env
            cmd_restore "$@"
            ;;
        upgrade)
            load_env
            cmd_upgrade "$@"
            ;;
        rollback)
            load_env
            cmd_rollback "$@"
            ;;
        health)
            load_env
            cmd_health "$@"
            ;;
        clean)
            load_env
            cmd_clean "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            die "Unknown command: $command. Use --help for usage."
            ;;
    esac
}

main "$@"
