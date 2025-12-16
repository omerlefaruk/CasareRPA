# Deployment Guide

Deploy CasareRPA in production environments with robots, orchestration, and monitoring.

---

## In This Section

| Document | Description |
|----------|-------------|
| [Robot Setup](robot-setup.md) | Configure robot execution agents |
| [Orchestrator Setup](orchestrator-setup.md) | Deploy the central orchestrator |
| [Fleet Dashboard](fleet-dashboard.md) | Manage robots, jobs, and API keys from Canvas |
| [Scheduling](scheduling.md) | Configure workflow schedules |
| [Monitoring](monitoring.md) | Track execution and health |

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CasareRPA Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐         ┌─────────────────┐               │
│  │   Canvas    │────────→│   Orchestrator  │               │
│  │  Designer   │         │                 │               │
│  └─────────────┘         │  ┌───────────┐  │               │
│                          │  │ Job Queue │  │               │
│  ┌─────────────┐         │  └─────┬─────┘  │               │
│  │ CLI / API   │────────→│        │        │               │
│  └─────────────┘         └────────┼────────┘               │
│                                   │                         │
│         ┌─────────────────────────┼─────────────────────┐  │
│         │                         │                     │  │
│         ▼                         ▼                     ▼  │
│  ┌─────────────┐         ┌─────────────┐       ┌─────────────┐
│  │   Robot 1   │         │   Robot 2   │       │   Robot N   │
│  │  (Windows)  │         │  (Windows)  │  ...  │  (Windows)  │
│  └─────────────┘         └─────────────┘       └─────────────┘
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start Deployment

### 1. Start Orchestrator

```bash
# Start the orchestrator server
casare-rpa orchestrator start --port 8000
```

### 2. Configure Robot

```bash
# Register robot with orchestrator
casare-rpa agent register \
  --orchestrator http://localhost:8000 \
  --name "Robot-01"

# Start robot agent
casare-rpa agent start
```

### 3. Deploy Workflow

```bash
# Upload workflow to orchestrator
casare-rpa workflow deploy my-workflow.json

# Schedule execution
casare-rpa schedule create \
  --workflow my-workflow \
  --cron "0 9 * * MON-FRI"
```

---

## Deployment Options

| Option | Robots | Orchestrator | Use Case |
|--------|--------|--------------|----------|
| **Local** | 1 | None | Development |
| **Single Robot** | 1 | Yes | Simple production |
| **Multi-Robot** | N | Yes | Enterprise |
| **High Availability** | N | Clustered | Critical systems |

---

## Component Requirements

### Orchestrator Server

| Requirement | Specification |
|-------------|---------------|
| **OS** | Windows Server 2019+ / Linux |
| **CPU** | 2+ cores |
| **RAM** | 4+ GB |
| **Storage** | 20+ GB |
| **Network** | Static IP or DNS |

### Robot Agent

| Requirement | Specification |
|-------------|---------------|
| **OS** | Windows 10/11 |
| **CPU** | 2+ cores |
| **RAM** | 4+ GB |
| **Desktop** | Interactive session (for UI automation) |
| **Network** | Access to orchestrator |

---

## Configuration

### Environment Variables

```bash
# Orchestrator
CASARE_ORCHESTRATOR_HOST=0.0.0.0
CASARE_ORCHESTRATOR_PORT=8000
CASARE_DATABASE_URL=postgresql://user:pass@host/db

# Robot
CASARE_ORCHESTRATOR_URL=http://orchestrator:8000
CASARE_ROBOT_NAME=Robot-01
CASARE_ROBOT_API_KEY=robot_xxxxxxxxxxxxx
```

### Config File

```yaml
# config.yaml
orchestrator:
  host: 0.0.0.0
  port: 8000

robot:
  name: Robot-01
  orchestrator_url: http://localhost:8000
  heartbeat_interval: 30

logging:
  level: INFO
  file: logs/casare.log
```

---

## Monitoring

### Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Orchestrator health check |
| `/metrics` | Prometheus metrics |
| `/api/v1/robots` | Robot status |
| `/api/v1/jobs/active` | Active executions |

### Key Metrics

| Metric | Description |
|--------|-------------|
| `jobs_total` | Total jobs executed |
| `jobs_failed` | Failed job count |
| `job_duration_seconds` | Execution time |
| `robots_online` | Connected robots |

---

## Next Steps

| Goal | Document |
|------|----------|
| Set up robot agent | [Robot Setup](robot-setup.md) |
| Deploy orchestrator | [Orchestrator Setup](orchestrator-setup.md) |
| Configure schedules | [Scheduling](scheduling.md) |
| Set up monitoring | [Monitoring](monitoring.md) |

---

## Related Documentation

- [Security Best Practices](../../security/best-practices.md)
- [Troubleshooting](../../operations/troubleshooting.md)
- [API Reference](../../developer-guide/api-reference/index.md)
