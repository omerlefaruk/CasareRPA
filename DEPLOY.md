# CasareRPA Complete Setup & Deployment Guide

---
# 🆕 ENTERPRISE ARCHITECTURE (UPDATED 2025-11-29)

## Overview

**NEW**: CasareRPA now uses a **full enterprise architecture** with FastAPI backend, React monitoring dashboard, PostgreSQL job queue, and distributed robot execution.

**System Components:**
1. **Canvas (Designer)** - PySide6 visual workflow editor → submits to Orchestrator API
2. **Orchestrator API** - FastAPI REST/WebSocket server (port 8000)
3. **Monitoring Dashboard** - React 19 + Vite real-time monitoring UI (port 5173)
4. **Robot Agent** - Distributed event-based workflow executor (PgQueuer)
5. **PostgreSQL** - Job queue + workflow storage (PgQueuer: 18k+ jobs/sec)

**Architecture Flow:**
```
┌────────────┐   POST /api/v1/workflows   ┌─────────────────┐
│   Canvas   │──────────────────────────→ │ Orchestrator API│
│  (PySide6) │   3 Execution Modes:       │   (FastAPI)     │
│            │   - Run Local (F8)         │   - REST API    │
│            │   - Run on Robot (Ctrl+F5) │   - WebSocket   │
│            │   - Submit (Ctrl+Shift+F5) └────────┬────────┘
└────────────┘                                     │
                                                   │ PostgreSQL
                                                   │ (PgQueuer)
                                                   ▼
┌──────────────┐   Real-time Updates    ┌──────────────────┐
│  Monitoring  │◄──────WebSocket────────│   Robot Agent    │
│  Dashboard   │                         │  (Event-based)   │
│ (React/Vite) │                         │  - DBOS Executor │
└──────────────┘                         │  - Heartbeat     │
                                         └──────────────────┘
```

## Quick Start (2 Scripts)

### Windows
```bat
start_platform.bat   # Starts API + Dashboard
python run.py        # Canvas Designer (separate)
```

### Linux/Mac
```bash
./start_dev.sh       # Starts API + Dashboard
python run.py        # Canvas Designer (separate)
```

**URLs:**
- Orchestrator API: `http://localhost:8000`
- API Docs (Swagger): `http://localhost:8000/docs`
- Monitoring Dashboard: `http://localhost:5173`

---

## Part 0: PostgreSQL Setup (REQUIRED for Production)

### Prerequisites

**Required:**
- Windows 10/11 or Linux/macOS
- Python 3.12+
- Node.js 18+ (for monitoring dashboard)
- PostgreSQL 15+ (or use in-memory fallback for dev)
- Git
- 4GB RAM minimum (8GB recommended)

### Option A: Install PostgreSQL (Production)

#### Windows
```bash
# Download installer from postgresql.org
# Install PostgreSQL 15+ with default settings
# Note the password you set for the 'postgres' user

# Create database
psql -U postgres
CREATE DATABASE casare_rpa;
CREATE USER casare_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE casare_rpa TO casare_user;
\q
```

#### Linux/Mac
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS (Homebrew)
brew install postgresql@15

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql@15  # macOS

# Create database
sudo -u postgres psql
CREATE DATABASE casare_rpa;
CREATE USER casare_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE casare_rpa TO casare_user;
\q
```

#### Run Migrations
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Run database migrations
python -m casare_rpa.infrastructure.persistence.setup_db

# Verify setup
python -c "from casare_rpa.infrastructure.queue import get_memory_queue; print('✓ Queue imports OK')"
```

#### Configure Environment
Create `.env` in project root:
```bash
# PostgreSQL Configuration
DB_ENABLED=true
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=casare_rpa
DB_USER=casare_user
DB_PASSWORD=your_password_here

# PgQueuer (Job Queue)
PGQUEUER_DB_URL=postgresql://casare_user:your_password_here@localhost:5432/casare_rpa

# Orchestrator API
ORCHESTRATOR_URL=http://localhost:8000

# Workflow Storage
WORKFLOWS_DIR=./workflows
WORKFLOW_BACKUP_ENABLED=true  # Dual storage: DB + filesystem
```

### Option B: In-Memory Queue Fallback (Development Only)

For local development without PostgreSQL:

```bash
# .env configuration
USE_MEMORY_QUEUE=true  # Fallback to asyncio.Queue
DB_ENABLED=false
```

**⚠️ WARNING:** Memory queue loses all jobs on restart. Use only for development.

---

## Part 1: Platform Setup

### Step 1: Installation

```bash
# Clone repository
git clone https://github.com/yourusername/CasareRPA.git
cd CasareRPA

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium

# Install monitoring dashboard dependencies
cd monitoring-dashboard
npm install
cd ..
```

### Step 2: Start Platform with Scripts

#### Windows
```bat
# Start Orchestrator API + Monitoring Dashboard
start_platform.bat

# Components started:
# - Orchestrator API: http://localhost:8000
# - Monitoring Dashboard: http://localhost:5173

# (Optional) Start Canvas Designer
python run.py

# (Optional) Start Robot Agent
python -m casare_rpa.robot.cli start
```

#### Linux/Mac
```bash
# Start platform (API + Dashboard in background)
./start_dev.sh

# Check status
./start_dev.sh status

# Stop platform
./start_dev.sh stop

# (Optional) Start Canvas Designer
python run.py

# (Optional) Start Robot Agent
python -m casare_rpa.robot.cli start
```

### Step 3: Verify Platform

Open browser and verify:

1. **Orchestrator API Health**: http://localhost:8000/health
   ```json
   {
     "status": "healthy",
     "service": "casare-rpa-monitoring"
   }
   ```

2. **API Documentation**: http://localhost:8000/docs
   - Interactive Swagger UI
   - Test workflow submission endpoints

3. **Monitoring Dashboard**: http://localhost:5173
   - Real-time job status
   - Robot fleet monitoring
   - Queue metrics

---

## Part 2: Canvas Workflow Submission (3 Execution Modes)

### Execution Modes Overview

Canvas now has **three execution modes** accessible via toolbar buttons and `Workflow > Execute` menu:

| Mode | Shortcut | Button | Description |
|------|----------|--------|-------------|
| **Run Local** | F8 | ▶ Run Local | Execute in Canvas process (local testing) |
| **Run on Robot** | Ctrl+F5 | 🤖 Run on Robot | Submit to LAN robot via Orchestrator |
| **Submit** | Ctrl+Shift+F5 | ☁ Submit | Queue for internet robots (client PCs) |

### Mode 1: Run Local (F8)

**Use Case:** Quick local testing, debugging workflows

```
Canvas → Execute Locally → See results in Canvas debug panel
```

**Steps:**
1. Open Canvas: `python run.py`
2. Create workflow (add nodes, connect them)
3. Click **▶ Run Local** toolbar button (or press F8)
4. View results in bottom panel (Variables, Output, Log tabs)

**No Orchestrator Required** - runs directly in Canvas process.

### Mode 2: Run on Robot (Ctrl+F5)

**Use Case:** Execute on local/LAN robot for real automation

```
Canvas → POST /api/v1/workflows (mode=lan) → Orchestrator → Robot → Execution
```

**Steps:**
1. Ensure Orchestrator API is running (http://localhost:8000)
2. Start a Robot: `python -m casare_rpa.robot.cli start`
3. In Canvas, click **🤖 Run on Robot** toolbar button (or Ctrl+F5)
4. Workflow is submitted to Orchestrator API
5. Robot claims job from queue and executes
6. Monitor in real-time at http://localhost:5173

**Requirements:**
- Orchestrator API running
- At least one Robot connected
- PostgreSQL or memory queue configured

### Mode 3: Submit (Ctrl+Shift+F5)

**Use Case:** Queue workflow for internet robots (client PCs, remote workers)

```
Canvas → POST /api/v1/workflows (mode=internet) → Orchestrator → Internet Robot → Execution
```

**Steps:**
1. Ensure Orchestrator API is running
2. In Canvas, click **☁ Submit** toolbar button (or Ctrl+Shift+F5)
3. Workflow is queued with `execution_mode=internet`
4. First available internet robot claims and executes
5. Monitor execution in dashboard

**Use Cases:**
- Client-side automation (RPA on customer PCs)
- Distributed processing across multiple locations
- Load balancing across remote robots

---

## Part 3: API Integration

### Workflow Submission API

**Endpoint:** `POST /api/v1/workflows`

**Request Body:**
```json
{
  "workflow_name": "MyWorkflow",
  "workflow_json": {
    "nodes": [...],
    "connections": [...]
  },
  "trigger_type": "manual",
  "execution_mode": "lan",  // or "internet"
  "priority": 10,
  "metadata": {}
}
```

**Response:**
```json
{
  "workflow_id": "uuid",
  "job_id": "uuid",
  "status": "success",
  "message": "Workflow submitted and queued for lan execution",
  "created_at": "2025-11-29T..."
}
```

**Dual Storage:**
- **Primary:** PostgreSQL (`workflows` table)
- **Backup:** Filesystem (`./workflows/{workflow_id}.json`)

### Schedule Management API

**Create Schedule:** `POST /api/v1/schedules`

```json
{
  "workflow_id": "uuid",
  "schedule_name": "Daily Report",
  "cron_expression": "0 9 * * 1-5",  // 9 AM weekdays
  "enabled": true,
  "priority": 10,
  "execution_mode": "lan"
}
```

**Other Endpoints:**
- `GET /api/v1/schedules` - List schedules
- `PUT /api/v1/schedules/{id}/enable` - Enable schedule
- `PUT /api/v1/schedules/{id}/disable` - Disable schedule
- `DELETE /api/v1/schedules/{id}` - Delete schedule

### WebSocket Real-time Updates

**Endpoints:**
- `/ws/live-jobs` - Job status updates
- `/ws/robot-status` - Robot heartbeats
- `/ws/queue-metrics` - Queue depth metrics

**Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live-jobs');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Job update:', data);
};
```

---

## Original Documentation (Legacy)

**⚠️ NOTE:** The following sections reference the **old PySide6 Orchestrator dashboard** which has been **removed**. Use the new FastAPI API + React dashboard instead.

---

## Part 1: Local Deployment & Testing

### Prerequisites

**Required:**
- Windows 10/11 (64-bit)
- Python 3.12+
- Git
- 4GB RAM minimum (8GB recommended)

**Optional:**
- Supabase account (for cloud persistence)
- PostgreSQL/MySQL (for production)

### Step 1: Installation

```bash
# Clone repository
git clone https://github.com/yourusername/CasareRPA.git
cd CasareRPA

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### Step 2: Run Orchestrator (Local Mode)

**Terminal 1 - Start Orchestrator:**

```bash
# Activate environment
.venv\Scripts\activate

# Run orchestrator
python run_orchestrator.py
```

**What Happens:**
- Loads `OrchestratorEngine` with default config
- Starts job queue, scheduler, dispatcher
- Launches WebSocket server on `localhost:8765`
- Opens PySide6 monitoring dashboard
- Uses local JSON storage (`~/.casare_rpa/orchestrator/`)

**Expected Output:**
```
[INFO] Orchestrator starting...
[INFO] Job queue initialized
[INFO] Scheduler started
[INFO] WebSocket server listening on ws://localhost:8765
[INFO] Dashboard opened
```

**Dashboard Features:**
- **Jobs Panel:** View queued/running/completed jobs
- **Robots Panel:** Connected robot list with status
- **Metrics Panel:** System performance graphs
- **Dashboard Panel:** Fleet overview

### Step 3: Run Robot (Local Connection)

**Terminal 2 - Start Robot:**

```bash
# Activate environment
.venv\Scripts\activate

# Create config directory
mkdir %USERPROFILE%\.casare_rpa

# Create minimal config (optional - robot works without this)
echo SUPABASE_URL=http://localhost:8765 > %USERPROFILE%\.casare_rpa\.env

# Start robot
python -m casare_rpa.robot.cli start --verbose
```

**What Happens:**
- Robot generates unique ID (saved to `~/.casare_rpa/robot_id`)
- Auto-assigns name based on hostname
- Attempts Supabase connection (falls back to offline mode if unavailable)
- **WebSocket mode:** Connects to `ws://localhost:8765` if orchestrator running
- Polls for jobs every 5 seconds
- Heartbeat every 5 seconds

**Expected Output:**
```
[INFO] Robot starting...
[INFO] Robot ID: 550e8400-e29b-41d4-a716-446655440000
[INFO] Robot Name: DESKTOP-PC-Worker
[INFO] Connection mode: Local (WebSocket)
[INFO] Connected to orchestrator at ws://localhost:8765
[INFO] Registration successful
[INFO] Polling for jobs (interval: 5.0s)
```

**Verify Connection:**
- Check Orchestrator dashboard → Robots Panel
- Robot should appear as "ONLINE" with green indicator
- Status: IDLE (no jobs assigned yet)

### Step 4: Create Workflow in Canvas

**Terminal 3 - Start Canvas:**

```bash
# Activate environment
.venv\Scripts\activate

# Launch Canvas designer
python -m casare_rpa.main
```

**Canvas opens with:**
- Node palette (left sidebar)
- Graph canvas (center)
- Properties panel (right sidebar)
- Bottom panel (Variables, Triggers, Logs tabs)

**Create Simple Test Workflow:**

1. **Add Start Node:**
   - Drag "Start" from Control Flow category
   - Place on canvas

2. **Add Log Node:**
   - Drag "Log Message" from Utility category
   - Connect Start → Log Message

3. **Configure Log Node:**
   - Click Log Message node
   - Properties panel opens
   - Set message: "Hello from Robot!"
   - Set level: INFO

4. **Add End Node:**
   - Drag "End" from Control Flow
   - Connect Log Message → End

5. **Save Workflow:**
   - Press `Ctrl+S`
   - Choose location: `workflows/test_hello.json`
   - Workflow saved

**Workflow JSON Structure Generated:**
```json
{
  "metadata": {
    "name": "Test Hello",
    "version": "1.0.0"
  },
  "nodes": {
    "start_1": {
      "node_type": "StartNode",
      "config": {}
    },
    "log_1": {
      "node_type": "LogMessageNode",
      "config": {
        "message": "Hello from Robot!",
        "level": "INFO"
      }
    },
    "end_1": {
      "node_type": "EndNode",
      "config": {}
    }
  },
  "connections": [
    {"source_node": "start_1", "target_node": "log_1"},
    {"source_node": "log_1", "target_node": "end_1"}
  ]
}
```

### Step 5: Test Local Execution (Canvas Only)

**Run in Canvas:**
- Press `F3` or click "Run" button
- Workflow executes locally (NOT via Orchestrator)
- Watch node colors:
  - Yellow: Running
  - Green: Completed
  - Red: Error

**Logs Tab:**
```
[INFO] Workflow started: Test Hello
[INFO] Executing node: start_1
[INFO] Executing node: log_1
[INFO] Hello from Robot!
[INFO] Executing node: end_1
[INFO] Workflow completed successfully
```

**This proves:**
- Workflow design works
- Node execution works
- Ready for orchestrator submission

### Step 6: Submit Workflow to Orchestrator

**Current Implementation Note:**
Canvas does NOT have direct orchestrator submission yet. Workflows are executed locally.

**Workaround for Testing (Manual Submission):**

Create Python script `submit_job.py`:

```python
import asyncio
import orjson
from pathlib import Path
from casare_rpa.application.orchestrator.orchestrator_engine import OrchestratorEngine
from casare_rpa.domain.orchestrator.entities import JobPriority

async def submit_workflow():
    # Load workflow JSON
    workflow_path = Path("workflows/test_hello.json")
    workflow_data = orjson.loads(workflow_path.read_bytes())

    # Initialize orchestrator (connects to running instance)
    orchestrator = OrchestratorEngine()
    await orchestrator.start()

    # Submit job
    job = await orchestrator.submit_job(
        workflow_id="test-workflow-001",
        workflow_name=workflow_data["metadata"]["name"],
        workflow_json=orjson.dumps(workflow_data).decode(),
        robot_id=None,  # Any available robot
        priority=JobPriority.NORMAL,
        scheduled_time=None,
        params=None
    )

    print(f"✓ Job submitted: {job.id}")
    print(f"  Status: {job.status}")
    print(f"  Priority: {job.priority}")

    await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(submit_workflow())
```

**Run submission script:**
```bash
python submit_job.py
```

**Expected Output:**
```
✓ Job submitted: 3c9e1b4a-7f2d-4e8c-9a5b-1d3e8f7c2b6a
  Status: QUEUED
  Priority: NORMAL
```

**Verify in Orchestrator Dashboard:**
- Jobs Panel shows new job as "QUEUED"
- After ~5 seconds: Status changes to "RUNNING"
- Robot Panel shows robot status: "BUSY"
- After completion: Status changes to "COMPLETED"

**Verify in Robot Terminal:**
```
[INFO] Job received: 3c9e1b4a-7f2d-4e8c-9a5b-1d3e8f7c2b6a
[INFO] Job claimed successfully
[INFO] Starting workflow execution: Test Hello
[INFO] Executing node: start_1
[INFO] Executing node: log_1
[INFO] Hello from Robot!
[INFO] Executing node: end_1
[INFO] Workflow completed successfully
[INFO] Job completed: 3c9e1b4a-7f2d-4e8c-9a5b-1d3e8f7c2b6a
```

**Local Testing Complete! ✓**

---

## Part 2: Internet Deployment (Distributed Robots)

### Architecture for Internet Deployment

```
┌─────────────────────────────────────────────┐
│  Cloud VM (DigitalOcean/AWS)                │
│  ├─ Orchestrator (Public IP/Domain)         │
│  ├─ FastAPI REST API (:8000)                │
│  ├─ WebSocket Server (:8765)                │
│  └─ PostgreSQL Database                     │
└──────────────┬──────────────────────────────┘
               │ HTTPS + WSS (encrypted)
               │
    ┌──────────┴──────────┬─────────────┬──────────┐
    │                     │             │          │
┌───▼────┐         ┌──────▼──┐   ┌─────▼───┐  ┌──▼────┐
│Robot-01│         │Robot-02 │   │Robot-03 │  │Canvas │
│Client-A│         │Client-B │   │Client-C │  │ GUI   │
│Network-1│        │Network-2│   │Network-3│  │       │
└────────┘         └─────────┘   └─────────┘  └───────┘
```

### Option A: Cloud VM Deployment (Recommended)

**Step 1: Provision Cloud VM**

**DigitalOcean Droplet:**
```bash
# Create droplet via dashboard or CLI
doctl compute droplet create casare-orchestrator \
  --region nyc3 \
  --size s-1vcpu-1gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys <your-ssh-key-id>

# Note the public IP: 203.0.113.45
```

**AWS EC2 Instance:**
```bash
# Launch t3.micro instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --key-name my-key-pair \
  --security-group-ids sg-orchestrator

# Configure security group:
# - Port 22 (SSH) - Your IP only
# - Port 443 (HTTPS) - 0.0.0.0/0
# - Port 8765 (WSS) - 0.0.0.0/0
```

**Step 2: Install Dependencies on VM**

```bash
# SSH into VM
ssh root@203.0.113.45

# Update system
apt update && apt upgrade -y

# Install Python 3.12
apt install python3.12 python3.12-venv python3-pip git -y

# Install nginx (for reverse proxy)
apt install nginx certbot python3-certbot-nginx -y

# Install PostgreSQL (optional)
apt install postgresql postgresql-contrib -y
```

**Step 3: Deploy Orchestrator Code**

```bash
# Clone repository
cd /opt
git clone https://github.com/yourusername/CasareRPA.git
cd CasareRPA

# Create venv
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
playwright install chromium --with-deps
```

**Step 4: Configure Domain & SSL**

**Register domain:** `orchestrator.yourdomain.com`

**Point DNS A record to VM IP:** `203.0.113.45`

**Get SSL certificate:**
```bash
# Stop nginx temporarily
systemctl stop nginx

# Get certificate (standalone mode)
certbot certonly --standalone -d orchestrator.yourdomain.com

# Certificate saved to:
# /etc/letsencrypt/live/orchestrator.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/orchestrator.yourdomain.com/privkey.pem

# Start nginx
systemctl start nginx
```

**Step 5: Configure Nginx Reverse Proxy**

Create `/etc/nginx/sites-available/orchestrator`:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name orchestrator.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name orchestrator.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/orchestrator.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/orchestrator.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # REST API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket for robots
    location /ws/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

**Enable site:**
```bash
ln -s /etc/nginx/sites-available/orchestrator /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

**Step 6: Configure Orchestrator Environment**

Create `/opt/CasareRPA/.env`:

```bash
# Database (optional)
DB_ENABLED=true
DB_HOST=localhost
DB_PORT=5432
DB_NAME=casare_orchestrator
DB_USER=orchestrator
DB_PASSWORD=secure_password_here

# Supabase (if using cloud)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-api-key

# Security
ROBOT_AUTH_ENABLED=true
ROBOT_TOKENS="robot-001:hash1,robot-002:hash2"

# Orchestrator settings
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8765
API_PORT=8000
```

**Step 7: Generate Robot API Tokens**

```bash
cd /opt/CasareRPA
source .venv/bin/activate

# Generate tokens for 3 robots
python tools/generate_robot_token.py robot-001 robot-002 robot-003
```

**Output:**
```
Robot ID: robot-001
  Raw Token:  xJk3m9PqR7TvWn2LsZ8Yf5Gh1Dc4Ba6N
  Token Hash: abc123def456...

Robot ID: robot-002
  Raw Token:  pL7mK2nR9qT8vW3xZ5yF1gH4dC6bA0nM
  Token Hash: def789ghi012...

Robot ID: robot-003
  Raw Token:  rT5vW8nL2kM9pQ7sZ3xF6yG1hD4cB0aM
  Token Hash: ghi345jkl678...

Orchestrator Environment Variable:
ROBOT_TOKENS="robot-001:abc123def456,robot-002:def789ghi012,robot-003:ghi345jkl678"
```

**Add to `.env`:**
```bash
echo 'ROBOT_TOKENS="robot-001:abc123...,robot-002:def789...,robot-003:ghi345..."' >> .env
```

**Step 8: Create Systemd Service**

Create `/etc/systemd/system/casare-orchestrator.service`:

```ini
[Unit]
Description=CasareRPA Orchestrator
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/CasareRPA
Environment="PATH=/opt/CasareRPA/.venv/bin"
ExecStart=/opt/CasareRPA/.venv/bin/python run_orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
systemctl daemon-reload
systemctl enable casare-orchestrator
systemctl start casare-orchestrator
systemctl status casare-orchestrator
```

**Step 9: Verify Orchestrator Running**

```bash
# Check service status
systemctl status casare-orchestrator

# Check logs
journalctl -u casare-orchestrator -f

# Test health endpoint
curl https://orchestrator.yourdomain.com/health

# Test WebSocket (from local machine)
wscat -c wss://orchestrator.yourdomain.com/ws/
```

**Expected health response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-29T15:30:00Z",
  "version": "2.0.0"
}
```

### Step 10: Configure Remote Robots

**On each client PC (Robot-01, Robot-02, Robot-03):**

**A. Install Python & CasareRPA:**
```powershell
# Install Python 3.12
winget install Python.Python.3.12

# Clone repository
git clone https://github.com/yourusername/CasareRPA.git
cd CasareRPA

# Create venv
python -m venv .venv
.venv\Scripts\activate

# Install
pip install -e .
playwright install chromium
```

**B. Create Robot Config:**

Create `%USERPROFILE%\.casare_rpa\robot_config.json`:

```json
{
  "robot_id": "robot-001",
  "robot_name": "Client-A-Worker",
  "connection": {
    "url": "wss://orchestrator.yourdomain.com/ws/",
    "api_token": "xJk3m9PqR7TvWn2LsZ8Yf5Gh1Dc4Ba6N",
    "initial_delay": 2.0,
    "max_delay": 300.0,
    "heartbeat_interval": 10.0,
    "connection_timeout": 60.0
  },
  "job_execution": {
    "max_concurrent_jobs": 3,
    "job_poll_interval": 10.0
  },
  "observability": {
    "metrics_enabled": true,
    "audit_enabled": true
  }
}
```

**Important:** Use the **raw token** from Step 7 (not the hash)

**C. Test Connection:**
```powershell
cd CasareRPA
.venv\Scripts\activate
python -m casare_rpa.robot.cli start --config %USERPROFILE%\.casare_rpa\robot_config.json --verbose
```

**Expected Output:**
```
[INFO] Robot starting...
[INFO] Robot ID: robot-001
[INFO] Robot Name: Client-A-Worker
[INFO] Connecting to wss://orchestrator.yourdomain.com/ws/
[INFO] Connection established
[INFO] Sending REGISTER message
[INFO] Registration acknowledged
[INFO] Heartbeat started (interval: 10.0s)
[INFO] Polling for jobs
```

**D. Verify in Orchestrator:**
- Check VM logs: `journalctl -u casare-orchestrator -f`
- Should see: `[INFO] Robot registered: robot-001 (Client-A-Worker)`
- Dashboard shows robot as ONLINE

**E. Setup as Windows Service (Optional):**

Install NSSM (Non-Sucking Service Manager):
```powershell
# Download NSSM
Invoke-WebRequest -Uri https://nssm.cc/release/nssm-2.24.zip -OutFile nssm.zip
Expand-Archive nssm.zip
Move-Item nssm\win64\nssm.exe C:\Windows\System32\

# Create service
nssm install CasareRobot "C:\Users\YourUser\CasareRPA\.venv\Scripts\python.exe" "-m casare_rpa.robot.cli start --config %USERPROFILE%\.casare_rpa\robot_config.json"
nssm set CasareRobot AppDirectory "C:\Users\YourUser\CasareRPA"
nssm set CasareRobot DisplayName "CasareRPA Robot Agent"
nssm set CasareRobot Description "Distributed RPA workflow executor"
nssm set CasareRobot Start SERVICE_AUTO_START

# Start service
nssm start CasareRobot
```

**Repeat for Robot-02 and Robot-03 on other client PCs.**

### Step 11: Test End-to-End Workflow

**From Canvas (on any PC):**

1. Create workflow in Canvas
2. Save to JSON: `workflows/distributed_test.json`
3. Submit via API:

```python
import httpx
import orjson
from pathlib import Path

workflow_data = orjson.loads(Path("workflows/distributed_test.json").read_bytes())

response = httpx.post(
    "https://orchestrator.yourdomain.com/api/jobs/submit",
    json={
        "workflow_id": "test-001",
        "workflow_name": workflow_data["metadata"]["name"],
        "workflow_json": workflow_data,
        "priority": "NORMAL"
    },
    headers={"X-Api-Token": "admin-token-here"}  # If admin auth enabled
)

print(response.json())
```

**Expected Flow:**
1. Job submitted to orchestrator
2. Orchestrator queues job
3. Dispatcher selects available robot (robot-001, robot-002, or robot-003)
4. Job assigned via WebSocket
5. Robot executes workflow
6. Progress updates streamed back
7. Results stored in orchestrator database

**Monitor in Real-Time:**
- Orchestrator logs: `journalctl -u casare-orchestrator -f`
- Robot logs: Check robot terminal or service logs
- Dashboard: Job status updates

---

## Option B: Cloudflare Tunnel (Zero-Cost Alternative)

**If you don't want to pay for cloud VM:**

### Step 1: Install Cloudflare Tunnel

**On your local PC (running orchestrator):**

```powershell
# Download cloudflared
winget install Cloudflare.cloudflared

# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create casare-orchestrator

# Note the tunnel ID and credentials file path
```

### Step 2: Configure Tunnel

Create `%USERPROFILE%\.cloudflared\config.yml`:

```yaml
url: http://localhost:8765
tunnel: <TUNNEL-ID-HERE>
credentials-file: C:\Users\YourUser\.cloudflared\<TUNNEL-ID>.json

ingress:
  - hostname: orchestrator.yourdomain.com
    service: http://localhost:8765
  - service: http_status:404
```

### Step 3: Route DNS

```bash
cloudflared tunnel route dns casare-orchestrator orchestrator.yourdomain.com
```

### Step 4: Start Tunnel

```powershell
cloudflared tunnel run casare-orchestrator
```

**Your orchestrator is now accessible at:**
`https://orchestrator.yourdomain.com` (Cloudflare provides free SSL)

**Robots connect to:**
`wss://orchestrator.yourdomain.com/ws/`

**Pros:**
- Free
- Automatic SSL
- No port forwarding
- DDoS protection

**Cons:**
- Your PC must stay running
- Not as reliable as cloud VM

---

## Part 3: Complete Workflow Guide

### Workflow: Canvas → Orchestrator → Robot

**1. Design Workflow in Canvas**

**Example: Web Scraping Workflow**

```
Start
  ↓
LaunchBrowser (chromium, headless=false, url=https://example.com)
  ↓
WaitForSelector (.product-price)
  ↓
ExtractText (selector=.product-price, all=true, variable=prices)
  ↓
LogMessage (message={{prices}})
  ↓
CloseBrowser
  ↓
End
```

**Steps:**
1. Drag nodes from palette
2. Connect nodes
3. Configure each node
4. Define variables
5. Save workflow: `Ctrl+S`

**2. Configure Trigger (Optional)**

**In Canvas → Bottom Panel → Triggers Tab:**

- Click "Add Trigger"
- Type: Scheduled
- Cron: `0 9 * * *` (daily at 9 AM)
- Workflow: Select "Web Scraping Workflow"
- Enable: Yes
- Save

**Alternative triggers:**
- Manual: Click "Run" button
- Webhook: POST to `https://orchestrator.yourdomain.com/api/triggers/webhook/{trigger_id}`
- File: Watch folder for new files

**3. Submit to Orchestrator**

**Method A: Manual Python Submission**

```python
import httpx
import orjson
from pathlib import Path

workflow_path = Path("workflows/web_scraping.json")
workflow_data = orjson.loads(workflow_path.read_bytes())

response = httpx.post(
    "https://orchestrator.yourdomain.com/api/v1/jobs/submit",
    json={
        "workflow_id": "scraping-001",
        "workflow_name": workflow_data["metadata"]["name"],
        "workflow_json": orjson.dumps(workflow_data).decode(),
        "robot_id": None,  # Any available
        "priority": "HIGH",
        "environment": "production"
    }
)

job = response.json()
print(f"Job ID: {job['id']}")
print(f"Status: {job['status']}")
```

**Method B: Via Scheduled Trigger**

Trigger automatically submits jobs based on schedule.

**Method C: Via Webhook**

```bash
curl -X POST https://orchestrator.yourdomain.com/api/triggers/webhook/abc-123 \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "12345"}'
```

**4. Orchestrator Processing**

**Job Queue State Machine:**
```
PENDING → QUEUED → RUNNING → COMPLETED
                            ↘ FAILED
                            ↘ TIMEOUT
                            ↘ CANCELLED
```

**Dispatcher Logic:**
1. Scan job queue every 5 seconds
2. Find QUEUED jobs
3. Filter available robots (ONLINE, not at max jobs)
4. Apply load balancing strategy:
   - ROUND_ROBIN: Next robot in rotation
   - LEAST_LOADED: Fewest active jobs
   - RANDOM: Random selection
   - AFFINITY: Robot with matching environment/tags
5. Assign job via WebSocket JOB_ASSIGN message

**5. Robot Execution**

**Robot Workflow:**
```
1. Receive JOB_ASSIGN message
2. Parse workflow JSON
3. Load workflow → domain objects
4. Create execution context
5. For each node (topological order):
   - Send JOB_PROGRESS update
   - Execute node.execute(context)
   - Save checkpoint
   - Check for cancellation
6. Send JOB_COMPLETE or JOB_FAILED
7. Cleanup resources
```

**Progress Updates:**
```json
{
  "job_id": "abc-123",
  "progress": 45,
  "current_node": "extract_text_node",
  "message": "Extracting prices from 15 products",
  "timestamp": "2025-11-29T15:30:00Z"
}
```

**6. Monitor Execution**

**Orchestrator Dashboard:**
- Real-time job status
- Robot fleet status
- Logs streaming
- Performance metrics

**REST API Monitoring:**
```bash
# Get job details
curl https://orchestrator.yourdomain.com/api/v1/jobs/{job_id}

# Get job logs
curl https://orchestrator.yourdomain.com/api/v1/jobs/{job_id}/logs

# Get robot status
curl https://orchestrator.yourdomain.com/api/v1/robots/{robot_id}
```

**WebSocket Live Updates:**
```javascript
const ws = new WebSocket('wss://orchestrator.yourdomain.com/ws/live-jobs');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Job ${update.job_id}: ${update.status}`);
};
```

**7. Handle Results**

**Job Completion:**
```json
{
  "job_id": "abc-123",
  "status": "COMPLETED",
  "started_at": "2025-11-29T15:30:00Z",
  "completed_at": "2025-11-29T15:32:45Z",
  "duration_seconds": 165,
  "robot_id": "robot-002",
  "result": {
    "success": true,
    "variables": {
      "prices": ["$19.99", "$24.99", "$39.99"]
    }
  }
}
```

**Error Handling:**
```json
{
  "job_id": "abc-123",
  "status": "FAILED",
  "error": {
    "node_id": "wait_for_selector",
    "error_type": "TimeoutError",
    "message": "Selector .product-price not found within 10000ms"
  }
}
```

---

## Testing Checklist

### Local Testing

- [ ] Orchestrator starts without errors
- [ ] Dashboard opens and displays correctly
- [ ] Robot connects to orchestrator
- [ ] Robot appears in dashboard as ONLINE
- [ ] Canvas workflow saves to JSON
- [ ] Manual job submission works
- [ ] Job appears in orchestrator queue
- [ ] Robot claims and executes job
- [ ] Job completes successfully
- [ ] Logs visible in both orchestrator and robot

### Internet Testing

- [ ] Cloud VM accessible via SSH
- [ ] Nginx serving HTTPS correctly
- [ ] SSL certificate valid
- [ ] Orchestrator service running
- [ ] Health endpoint returns 200
- [ ] WebSocket connection established from remote robot
- [ ] Remote robot registers successfully
- [ ] Job dispatched to remote robot
- [ ] Progress updates received
- [ ] Job completes on remote robot
- [ ] Results synced to orchestrator

### Multi-Robot Testing

- [ ] 3+ robots connected simultaneously
- [ ] Load balancing distributes jobs evenly
- [ ] Robot failure doesn't affect others
- [ ] Job reassignment on robot crash
- [ ] Heartbeat timeout detection works
- [ ] Concurrent job execution (multiple robots)

---

## Troubleshooting

### Robot Won't Connect

**Check:**
1. Orchestrator WebSocket server running
2. Firewall allows port 8765
3. Correct URL in robot config
4. API token matches (if auth enabled)
5. Network connectivity: `ping orchestrator.yourdomain.com`

**Debug:**
```bash
# Enable verbose logging
python -m casare_rpa.robot.cli start --verbose

# Check connection
wscat -c wss://orchestrator.yourdomain.com/ws/
```

### Jobs Not Dispatching

**Check:**
1. Job status is QUEUED (not PENDING)
2. At least one robot ONLINE
3. Robot not at max concurrent jobs
4. Dispatcher service running
5. Environment matching (if using pools)

**Debug:**
```bash
# Check orchestrator logs
journalctl -u casare-orchestrator -f | grep -i dispatch

# Check job queue
curl https://orchestrator.yourdomain.com/api/v1/metrics/jobs?status=queued
```

### Workflow Execution Fails

**Check:**
1. Workflow JSON valid
2. All node types registered
3. Node configurations valid
4. Required resources available (browser, desktop app, etc.)
5. Timeout settings appropriate

**Debug:**
```bash
# Check robot logs
python -m casare_rpa.robot.cli status --robot-id <id> --json

# Audit logs
cat %USERPROFILE%\.casare_rpa\audit\robot_*.log
```

---

## Key Files Reference

### Orchestrator
- Entry: `run_orchestrator.py`
- Engine: `src/casare_rpa/application/orchestrator/orchestrator_engine.py`
- WebSocket: `src/casare_rpa/infrastructure/orchestrator/communication/websocket_server.py`
- API: `src/casare_rpa/infrastructure/orchestrator/api/main.py`
- Dashboard: `src/casare_rpa/orchestrator/monitor_window.py`

### Robot
- CLI: `src/casare_rpa/robot/cli.py`
- Agent: `src/casare_rpa/robot/agent.py`
- Config: `src/casare_rpa/robot/config.py`
- Executor: `src/casare_rpa/robot/job_executor.py`

### Canvas
- Main: `src/casare_rpa/main.py`
- Serializer: `src/casare_rpa/presentation/canvas/serialization/workflow_serializer.py`
- Execution: `src/casare_rpa/presentation/canvas/execution/canvas_workflow_runner.py`

### Configuration Locations
- Orchestrator: `~/.casare_rpa/orchestrator/`
- Robot: `~/.casare_rpa/` (config, PID, status, audit logs)
- Workflows: `workflows/`

---

## Next Steps

1. **Start with local testing** - Validate all components work
2. **Deploy orchestrator to cloud** - Use DigitalOcean or AWS
3. **Connect 1 remote robot** - Test internet connectivity
4. **Scale to multiple robots** - Add robots on different networks
5. **Setup monitoring** - Use dashboard and API endpoints
6. **Implement CI/CD** - Automate deployments
7. **Add authentication** - Secure orchestrator API
8. **Setup backups** - Database and workflow files
