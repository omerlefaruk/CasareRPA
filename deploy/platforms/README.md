# CasareRPA Cloud Platform Deployment

Platform-specific deployment configurations for the CasareRPA Orchestrator.

## Quick Start

All platforms use the unified Dockerfile at `deploy/docker/Dockerfile` with the `orchestrator-cloud` target.

### Prerequisites

1. Generate an API secret:
   ```bash
   openssl rand -hex 32
   ```

2. (Optional) Set up Supabase:
   - Create project at https://app.supabase.com
   - Get URL and anon key from Settings > API

---

## Fly.io

**Best for:** Global edge deployment, persistent WebSocket connections

### Deployment

```bash
# Install CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch (first time)
fly launch --config deploy/platforms/fly.toml

# Create PostgreSQL
fly pg create --name casare-db

# Attach database
fly pg attach casare-db

# Set secrets
fly secrets set API_SECRET=<your-secret>
fly secrets set SUPABASE_URL=https://xxx.supabase.co
fly secrets set SUPABASE_KEY=<your-key>

# Deploy
fly deploy
```

### Scaling

```bash
# Scale horizontally
fly scale count 3

# Scale vertically
fly scale vm shared-cpu-2x
fly scale memory 1024
```

### Logs

```bash
fly logs
fly logs --app casare-orchestrator
```

---

## Railway

**Best for:** Easy deployment, built-in PostgreSQL/Redis

### Deployment

```bash
# Install CLI
npm i -g @railway/cli

# Login
railway login

# Create project
railway init

# Add PostgreSQL
railway add --plugin postgresql

# Add Redis (optional)
railway add --plugin redis

# Set secrets in dashboard
# Then deploy
railway up
```

### Environment Variables

Set in Railway dashboard:
- `API_SECRET` (required)
- `SUPABASE_URL` (optional)
- `SUPABASE_KEY` (optional)

Auto-populated by plugins:
- `DATABASE_URL`
- `REDIS_URL`

### Domains

```bash
railway domain
```

---

## Render

**Best for:** Automatic scaling, managed databases

### Deployment

1. Push code to GitHub
2. Go to https://dashboard.render.com/blueprints
3. Click "New Blueprint Instance"
4. Connect repository
5. Select `deploy/platforms/render.yaml`
6. Set secrets in dashboard
7. Deploy

### Manual Setup

If not using blueprint:

1. Create Web Service:
   - Runtime: Docker
   - Dockerfile: `deploy/docker/Dockerfile`
   - Docker Target: `orchestrator-cloud`

2. Create PostgreSQL database

3. Create Redis instance (optional)

4. Link services via environment variables

### Scaling

Configure in `render.yaml` or dashboard:
```yaml
scaling:
  minInstances: 1
  maxInstances: 5
  targetMemoryPercent: 80
```

---

## Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `PORT` | Yes | Server port | `8000` |
| `HOST` | No | Bind address | `0.0.0.0` |
| `WORKERS` | No | Uvicorn workers | `1` |
| `DATABASE_URL` | Yes | PostgreSQL connection string | - |
| `REDIS_URL` | No | Redis connection string | - |
| `API_SECRET` | Yes | Admin API authentication | - |
| `CORS_ORIGINS` | No | Allowed CORS origins | `*` |
| `SUPABASE_URL` | No | Supabase project URL | - |
| `SUPABASE_KEY` | No | Supabase anon key | - |
| `ROBOT_HEARTBEAT_TIMEOUT` | No | Robot timeout (seconds) | `90` |
| `JOB_TIMEOUT_DEFAULT` | No | Job timeout (seconds) | `3600` |
| `WS_PING_INTERVAL` | No | WebSocket ping interval | `30` |

---

## Health Checks

All platforms should configure health checks to:
- Path: `/health`
- Interval: 30s
- Timeout: 10s

---

## Connecting Robots

After deployment, configure robots to connect:

```bash
# Get orchestrator URL
ORCHESTRATOR_URL=https://casare-orchestrator.fly.dev  # or your domain

# Start robot
python -m casare_rpa.robot.cli start \
  --name "Robot1" \
  --orchestrator-url $ORCHESTRATOR_URL \
  --api-key <robot-api-key>
```

---

## Monitoring

### Metrics Endpoint

All deployments expose metrics at `/metrics` for Prometheus scraping.

### Logs

- **Fly.io:** `fly logs`
- **Railway:** Dashboard or `railway logs`
- **Render:** Dashboard logs tab

---

## Cost Comparison (Approximate)

| Platform | Free Tier | Starter | Notes |
|----------|-----------|---------|-------|
| Fly.io | 3 shared VMs | $1.94/mo | Global regions |
| Railway | $5/mo credit | Usage-based | Easy plugins |
| Render | Limited | $7/mo | Auto-scaling |

---

## Troubleshooting

### Connection Refused

1. Check service is running
2. Verify PORT environment variable
3. Check health endpoint: `curl https://your-domain/health`

### Database Connection Failed

1. Verify DATABASE_URL is set
2. Check database service is healthy
3. Test connection: `psql $DATABASE_URL`

### WebSocket Issues

1. Ensure `auto_stop_machines = false` (Fly.io)
2. Check WebSocket upgrade headers are passed
3. Verify CORS configuration

### Slow Cold Starts

1. Increase minimum instances
2. Use larger VM size
3. Enable keep-alive/warm-up
