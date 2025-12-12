# Orchestrator Setup

The Orchestrator is the central management server for CasareRPA that coordinates workflow scheduling, job distribution, and robot fleet management.

---

## Architecture

```
                    +-------------------+
                    |   Orchestrator    |
                    |     Server        |
                    +--------+----------+
                             |
        +--------------------+--------------------+
        |                    |                    |
+-------v-------+    +-------v-------+    +-------v-------+
|   Robot 1     |    |   Robot 2     |    |   Robot N     |
|  (browser)    |    |  (desktop)    |    |  (mixed)      |
+---------------+    +---------------+    +---------------+
```

The Orchestrator provides:

- **REST API** for workflow management
- **WebSocket** for real-time robot communication
- **Job Queue** for reliable task distribution
- **Scheduler** for cron-based triggers
- **Dashboard** for fleet monitoring

---

## Deployment Options

### Option 1: Manual Installation

#### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.12+ |
| PostgreSQL | 15+ |
| Redis | 7+ (optional, for caching) |

#### Install Steps

```bash
# Install CasareRPA with orchestrator dependencies
pip install casare-rpa[orchestrator]

# Initialize database schema
casare-rpa orchestrator init-db

# Start orchestrator
casare-rpa orchestrator start
```

### Option 2: Docker Deployment

#### docker-compose.yml

```yaml
version: '3.8'

services:
  orchestrator:
    image: casare-rpa/orchestrator:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/casare
      - ORCHESTRATOR_HOST=0.0.0.0
      - ORCHESTRATOR_PORT=8000
      - ORCHESTRATOR_WORKERS=4
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=casare
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    restart: unless-stopped

volumes:
  postgres_data:
```

Start with:

```bash
docker-compose up -d
```

### Option 3: Cloud Platforms

#### Supabase + Cloud Run

1. Create Supabase project for database
2. Deploy to Cloud Run:

```bash
gcloud run deploy casare-orchestrator \
  --image casare-rpa/orchestrator:latest \
  --set-env-vars DATABASE_URL=$SUPABASE_URL
```

#### Railway

```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "casare-rpa orchestrator start"

[[services]]
port = 8000
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `ORCHESTRATOR_HOST` | Bind host | `127.0.0.1` |
| `ORCHESTRATOR_PORT` | HTTP port | `8000` |
| `ORCHESTRATOR_WORKERS` | Worker processes | `1` |
| `CASARE_API_URL` | Public API URL | Auto-detect |
| `CASARE_WEBHOOK_URL` | Public webhook URL | Auto-detect |

### Configuration File

Create `config/orchestrator.yaml`:

```yaml
orchestrator:
  host: 0.0.0.0
  port: 8000
  workers: 4

  # JWT settings
  secret_key: ${ORCHESTRATOR_SECRET_KEY}
  token_expiry_hours: 24

  # Rate limiting
  rate_limit:
    requests_per_minute: 100
    burst: 20

database:
  url: ${DATABASE_URL}
  pool_size: 20
  max_overflow: 10

queue:
  # Job queue settings
  max_retries: 3
  retry_delay_seconds: 60
  visibility_timeout_seconds: 300

scheduler:
  # Cron scheduler settings
  timezone: UTC
  max_concurrent_schedules: 100

logging:
  level: INFO
  format: json
  path: /var/log/casare-rpa/orchestrator.log
```

---

## Database Setup

### PostgreSQL Schema Initialization

```bash
# Initialize schema (first time)
casare-rpa orchestrator init-db

# Run migrations (upgrades)
casare-rpa orchestrator migrate

# Check migration status
casare-rpa orchestrator db-status
```

### Required Extensions

The following PostgreSQL extensions are used:

```sql
-- Usually auto-enabled in managed PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

### Connection Pooling

For production, use connection pooling:

```yaml
database:
  url: postgresql://user:pass@pgbouncer:6432/casare
  pool_size: 5  # Lower with external pooler
```

---

## Starting the Orchestrator

### Development Mode

```bash
# Start with hot reload
casare-rpa orchestrator start --reload --debug

# Start on specific port
casare-rpa orchestrator start --port 8080
```

### Production Mode

```bash
# Start with multiple workers
casare-rpa orchestrator start --workers 4

# Start as daemon
casare-rpa orchestrator start --daemon

# Check status
casare-rpa orchestrator status
```

### Health Verification

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "queue": "active",
  "robots_online": 5
}

# Readiness check (for load balancers)
curl http://localhost:8000/ready
```

---

## API Authentication

### Creating API Keys

```bash
# Create admin API key
casare-rpa orchestrator create-api-key \
  --name "Admin Key" \
  --role admin

# Create robot API key
casare-rpa orchestrator create-api-key \
  --name "Robot Production 1" \
  --role robot

# List API keys
casare-rpa orchestrator list-api-keys
```

### Using API Keys

```bash
# API request with key
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/v1/workflows

# Or via header
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/v1/workflows
```

---

## SSL/TLS Configuration

### Using Reverse Proxy (Recommended)

Configure nginx or Traefik in front of Orchestrator:

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name orchestrator.example.com;

    ssl_certificate /etc/ssl/certs/orchestrator.crt;
    ssl_certificate_key /etc/ssl/private/orchestrator.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Direct SSL (Alternative)

```bash
casare-rpa orchestrator start \
  --ssl-cert /path/to/cert.pem \
  --ssl-key /path/to/key.pem
```

---

## Workflow Deployment

### Upload Workflow

```bash
# Deploy workflow via CLI
casare-rpa orchestrator deploy workflow.json

# Deploy with trigger
casare-rpa orchestrator deploy workflow.json --trigger schedule --cron "0 9 * * *"
```

### API Deployment

```python
import httpx

async def deploy_workflow():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/workflows",
            headers={"Authorization": "Bearer YOUR_API_KEY"},
            json={
                "name": "Daily Report",
                "workflow_data": {...},  # Workflow JSON
                "trigger": {
                    "type": "schedule",
                    "cron": "0 9 * * *"
                }
            }
        )
        return response.json()
```

---

## Scaling

### Horizontal Scaling

Deploy multiple Orchestrator instances behind a load balancer:

```yaml
# docker-compose.yml
services:
  orchestrator:
    image: casare-rpa/orchestrator:latest
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql://db:5432/casare
```

Requirements for horizontal scaling:

- Shared PostgreSQL database
- Load balancer with WebSocket support
- Sticky sessions for WebSocket connections

### Worker Scaling

```bash
# Start with more workers
casare-rpa orchestrator start --workers 8
```

Recommended workers: 2x CPU cores

---

## Backup Procedures

### Database Backup

```bash
# Using pg_dump
pg_dump -h localhost -U postgres casare > backup.sql

# Scheduled backup (cron)
0 2 * * * pg_dump -h localhost -U postgres casare | gzip > /backups/casare_$(date +\%Y\%m\%d).sql.gz
```

### Workflow Export

```bash
# Export all workflows
casare-rpa orchestrator export-workflows --output workflows_backup.json

# Export specific workflow
casare-rpa orchestrator export-workflow WF_123 --output workflow.json
```

---

## Monitoring

### Prometheus Metrics

```bash
# Metrics endpoint
curl http://localhost:8000/metrics

# Key metrics
casare_workflows_total{status="success"}
casare_workflows_total{status="failed"}
casare_jobs_queue_depth
casare_robots_active
casare_api_requests_total{method="POST",endpoint="/api/v1/jobs"}
```

### Grafana Dashboard

Import the CasareRPA Grafana dashboard from `docs/monitoring/grafana-dashboard.json`.

---

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
casare-rpa orchestrator check-db

# Check connection string
echo $DATABASE_URL
```

### Workers Not Starting

```bash
# Check logs
journalctl -u casare-orchestrator -f

# Verify port availability
lsof -i :8000
```

### Robots Not Connecting

```bash
# Check WebSocket endpoint
wscat -c ws://localhost:8000/ws/robots

# Verify firewall rules
# Port 8000 must accept WebSocket connections
```

---

## Production Checklist

- [ ] PostgreSQL configured with connection pooling
- [ ] SSL/TLS enabled via reverse proxy
- [ ] API keys generated for robots
- [ ] Health check endpoint monitored
- [ ] Database backups scheduled
- [ ] Log aggregation configured
- [ ] Metrics collection enabled
- [ ] Rate limiting configured
- [ ] Resource limits set (memory, CPU)

---

## Related Documentation

- [Robot Setup](robot-setup.md) - Execution agents
- [Scheduling](scheduling.md) - Cron configuration
- [REST API Reference](../../developer-guide/api-reference/orchestrator-rest.md)
- [WebSocket API](../../developer-guide/api-reference/orchestrator-websocket.md)
