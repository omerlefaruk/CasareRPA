# Monitoring and Observability

CasareRPA provides comprehensive monitoring capabilities through metrics, logs, and health checks. This guide covers setting up production monitoring for robots and orchestrators.

---

## Overview

```
+------------------+     +------------------+     +-----------------+
|   CasareRPA      | --> |   Prometheus     | --> |   Grafana       |
|   Components     |     |   (Scrape)       |     |   (Dashboard)   |
+------------------+     +------------------+     +-----------------+
         |
         v
+------------------+     +------------------+
|   Log Files      | --> |   Log Aggregator |
|   (JSON)         |     |   (ELK/Loki)     |
+------------------+     +------------------+
```

---

## Metrics

### Metrics Endpoints

Both Orchestrator and Robot expose Prometheus-compatible metrics:

| Component | Endpoint | Default Port |
|-----------|----------|--------------|
| Orchestrator | `/metrics` | 8000 |
| Robot | `/metrics` | 8001 |

### Key Metrics

#### Orchestrator Metrics

```prometheus
# Workflow execution
casare_workflows_total{status="success"}
casare_workflows_total{status="failed"}
casare_workflow_duration_seconds{quantile="0.95"}

# Job queue
casare_jobs_queue_depth
casare_jobs_pending
casare_jobs_running

# Robot fleet
casare_robots_total{status="online"}
casare_robots_total{status="offline"}

# API
casare_api_requests_total{method="POST",endpoint="/api/v1/jobs"}
casare_api_request_duration_seconds{quantile="0.95"}

# Schedules
casare_schedules_active
casare_schedule_runs_total{status="success"}
```

#### Robot Metrics

```prometheus
# Job execution
casare_jobs_completed_total{status="success"}
casare_jobs_completed_total{status="failed"}
casare_job_duration_seconds{quantile="0.95"}

# Node execution
casare_nodes_executed_total{type="ClickElementNode"}
casare_node_duration_seconds{type="HttpRequestNode",quantile="0.95"}

# Resources
casare_browser_pool_active
casare_browser_pool_available
casare_db_connections_active
casare_http_sessions_active

# System
casare_cpu_usage_percent
casare_memory_usage_bytes
casare_disk_usage_percent
```

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'casare-orchestrator'
    static_configs:
      - targets: ['orchestrator.example.com:8000']
    scrape_interval: 15s

  - job_name: 'casare-robots'
    static_configs:
      - targets:
        - 'robot-01.example.com:8001'
        - 'robot-02.example.com:8001'
        - 'robot-03.example.com:8001'
    scrape_interval: 15s
```

---

## Grafana Dashboards

### Fleet Overview Dashboard

Key panels:

| Panel | Query | Description |
|-------|-------|-------------|
| Active Robots | `casare_robots_total{status="online"}` | Online robot count |
| Queue Depth | `casare_jobs_queue_depth` | Pending jobs |
| Success Rate | `rate(casare_workflows_total{status="success"}[1h]) / rate(casare_workflows_total[1h]) * 100` | Hourly success % |
| Avg Duration | `histogram_quantile(0.95, rate(casare_workflow_duration_seconds_bucket[1h]))` | P95 duration |

### Robot Detail Dashboard

| Panel | Query | Description |
|-------|-------|-------------|
| CPU Usage | `casare_cpu_usage_percent{robot="$robot"}` | Robot CPU |
| Memory | `casare_memory_usage_bytes{robot="$robot"}` | Robot memory |
| Active Jobs | `casare_jobs_running{robot="$robot"}` | Current jobs |
| Browser Pool | `casare_browser_pool_active{robot="$robot"}` | Browser instances |

### Import Dashboard

Import pre-built dashboards:

```bash
# Download dashboard JSON
curl -O https://raw.githubusercontent.com/casare-rpa/dashboards/main/grafana/fleet-overview.json

# Import via Grafana API
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @fleet-overview.json
```

---

## Logging

### Log Configuration

CasareRPA uses structured JSON logging by default:

```yaml
# config/logging.yaml
logging:
  level: INFO
  format: json
  path: /var/log/casare-rpa/

  # Log files
  files:
    - name: app.log
      level: INFO
      rotation: daily
      retention: 30 days

    - name: error.log
      level: ERROR
      rotation: daily
      retention: 90 days

    - name: audit.log
      level: INFO
      rotation: daily
      retention: 365 days
```

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "casare_rpa.robot",
  "message": "Job completed successfully",
  "job_id": "JOB_abc123",
  "workflow_id": "WF_xyz789",
  "robot_id": "ROBOT_001",
  "duration_ms": 4532,
  "nodes_executed": 15
}
```

### Log Locations

| Component | Log Path | Purpose |
|-----------|----------|---------|
| Canvas | `~/.casare-rpa/logs/canvas.log` | UI logs |
| Robot | `~/.casare-rpa/logs/robot.log` | Execution logs |
| Orchestrator | `/var/log/casare-rpa/orchestrator.log` | Server logs |
| Workflows | `~/.casare-rpa/logs/workflows/` | Per-workflow logs |

### Log Aggregation

#### Loki + Promtail

```yaml
# promtail.yml
server:
  http_listen_port: 9080

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: casare-rpa
    static_configs:
      - targets:
          - localhost
        labels:
          job: casare-rpa
          __path__: /var/log/casare-rpa/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            job_id: job_id
            workflow_id: workflow_id
      - labels:
          level:
          job_id:
          workflow_id:
```

#### Elasticsearch + Filebeat

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/casare-rpa/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "casare-rpa-%{+yyyy.MM.dd}"
```

---

## Health Checks

### Orchestrator Health

```bash
# Liveness probe
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "uptime_seconds": 86400,
  "database": "connected",
  "queue": "active"
}

# Readiness probe (for load balancers)
curl http://localhost:8000/ready

# Response
{
  "ready": true,
  "database": "connected",
  "migrations": "current"
}
```

### Robot Health

```bash
# Health check
curl http://localhost:8001/health

# Response
{
  "status": "healthy",
  "robot_id": "ROBOT_001",
  "state": "running",
  "uptime_seconds": 3600,
  "current_jobs": 2,
  "jobs_completed": 42,
  "jobs_failed": 1,
  "circuit_breaker": "closed",
  "resources": {
    "browser_pool": {"active": 2, "available": 3},
    "db_pool": {"active": 5, "available": 5},
    "http_pool": {"active": 8, "available": 12}
  }
}
```

### Kubernetes Probes

```yaml
# kubernetes deployment
spec:
  containers:
    - name: casare-orchestrator
      livenessProbe:
        httpGet:
          path: /health
          port: 8000
        initialDelaySeconds: 10
        periodSeconds: 30

      readinessProbe:
        httpGet:
          path: /ready
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 10
```

---

## Alerting

### Alert Rules

#### Prometheus Alert Rules

```yaml
# alerts.yml
groups:
  - name: casare-rpa
    rules:
      # Service down
      - alert: OrchestratorDown
        expr: up{job="casare-orchestrator"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Orchestrator is down"

      - alert: RobotOffline
        expr: casare_robots_total{status="offline"} > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $value }} robots are offline"

      # Queue backup
      - alert: JobQueueBackup
        expr: casare_jobs_queue_depth > 100
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Job queue has {{ $value }} pending jobs"

      # High error rate
      - alert: HighErrorRate
        expr: rate(casare_workflows_total{status="failed"}[5m]) / rate(casare_workflows_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Workflow error rate is {{ $value | humanizePercentage }}"

      # Long running job
      - alert: LongRunningJob
        expr: casare_job_duration_seconds > 3600
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "Job running for over 1 hour"

      # Resource exhaustion
      - alert: BrowserPoolExhausted
        expr: casare_browser_pool_available == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Browser pool exhausted on {{ $labels.robot }}"
```

### Alertmanager Configuration

```yaml
# alertmanager.yml
route:
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: warning
      receiver: 'webhook'

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops@example.com'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<pagerduty-key>'

  - name: 'webhook'
    webhook_configs:
      - url: 'https://your-webhook-endpoint.com/alerts'
        send_resolved: true
```

---

## Audit Logging

### Audit Events

CasareRPA logs security-relevant events:

| Event | Description |
|-------|-------------|
| `AUTH_SUCCESS` | Successful authentication |
| `AUTH_FAILURE` | Failed authentication attempt |
| `API_KEY_CREATED` | New API key generated |
| `WORKFLOW_DEPLOYED` | Workflow deployed to orchestrator |
| `JOB_STARTED` | Job execution started |
| `JOB_COMPLETED` | Job execution completed |
| `CREDENTIAL_ACCESSED` | Credential retrieved from vault |

### Audit Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "JOB_STARTED",
  "actor": "robot-001",
  "resource": "JOB_abc123",
  "details": {
    "workflow_id": "WF_xyz789",
    "trigger": "schedule"
  },
  "ip_address": "192.168.1.100",
  "user_agent": "CasareRPA-Robot/1.0"
}
```

### Audit Retention

```yaml
audit:
  enabled: true
  retention_days: 365
  path: /var/log/casare-rpa/audit.log

  # Forward to SIEM
  forward:
    - type: syslog
      host: siem.example.com
      port: 514
```

---

## Dashboard Examples

### Real-Time Execution View

```
+------------------------------------------+
|          Active Workflows (3)            |
+------------------------------------------+
| Workflow         | Status    | Duration  |
|------------------|-----------|-----------|
| Daily Report     | Running   | 2m 15s    |
| Email Process    | Running   | 45s       |
| Data Sync        | Running   | 5m 30s    |
+------------------------------------------+

+------------------------------------------+
|            Robot Fleet (5)               |
+------------------------------------------+
| Robot            | Status | Jobs | CPU   |
|------------------|--------|------|-------|
| production-01    | Online |  2   | 45%   |
| production-02    | Online |  1   | 30%   |
| production-03    | Online |  0   | 10%   |
| staging-01       | Offline|  -   |  -    |
| dev-01           | Online |  0   |  5%   |
+------------------------------------------+
```

---

## Best Practices

### 1. Set Appropriate Alert Thresholds

Start conservative, then tune based on baseline:

```yaml
# Start with high thresholds
- alert: HighErrorRate
  expr: rate(casare_workflows_total{status="failed"}[5m]) > 0.2  # 20%

# After baseline, tighten
- alert: HighErrorRate
  expr: rate(casare_workflows_total{status="failed"}[5m]) > 0.05  # 5%
```

### 2. Use Log Levels Appropriately

| Level | Use For |
|-------|---------|
| DEBUG | Development troubleshooting |
| INFO | Normal operations |
| WARNING | Recoverable issues |
| ERROR | Failed operations |
| CRITICAL | System failures |

### 3. Correlate Logs and Metrics

Include identifiers in both:

```json
// Log entry
{"job_id": "JOB_123", "message": "Node failed"}

// Metric label
casare_node_failures{job_id="JOB_123"}
```

### 4. Monitor Resource Pools

Prevent exhaustion with alerts:

```yaml
- alert: ResourcePoolLow
  expr: casare_browser_pool_available < 2
  annotations:
    summary: "Browser pool running low"
```

---

## Troubleshooting

### Missing Metrics

```bash
# Verify metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets
```

### Log Not Appearing

```bash
# Check log file permissions
ls -la /var/log/casare-rpa/

# Verify logging config
casare-rpa config show | grep logging
```

### Alert Not Firing

```bash
# Check alert rule
curl http://prometheus:9090/api/v1/rules

# Test alert expression
curl http://prometheus:9090/api/v1/query?query=up{job="casare-orchestrator"}
```

---

## Related Documentation

- [Robot Setup](robot-setup.md) - Agent configuration
- [Orchestrator Setup](orchestrator-setup.md) - Server configuration
- [Troubleshooting](../../operations/troubleshooting.md) - Common issues
- [Runbook](../../operations/runbook.md) - Operating procedures
