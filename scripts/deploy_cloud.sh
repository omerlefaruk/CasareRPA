#!/usr/bin/env bash
# =============================================================================
# CasareRPA DBOS Cloud Deployment Script
# =============================================================================
#
# One-command deployment to DBOS Cloud with auto-scaling, managed PostgreSQL,
# and zero-downtime deployments.
#
# Usage:
#   ./scripts/deploy_cloud.sh --app casare-rpa --env production
#   ./scripts/deploy_cloud.sh --app casare-rpa --env staging --dry-run
#   ./scripts/deploy_cloud.sh status --app casare-rpa
#   ./scripts/deploy_cloud.sh logs --app casare-rpa --tail 100
#
# Commands:
#   deploy        Deploy application to DBOS Cloud (default)
#   status        Show deployment status
#   logs          Show application logs
#   scale         Configure auto-scaling
#   rollback      Rollback to previous version
#   destroy       Destroy deployment (DANGEROUS)
#   health        Check application health
#   env           Manage environment variables
#   db            Manage PostgreSQL database
#
# Options:
#   -a, --app NAME        Application name (default: casare-rpa)
#   -e, --env ENV         Environment: production, staging, development
#   -c, --config FILE     Config file (default: dbos-config.yaml)
#   -t, --token TOKEN     DBOS Cloud API token (or use DBOS_CLOUD_TOKEN env)
#   -n, --dry-run         Validate without deploying
#   -f, --force           Skip confirmation prompts
#   -v, --verbose         Enable verbose output
#   -h, --help            Show this help message
#
# Environment Variables:
#   DBOS_CLOUD_TOKEN      API token for authentication
#   SUPABASE_URL          Supabase project URL
#   SUPABASE_KEY          Supabase service role key
#   JWT_SECRET            JWT signing secret
#   VAULT_ADDR            HashiCorp Vault address
#   VAULT_ROLE_ID         Vault AppRole ID
#   VAULT_SECRET_ID       Vault AppRole secret
#
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
APP_NAME="casare-rpa"
ENVIRONMENT="production"
CONFIG_FILE="${PROJECT_ROOT}/dbos-config.yaml"
DBOS_TOKEN="${DBOS_CLOUD_TOKEN:-}"
DRY_RUN=false
FORCE=false
VERBOSE=false

# DBOS CLI
DBOS_CLI="dbos-cloud"
DBOS_NPM_PACKAGE="@dbos-inc/dbos-cloud"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

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
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

die() {
    log_error "$1"
    exit 1
}

confirm() {
    local prompt="$1"
    if [[ "$FORCE" == "true" ]]; then
        return 0
    fi
    read -rp "$prompt [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]]
}

run_cmd() {
    local cmd="$*"
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would execute: $cmd"
        return 0
    fi
    log_debug "Executing: $cmd"
    eval "$cmd"
}

# =============================================================================
# DBOS CLI Management
# =============================================================================

check_dbos_cli() {
    if command -v "$DBOS_CLI" &> /dev/null; then
        log_debug "DBOS Cloud CLI found"
        return 0
    fi
    return 1
}

install_dbos_cli() {
    log_info "Installing DBOS Cloud CLI..."

    if ! command -v npm &> /dev/null; then
        die "npm not found. Please install Node.js and npm first."
    fi

    npm install -g "$DBOS_NPM_PACKAGE" || die "Failed to install DBOS Cloud CLI"
    log_success "DBOS Cloud CLI installed successfully"
}

ensure_dbos_cli() {
    if ! check_dbos_cli; then
        log_warn "DBOS Cloud CLI not found"
        if confirm "Install DBOS Cloud CLI now?"; then
            install_dbos_cli
        else
            die "DBOS Cloud CLI is required. Install with: npm install -g $DBOS_NPM_PACKAGE"
        fi
    fi
}

# =============================================================================
# Authentication
# =============================================================================

dbos_login() {
    log_info "Authenticating with DBOS Cloud..."

    if [[ -n "$DBOS_TOKEN" ]]; then
        run_cmd "$DBOS_CLI login --token '$DBOS_TOKEN'"
    else
        run_cmd "$DBOS_CLI login"
    fi

    log_success "Authentication successful"
}

check_auth() {
    # Try to list apps to check if authenticated
    if ! $DBOS_CLI app list &> /dev/null; then
        log_warn "Not authenticated with DBOS Cloud"
        dbos_login
    fi
}

# =============================================================================
# Configuration Loading
# =============================================================================

load_config() {
    local env_config="${PROJECT_ROOT}/dbos-config.${ENVIRONMENT}.yaml"

    # Check for environment-specific config
    if [[ -f "$env_config" ]]; then
        CONFIG_FILE="$env_config"
        log_info "Using environment config: $CONFIG_FILE"
    elif [[ ! -f "$CONFIG_FILE" ]]; then
        die "Config file not found: $CONFIG_FILE"
    fi

    log_debug "Loading configuration from $CONFIG_FILE"
}

# Build environment variable arguments
build_env_args() {
    local env_args=""

    # Required secrets
    if [[ -n "${JWT_SECRET:-}" ]]; then
        env_args+=" --env JWT_SECRET='$JWT_SECRET'"
    fi

    # Supabase configuration
    if [[ -n "${SUPABASE_URL:-}" ]]; then
        env_args+=" --env SUPABASE_URL='$SUPABASE_URL'"
    fi
    if [[ -n "${SUPABASE_KEY:-}" ]]; then
        env_args+=" --env SUPABASE_KEY='$SUPABASE_KEY'"
    fi

    # Vault configuration
    if [[ -n "${VAULT_ADDR:-}" ]]; then
        env_args+=" --env VAULT_ADDR='$VAULT_ADDR'"
    fi
    if [[ -n "${VAULT_ROLE_ID:-}" ]]; then
        env_args+=" --env VAULT_ROLE_ID='$VAULT_ROLE_ID'"
    fi
    if [[ -n "${VAULT_SECRET_ID:-}" ]]; then
        env_args+=" --env VAULT_SECRET_ID='$VAULT_SECRET_ID'"
    fi

    # Environment identifier
    env_args+=" --env ENVIRONMENT='$ENVIRONMENT'"
    env_args+=" --env OTEL_DEPLOYMENT_ENVIRONMENT='$ENVIRONMENT'"

    echo "$env_args"
}

# =============================================================================
# Deploy Command
# =============================================================================

cmd_deploy() {
    log_info "Deploying $APP_NAME to $ENVIRONMENT..."

    ensure_dbos_cli
    check_auth
    load_config

    # Build deploy command
    local cmd="$DBOS_CLI app deploy --app '$APP_NAME'"

    # Add PostgreSQL if configured
    cmd+=" --postgres"

    # Add environment variables
    cmd+=$(build_env_args)

    # Add dry-run flag
    if [[ "$DRY_RUN" == "true" ]]; then
        cmd+=" --dry-run"
    fi

    log_info "Starting deployment..."
    run_cmd "$cmd"

    if [[ "$DRY_RUN" != "true" ]]; then
        # Configure auto-scaling
        cmd_scale_internal

        log_success "Deployment completed successfully!"
        echo ""
        cmd_status
    else
        log_info "Dry run completed. No changes made."
    fi
}

# =============================================================================
# Status Command
# =============================================================================

cmd_status() {
    log_info "Checking status of $APP_NAME..."

    ensure_dbos_cli
    check_auth

    echo ""
    echo "=============================================="
    echo "  $APP_NAME - $ENVIRONMENT"
    echo "=============================================="
    echo ""

    $DBOS_CLI app status --app "$APP_NAME" 2>/dev/null || {
        log_warn "Could not retrieve status. App may not be deployed."
        return 1
    }

    echo ""

    # Show health check
    local url
    url=$($DBOS_CLI app status --app "$APP_NAME" --output json 2>/dev/null | grep -o '"url":"[^"]*"' | cut -d'"' -f4 || echo "")

    if [[ -n "$url" ]]; then
        log_info "Application URL: $url"
        log_info "Health endpoint: ${url}/health"
    fi
}

# =============================================================================
# Logs Command
# =============================================================================

cmd_logs() {
    local tail="${1:-100}"
    local follow="${2:-false}"

    log_info "Retrieving logs for $APP_NAME..."

    ensure_dbos_cli
    check_auth

    local cmd="$DBOS_CLI app logs --app '$APP_NAME' --tail $tail"

    if [[ "$follow" == "true" ]]; then
        cmd+=" --follow"
    fi

    run_cmd "$cmd"
}

# =============================================================================
# Scale Command
# =============================================================================

cmd_scale() {
    local min_instances="${1:-2}"
    local max_instances="${2:-10}"
    local target_cpu="${3:-70}"

    log_info "Configuring auto-scaling for $APP_NAME..."

    ensure_dbos_cli
    check_auth

    run_cmd "$DBOS_CLI app scale --app '$APP_NAME' \
        --min-instances $min_instances \
        --max-instances $max_instances \
        --target-cpu $target_cpu"

    log_success "Auto-scaling configured: min=$min_instances, max=$max_instances, target_cpu=$target_cpu%"
}

cmd_scale_internal() {
    # Default scaling based on environment
    local min_instances max_instances target_cpu

    case "$ENVIRONMENT" in
        production)
            min_instances=2
            max_instances=10
            target_cpu=70
            ;;
        staging)
            min_instances=1
            max_instances=3
            target_cpu=70
            ;;
        *)
            min_instances=1
            max_instances=2
            target_cpu=80
            ;;
    esac

    log_info "Applying auto-scaling configuration..."
    cmd_scale "$min_instances" "$max_instances" "$target_cpu"
}

# =============================================================================
# Rollback Command
# =============================================================================

cmd_rollback() {
    local version="${1:-}"

    log_warn "Rolling back $APP_NAME..."

    if ! confirm "Are you sure you want to rollback $APP_NAME?"; then
        log_info "Rollback cancelled"
        return 0
    fi

    ensure_dbos_cli
    check_auth

    local cmd="$DBOS_CLI app rollback --app '$APP_NAME'"

    if [[ -n "$version" ]]; then
        cmd+=" --version '$version'"
    fi

    run_cmd "$cmd"
    log_success "Rollback completed"

    cmd_status
}

# =============================================================================
# Destroy Command
# =============================================================================

cmd_destroy() {
    log_error "WARNING: This will permanently destroy $APP_NAME and all its data!"
    echo ""

    if ! confirm "Type 'yes' to confirm destruction of $APP_NAME:"; then
        log_info "Destroy cancelled"
        return 0
    fi

    ensure_dbos_cli
    check_auth

    run_cmd "$DBOS_CLI app destroy --app '$APP_NAME' --force"
    log_success "$APP_NAME has been destroyed"
}

# =============================================================================
# Health Command
# =============================================================================

cmd_health() {
    log_info "Checking health of $APP_NAME..."

    ensure_dbos_cli
    check_auth

    # Get app URL
    local url
    url=$($DBOS_CLI app status --app "$APP_NAME" --output json 2>/dev/null | grep -o '"url":"[^"]*"' | cut -d'"' -f4 || echo "")

    if [[ -z "$url" ]]; then
        die "Could not retrieve application URL"
    fi

    local health_url="${url}/health"
    log_info "Health check URL: $health_url"

    # Perform health check
    local response
    response=$(curl -sf "$health_url" 2>/dev/null) || {
        log_error "Health check failed"
        return 1
    }

    echo ""
    echo "Health Check Response:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""

    log_success "Application is healthy"
}

# =============================================================================
# Environment Variables Command
# =============================================================================

cmd_env() {
    local action="${1:-list}"
    shift || true

    ensure_dbos_cli
    check_auth

    case "$action" in
        list)
            log_info "Environment variables for $APP_NAME:"
            run_cmd "$DBOS_CLI app env list --app '$APP_NAME'"
            ;;
        set)
            local name="$1"
            local value="$2"
            local secret="${3:-false}"

            if [[ -z "$name" || -z "$value" ]]; then
                die "Usage: deploy_cloud.sh env set NAME VALUE [--secret]"
            fi

            local cmd="$DBOS_CLI app env set --app '$APP_NAME' '$name' '$value'"
            if [[ "$secret" == "--secret" || "$secret" == "true" ]]; then
                cmd+=" --secret"
            fi

            run_cmd "$cmd"
            log_success "Environment variable $name set successfully"
            ;;
        unset)
            local name="$1"
            if [[ -z "$name" ]]; then
                die "Usage: deploy_cloud.sh env unset NAME"
            fi

            run_cmd "$DBOS_CLI app env unset --app '$APP_NAME' '$name'"
            log_success "Environment variable $name removed"
            ;;
        *)
            die "Unknown env action: $action. Use: list, set, unset"
            ;;
    esac
}

# =============================================================================
# Database Command
# =============================================================================

cmd_db() {
    local action="${1:-status}"
    shift || true

    ensure_dbos_cli
    check_auth

    case "$action" in
        status)
            log_info "PostgreSQL status for $APP_NAME:"
            run_cmd "$DBOS_CLI db status --app '$APP_NAME'"
            ;;
        connection-string)
            log_info "PostgreSQL connection string:"
            run_cmd "$DBOS_CLI db connection-string --app '$APP_NAME'"
            ;;
        backup)
            log_info "Creating database backup..."
            run_cmd "$DBOS_CLI db backup --app '$APP_NAME'"
            log_success "Backup created"
            ;;
        restore)
            local backup_id="$1"
            if [[ -z "$backup_id" ]]; then
                die "Usage: deploy_cloud.sh db restore BACKUP_ID"
            fi

            if ! confirm "Restore database from backup $backup_id?"; then
                log_info "Restore cancelled"
                return 0
            fi

            run_cmd "$DBOS_CLI db restore --app '$APP_NAME' --backup-id '$backup_id'"
            log_success "Database restored"
            ;;
        *)
            die "Unknown db action: $action. Use: status, connection-string, backup, restore"
            ;;
    esac
}

# =============================================================================
# Metrics Command
# =============================================================================

cmd_metrics() {
    local time_range="${1:-1h}"

    log_info "Retrieving metrics for $APP_NAME (last $time_range)..."

    ensure_dbos_cli
    check_auth

    run_cmd "$DBOS_CLI app metrics --app '$APP_NAME' --range '$time_range'"
}

# =============================================================================
# Help
# =============================================================================

show_help() {
    head -60 "$0" | tail -n +2 | sed 's/^# //' | sed 's/^#//'
}

show_usage() {
    echo "Usage: deploy_cloud.sh [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy       Deploy application (default)"
    echo "  status       Show deployment status"
    echo "  logs         Show application logs"
    echo "  scale        Configure auto-scaling"
    echo "  rollback     Rollback to previous version"
    echo "  health       Check application health"
    echo "  env          Manage environment variables"
    echo "  db           Manage PostgreSQL database"
    echo "  metrics      Show application metrics"
    echo "  destroy      Destroy deployment"
    echo ""
    echo "Options:"
    echo "  -a, --app NAME     Application name (default: casare-rpa)"
    echo "  -e, --env ENV      Environment (default: production)"
    echo "  -n, --dry-run      Validate without deploying"
    echo "  -v, --verbose      Enable verbose output"
    echo "  -h, --help         Show full help"
    echo ""
    echo "Examples:"
    echo "  ./deploy_cloud.sh --app casare-rpa --env production"
    echo "  ./deploy_cloud.sh status --app casare-rpa"
    echo "  ./deploy_cloud.sh logs --app casare-rpa --tail 100"
}

# =============================================================================
# Main
# =============================================================================

main() {
    local command="deploy"
    local extra_args=()

    # Parse options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -a|--app)
                APP_NAME="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -t|--token)
                DBOS_TOKEN="$2"
                shift 2
                ;;
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -f|--force)
                FORCE=true
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
            --tail)
                extra_args+=("$2")
                shift 2
                ;;
            --follow)
                extra_args+=("true")
                shift
                ;;
            --min-instances)
                extra_args+=("$2")
                shift 2
                ;;
            --max-instances)
                extra_args+=("$2")
                shift 2
                ;;
            --target-cpu)
                extra_args+=("$2")
                shift 2
                ;;
            --range)
                extra_args+=("$2")
                shift 2
                ;;
            deploy|status|logs|scale|rollback|destroy|health|env|db|metrics)
                command="$1"
                shift
                ;;
            *)
                extra_args+=("$1")
                shift
                ;;
        esac
    done

    # Validate environment
    case "$ENVIRONMENT" in
        production|staging|development)
            ;;
        *)
            die "Invalid environment: $ENVIRONMENT. Use: production, staging, development"
            ;;
    esac

    log_info "CasareRPA DBOS Cloud Deployment"
    log_info "App: $APP_NAME | Environment: $ENVIRONMENT"
    echo ""

    # Execute command
    case "$command" in
        deploy)
            cmd_deploy
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs "${extra_args[@]:-100}" "${extra_args[1]:-false}"
            ;;
        scale)
            if [[ ${#extra_args[@]} -ge 3 ]]; then
                cmd_scale "${extra_args[0]}" "${extra_args[1]}" "${extra_args[2]}"
            else
                cmd_scale_internal
            fi
            ;;
        rollback)
            cmd_rollback "${extra_args[0]:-}"
            ;;
        destroy)
            cmd_destroy
            ;;
        health)
            cmd_health
            ;;
        env)
            cmd_env "${extra_args[@]}"
            ;;
        db)
            cmd_db "${extra_args[@]}"
            ;;
        metrics)
            cmd_metrics "${extra_args[0]:-1h}"
            ;;
        *)
            show_usage
            die "Unknown command: $command"
            ;;
    esac
}

main "$@"
