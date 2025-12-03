# Internet-Connected Robot Deployment Guide

## Overview

Architecture: Centralized Orchestrator on one PC, Robots deployed to client PCs across **different networks** (internet-connected).

**Key Requirement**: Robots connect to orchestrator over the public internet, not LAN.

---

## Deployment Options

### Option 1: Cloud Hosting (Recommended for Production)

**Deploy orchestrator to cloud provider**:
- AWS (EC2), Azure (VM), DigitalOcean (Droplet), or Linode
- Fixed public IP or domain name
- Professional SSL certificate (Let's Encrypt)
- DDoS protection and firewall rules

**Pros**:
- ✅ High availability (99.9% uptime)
- ✅ Scalable (add more instances if needed)
- ✅ No home network configuration required
- ✅ Professional security posture

**Cons**:
- ❌ Monthly cost (~$5-20/month for small VM)
- ❌ Requires cloud provider account

**Cost Estimate**:
- DigitalOcean Basic Droplet: $6/month (1 vCPU, 1GB RAM)
- AWS EC2 t3.micro: ~$8/month (2 vCPU, 1GB RAM)
- Domain name: ~$12/year

---

### Option 2: Dynamic DNS + Port Forwarding (Budget Option)

**Use your PC as server with public access**:
- Register free Dynamic DNS (No-IP, DuckDNS, Dynu)
- Configure router port forwarding (8000 → PC IP)
- Use Certbot for SSL certificate
- Keep PC running 24/7

**Pros**:
- ✅ Zero monthly cost
- ✅ Full control over hardware

**Cons**:
- ❌ Residential internet uptime not guaranteed
- ❌ ISP may block port 80/443 or use CGNAT
- ❌ Manual router configuration required
- ❌ Power/internet outages break system
- ❌ Security responsibility on you

**Not Recommended If**:
- ISP uses CGNAT (Carrier-Grade NAT) - many mobile ISPs do this
- Dynamic IP changes frequently
- Unreliable power/internet

---

### Option 3: Tunneling Solutions (Easiest Setup)

**Use tunneling service to expose local orchestrator**:

#### A. Cloudflare Tunnel (Free, Recommended)
```bash
# Install cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

cloudflared tunnel create casare-orchestrator
cloudflared tunnel route dns casare-orchestrator orchestrator.yourdomain.com
cloudflared tunnel run casare-orchestrator
```

**Config** (`~/.cloudflared/config.yml`):
```yaml
url: http://localhost:8000
tunnel: <TUNNEL-ID>
credentials-file: /path/to/credentials.json
```

**Pros**:
- ✅ Free tier available
- ✅ Automatic SSL
- ✅ No port forwarding needed
- ✅ DDoS protection included
- ✅ Works behind CGNAT

**Cons**:
- ❌ Requires Cloudflare account + domain
- ❌ Still need PC running 24/7

#### B. ngrok (Quick Testing)
```bash
ngrok http 8000
```

**Pros**:
- ✅ Zero config testing
- ✅ Instant public URL

**Cons**:
- ❌ Random URL on free tier
- ❌ $8/month for fixed domain
- ❌ Session limits on free tier

#### C. Tailscale (VPN Mesh Network)
- Creates secure mesh VPN between orchestrator and robots
- No public exposure, all traffic encrypted
- Free for up to 100 devices

**Pros**:
- ✅ Zero-trust security model
- ✅ No public internet exposure
- ✅ Works behind any NAT/firewall

**Cons**:
- ❌ Requires Tailscale client on every robot
- ❌ Each robot needs internet + VPN connection

---

## Security Requirements (Mandatory)

### 1. HTTPS/WSS (SSL/TLS Encryption)

**Why**: HTTP/WS traffic is plaintext over internet - credentials visible to ISPs/attackers.

**Implementation**:

**Option A - Reverse Proxy (nginx)**:
```nginx
# /etc/nginx/sites-available/orchestrator
server {
    listen 443 ssl http2;
    server_name orchestrator.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/orchestrator.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/orchestrator.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Option B - FastAPI SSL Support**:
```python
# src/casare_rpa/infrastructure/orchestrator/api/main.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "casare_rpa.infrastructure.orchestrator.api.main:app",
        host="0.0.0.0",
        port=8443,
        ssl_keyfile="/path/to/privkey.pem",
        ssl_certfile="/path/to/fullchain.pem",
    )
```

**Get Free SSL Certificate**:
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate (nginx)
sudo certbot --nginx -d orchestrator.yourdomain.com

# Get certificate (standalone - if no nginx)
sudo certbot certonly --standalone -d orchestrator.yourdomain.com
```

---

### 2. API Authentication for Robots

**Current Issue**: No authentication - anyone can connect to orchestrator.

**Solution**: Implement API key authentication for robots.

**Step 1 - Generate Robot API Keys**:
```python
# tools/generate_robot_token.py
import secrets
import hashlib

def generate_robot_token(robot_id: str) -> str:
    """Generate secure API token for robot."""
    token = secrets.token_urlsafe(32)
    print(f"Robot ID: {robot_id}")
    print(f"API Token: {token}")
    print(f"Add to robot config: ROBOT_API_TOKEN={token}")

    # Hash for storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    print(f"Store in DB: {token_hash}")
    return token

if __name__ == "__main__":
    generate_robot_token("robot-001")
```

**Step 2 - Add Authentication Middleware**:
```python
# src/casare_rpa/orchestrator/api/auth.py
from fastapi import Header, HTTPException, status
import hashlib

# TODO: Load from database or environment
VALID_TOKEN_HASHES = {
    "abc123hash": "robot-001",  # Replace with actual hashes
}

async def verify_robot_token(x_api_token: str = Header(...)) -> str:
    """
    Verify robot API token from X-Api-Token header.

    Returns:
        robot_id if valid

    Raises:
        HTTPException 401 if invalid
    """
    token_hash = hashlib.sha256(x_api_token.encode()).hexdigest()

    robot_id = VALID_TOKEN_HASHES.get(token_hash)
    if not robot_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return robot_id
```

**Step 3 - Protect Endpoints**:
```python
# src/casare_rpa/orchestrator/api/routers/metrics.py
from fastapi import Depends
from ..auth import verify_robot_token

@router.post("/jobs/claim", dependencies=[Depends(verify_robot_token)])
async def claim_job():
    """Protected: requires X-Api-Token header."""
    pass
```

**Step 4 - Robot Configuration**:
```yaml
# config/robot.yaml (on client PC)
orchestrator:
  url: "https://orchestrator.yourdomain.com"  # HTTPS now
  api_token: "xJk3m9PqR7TvWn2LsZ8Yf5Gh1Dc4Ba6N"  # From generate_robot_token.py
```

---

### 3. Rate Limiting (DDoS Protection)

**Prevent abuse if orchestrator URL is discovered**:

```python
# src/casare_rpa/orchestrator/api/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/metrics/robots")
@limiter.limit("100/minute")  # Max 100 requests per minute per IP
async def get_robots(request: Request):
    pass
```

**Install**:
```bash
pip install slowapi
```

---

### 4. Firewall Rules

**Cloud VM** (AWS Security Group / DigitalOcean Firewall):
```
Allow Inbound:
- Port 443 (HTTPS) from 0.0.0.0/0
- Port 22 (SSH) from YOUR_IP only

Allow Outbound:
- All traffic (for database, external APIs)
```

**Local PC** (Windows Firewall):
```powershell
# Allow inbound on port 8000 (if using port forwarding)
New-NetFirewallRule -DisplayName "CasareRPA Orchestrator" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

---

## Robot Configuration Changes

### Before (LAN):
```yaml
# config/robot.yaml
orchestrator:
  url: "http://192.168.1.100:8000"  # Local IP, HTTP
```

### After (Internet):
```yaml
# config/robot.yaml
orchestrator:
  url: "https://orchestrator.yourdomain.com"  # Public domain, HTTPS
  api_token: "xJk3m9PqR7TvWn2LsZ8Yf5Gh1Dc4Ba6N"

connection:
  timeout: 30  # Increased for internet latency
  retry_attempts: 5
  retry_delay: 10
```

---

## Recommended Setup for Your Use Case

**Phase 1 - Immediate Testing** (1-2 hours):
1. Use **Cloudflare Tunnel** or **ngrok** for quick setup
2. Keep orchestrator on your PC
3. Test with 1-2 robots on client PCs

**Phase 2 - Production** (1-2 days):
1. Deploy orchestrator to **DigitalOcean Droplet** ($6/month)
2. Register domain name or use Dynamic DNS
3. Install Let's Encrypt SSL certificate
4. Implement API token authentication
5. Configure robots with HTTPS URL and tokens

---

## Cost Comparison

| Option | Setup Time | Monthly Cost | Reliability | Security |
|--------|------------|--------------|-------------|----------|
| Cloud VM (DigitalOcean) | 2 hours | $6-12 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Cloudflare Tunnel | 1 hour | $0 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Dynamic DNS + Port Forward | 3 hours | $0 | ⭐⭐ | ⭐⭐⭐ |
| ngrok | 5 minutes | $8 (for fixed URL) | ⭐⭐ | ⭐⭐⭐ |

---

## Next Steps

1. **Choose deployment option** (recommend: Cloudflare Tunnel for testing, DigitalOcean for production)
2. **Implement HTTPS** (required for internet deployment)
3. **Add API authentication** (protect against unauthorized access)
4. **Test with 1 remote robot** before deploying to all clients
5. **Monitor logs** for connection issues, authentication failures

---

## Questions to Answer

1. Do you want to start with Cloudflare Tunnel (free, quick) or go straight to cloud VM?
2. Do you already have a domain name, or should we use free Dynamic DNS?
3. How many robots do you expect to deploy initially?
4. What's your budget for hosting (if any)?
