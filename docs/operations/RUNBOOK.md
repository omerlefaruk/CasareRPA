# CasareRPA Operations Runbook

This runbook provides operational procedures for running CasareRPA in production environments.

## Table of Contents

- [Startup Procedures](#startup-procedures)
- [Shutdown Procedures](#shutdown-procedures)
- [Scaling](#scaling)
- [Monitoring](#monitoring)
- [Backup](#backup)
- [Recovery](#recovery)

---

## Startup Procedures

### Canvas Application Startup

The Canvas is the visual workflow designer (GUI application).

#### Prerequisites

- Windows 10/11 with Python 3.12+
- PySide6 installed
- Display available (not headless)

#### Startup Command

```powershell
# Standard startup
python run.py

# With debug logging
set CASARE_LOG_LEVEL=DEBUG
python run.py

# Alternative using module
python -m casare_rpa.presentation.canvas
```

#### Startup Verification

1. Main window appears within 5 seconds
2. Status bar shows "Ready"
3. Node palette loads in left panel
4. No error dialogs appear

#### Common Startup Issues

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Black window | GPU driver issue | Set `QT_OPENGL=software` |
| Missing fonts | Font not installed | Install Segoe UI fonts |
| Crash on load | Corrupted settings | Delete `%APPDATA%\CasareRPA\settings.json` |

---

### Robot Agent Startup

Robot agents execute workflows assigned by the Orchestrator.

#### Environment Variables

```powershell
# Required
$env:CASARE_ROBOT_NAME = "robot-prod-01"
$env:CASARE_CONTROL_PLANE_URL = "wss://orchestrator.example.com/ws/robot"
$env:CASARE_API_KEY = "crpa_your_api_key_here"

# Optional
$env:CASARE_ROBOT_ID = "robot-prod-01"
$env:CASARE_HEARTBEAT_INTERVAL = "30"
$env:CASARE_MAX_CONCURRENT_JOBS = "1"
$env:CASARE_CAPABILITIES = "browser,desktop"
$env:CASARE_TAGS = "production,windows"
$env:CASARE_ENVIRONMENT = "production"
$env:CASARE_LOG_LEVEL = "INFO"
$env:CASARE_JOB_TIMEOUT = "3600"
```

#### Startup Command

```powershell
# Using CLI
python -m casare_rpa.robot.cli start

# Using environment variables
python -c "
import asyncio
from casare_rpa.infrastructure.agent import RobotAgent, RobotConfig

config = RobotConfig.from_env()
agent = RobotAgent(config)
asyncio.run(agent.start())
"

# As Windows Service (recommended for production)
# Use NSSM or similar to wrap the command
nssm install CasareRobotAgent python -m casare_rpa.robot.cli start
nssm start CasareRobotAgent
```

#### Startup Verification

Check these in logs:

```
INFO | Starting robot agent: robot-prod-01 (ID: robot-prod-01)
INFO | Control plane: wss://orchestrator.example.com/ws/robot
INFO | Capabilities: browser, desktop
INFO | Connecting to orchestrator...
INFO | Connected to orchestrator
INFO | Registering with orchestrator...
INFO | Registered with orchestrator as: robot-prod-01
```

---

### Orchestrator Startup

The Orchestrator manages robot fleet and job distribution.

#### Environment Variables

```bash
# Required
export HOST=0.0.0.0
export PORT=8000
export API_SECRET=your_secure_secret

# Optional - Database
export DATABASE_URL=postgresql://user:pass@host:5432/casare
export SUPABASE_URL=https://xxx.supabase.co
export SUPABASE_KEY=your_supabase_key

# Optional - Configuration
export WORKERS=4
export CORS_ORIGINS=https://dashboard.example.com,https://admin.example.com
export ROBOT_HEARTBEAT_TIMEOUT=90
export JOB_TIMEOUT_DEFAULT=3600
export WS_PING_INTERVAL=30

# Optional - Redis Queue
export REDIS_URL=redis://localhost:6379/0
```

#### Startup Command

```bash
# Development
python -m casare_rpa.infrastructure.orchestrator.server

# Production with uvicorn
uvicorn casare_rpa.infrastructure.orchestrator.server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info

# With gunicorn (recommended)
gunicorn casare_rpa.infrastructure.orchestrator.server:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

#### Docker Startup

```yaml
# docker-compose.yml
version: '3.8'
services:
  orchestrator:
    image: casare-rpa/orchestrator:latest
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - API_SECRET=${API_SECRET}
      - DATABASE_URL=${DATABASE_URL}
      - CORS_ORIGINS=*
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

### Health Check Verification

After all components are started, verify health:

#### Orchestrator Health Endpoints

```bash
# Basic health
curl http://orchestrator:8000/health
# Expected: {"status": "healthy", "service": "casare-orchestrator"}

# Liveness probe (Kubernetes)
curl http://orchestrator:8000/health/live
# Expected: {"alive": true}

# Readiness probe (includes robot/job counts)
curl http://orchestrator:8000/health/ready
# Expected: {"ready": true, "connected_robots": 5, "pending_jobs": 0}
```

#### Robot Agent Health

Check via Orchestrator API:

```bash
curl -H "X-Api-Key: $API_SECRET" \
    http://orchestrator:8000/api/robots
# Returns list of connected robots with status
```

---

## Shutdown Procedures

### Graceful Shutdown

#### Canvas Application

1. File > Exit or close window
2. Wait for "Saving preferences..." message
3. Application closes cleanly

#### Robot Agent

```powershell
# Send SIGTERM (Linux) or Ctrl+C
# Agent will:
# 1. Stop accepting new jobs
# 2. Wait for running jobs to complete (up to 60s)
# 3. Close WebSocket connection
# 4. Exit with status 0
```

Expected logs:
```
INFO | Received signal, initiating shutdown...
INFO | Stopping robot agent...
INFO | Waiting for 2 jobs to complete...
INFO | Robot agent stopped. Jobs completed: 15, Failed: 1
```

#### Orchestrator

```bash
# Send SIGTERM to main process
kill -TERM $ORCHESTRATOR_PID

# Or if using Docker
docker-compose stop orchestrator

# Or Kubernetes
kubectl rollout restart deployment/orchestrator
```

Shutdown sequence:
1. Stop accepting new connections
2. Close WebSocket connections to robots
3. Close database pool
4. Stop log streaming service
5. Exit

---

### Emergency Shutdown

When immediate shutdown is required:

#### Robot Agent Force Stop

```powershell
# Windows
taskkill /F /IM python.exe /T

# Linux
kill -9 $ROBOT_PID
```

> **Warning:** Force shutdown will abandon running jobs. Jobs will be requeued when robot reconnects.

#### Orchestrator Force Stop

```bash
# Kill all workers
pkill -9 -f "uvicorn.*orchestrator"

# Docker
docker-compose kill orchestrator
```

> **Warning:** Active WebSocket connections will be dropped. Robots will automatically reconnect.

---

### Job Drain Procedures

Before maintenance, drain jobs from robots:

1. **Stop Job Assignment**
   ```bash
   # Set robot to maintenance mode via API
   curl -X PUT -H "X-Api-Key: $API_SECRET" \
       http://orchestrator:8000/api/robots/robot-id/maintenance
   ```

2. **Wait for Completion**
   ```bash
   # Poll until no active jobs
   while true; do
       status=$(curl -s http://orchestrator:8000/api/robots/robot-id | jq '.active_jobs')
       if [ "$status" = "0" ]; then break; fi
       sleep 10
   done
   ```

3. **Proceed with Maintenance**

---

## Scaling

### Adding Robot Agents

#### Horizontal Scaling

1. **Deploy New Agent**
   ```powershell
   # Configure with unique robot name
   $env:CASARE_ROBOT_NAME = "robot-prod-02"
   $env:CASARE_ROBOT_ID = "robot-prod-02"
   python -m casare_rpa.robot.cli start
   ```

2. **Verify Registration**
   ```bash
   curl -H "X-Api-Key: $API_SECRET" \
       http://orchestrator:8000/api/robots | jq '.[] | select(.robot_name == "robot-prod-02")'
   ```

3. **Configure Capabilities**
   - `browser` - Can execute browser automation
   - `desktop` - Can execute desktop automation (Windows only)
   - `high_memory` - Has 8GB+ RAM for large workflows
   - `gpu` - Has GPU for vision tasks

#### Capacity Planning

| Workflow Type | Recommended Robots | Memory per Robot |
|--------------|-------------------|------------------|
| Browser only | 1 per 10 workflows/hour | 4GB |
| Desktop automation | 1 per 5 workflows/hour | 8GB |
| Mixed workload | 1 per 3 workflows/hour | 8GB |
| Vision/OCR heavy | 1 per 2 workflows/hour | 16GB |

---

### Load Balancing

The Orchestrator automatically load-balances jobs across available robots.

#### Selection Criteria (Priority Order)

1. **Target Robot** - If job specifies `target_robot_id`
2. **Required Capabilities** - Robot must have all required capabilities
3. **Environment Match** - Production jobs to production robots
4. **Tenant Isolation** - Multi-tenant deployments
5. **Available Slots** - Robot with most available capacity
6. **Least Recently Used** - Distribute load evenly

#### Configuring Job Assignment

```python
# Submit job with specific requirements
response = requests.post(
    "http://orchestrator:8000/api/jobs",
    json={
        "workflow_id": "my-workflow",
        "priority": 5,  # Higher = more urgent (0-10)
        "required_capabilities": ["browser", "high_memory"],
        "target_robot_id": None,  # Or specific robot
        "timeout": 1800,  # 30 minutes
    },
    headers={"X-Api-Key": API_SECRET}
)
```

---

### Resource Allocation

#### Robot Agent Resources

```yaml
# Kubernetes resource limits
resources:
  requests:
    memory: "4Gi"
    cpu: "1000m"
  limits:
    memory: "8Gi"
    cpu: "2000m"
```

#### Orchestrator Resources

```yaml
# Scale based on connected robots
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"

# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestrator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orchestrator
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Monitoring

### Key Metrics to Watch

#### Robot Agent Metrics

| Metric | Description | Warning Threshold | Critical Threshold |
|--------|-------------|-------------------|-------------------|
| `jobs_completed` | Total completed jobs | - | - |
| `jobs_failed` | Total failed jobs | >5% of completed | >10% of completed |
| `active_jobs` | Currently executing | = max_concurrent | - |
| `reconnect_count` | Connection reconnects | >3/hour | >10/hour |
| `heartbeat_age` | Time since last heartbeat | >60s | >90s |
| `memory_usage` | Process memory | >80% limit | >90% limit |
| `cpu_usage` | Process CPU | >80% | >95% |

#### Orchestrator Metrics

| Metric | Description | Warning Threshold | Critical Threshold |
|--------|-------------|-------------------|-------------------|
| `connected_robots` | Online robot count | <expected-1 | <expected/2 |
| `pending_jobs` | Jobs waiting | >10 | >50 |
| `websocket_connections` | Active connections | - | - |
| `request_latency_p99` | API response time | >500ms | >2000ms |
| `error_rate` | HTTP 5xx rate | >1% | >5% |

---

### Alert Thresholds

#### PagerDuty/OpsGenie Configuration

```yaml
# Critical (Page immediately)
- name: orchestrator_down
  condition: up == 0
  for: 1m

- name: no_robots_available
  condition: connected_robots == 0
  for: 5m

- name: job_queue_stuck
  condition: pending_jobs > 50 AND rate(jobs_completed[5m]) == 0
  for: 10m

# Warning (Ticket/Slack)
- name: robot_disconnected
  condition: delta(connected_robots[5m]) < 0
  for: 0m

- name: high_failure_rate
  condition: rate(jobs_failed[1h]) / rate(jobs_completed[1h]) > 0.1
  for: 15m

- name: slow_job_execution
  condition: avg(job_duration_seconds) > 1800
  for: 30m
```

---

### Dashboard Configuration

#### Grafana Dashboard Panels

```json
{
  "panels": [
    {
      "title": "Robot Fleet Status",
      "type": "stat",
      "targets": [
        {"expr": "casare_connected_robots", "legendFormat": "Connected"},
        {"expr": "casare_robots_busy", "legendFormat": "Busy"},
        {"expr": "casare_robots_idle", "legendFormat": "Idle"}
      ]
    },
    {
      "title": "Job Queue",
      "type": "graph",
      "targets": [
        {"expr": "casare_pending_jobs", "legendFormat": "Pending"},
        {"expr": "rate(casare_jobs_completed[5m])", "legendFormat": "Completed/min"}
      ]
    },
    {
      "title": "Error Rate",
      "type": "graph",
      "targets": [
        {"expr": "rate(casare_jobs_failed[5m]) / rate(casare_jobs_completed[5m]) * 100"}
      ],
      "alert": {"threshold": 10}
    }
  ]
}
```

---

### Log Aggregation

#### Loguru Configuration

```python
# Configure JSON logging for aggregation
from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stdout,
    format='{"timestamp":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}","level":"{level}","message":"{message}","module":"{module}","function":"{function}"}',
    serialize=True,
)
```

#### Loki/Promtail Configuration

```yaml
# promtail.yaml
scrape_configs:
  - job_name: casare_rpa
    static_configs:
      - targets:
          - localhost
        labels:
          job: casare-rpa
          __path__: /var/log/casare/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            module: module
            job_id: job_id
      - labels:
          level:
          module:
          job_id:
```

---

## Backup

### Workflow Backup

Workflows are stored as JSON files. Back up these locations:

| Component | Location | Backup Frequency |
|-----------|----------|------------------|
| Projects | `%USERPROFILE%\Documents\CasareRPA\projects\` | Daily |
| Workflows | `*.json` files in project folders | Daily |
| Subflows | `subflows/` directory in projects | Daily |
| Templates | `templates/` directory | Weekly |

#### PowerShell Backup Script

```powershell
# backup-workflows.ps1
$backupDir = "D:\Backups\CasareRPA\$(Get-Date -Format 'yyyy-MM-dd')"
$sourceDir = "$env:USERPROFILE\Documents\CasareRPA"

New-Item -ItemType Directory -Force -Path $backupDir

# Backup projects
Copy-Item -Recurse "$sourceDir\projects" "$backupDir\projects"

# Compress
Compress-Archive -Path "$backupDir\*" -DestinationPath "$backupDir.zip"
Remove-Item -Recurse -Force $backupDir

Write-Host "Backup completed: $backupDir.zip"
```

---

### Database Backup

If using PostgreSQL for Orchestrator:

```bash
#!/bin/bash
# backup-database.sh
BACKUP_DIR="/backups/casare/$(date +%Y-%m-%d)"
mkdir -p $BACKUP_DIR

pg_dump $DATABASE_URL > "$BACKUP_DIR/casare_db.sql"
gzip "$BACKUP_DIR/casare_db.sql"

# Upload to S3
aws s3 cp "$BACKUP_DIR/casare_db.sql.gz" "s3://backups/casare/$(date +%Y-%m-%d)/"

# Cleanup old backups (keep 30 days)
find /backups/casare -mtime +30 -delete
```

---

### Configuration Backup

```powershell
# backup-config.ps1
$backupDir = "D:\Backups\CasareRPA\config"
New-Item -ItemType Directory -Force -Path $backupDir

# Application settings
Copy-Item "$env:APPDATA\CasareRPA\settings.json" "$backupDir\"

# Credentials (encrypted)
Copy-Item "$env:APPDATA\CasareRPA\credentials.enc" "$backupDir\"

# Environment templates
Copy-Item "$env:USERPROFILE\Documents\CasareRPA\environments\*.json" "$backupDir\environments\"
```

---

### Backup Schedule

| Data | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| Workflows | Daily | 30 days | File copy + compress |
| Database | Daily | 30 days | pg_dump |
| Configuration | Weekly | 90 days | File copy |
| Logs | Hourly | 7 days | Log rotation |

---

## Recovery

### Restore from Backup

#### Workflow Restore

```powershell
# Restore specific workflow
$backupZip = "D:\Backups\CasareRPA\2024-01-15.zip"
$targetProject = "$env:USERPROFILE\Documents\CasareRPA\projects\my-project"

Expand-Archive -Path $backupZip -DestinationPath "C:\Temp\restore"
Copy-Item "C:\Temp\restore\projects\my-project\workflows\*.json" "$targetProject\workflows\"

# Restart Canvas to reload
```

#### Database Restore

```bash
# Restore PostgreSQL database
gunzip -c /backups/casare/2024-01-15/casare_db.sql.gz | psql $DATABASE_URL

# Verify
psql $DATABASE_URL -c "SELECT COUNT(*) FROM jobs;"
```

---

### Disaster Recovery

#### Complete System Failure

1. **Deploy Fresh Orchestrator**
   ```bash
   docker-compose up -d orchestrator
   ```

2. **Restore Database**
   ```bash
   gunzip -c /backups/latest/casare_db.sql.gz | psql $DATABASE_URL
   ```

3. **Deploy Robot Agents**
   - Use same API keys (stored in backup)
   - Robots will auto-reconnect

4. **Verify Fleet Status**
   ```bash
   curl http://orchestrator:8000/health/ready
   ```

5. **Resume Operations**
   - Pending jobs will be reprocessed
   - Running jobs at failure time are lost

---

### Failover Procedures

#### Orchestrator Failover

For high availability, run multiple Orchestrator instances behind a load balancer:

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
spec:
  replicas: 3  # Multiple instances
  selector:
    matchLabels:
      app: orchestrator
  template:
    spec:
      containers:
      - name: orchestrator
        image: casare-rpa/orchestrator:latest
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
```

> **Note:** When using multiple Orchestrator instances, ensure:
> - Shared database for job queue
> - Redis for session state (if needed)
> - Sticky sessions for WebSocket connections

#### Robot Failover

Robots automatically reconnect with exponential backoff:

```
Initial: 1s -> 2s -> 4s -> 8s -> ... -> max 60s
```

Jobs assigned to disconnected robots are automatically requeued.

---

## Appendix: Quick Reference Commands

### Status Checks

```bash
# Orchestrator status
curl http://orchestrator:8000/health/ready

# List all robots
curl -H "X-Api-Key: $API_SECRET" http://orchestrator:8000/api/robots

# List pending jobs
curl -H "X-Api-Key: $API_SECRET" http://orchestrator:8000/api/jobs?status=pending

# Robot details
curl -H "X-Api-Key: $API_SECRET" http://orchestrator:8000/api/robots/{robot_id}
```

### Emergency Actions

```bash
# Cancel all pending jobs
curl -X DELETE -H "X-Api-Key: $API_SECRET" \
    http://orchestrator:8000/api/jobs/pending

# Force disconnect robot
curl -X DELETE -H "X-Api-Key: $API_SECRET" \
    http://orchestrator:8000/api/robots/{robot_id}

# Restart Orchestrator (Kubernetes)
kubectl rollout restart deployment/orchestrator
```
