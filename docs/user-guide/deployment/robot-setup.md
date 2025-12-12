# Robot Agent Setup

The Robot Agent is the headless execution component of CasareRPA that runs workflows on individual machines. It connects to the Orchestrator for job assignment and reports execution status.

---

## Architecture Overview

```
+---------------------------+
|       RobotAgent          |
|   (Unified Coordinator)   |
+-------------+-------------+
              |
+-------------v-------------+
|     CircuitBreaker        |
|   (Failure Protection)    |
+-------------+-------------+
              |
+-------------v-------------+
|   CheckpointManager       |
|   (Crash Recovery)        |
+-------------+-------------+
              |
+-------------v-------------+
| UnifiedResourceManager    |
|  (Browser/DB/HTTP Pool)   |
+-------------+-------------+
              |
+-------------v-------------+
|  DBOSWorkflowExecutor     |
|   (Durable Execution)     |
+---------------------------+
```

---

## Installation

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Windows | 10/11 or Server 2022 |
| Python | 3.12+ |
| CasareRPA | Latest |

### Install Steps

```bash
# Install CasareRPA with robot dependencies
pip install casare-rpa[robot]

# Install Playwright browsers (for web automation)
playwright install chromium

# Verify installation
casare-rpa robot --help
```

---

## Configuration

### Configuration File

Create `~/.casare-rpa/robot_config.yaml`:

```yaml
robot:
  name: robot-production-01
  environment: production
  tags:
    - browser-capable
    - desktop-capable
  max_concurrent_jobs: 3
  job_timeout: 3600  # 1 hour

orchestrator:
  url: https://orchestrator.example.com
  api_key: ${ROBOT_API_KEY}
  heartbeat_interval: 10

browser:
  headless: true
  timeout: 30000

resource_pools:
  browser_pool_size: 5
  db_pool_size: 10
  http_pool_size: 20

checkpointing:
  enabled: true
  checkpoint_dir: ~/.casare-rpa/checkpoints

circuit_breaker:
  enabled: true
  failure_threshold: 5
  recovery_timeout: 60
```

### Environment Variables

All settings can be configured via environment variables with the `CASARE_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_ROBOT_ID` | Unique robot identifier | Auto-generated UUID |
| `CASARE_ROBOT_NAME` | Display name | Hostname |
| `CASARE_ROBOT_TAGS` | Comma-separated tags | Empty |
| `CASARE_ENVIRONMENT` | Environment name | `default` |
| `CASARE_MAX_CONCURRENT_JOBS` | Max parallel jobs | `1` |
| `CASARE_CONFIG_PATH` | Config file path | `~/.casare-rpa/robot_config.yaml` |

### Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Full PostgreSQL URL | None |
| `POSTGRES_URL` | Alias for DATABASE_URL | None |
| `DB_PASSWORD` | Database password (for Supabase) | None |

### Performance Tuning

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_POLL_INTERVAL` | Job poll interval (seconds) | `1.0` |
| `CASARE_BATCH_SIZE` | Jobs per poll | `1` |
| `CASARE_JOB_TIMEOUT` | Job timeout (seconds) | `3600` |
| `CASARE_NODE_TIMEOUT` | Node timeout (seconds) | `120.0` |
| `CASARE_HEARTBEAT_INTERVAL` | Heartbeat interval (seconds) | `10.0` |
| `CASARE_SHUTDOWN_GRACE` | Graceful shutdown time (seconds) | `60` |

### Resource Pool Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_BROWSER_POOL_SIZE` | Browser instance pool | `5` |
| `CASARE_DB_POOL_SIZE` | Database connection pool | `10` |
| `CASARE_HTTP_POOL_SIZE` | HTTP session pool | `20` |

### Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_ENABLE_CHECKPOINTING` | Enable crash recovery | `true` |
| `CASARE_ENABLE_REALTIME` | Enable WebSocket updates | `true` |
| `CASARE_ENABLE_CIRCUIT_BREAKER` | Enable failure protection | `true` |

---

## Starting the Robot

### Command Line

```bash
# Start robot with default settings
casare-rpa robot start

# Start with specific environment
casare-rpa robot start --environment production

# Start with custom config
casare-rpa robot start --config /path/to/config.yaml

# Start with verbose logging
casare-rpa robot start -v
```

### As a Windows Service

```bash
# Install as Windows service
casare-rpa robot install

# Start the service
casare-rpa robot start-service

# Check service status
casare-rpa robot status

# Stop the service
casare-rpa robot stop-service

# Uninstall service
casare-rpa robot uninstall
```

### Using Environment File

Create `.env` file in working directory:

```bash
CASARE_ROBOT_NAME=production-robot-01
CASARE_ENVIRONMENT=production
CASARE_MAX_CONCURRENT_JOBS=3
DATABASE_URL=postgresql://user:pass@db.example.com:5432/casare
CASARE_ENABLE_CHECKPOINTING=true
```

Then start:

```bash
casare-rpa robot start
```

---

## Connecting to Orchestrator

### API Key Authentication

1. Generate API key in Orchestrator dashboard
2. Configure robot with key:

```bash
# Via environment variable
export ROBOT_API_KEY=your-api-key

# Or in config file
orchestrator:
  api_key: your-api-key
```

### Connection Verification

```bash
# Check connection to orchestrator
casare-rpa robot check-connection

# Expected output:
# Connected to orchestrator at https://orchestrator.example.com
# Robot ID: abc123-def456
# Status: online
```

---

## Robot Capabilities

Robots advertise their capabilities for workflow routing:

```yaml
robot:
  tags:
    - browser-capable      # Can run browser automation
    - desktop-capable      # Can run desktop automation
    - ocr-capable          # Has OCR dependencies
    - gpu-available        # Has GPU for AI workloads
```

Orchestrator routes workflows to robots with matching capabilities.

---

## Health Monitoring

### Health Check Endpoint

The robot exposes a health endpoint on port 8001:

```bash
curl http://localhost:8001/health

# Response:
{
  "status": "healthy",
  "robot_id": "abc123",
  "uptime_seconds": 3600,
  "jobs_completed": 42,
  "current_jobs": 2
}
```

### Metrics Endpoint

```bash
curl http://localhost:8001/metrics

# Prometheus format metrics
casare_jobs_completed_total{status="success"} 42
casare_jobs_completed_total{status="failed"} 3
casare_job_duration_seconds{quantile="0.95"} 45.2
casare_active_jobs 2
```

---

## Troubleshooting

### Robot Not Starting

```bash
# Check logs
tail -f ~/.casare-rpa/logs/robot.log

# Verify Python version
python --version  # Should be 3.12+

# Check database connection
casare-rpa robot check-db
```

### Jobs Not Processing

1. Verify robot is online in Orchestrator dashboard
2. Check workflow requirements match robot capabilities
3. Review job logs for errors:

```bash
casare-rpa robot logs --job-id abc123
```

### Connection Issues

```bash
# Test network connectivity
casare-rpa robot ping

# Check firewall rules
# Port 8001 (robot health) must be accessible
# Port 443 (orchestrator) must be open outbound
```

---

## Production Checklist

- [ ] Configure unique `CASARE_ROBOT_NAME`
- [ ] Set appropriate `CASARE_MAX_CONCURRENT_JOBS`
- [ ] Enable `CASARE_ENABLE_CHECKPOINTING` for crash recovery
- [ ] Configure `CASARE_ENABLE_CIRCUIT_BREAKER` for failure protection
- [ ] Set up log rotation for `~/.casare-rpa/logs/`
- [ ] Configure monitoring to scrape `/metrics` endpoint
- [ ] Set up alerting on health check failures
- [ ] Test graceful shutdown behavior

---

## Related Documentation

- [Orchestrator Setup](orchestrator-setup.md) - Central management
- [Scheduling](scheduling.md) - Production scheduling
- [Monitoring](monitoring.md) - Metrics and alerting
- [Environment Variables](../../reference/environment-variables.md) - Complete reference
