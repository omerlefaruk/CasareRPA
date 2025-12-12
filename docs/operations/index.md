# Operations Documentation

Operational guides for deploying, running, and maintaining CasareRPA in production environments.

---

## Operations Overview

This section provides guidance for:

- **System Administrators** - Deploy and maintain CasareRPA infrastructure
- **Operations Teams** - Monitor and troubleshoot running systems
- **DevOps Engineers** - Automate deployments and manage configurations

```mermaid
graph LR
    A[Operations] --> B[Runbook]
    A --> C[Troubleshooting]
    A --> D[Backup & Restore]

    B --> B1[Startup/Shutdown]
    B --> B2[Deployment]
    B --> B3[Maintenance]

    C --> C1[Common Issues]
    C --> C2[Diagnostics]
    C --> C3[Recovery]

    D --> D1[Backup Procedures]
    D --> D2[Restore Procedures]
    D --> D3[Disaster Recovery]
```

---

## Operations Sections

### [Runbook](runbook.md)

Standard operating procedures for CasareRPA operations.

| Procedure | Description |
|-----------|-------------|
| [Startup](runbook.md#startup) | Start CasareRPA services |
| [Shutdown](runbook.md#shutdown) | Graceful shutdown procedures |
| [Deployment](runbook.md#deployment) | Deploy new versions |
| [Scaling](runbook.md#scaling) | Add/remove robot agents |
| [Maintenance](runbook.md#maintenance) | Routine maintenance tasks |
| [Health Checks](runbook.md#health-checks) | Verify system health |

### [Troubleshooting](troubleshooting.md)

Diagnose and resolve common issues.

| Topic | Description |
|-------|-------------|
| [Common Issues](troubleshooting.md#common) | Frequently encountered problems |
| [Diagnostics](troubleshooting.md#diagnostics) | Diagnostic commands and tools |
| [Log Analysis](troubleshooting.md#logs) | Reading and analyzing logs |
| [Performance](troubleshooting.md#performance) | Performance troubleshooting |
| [Recovery](troubleshooting.md#recovery) | Recovery procedures |

### [Backup & Restore](backup-restore.md)

Data protection and disaster recovery.

| Topic | Description |
|-------|-------------|
| [Backup Procedures](backup-restore.md#backup) | What and how to backup |
| [Restore Procedures](backup-restore.md#restore) | Recovery steps |
| [Disaster Recovery](backup-restore.md#dr) | Full system recovery |
| [Testing](backup-restore.md#testing) | Verify backup integrity |

---

## Quick Reference

### Service Commands

```bash
# Canvas (Visual Designer)
python run.py                    # Start canvas
python run.py --debug            # Start with debug mode

# Robot Agent
casare-rpa agent start           # Start robot agent
casare-rpa agent status          # Check agent status
casare-rpa agent stop            # Stop robot agent

# Orchestrator
casare-rpa orchestrator start    # Start orchestrator server
casare-rpa orchestrator status   # Check orchestrator health

# CLI Execution
casare-rpa run workflow.json     # Execute workflow
casare-rpa run workflow.json -v  # Execute with verbose logging
```

### Log Locations

| Component | Log Path | Purpose |
|-----------|----------|---------|
| Canvas | `~/.casare-rpa/logs/canvas.log` | UI and designer logs |
| Robot | `~/.casare-rpa/logs/robot.log` | Execution logs |
| Orchestrator | `~/.casare-rpa/logs/orchestrator.log` | Server logs |
| Workflows | `~/.casare-rpa/logs/workflows/` | Per-workflow execution logs |

### Health Check Endpoints

```bash
# Orchestrator health
curl http://localhost:8000/health

# Orchestrator readiness
curl http://localhost:8000/ready

# Robot agent health
curl http://localhost:8001/health
```

### Metrics Endpoints

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Example response
casare_workflows_total{status="success"} 1234
casare_workflows_total{status="failed"} 56
casare_jobs_queue_depth 12
casare_robots_active 3
```

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10/11 (64-bit) |
| **CPU** | 4 cores |
| **RAM** | 8 GB |
| **Storage** | 10 GB available |
| **Python** | 3.12+ |

### Recommended (Production)

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows Server 2022 |
| **CPU** | 8+ cores |
| **RAM** | 16+ GB |
| **Storage** | 50+ GB SSD |
| **Database** | PostgreSQL 15+ |

### Network Requirements

| Port | Service | Description |
|------|---------|-------------|
| 8000 | Orchestrator API | REST API and WebSocket |
| 8001 | Robot Agent | Agent health and metrics |
| 5432 | PostgreSQL | Database (if external) |

---

## Deployment Checklist

### Pre-Deployment

- [ ] Verify system requirements met
- [ ] Configure network/firewall rules
- [ ] Prepare SSL/TLS certificates
- [ ] Set up database (if using Orchestrator)
- [ ] Configure credential provider
- [ ] Prepare environment variables

### Deployment

- [ ] Install Python dependencies
- [ ] Configure application settings
- [ ] Initialize database schema
- [ ] Start services
- [ ] Verify health checks
- [ ] Configure monitoring

### Post-Deployment

- [ ] Run smoke tests
- [ ] Verify logging working
- [ ] Check metrics collection
- [ ] Document configuration
- [ ] Set up alerting

---

## Configuration Files

### Application Configuration

```yaml
# config/settings.yaml
app:
  name: casare-rpa
  environment: production
  debug: false

logging:
  level: INFO
  format: json
  path: /var/log/casare-rpa

database:
  url: postgresql://user:pass@localhost/casare
  pool_size: 10

orchestrator:
  url: http://localhost:8000
  api_key: ${ORCHESTRATOR_API_KEY}
```

### Robot Configuration

```yaml
# config/robot.yaml
robot:
  name: robot-001
  tags:
    - production
    - browser-capable
  max_concurrent_jobs: 3

orchestrator:
  url: https://orchestrator.example.com
  api_key: ${ROBOT_API_KEY}
  heartbeat_interval: 30

browser:
  headless: true
  timeout: 30000
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CASARE_ENV` | Environment name | `development` |
| `CASARE_LOG_LEVEL` | Log level | `INFO` |
| `CASARE_CONFIG_PATH` | Config file path | `~/.casare-rpa/config` |
| `DATABASE_URL` | PostgreSQL connection | - |
| `ORCHESTRATOR_API_KEY` | API key for orchestrator | - |
| `VAULT_ADDR` | HashiCorp Vault address | - |

---

## Monitoring

### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `workflow_success_rate` | % of successful workflows | < 95% |
| `workflow_duration_p95` | 95th percentile duration | > 5 min |
| `job_queue_depth` | Pending jobs in queue | > 100 |
| `robot_availability` | % of robots online | < 80% |
| `error_rate` | Errors per minute | > 10 |

### Log Aggregation

Configure log shipping to your log aggregation system:

```yaml
# config/logging.yaml
handlers:
  - type: file
    path: /var/log/casare-rpa/app.log
    format: json

  - type: stdout
    format: json

  - type: http
    url: https://logs.example.com/ingest
    format: json
```

### Alerting

Recommended alerts:

| Alert | Condition | Severity |
|-------|-----------|----------|
| Service Down | Health check fails 3x | Critical |
| High Error Rate | > 10 errors/min for 5 min | Warning |
| Queue Backup | > 100 jobs for 15 min | Warning |
| Robot Offline | Robot missing heartbeat | Warning |
| Disk Space Low | < 10% free | Warning |

---

## Maintenance Windows

### Routine Maintenance

| Task | Frequency | Duration |
|------|-----------|----------|
| Log rotation | Daily | Automatic |
| Database vacuum | Weekly | 30 min |
| Dependency updates | Monthly | 1 hour |
| Security patches | As needed | Varies |

### Maintenance Procedure

1. **Announce** - Notify stakeholders
2. **Drain** - Stop accepting new jobs
3. **Wait** - Allow running jobs to complete
4. **Backup** - Create pre-maintenance backup
5. **Execute** - Perform maintenance
6. **Verify** - Run health checks
7. **Resume** - Re-enable job processing
8. **Monitor** - Watch for issues

---

## Incident Response

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| **SEV1** | Complete service outage | 15 min |
| **SEV2** | Major feature impacted | 1 hour |
| **SEV3** | Minor feature impacted | 4 hours |
| **SEV4** | Low-impact issue | 24 hours |

### Incident Procedure

1. **Detect** - Alert received or issue reported
2. **Acknowledge** - Assign incident owner
3. **Diagnose** - Identify root cause
4. **Mitigate** - Restore service
5. **Resolve** - Implement permanent fix
6. **Review** - Post-incident analysis

---

## Support

### Getting Help

- **Documentation** - Check troubleshooting guides
- **Logs** - Review application logs
- **Metrics** - Check monitoring dashboards
- **Issues** - Report on GitHub

### Information to Collect

When reporting issues, include:

- CasareRPA version
- OS and Python version
- Error messages and stack traces
- Relevant log excerpts
- Steps to reproduce
- Configuration (sanitized)

---

## Related Documentation

- [User Guide - Deployment](../user-guide/deployment/index.md)
- [Developer Guide - Architecture](../developer-guide/architecture/index.md)
- [Security - Best Practices](../security/best-practices.md)
