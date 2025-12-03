# Cloud Platform Deployment Guides

Deploy CasareRPA Orchestrator to cloud platforms with automated configuration.

## Platform Comparison

| Platform | Type | Cost | Setup Time | Scaling | Cold Starts | Best For |
|----------|------|------|-----------|---------|-------------|----------|
| **Fly.io** | Container | $5-100/mo | 5 min | Auto | < 100ms | Global apps, WebSockets |
| **Railway** | Container | $5-100/mo | 5 min | Manual | 1-2s | Simple deployments, GitHub CI |
| **Render** | Container | $7-50/mo | 10 min | Auto | 2-5s | Free tier with caveats |
| **Docker Compose** | Local/VPS | Varies | 10 min | Manual | N/A | Development, self-hosted |

## Fly.io Deployment

**Best for:** Global distribution, WebSocket support, automatic scaling

### Prerequisites
```bash
# 1. Install Fly CLI
# https://fly.io/docs/hands-on/install-flyctl/

# 2. Create Fly account
fly auth signup
fly auth login

# 3. Install Postgres plugin
fly postgres create --name casare-db
```

### Deploy
```bash
# From project root
cd /path/to/casarerpa

# 1. Launch app
fly launch --config deploy/platforms/fly.toml

# 2. Attach database
fly postgres attach casare-db

# 3. Generate secrets
JWT_SECRET=$(openssl rand -hex 32)
API_SECRET=$(openssl rand -hex 32)

# 4. Set secrets
fly secrets set JWT_SECRET_KEY=$JWT_SECRET
fly secrets set API_SECRET=$API_SECRET
fly secrets set SUPABASE_URL=https://your-project.supabase.co
fly secrets set SUPABASE_KEY=your-key

# 5. Deploy
fly deploy
```

### Verification
```bash
# Check deployment status
fly status

# View logs
fly logs

# Test health endpoint
curl https://casare-orchestrator.fly.dev/health/live

# SSH into machine
fly ssh console
```

### Configuration
Edit `fly.toml`:
- Change `primary_region` (default: iad)
- Adjust `WORKERS` (default: 1)
- Modify auto-stop behavior
- Add custom environment variables

### Costs
- $5/month base (always-on machine)
- $0.01–0.15 per CPU-hour (variable)
- $10-30/month PostgreSQL (shared instance)
- **Typical:** $20-50/month for small deployments

### Scaling
```bash
# Scale to multiple regions
fly regions add lhr syd  # London, Sydney

# Add machines
fly machine create --region iad

# Scale down
fly scale count 0
```

## Railway Deployment

**Best for:** GitHub-connected deployments, simple CI/CD

### Prerequisites
```bash
# 1. Create Railway account
# https://railway.app

# 2. Connect GitHub repository
# Via Railway dashboard
```

### Deploy via Dashboard
1. Create new project
2. Add PostgreSQL plugin
3. Select "GitHub" → Choose `casarerpa` repository
4. Configure service:
   - **Build:** `./deploy/docker/Dockerfile`
   - **Build Args:** `target=orchestrator-cloud`
   - **Start:** Port detection auto
5. Environment variables (auto from PostgreSQL):
   - `DATABASE_URL` ← PostgreSQL plugin
   - `JWT_SECRET_KEY` ← Generate and set
   - `API_SECRET` ← Generate and set
6. Deploy

### Verification
```bash
# View logs in dashboard
# Or: railway logs

# Test health
curl https://your-railway-domain/health/live
```

### Configuration
Edit `railway.toml`:
- Adjust `WORKERS` (default: 2)
- Modify build cache settings
- Add custom environment variables

### Costs
- Free tier: $5 credit/month (covers small app)
- Pay-as-you-go: ~$10/month for small deployments
- PostgreSQL: Included in free tier (limited)

### GitHub Integration
```bash
# Auto-deploy on push
git push origin main
# → Railway detects, builds, deploys automatically

# Disable auto-deploy
# Railway dashboard → Settings → Build & Deploy → Uncheck Auto-deploy
```

## Render.com Deployment

**Best for:** Simple deployments, free tier starter

### Prerequisites
```bash
# 1. Create Render account
# https://render.com

# 2. Connect GitHub repository
# Via Render dashboard
```

### Deploy via Blueprint
1. Create new Blueprint
2. Select GitHub repository
3. Select branch (typically `main`)
4. Render reads `deploy/platforms/render.yaml`
5. Services created automatically:
   - PostgreSQL database
   - Web service (Orchestrator)
   - Redis cache
6. Set secrets in dashboard:
   - `JWT_SECRET_KEY`
   - `API_SECRET`
7. Deploy

### Verification
```bash
# View deployment status in dashboard
# Logs viewable via Render dashboard

# Test health
curl https://your-render-service.onrender.com/health/live
```

### Configuration
Edit `render.yaml`:
- Adjust `plan` (starter, standard, pro)
- Change `region` (oregon, frankfurt, singapore, sydney)
- Modify environment variables
- Update resource allocations

### Costs
- Free tier: Limited hours per month
- Paid plans: ~$12-30/month for small deployments
- PostgreSQL: $15/month (smallest paid tier)
- Redis: $5/month

### Auto-Deploy
```bash
# Enable auto-deploy on push
git push origin main
# → Render detects, builds, deploys

# Disable auto-deploy
# Render dashboard → Settings → Auto-Deploy → Uncheck
```

## Docker Compose (Self-Hosted)

**Best for:** Local development, VPS, complete control

### Prerequisites
- Docker & Docker Compose installed
- Linux/Mac or Windows with WSL2
- Terminal access

### Deploy
```bash
# 1. Clone repository
git clone https://github.com/casarerpa/casarerpa.git
cd casarerpa

# 2. Configure environment
cp deploy/docker/.env.example deploy/docker/.env
# Edit deploy/docker/.env with production values

# 3. Start services
cd deploy/docker
docker compose --profile prod up -d

# 4. Verify
docker compose ps
curl http://localhost:8001/health/live
```

### Configuration
Create `deploy/docker/.env`:
```bash
# Database
POSTGRES_DB=casare_rpa
POSTGRES_USER=casare
POSTGRES_PASSWORD=<strong-password>

# Security
JWT_SECRET_KEY=<generated-secret>
API_SECRET=<generated-secret>

# Server
ORCHESTRATOR_WORKERS=4
ROBOT_REPLICAS=2

# Monitoring (optional)
PROMETHEUS_HOST_PORT=9090
GRAFANA_USER=admin
GRAFANA_PASSWORD=<strong-password>
```

### Scaling Robots
```bash
# Scale to 5 robots
docker compose --profile prod up -d --scale browser-robot=5

# Scale to 3
docker compose --profile prod up -d --scale browser-robot=3

# View status
docker compose ps
```

### Costs
- Server: $5-50/month (VPS)
- Database: Included (PostgreSQL on same machine)
- Redis: Included
- **Typical:** $5-20/month for small VPS

### Maintenance
```bash
# View logs
docker compose logs -f orchestrator

# Backup database
docker exec casare-db pg_dump -U casare casare_rpa > backup.sql

# Update application
git pull origin main
docker compose build --no-cache
docker compose up -d
```

## Environment Variables by Platform

### Fly.io (fly.toml)
```toml
[env]
  JWT_SECRET_KEY = "generated"
  API_SECRET = "generated"
  ROBOT_HEARTBEAT_TIMEOUT = "90"
```

### Railway (railway.toml)
```toml
[env]
JWT_SECRET_KEY = "set in dashboard"
API_SECRET = "set in dashboard"
ROBOT_HEARTBEAT_TIMEOUT = "90"
```

### Render (render.yaml)
```yaml
- key: JWT_SECRET_KEY
  scope: RUN_AND_BUILD
- key: API_SECRET
  scope: RUN_AND_BUILD
```

### Docker Compose (.env)
```bash
JWT_SECRET_KEY=<generated>
API_SECRET=<generated>
POSTGRES_PASSWORD=<strong-password>
ROBOT_REPLICAS=2
```

## Generate Secrets

```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
[System.Convert]::ToBase64String(([System.Security.Cryptography.RNGCryptoServiceProvider]::new()).GetBytes(32))

# Python
import secrets
secrets.token_hex(32)
```

## Monitoring & Logging

### Platform-Specific Logging
- **Fly.io:** `fly logs` or dashboard
- **Railway:** Railway dashboard → Logs
- **Render:** Render dashboard → Logs
- **Docker:** `docker compose logs -f`

### Health Checks
```bash
curl https://<your-domain>/health/live
```

### Prometheus Metrics
(Optional, requires monitoring profile)
- Fly.io: Configure in fly.toml
- Railway/Render: Set up external monitoring
- Docker: `http://localhost:9090`

## Troubleshooting

### Deployment Fails
```bash
# Check build logs
fly logs  # Fly.io
# Or via dashboard (Railway/Render)

# Verify Dockerfile target
docker build --target orchestrator-cloud .

# Test locally first
docker compose --profile dev up -d
```

### Database Connection Error
```bash
# Check DATABASE_URL format
postgresql://user:password@host:5432/database

# Verify database is healthy
fly postgres connect casare-db  # Fly.io
# Or check dashboard (Railway/Render)
```

### Out of Memory
- Reduce `WORKERS` (1-2 for small servers)
- Use `robot-headless` instead of `robot`
- Reduce `ROBOT_REPLICAS`

### High Cold Start Time
- Fly.io: Use `auto_start_machines = true`
- Railway: Enable paid tier
- Render: Switch to standard plan

## Migration Between Platforms

### From Local to Fly.io
```bash
# 1. Backup local database
docker exec casare-db pg_dump -U casare casare_rpa > backup.sql

# 2. Deploy to Fly.io (follow Fly.io section)

# 3. Restore database
fly ssh console
psql -U casare -d casare_rpa < backup.sql
```

### From Fly.io to Docker Compose
```bash
# 1. Backup Fly.io database
fly ssh console
pg_dump -U postgres -d postgres > backup.sql

# 2. Move backup to local machine
scp backup.sql local:/path/to/

# 3. Restore to Docker Compose
docker exec casare-db psql -U casare casare_rpa < backup.sql
```

## Security Best Practices

1. **Secrets Management**
   - Never commit secrets to repository
   - Use platform secret management
   - Rotate regularly (monthly)

2. **HTTPS/TLS**
   - All platforms enforce HTTPS
   - Generate certificates automatically
   - Verify certificate chains

3. **Network Isolation**
   - Use private databases (not public)
   - Restrict CORS to known domains
   - Use VPCs/private networks if available

4. **Access Control**
   - Limit database credentials
   - Use separate API keys for robots
   - Enable audit logging

5. **Monitoring**
   - Set up alerts for errors
   - Monitor resource usage
   - Track API latency

## Support

- Fly.io: https://community.fly.io
- Railway: https://railway.app/support
- Render: https://render.com/docs
- CasareRPA: https://github.com/casarerpa/casarerpa/issues
