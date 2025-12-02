# CasareRPA Client Deployment Guide

This document clarifies the deployment model for CasareRPA, explaining what clients need and what admins manage.

## Deployment Model Overview

```
ADMIN (You):
+-- Deploy orchestrator to Railway/Render/Fly.io (or run locally)
+-- Setup Supabase (one-time, automated via setup.py)
+-- Generate API keys for clients
+-- Send: Installer .exe + API key to each client

CLIENT (Them):
+-- Run CasareRPA-Setup.exe (includes Python runtime, no Docker needed)
+-- Enter: Orchestrator URL + API key in setup wizard
+-- Done! Robot auto-registers with orchestrator
```

## What Clients DO NOT Need

| Not Required | Reason |
|--------------|--------|
| Docker | Runtime bundled via PyInstaller |
| Python | Embedded in installer |
| Database | Managed by orchestrator |
| Supabase account | Admin manages centrally |
| Cloud deployment | Client is just an agent |
| Technical knowledge | Wizard-based setup |

## What Clients DO Need

| Required | Source |
|----------|--------|
| CasareRPA-Setup.exe | Admin provides download link |
| Orchestrator URL | Admin provides (e.g., `https://casare.railway.app`) |
| API Key | Admin generates per client/robot |
| Windows 10/11 | Client's machine |
| Internet connection | To reach orchestrator |

## Client Installation Process

### Step 1: Download Installer

Admin shares the installer via:
- Company file share
- Direct download link
- Email attachment

File: `CasareRPA-3.x.x-Setup.exe` (~50-100MB without browsers, ~250MB with browsers)

### Step 2: Run Installer

1. Double-click `CasareRPA-Setup.exe`
2. Accept license agreement
3. Choose installation directory (default: `C:\Program Files\CasareRPA`)
4. Select components:
   - [x] Robot Agent (required)
   - [x] Designer (optional - for workflow editing)
   - [ ] Playwright Browsers (if using web automation)

### Step 3: Configure Orchestrator Connection

Setup wizard appears on first launch:

```
+------------------------------------------+
|  CasareRPA Setup Wizard                  |
+------------------------------------------+
|                                          |
|  Orchestrator URL:                       |
|  [https://casare.railway.app          ]  |
|                                          |
|  API Key:                                |
|  [crpa_xxxxxxxxxxxxxxxxxxxxx          ]  |
|                                          |
|  [Test Connection]                       |
|                                          |
|  Robot Name: [WORKSTATION-01          ]  |
|                                          |
+------------------------------------------+
```

### Step 4: Automatic Registration

Once connected, the robot:
1. Registers with orchestrator
2. Sends heartbeat every 30 seconds
3. Appears in Fleet Dashboard
4. Ready to receive jobs

## What the Installer Contains

The bundled installer includes:

```
CasareRPA/
+-- CasareRPA.exe           # Designer GUI (optional)
+-- CasareRPA-Robot.exe     # Robot agent (headless)
+-- python312.dll           # Embedded Python runtime
+-- PySide6/                # Qt framework (bundled)
+-- playwright/             # Browser automation (optional)
+-- *.pyd, *.dll            # All dependencies bundled
```

No external Python installation required. Everything runs from the install directory.

## Configuration Storage

After installation, configuration is stored in:

```
%APPDATA%\CasareRPA\
+-- config.yaml            # Connection settings
+-- logs/                  # Local log files
+-- workflows/             # Downloaded workflows
```

Example `config.yaml`:
```yaml
orchestrator:
  url: https://casare.railway.app
  api_key: crpa_xxxxxxxxxxxxxxxxxxxx

robot:
  name: WORKSTATION-01
  environment: production
  max_concurrent_jobs: 1

capabilities:
  browser: true
  desktop: true
```

## Admin Responsibilities

### 1. Deploy Orchestrator (One-Time)

Choose a platform and deploy:

**Railway (Recommended)**
```bash
cd deploy/orchestrator
railway init
railway add postgres
railway up
```

**Render**
```bash
# Push to GitHub, create Blueprint from render.yaml
```

**Fly.io**
```bash
fly launch
fly pg create
fly pg attach
fly deploy
```

### 2. Setup Supabase (One-Time)

```bash
cd deploy/supabase
python setup.py --project-ref YOUR_REF --service-key YOUR_KEY
```

This creates database tables and initial configuration.

### 3. Generate API Keys (Per Client)

Via Fleet Dashboard or API:

```bash
# Using curl
curl -X POST https://your-orchestrator/api/robots \
  -H "X-Api-Key: $ADMIN_KEY" \
  -d '{"name": "client-robot-01", "environment": "production"}'

# Returns robot_id

curl -X POST https://your-orchestrator/api/robots/{robot_id}/keys \
  -H "X-Api-Key: $ADMIN_KEY" \
  -d '{"name": "Initial Key", "expires_days": 365}'

# Returns: crpa_xxxxxxxxxxxxxxxxxxxx (save this!)
```

### 4. Distribute to Clients

Send to each client:
1. Download link for installer
2. Orchestrator URL
3. Their unique API key

Email template:
```
Subject: CasareRPA Robot Installation

Hi,

Please install the CasareRPA robot on your workstation:

1. Download: [link to CasareRPA-Setup.exe]
2. Run the installer
3. When prompted, enter:
   - Orchestrator URL: https://casare.railway.app
   - API Key: crpa_your_unique_key_here

The robot will automatically connect to our fleet.

Questions? Contact IT support.
```

## Updating Clients

### Option A: Auto-Update (Future)
Robot agent checks for updates and downloads new version.

### Option B: Manual Update
1. Distribute new installer
2. Client runs over existing installation
3. Settings preserved in %APPDATA%

### Option C: Silent Update (Enterprise)
```powershell
# PowerShell script for IT deployment
$installerPath = "\\server\share\CasareRPA-3.1.0-Setup.exe"
Start-Process $installerPath -ArgumentList "/S" -Wait
```

## Troubleshooting Client Issues

### Robot Not Connecting

1. Check orchestrator URL (no trailing slash)
2. Verify API key is correct (starts with `crpa_`)
3. Check firewall allows outbound HTTPS
4. View logs: `%APPDATA%\CasareRPA\logs\`

### "Unauthorized" Error

- API key may be revoked or expired
- Generate new key in Fleet Dashboard

### Robot Shows "Offline"

- Check robot process is running
- Verify internet connectivity
- Review heartbeat logs

### Designer Crashes

- Check Qt/PySide6 compatibility
- Try running as Administrator
- Check for antivirus interference

## Security Notes

1. **API Keys are Secrets**: Treat like passwords
2. **One Key Per Robot**: Never share keys between machines
3. **Rotate Regularly**: Keys can expire, rotate annually
4. **Revoke on Compromise**: Immediately revoke if key is exposed
5. **HTTPS Only**: Orchestrator should use TLS

## Support Resources

- Fleet Dashboard: Monitor all robots in real-time
- Log Viewer: Stream logs from any robot
- GitHub Issues: Report bugs and feature requests

---

**Summary**: Clients just run the installer and enter their API key. Everything else is bundled. No Docker, no Python install, no database setup. Simple.
