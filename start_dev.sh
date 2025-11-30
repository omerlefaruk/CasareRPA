#!/bin/bash
# ===================================================================
# CasareRPA Enterprise Platform - Linux/Mac Startup Script
# ===================================================================
# Starts all platform components in background with proper logging
#
# Components:
#   1. Orchestrator API (FastAPI) - Port 8000
#   2. Monitoring Dashboard (React/Vite) - Port 5173
#   3. Robot Agent (optional - run manually if needed)
#
# Prerequisites:
#   - Python 3.12+ with casare_rpa installed
#   - Node.js 18+ with monitoring-dashboard dependencies installed
#   - PostgreSQL 15+ running (or set USE_MEMORY_QUEUE=true)
#
# Usage:
#   ./start_dev.sh          # Start platform
#   ./start_dev.sh stop     # Stop all components
#   ./start_dev.sh status   # Check component status
# ===================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log files
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
API_LOG="$LOG_DIR/orchestrator_api.log"
DASHBOARD_LOG="$LOG_DIR/dashboard.log"
PID_FILE="$LOG_DIR/platform.pid"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

check_dependencies() {
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found! Please install Python 3.12+"
        exit 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found! Please install Node.js 18+"
        exit 1
    fi

    print_success "Dependencies check passed"
}

start_platform() {
    print_header "CasareRPA Enterprise Platform"
    echo ""

    check_dependencies

    # Check if already running
    if [ -f "$PID_FILE" ]; then
        print_error "Platform already running! Use './start_dev.sh stop' first"
        exit 1
    fi

    # Start Orchestrator API
    print_info "Starting Orchestrator API (port 8000)..."
    python3 -m uvicorn casare_rpa.infrastructure.orchestrator.api.main:app \
        --host 0.0.0.0 --port 8000 \
        > "$API_LOG" 2>&1 &
    API_PID=$!
    echo "API_PID=$API_PID" > "$PID_FILE"

    # Wait for API to start
    sleep 3

    if ps -p $API_PID > /dev/null; then
        print_success "Orchestrator API started (PID: $API_PID)"
    else
        print_error "Failed to start Orchestrator API. Check $API_LOG"
        rm -f "$PID_FILE"
        exit 1
    fi

    # Start Monitoring Dashboard
    print_info "Starting Monitoring Dashboard (port 5173)..."

    # Check if node_modules exists
    if [ ! -d "monitoring-dashboard/node_modules" ]; then
        print_info "Installing dashboard dependencies..."
        cd monitoring-dashboard
        npm install
        cd ..
    fi

    cd monitoring-dashboard
    npm run dev > "../$DASHBOARD_LOG" 2>&1 &
    DASHBOARD_PID=$!
    cd ..

    echo "DASHBOARD_PID=$DASHBOARD_PID" >> "$PID_FILE"

    # Wait for dashboard to start
    sleep 2

    if ps -p $DASHBOARD_PID > /dev/null; then
        print_success "Monitoring Dashboard started (PID: $DASHBOARD_PID)"
    else
        print_error "Failed to start Dashboard. Check $DASHBOARD_LOG"
        kill $API_PID 2>/dev/null || true
        rm -f "$PID_FILE"
        exit 1
    fi

    echo ""
    print_header "Platform Started Successfully!"
    echo ""
    echo -e "${GREEN}Orchestrator API:${NC}       http://localhost:8000"
    echo "  - Health Check:       http://localhost:8000/health"
    echo "  - API Docs:           http://localhost:8000/docs"
    echo ""
    echo -e "${GREEN}Monitoring Dashboard:${NC}   http://localhost:5173"
    echo "  - Real-time updates via WebSocket"
    echo ""
    echo -e "${YELLOW}Logs:${NC}"
    echo "  - API:                $API_LOG"
    echo "  - Dashboard:          $DASHBOARD_LOG"
    echo ""
    echo -e "${YELLOW}Optional Components:${NC}"
    echo "  - Canvas Designer:    python run.py"
    echo "  - Robot Agent:        python -m casare_rpa.robot.cli start"
    echo ""
    echo -e "${BLUE}To stop the platform:${NC} ./start_dev.sh stop"
    echo ""
}

stop_platform() {
    print_header "Stopping CasareRPA Platform"
    echo ""

    if [ ! -f "$PID_FILE" ]; then
        print_error "Platform not running (no PID file found)"
        exit 1
    fi

    # Read PIDs
    source "$PID_FILE"

    # Stop API
    if [ -n "$API_PID" ]; then
        if ps -p $API_PID > /dev/null; then
            kill $API_PID
            print_success "Stopped Orchestrator API (PID: $API_PID)"
        else
            print_info "Orchestrator API already stopped"
        fi
    fi

    # Stop Dashboard
    if [ -n "$DASHBOARD_PID" ]; then
        if ps -p $DASHBOARD_PID > /dev/null; then
            kill $DASHBOARD_PID
            # Also kill the Vite dev server child process
            pkill -P $DASHBOARD_PID 2>/dev/null || true
            print_success "Stopped Monitoring Dashboard (PID: $DASHBOARD_PID)"
        else
            print_info "Monitoring Dashboard already stopped"
        fi
    fi

    rm -f "$PID_FILE"
    print_success "Platform stopped"
    echo ""
}

status_platform() {
    print_header "CasareRPA Platform Status"
    echo ""

    if [ ! -f "$PID_FILE" ]; then
        print_error "Platform not running (no PID file found)"
        echo ""
        echo "Start with: ./start_dev.sh"
        exit 1
    fi

    # Read PIDs
    source "$PID_FILE"

    # Check API
    if [ -n "$API_PID" ] && ps -p $API_PID > /dev/null; then
        print_success "Orchestrator API running (PID: $API_PID)"
        echo "         URL: http://localhost:8000"
    else
        print_error "Orchestrator API not running"
    fi

    # Check Dashboard
    if [ -n "$DASHBOARD_PID" ] && ps -p $DASHBOARD_PID > /dev/null; then
        print_success "Monitoring Dashboard running (PID: $DASHBOARD_PID)"
        echo "         URL: http://localhost:5173"
    else
        print_error "Monitoring Dashboard not running"
    fi

    echo ""
}

# Main script
case "${1:-start}" in
    start)
        start_platform
        ;;
    stop)
        stop_platform
        ;;
    status)
        status_platform
        ;;
    restart)
        stop_platform
        sleep 2
        start_platform
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  start    - Start platform components"
        echo "  stop     - Stop all components"
        echo "  status   - Check component status"
        echo "  restart  - Restart all components"
        exit 1
        ;;
esac
