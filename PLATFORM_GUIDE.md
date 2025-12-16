# 🎯 CasareRPA Platform - Unified Architecture

## 🚀 Quick Start

### **Option 1: Smart Launcher (Recommended)**
```bash
launch.bat
```

That's it! This will:
- ✅ Check all prerequisites
- ✅ Start the orchestrator API
- ✅ Start the robot agent
- ✅ Open Canvas UI
- ✅ Monitor all services

### **Option 2: Manual Launch**
```bash
# Terminal 1: Orchestrator
python manage.py orchestrator start --dev

# Terminal 2: Robot
python -m casare_rpa.robot.tray_icon

# Terminal 3: Canvas
python manage.py canvas
```

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Canvas UI (Main)                       │
│  ┌────────────┬──────────────┬─────────────────────┐    │
│  │ Workflows  │ Fleet Dash   │ Service Manager     │    │
│  │            │              │  ● Orchestrator ✓   │    │
│  │            │  ┌────────┐  │  ● Database     ✓   │    │
│  │            │  │Robots  │  │  ● Robot Agent  ✓   │    │
│  │            │  │Jobs    │  │                      │    │
│  │            │  │Schedule│  │                      │    │
│  │            │  └────────┘  │                      │    │
│  └────────────┴──────────────┴─────────────────────┘    │
└──────────────────────────────────────────────────────────┘
                        ▲
                        │ Auto-Discovery & Health Checks
                        ▼
┌──────────────────────────────────────────────────────────┐
│              Service Registry (Centralized)               │
│                                                           │
│  ┌─────────────┬─────────────┬──────────────┬────────┐  │
│  │Orchestrator │ Database    │ Robot Agent  │ Tunnel │  │
│  │localhost:800│ PostgreSQL  │ Auto-Connect │Optional│  │
│  │Health: ✓    │ Health: ✓   │ Health: ✓    │        │  │
│  └─────────────┴─────────────┴──────────────┴────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## ✨ What's New

### **1. Zero-Config Robot Startup**
Robots now auto-discover the orchestrator:

**Before**:
```bash
# Had to manually configure URLs
set CASARE_ORCHESTRATOR_URL=http://localhost:8000
set ORCHESTRATOR_API_KEY=...
python -m casare_rpa.robot.tray_icon
```

**After**:
```bash
# Just start it!
python -m casare_rpa.robot.tray_icon
# → Auto-discovers localhost:8000
# → Registers automatically
# → Shows in Fleet Dashboard
```

---

### **2. Service Health Monitoring**
Real-time health checks for all services:

```bash
python test_platform.py
```

**Output**:
```
📊 Checking Services...
   ✓ orchestrator   online     (45ms)   [REQUIRED]
   ✓ database       online     (23ms)   [REQUIRED]
   ○ tunnel         offline
   ○ redis          offline

🔍 Testing Auto-Discovery...
   ✓ Found orchestrator: http://localhost:8000

✅ Platform Ready! (2/4 services online)
   All required services are healthy
```

---

### **3. Smart Launcher**
One command to rule them all:

```bash
launch.bat
```

**Features**:
- Checks if services already running (no duplicates)
- Waits for orchestrator to be healthy before starting robot
- Clear progress indicators
- Graceful shutdown on Ctrl+C
- Auto-opens Canvas

---

### **4. Persistent Robot Identity**
Robot IDs no longer change on restart:

**Before**:
```
Start 1: robot-R-abc123
Start 2: robot-R-xyz789  ← Different ID!
Start 3: robot-R-def456  ← Different again!
```

**After**:
```
Start 1: robot-R-abc123
Start 2: robot-R-abc123  ← Same ID!
Start 3: robot-R-abc123  ← Always the same!
```

**Identity File**: `%APPDATA%\CasareRPA\robot_identity.json`

---

### **5. No More Race Conditions**
Fixed the "immediate unlink on startup" bug:

**Before**:
```
[23:18:06] Robot registered: robot-R-abc123
[23:18:06] Sending heartbeat...
[23:18:06] ERROR: 404 Not Found
[23:18:06] Unlinking from Fleet (404)
```

**After**:
```
[23:18:06] Robot registered: robot-R-abc123
[23:18:06] Registration confirmed ✓
[23:18:07] Sending heartbeat... ✓
[23:18:08] Robot online in Fleet Dashboard ✓
```

---

## 📊 Key Components

### **Service Registry**
`src/casare_rpa/infrastructure/services/registry.py`

```python
from casare_rpa.infrastructure.services import get_service_registry

registry = get_service_registry()

# Check all services
status = await registry.check_all_services()

# Wait for orchestrator
await registry.wait_for_service("orchestrator", timeout=30)

# Get service URL
url = registry.get_orchestrator_url()
```

---

### **Auto-Discovery**
`src/casare_rpa/robot/auto_discovery.py`

```python
from casare_rpa.robot.auto_discovery import get_auto_discovery

discovery = get_auto_discovery()

# Find orchestrator
url = await discovery.discover_orchestrator()
# Tries: ENV → localhost:8000 → api.casare.net

# Wait for it to become available
url = await discovery.wait_for_orchestrator(timeout=60)
```

---

### **Smart Launcher**
`src/casare_rpa/launcher/__main__.py`

```python
from casare_rpa.launcher import PlatformLauncher

launcher = PlatformLauncher()
await launcher.launch(
    start_orchestrator=True,
    start_robot=True,
    start_canvas=True,
    start_tunnel=False,  # Optional
)
```

---

## 🔧 Configuration

### **Environment Variables (Optional)**

All of these are **optional** now thanks to auto-discovery:

```bash
# Orchestrator
CASARE_ORCHESTRATOR_URL=http://localhost:8000  # Auto-discovered if not set
ORCHESTRATOR_API_KEY=your-api-key              # From .env API_SECRET

# Database
POSTGRES_URL=postgresql://...                  # Required

# Robot (all optional - auto-generated if not set)
CASARE_ROBOT_ID=                               # Auto-generated and persisted
CASARE_ROBOT_NAME=                             # Auto-generated from hostname
CASARE_ENVIRONMENT=default                     # Default: "default"

# Launcher
CASARE_START_ORCHESTRATOR=1                    # Start orchestrator? (1=yes)
CASARE_START_TUNNEL=0                          # Start tunnel? (0=no)
```

---

## 🎯 Common Tasks

### **Start Everything**
```bash
launch.bat
```

### **Check Platform Health**
```bash
python test_platform.py
```

### **View Robot Identity**
```bash
type %APPDATA%\CasareRPA\robot_identity.json
```

### **Reset Robot Identity**
```bash
del %APPDATA%\CasareRPA\robot_identity.json
# Robot will get new ID on next start
```

### **Check Orchestrator Health**
```bash
curl http://localhost:8000/health
```

---

## 🐛 Troubleshooting

### **Robot Not Showing in Fleet**

1. **Check orchestrator is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check auto-discovery**:
   ```bash
   python test_platform.py
   ```

3. **Check robot identity**:
   ```bash
   type %APPDATA%\CasareRPA\robot_identity.json
   ```

4. **Check robot logs**:
   ```bash
   type %USERPROFILE%\.casare_rpa\logs\robot_*.log
   ```

---

### **Orchestrator Won't Start**

1. **Check if port 8000 is in use**:
   ```bash
   netstat -ano | findstr :8000
   ```

2. **Check database connection**:
   ```bash
   echo %POSTGRES_URL%
   ```

3. **Start manually to see errors**:
   ```bash
   python manage.py orchestrator start --dev
   ```

---

### **Services Show as Offline**

Run the health check:
```bash
python test_platform.py
```

This will show:
- Which services are offline
- Error messages
- Suggested fixes

---

## 📈 Migration Guide

### **From Old launch_platform.bat**

**Old**:
```batch
launch_platform.bat
# Opens 4-5 terminal windows
# Manual URL configuration
# No health checks
# Complex error messages
```

**New**:
```batch
launch.bat
# Single smart launcher
# Auto-discovery
# Health checks built-in
# Clear error messages
```

### **Cleanup Steps**

1. **Stop all running services**
2. **Delete old identity** (optional, for fresh start):
   ```bash
   del %APPDATA%\CasareRPA\robot_identity.json
   ```
3. **Use new launcher**:
   ```bash
   launch.bat
   ```

---

## 🎓 Best Practices

### **Development**
```bash
# Use the smart launcher for consistency
launch.bat

# Or start services individually as needed
python manage.py orchestrator start --dev
python -m casare_rpa.robot.tray_icon
```

### **Production**
```bash
# Set environment variables in .env
API_SECRET=your-production-key
POSTGRES_URL=your-production-db

# Use launcher
launch.bat
```

### **Debugging**
```bash
# Check platform health first
python test_platform.py

# View service logs
type %USERPROFILE%\.casare_rpa\logs\robot_*.log
```

---

## 📚 Additional Resources

- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **Service Registry**: See `src/casare_rpa/infrastructure/services/registry.py`
- **Auto-Discovery**: See `src/casare_rpa/robot/auto_discovery.py`
- **Launcher**: See `src/casare_rpa/launcher/__main__.py`

---

## 🎉 Summary of Improvements

| Feature | Before | After |
|---------|--------|-------|
| **Startup** | 4-5 manual commands | 1 command (`launch.bat`) |
| **Robot ID** | Changes on every restart | Persists forever |
| **Discovery** | Manual URL configuration | Auto-discovers orchestrator |
| **Health Checks** | None | Built into all services |
| **Error Messages** | HTTP codes | Clear actionable guidance |
| **Service Management** | Manual terminal juggling | Automated with smart launcher |
| **Registration** | Race conditions, immediate unlink | Robust, waits for confirmation |
| **Schedule Jobs** | No workflow data | Full workflow in metadata |

---

**Everything now works in harmony! 🎵**
