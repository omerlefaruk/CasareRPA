# Cloudflare Tunnel Quick Start

Deploy CasareRPA orchestrator with Cloudflare Tunnel (zero-trust networking).

**Benefits**:
- ✅ Free tier available
- ✅ Automatic HTTPS/SSL
- ✅ No port forwarding needed
- ✅ Works behind CGNAT/NAT
- ✅ DDoS protection included
- ✅ No public IP required

---

## Prerequisites

1. **Cloudflare Account** (free): https://dash.cloudflare.com/sign-up
2. **Domain Name** added to Cloudflare (free or paid)
3. **Orchestrator PC** running Windows/Linux/macOS

---

## Step 1: Install cloudflared

### Windows
```powershell
# Download installer
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "C:\Program Files\cloudflared.exe"

# Add to PATH
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files", "Machine")
```

### Linux
```bash
# Debian/Ubuntu
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
```

---

## Step 2: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This opens browser for authentication. Select your domain.

---

## Step 3: Create Tunnel

```bash
# Create tunnel named 'casare-orchestrator'
cloudflared tunnel create casare-orchestrator

# Output:
# Created tunnel casare-orchestrator with id abc123-def456-ghi789
# Credentials file: C:\Users\YourUser\.cloudflared\abc123-def456-ghi789.json
```

**Save the tunnel ID** (e.g., `abc123-def456-ghi789`).

---

## Step 4: Configure DNS

```bash
# Route subdomain to tunnel
cloudflared tunnel route dns casare-orchestrator orchestrator.yourdomain.com
```

This creates a CNAME record pointing `orchestrator.yourdomain.com` to your tunnel.

---

## Step 5: Create Tunnel Configuration

### Windows
```powershell
# Create config directory
New-Item -ItemType Directory -Force -Path "C:\Users\$env:USERNAME\.cloudflared"

# Create config.yml
@"
url: http://localhost:8000
tunnel: abc123-def456-ghi789
credentials-file: C:\Users\$env:USERNAME\.cloudflared\abc123-def456-ghi789.json
"@ | Out-File -FilePath "C:\Users\$env:USERNAME\.cloudflared\config.yml" -Encoding UTF8
```

### Linux
```bash
# Create config file
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<EOF
url: http://localhost:8000
tunnel: abc123-def456-ghi789
credentials-file: /home/$(whoami)/.cloudflared/abc123-def456-ghi789.json
EOF
```

**Replace `abc123-def456-ghi789` with your actual tunnel ID.**

---

## Step 6: Start Orchestrator

```bash
# Terminal 1: Start FastAPI orchestrator
cd CasareRPA
python -m uvicorn casare_rpa.orchestrator.api.main:app --host 127.0.0.1 --port 8000
```

---

## Step 7: Start Cloudflare Tunnel

```bash
# Terminal 2: Start tunnel
cloudflared tunnel run casare-orchestrator
```

**Output**:
```
2025-11-29 INFO Connection registered connIndex=0
2025-11-29 INFO Route propagated successfully
Tunnel is now running at https://orchestrator.yourdomain.com
```

---

## Step 8: Test Connection

### From Browser
Open: https://orchestrator.yourdomain.com/health

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "casare-rpa-monitoring"
}
```

### From Robot PC (different network)
```bash
# Test health endpoint
curl https://orchestrator.yourdomain.com/health

# Test with API token (after generating)
curl -H "X-Api-Token: YOUR_TOKEN" https://orchestrator.yourdomain.com/api/v1/metrics/robots
```

---

## Step 9: Configure Robot

On client PC, edit `config/robot.yaml`:

```yaml
robot:
  id: "robot-001"

orchestrator:
  url: "https://orchestrator.yourdomain.com"  # ← Use HTTPS Cloudflare URL
  api_token: "YOUR_ROBOT_API_TOKEN_HERE"

connection:
  timeout: 30
  retry_attempts: 5
```

---

## Step 10: Run Tunnel as Service (Optional)

### Windows Service
```powershell
# Install as Windows service
cloudflared service install

# Start service
Start-Service cloudflared
```

### Linux systemd
```bash
# Install systemd service
sudo cloudflared service install

# Start and enable
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

---

## Monitoring & Logs

### View Tunnel Logs
```bash
# Linux
sudo journalctl -u cloudflared -f

# Windows (Event Viewer)
Get-EventLog -LogName Application -Source cloudflared -Newest 50
```

### Cloudflare Dashboard
View tunnel metrics at: https://dash.cloudflare.com/

Navigate to: **Zero Trust** → **Networks** → **Tunnels**

---

## Security Configuration

### Enable Robot Authentication

1. **Generate API tokens**:
```bash
python tools/generate_robot_token.py robot-001 robot-002 robot-003
```

2. **Add to orchestrator .env**:
```env
ROBOT_AUTH_ENABLED=true
ROBOT_TOKENS=robot-001:hash1,robot-002:hash2,robot-003:hash3
```

3. **Restart orchestrator**:
```bash
# Stop with Ctrl+C, then restart
python -m uvicorn casare_rpa.orchestrator.api.main:app --host 127.0.0.1 --port 8000
```

---

## Troubleshooting

### Tunnel Not Connecting
```bash
# Check tunnel status
cloudflared tunnel list

# Test configuration
cloudflared tunnel --config ~/.cloudflared/config.yml run
```

### DNS Not Resolving
```bash
# Verify DNS record
nslookup orchestrator.yourdomain.com

# Should show Cloudflare IP (104.x.x.x or 172.x.x.x)
```

### Robot Can't Connect
```bash
# Test from robot PC
curl -v https://orchestrator.yourdomain.com/health

# Check SSL certificate
openssl s_client -connect orchestrator.yourdomain.com:443 -servername orchestrator.yourdomain.com
```

### Orchestrator Not Responding
```bash
# Check local orchestrator
curl http://localhost:8000/health

# Check cloudflared is forwarding
cloudflared tunnel info casare-orchestrator
```

---

## Cost

**Free Tier Limits** (sufficient for most use cases):
- ✅ Unlimited bandwidth
- ✅ Up to 50 users
- ✅ Unlimited tunnels
- ✅ DDoS protection

**Paid Plans** (if needed):
- Teams Standard: $7/user/month (more users, advanced features)
- Teams Enterprise: Custom pricing (SLA, dedicated support)

For RPA orchestration with <50 robots: **Free tier is sufficient**.

---

## Next Steps

1. ✅ Tunnel running and accessible
2. Generate robot API tokens
3. Configure robots with HTTPS URL
4. Test job execution from remote robot
5. Monitor dashboard at https://orchestrator.yourdomain.com
6. Set up database persistence (PostgreSQL)
7. Configure logging and alerting

---

## Alternative: ngrok (Quick Testing)

For quick testing without domain:

```bash
# Install ngrok
choco install ngrok  # Windows
brew install ngrok   # macOS

# Start orchestrator
python -m uvicorn casare_rpa.orchestrator.api.main:app --port 8000

# Expose to internet
ngrok http 8000

# Use provided URL (e.g., https://abc123.ngrok.io)
```

**Note**: ngrok free tier has random URLs. Cloudflare Tunnel is better for production.
