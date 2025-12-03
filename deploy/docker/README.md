# CasareRPA Docker Deployment Guide

Complete Docker setup for CasareRPA with multi-stage builds, multiple deployment profiles, and cloud platform support.

## Quick Start

### Development Stack (5 minutes)
```bash
# Start all dev services (db, redis, orchestrator)
docker compose --profile dev up -d

# View logs
docker compose logs -f orchestrator

# Stop services
docker compose down
```

Visit: http://localhost:8001 (Orchestrator API)

### Production Stack
```bash
# Build and start with robot pool
docker compose --profile prod up -d

# Scale robots
docker compose up -d --scale browser-robot=5

# Stop services
docker compose down
```

## Docker Images

### Build Targets

Each `docker build --target <name>` creates a specialized image:

#### 1. **orchestrator** (full dependencies)
- Multi-threaded FastAPI server
- 4 Uvicorn workers by default
- For Docker Compose, local development
- Full PyProject dependencies

```bash
docker build --target orchestrator -t casare-orchestrator:latest .
docker run -p 8000:8000 casare-orchestrator:latest
```

#### 2. **orchestrator-cloud** (minimal dependencies)
- Single-threaded, cloud-optimized
- 1 Uvicorn worker
- For Fly.io, Railway, Render
- Uses orchestrator/requirements.txt (lightweight)

```bash
docker build --target orchestrator-cloud -t casare-orch-cloud:latest .
docker run -p 8000:8000 casare-orch-cloud:latest
```

#### 3. **robot** (all browsers)
- Playwright with Chromium, Firefox, WebKit
- Full browser automation capability
- ~3GB image size
- For production with multiple browser support

```bash
docker build --target robot -t casare-robot:latest .
docker run -e ORCHESTRATOR_URL=http://host.docker.internal:8000 casare-robot:latest
```

#### 4. **robot-headless** (chromium only)
- Lightweight Chromium-only variant
- ~1.5GB image size
- Faster builds and pulls
- For cost-conscious deployments

```bash
docker build --target robot-headless -t casare-robot-headless:latest .
```

#### 5. **development** (testing & debug)
- Includes pytest, mypy, ruff
- For CI/CD pipeline testing
- Hot-reload ready

```bash
docker build --target development -t casare-dev:latest .
docker run -v $(pwd):/app casare-dev:latest pytest tests/ -v
```

## Docker Compose Profiles

### Profile: dev (Development)
Services: PostgreSQL, Redis, Orchestrator, pgAdmin, Redis Commander
- **Use for:** Local development, debugging
- **Start:** `docker compose --profile dev up -d`
- **Ports:**
  - `5433` → PostgreSQL
  - `6380` → Redis
  - `8001` → Orchestrator API
  - `5050` → pgAdmin
  - `8081` → Redis Commander
- **Features:** Hot reload, development tools included

### Profile: prod (Production)
Services: PostgreSQL, Redis, Orchestrator, Robot Pool (2 instances)
- **Use for:** Staging, production-like testing
- **Start:** `docker compose --profile prod up -d`
- **Scale robots:** `docker compose up -d --scale browser-robot=5`
- **Resources:** Limited to 2 CPUs / 4GB RAM per robot
- **Ports:**
  - `5433` → PostgreSQL
  - `6380` → Redis
  - `8001` → Orchestrator API

### Profile: full (Complete Stack)
Services: All services + Prometheus + Grafana + Headless Robots
- **Use for:** End-to-end testing, monitoring verification
- **Start:** `docker compose --profile full up -d`
- **Ports:**
  - All from prod +
  - `9090` → Prometheus
  - `3000` → Grafana

### Profile: monitoring
Services: Prometheus + Grafana only
- **Use for:** Add observability to existing stack
- **Start:** `docker compose --profile monitoring up -d`
- **Connect to:** Any running orchestrator

### Profile: tools
Services: pgAdmin, Redis Commander
- **Use for:** Database/cache inspection
- **Start:** `docker compose --profile tools up -d`

## Build Configuration

### BuildKit for Faster Builds
Enable BuildKit for parallel layer building:

```bash
# Linux/Mac
export DOCKER_BUILDKIT=1
docker build --target orchestrator -t casare-orch .

# Windows
$env:DOCKER_BUILDKIT=1
docker build --target orchestrator -t casare-orch .
```

### Multi-Stage Layer Caching
Dockerfile is structured for optimal caching:
1. `python-base` - Common Python 3.12 environment
2. `builder` → `orchestrator` (full deps)
3. `builder-minimal` → `orchestrator-cloud` (lightweight)
4. `robot-base` → `robot` / `robot-headless` (playwright-based)

Changing `src/` code doesn't rebuild pip dependencies.

## Environment Variables

### Common Variables
```bash
# Application
CASARE_ENV=production          # development|staging|production
CASARE_LOG_LEVEL=INFO          # DEBUG|INFO|WARNING|ERROR

# Network
HOST=0.0.0.0
PORT=8000
WORKERS=4                       # Uvicorn workers (orchestrator)

# Database
DATABASE_URL=postgresql://...   # Auto-set in docker-compose
POSTGRES_USER=casare
POSTGRES_PASSWORD=changeme      # CHANGE IN PRODUCTION

# Redis
REDIS_URL=redis://redis:6379   # Auto-set in docker-compose

# Security
JWT_SECRET_KEY=<generate>       # Use: openssl rand -hex 32
API_SECRET=<generate>           # Use: openssl rand -hex 32
CORS_ORIGINS=http://localhost:3000,https://example.com

# Robot Configuration
ROBOT_HEARTBEAT_TIMEOUT=90      # Seconds
JOB_TIMEOUT_DEFAULT=3600        # Seconds
WS_PING_INTERVAL=30             # Seconds

# Monitoring
PROMETHEUS_HOST_PORT=9090
GRAFANA_USER=admin
GRAFANA_PASSWORD=<generate>
```

### Generate Secrets
```bash
# Linux/Mac
openssl rand -hex 32

# Windows (PowerShell)
[System.Convert]::ToBase64String(([System.Security.Cryptography.RNGCryptoServiceProvider]::new()).GetBytes(32))
```

## Health Checks

All services include health checks:

```bash
# Check orchestrator health
curl http://localhost:8001/health/live

# Check database
docker exec casare-db pg_isready -U casare

# Check Redis
docker exec casare-redis redis-cli ping

# View health status
docker compose ps
```

## Volumes & Persistence

### Development Stack Volumes
- `pgdata` → PostgreSQL database files
- `redisdata` → Redis persistence
- `pgadmindata` → pgAdmin configuration

### Production Stack Additional Volumes
- `browser-cache` → Playwright browser cache (shared between robots)
- `robot-data` → Robot execution logs and artifacts
- `headless-cache` → Headless robot browser cache

### Clean Data
```bash
# Remove all volumes (DESTRUCTIVE)
docker compose down -v

# Remove specific volume
docker volume rm casare-pgdata
```

## Network Configuration

### Internal Network
- **Bridge network:** `casare-network` (172.28.0.0/16)
- **Service names** resolve automatically (e.g., `db:5432`, `redis:6379`)

### Expose Services
```bash
# Forward specific port
docker compose exec orchestrator curl http://db:5432

# Access from host
curl http://localhost:8001/health
```

## Monitoring & Logging

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f orchestrator

# Last 100 lines
docker compose logs --tail=100 orchestrator
```

### Prometheus Metrics
- Access: http://localhost:9090
- Data retention: 15 days
- Scrape interval: 15s (configurable in prometheus.yml)

### Grafana Dashboards
- Access: http://localhost:3000
- Default credentials: admin/admin
- Auto-provisioned datasources and dashboards

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8001  # Linux/Mac
netstat -ano | findstr :8001  # Windows

# Kill process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

### Database Connection Failed
```bash
# Check database status
docker compose ps db

# Check logs
docker compose logs db

# Verify credentials
echo "POSTGRES_USER=${POSTGRES_USER:-casare}"
echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-changeme}"
```

### Out of Disk Space
```bash
# Clean up dangling images/containers
docker system prune -a

# Check disk usage
docker system df
```

### Memory Issues (Robot Pool)
```bash
# Reduce robot replicas
docker compose down
docker compose --profile prod up -d --scale browser-robot=2

# Check resource limits in docker-compose.yml
```

## Production Checklist

Before deploying to production:

- [ ] Change `POSTGRES_PASSWORD` (use strong password)
- [ ] Generate `JWT_SECRET_KEY` and `API_SECRET`
- [ ] Set `CASARE_ENV=production`
- [ ] Set `CORS_ORIGINS` to specific domains
- [ ] Configure `ROBOT_HEARTBEAT_TIMEOUT` appropriately
- [ ] Enable SSL/TLS (use reverse proxy like nginx)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log rotation
- [ ] Set resource limits (RAM, CPU) for robots
- [ ] Enable automatic backups for PostgreSQL
- [ ] Test health checks
- [ ] Document custom configuration

## Advanced Configuration

### Custom Database Initialization
Place SQL files in `deploy/docker/init-db.d/` (alphabetically executed):
```bash
deploy/docker/
├── init-db.d/
│   ├── 01-schema.sql
│   ├── 02-seed-data.sql
│   └── 03-permissions.sql
```

### Custom Prometheus Configuration
Edit `deploy/docker/prometheus.yml`:
- Scrape targets
- Alert rules
- Data retention

### Custom Grafana Dashboards
Place in `deploy/docker/grafana/provisioning/dashboards/`

### Robot Resource Constraints
Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

## Cloud Deployment

### Fly.io
See: `deploy/platforms/fly.toml`
```bash
fly launch --config deploy/platforms/fly.toml
fly secrets set JWT_SECRET_KEY=...
fly deploy
```

### Railway
See: `deploy/platforms/railway.toml`
Connect GitHub repo to Railway dashboard.

### Render
See: `deploy/platforms/render.yaml`
Create Blueprint on Render dashboard from this file.

## Building Custom Images

### Add Custom Dependencies
1. Update `pyproject.toml` or `deploy/orchestrator/requirements.txt`
2. Rebuild:
```bash
docker compose build orchestrator --no-cache
```

### Custom Robot Image
```dockerfile
# Dockerfile.custom
FROM casare-robot:latest
RUN pip install custom-package
```

```bash
docker build -f Dockerfile.custom -t casare-robot-custom .
```

## Security Best Practices

1. **Non-root User Execution**
   - Orchestrator runs as `casare` user
   - Robots run as `robot` user

2. **Secrets Management**
   - Never commit secrets to repository
   - Use environment variables
   - Rotate regularly in production

3. **Network Isolation**
   - Internal bridge network (`casare-network`)
   - Only expose necessary ports
   - Use firewall rules

4. **Image Scanning**
   ```bash
   docker scan casare-orchestrator:latest
   trivy image casare-orchestrator:latest
   ```

5. **Registry Authentication**
   - Use private registries in production
   - Implement image signing

## Performance Tuning

### Orchestrator Performance
- Increase `WORKERS` (CPU-bound, use 2x CPU cores)
- Adjust `WS_PING_INTERVAL` for stability
- Configure connection pooling in PostgreSQL

### Robot Performance
- Use `robot-headless` for text-only workflows
- Scale horizontally (replicas) not vertically
- Monitor browser cache (shared volume)

### Database Performance
- Increase PostgreSQL `shared_buffers` (25% of RAM)
- Tune `effective_cache_size` (50-75% of RAM)
- Set up replication for high-availability

### Redis Performance
- Increase `maxmemory` for larger job queues
- Use `RDB` for persistence (slower) or `AOF` (faster)
- Monitor eviction policy (`allkeys-lru` by default)

## Maintenance

### Regular Tasks
- [ ] Backup PostgreSQL database daily
- [ ] Rotate secrets monthly
- [ ] Update base images (Python, Alpine, Playwright)
- [ ] Review logs and metrics
- [ ] Clean up old volumes/images

### Updating CasareRPA
```bash
git pull origin main
docker compose build --no-cache
docker compose up -d
```

## Support

- GitHub Issues: https://github.com/casarerpa/casarerpa/issues
- Documentation: https://docs.casarerpa.io
- Slack Community: [link]
