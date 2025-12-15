# CasareRPA Troubleshooting Guide

This guide provides solutions for common issues encountered when operating CasareRPA.

## Table of Contents

- [Canvas Application Issues](#canvas-application-issues)
- [Robot Agent Issues](#robot-agent-issues)
- [Workflow Execution Failures](#workflow-execution-failures)
- [Browser Automation Errors](#browser-automation-errors)
- [Desktop Automation Errors](#desktop-automation-errors)
- [Performance Issues](#performance-issues)
- [Memory Leaks](#memory-leaks)
- [Network Connectivity](#network-connectivity)
- [Authentication Failures](#authentication-failures)
- [Database Connection Issues](#database-connection-issues)

---

## Canvas Application Issues

### Canvas Won't Start

#### Symptom: Application crashes immediately on startup

**Probable Causes:**
- Corrupted settings file
- Missing Qt libraries
- GPU driver incompatibility
- Python environment issues

**Solutions:**

1. **Reset Settings**
   ```powershell
   # Backup and remove settings
   Move-Item "$env:APPDATA\CasareRPA\settings.json" "$env:APPDATA\CasareRPA\settings.json.bak"

   # Try starting again
   python run.py
   ```

2. **Force Software Rendering**
   ```powershell
   $env:QT_OPENGL = "software"
   python run.py
   ```

3. **Check Python Environment**
   ```powershell
   # Verify dependencies
   pip check

   # Reinstall PySide6
   pip uninstall PySide6 -y
   pip install PySide6
   ```

4. **Check Error Logs**
   ```powershell
   # Look for crash logs
   Get-Content "$env:APPDATA\CasareRPA\logs\canvas.log" -Tail 100
   ```

---

#### Symptom: Black or blank window appears

**Probable Causes:**
- GPU acceleration issues
- Display scaling problems
- Theme loading failure

**Solutions:**

1. **Disable GPU Acceleration**
   ```powershell
   $env:QT_OPENGL = "software"
   $env:QT_QUICK_BACKEND = "software"
   python run.py
   ```

2. **Fix Display Scaling**
   ```powershell
   $env:QT_ENABLE_HIGHDPI_SCALING = "0"
   $env:QT_AUTO_SCREEN_SCALE_FACTOR = "0"
   python run.py
   ```

3. **Check Theme File**
   ```python
   # Verify theme loads
   from casare_rpa.presentation.canvas.ui.theme import THEME
   print(THEME.BACKGROUND_PRIMARY)
   ```

---

#### Symptom: Node palette is empty

**Probable Causes:**
- Node registry failed to load
- Import errors in node modules
- Corrupted node cache

**Solutions:**

1. **Check Node Registry**
   ```python
   from casare_rpa.nodes.registry_data import NODE_REGISTRY
   registry = set(NODE_REGISTRY.keys())
   print(f"Registered nodes: {len(registry)}")
   ```

2. **Clear Node Cache**
   ```powershell
   Remove-Item "$env:APPDATA\CasareRPA\cache\nodes.cache" -Force
   python run.py
   ```

3. **Check for Import Errors**
   ```powershell
   # Run with verbose logging
   $env:CASARE_LOG_LEVEL = "DEBUG"
   python run.py 2>&1 | Select-String "ImportError|ModuleNotFoundError"
   ```

---

## Robot Agent Issues

### Robot Agent Connection Issues

#### Symptom: Robot cannot connect to Orchestrator

**Probable Causes:**
- Incorrect WebSocket URL
- Firewall blocking connection
- SSL/TLS certificate issues
- API key invalid or expired

**Solutions:**

1. **Verify URL Format**
   ```powershell
   # Must be ws:// or wss://
   echo $env:CASARE_CONTROL_PLANE_URL
   # Correct: wss://orchestrator.example.com/ws/robot
   # Wrong: https://orchestrator.example.com/ws/robot
   ```

2. **Test Network Connectivity**
   ```powershell
   # Check if port is reachable
   Test-NetConnection -ComputerName orchestrator.example.com -Port 443

   # Test WebSocket with wscat (install via npm)
   npx wscat -c wss://orchestrator.example.com/ws/robot
   ```

3. **Verify API Key**
   ```powershell
   # API key must start with crpa_ and be at least 40 characters
   $key = $env:CASARE_API_KEY
   if (-not $key.StartsWith("crpa_")) { Write-Error "Invalid API key prefix" }
   if ($key.Length -lt 40) { Write-Error "API key too short" }
   ```

4. **Check SSL Certificate**
   ```powershell
   # Temporarily disable SSL verification (NOT for production)
   $env:CASARE_VERIFY_SSL = "false"
   python -m casare_rpa.robot.cli start
   ```

---

#### Symptom: Robot keeps disconnecting and reconnecting

**Probable Causes:**
- Heartbeat timeout
- Network instability
- Orchestrator overloaded
- WebSocket ping timeout

**Solutions:**

1. **Increase Heartbeat Interval**
   ```powershell
   $env:CASARE_HEARTBEAT_INTERVAL = "60"  # Increase from 30s default
   ```

2. **Check Network Stability**
   ```powershell
   # Monitor packet loss
   ping -t orchestrator.example.com

   # Check for dropped connections
   netstat -an | Select-String "ESTABLISHED|TIME_WAIT"
   ```

3. **Review Orchestrator Logs**
   ```bash
   # Check for timeout messages
   grep -i "heartbeat timeout" /var/log/orchestrator.log
   grep -i "connection closed" /var/log/orchestrator.log
   ```

---

#### Symptom: Robot registers but never receives jobs

**Probable Causes:**
- Capability mismatch
- Environment mismatch
- Tenant isolation
- Job queue empty

**Solutions:**

1. **Verify Capabilities Match**
   ```bash
   # Check robot capabilities
   curl -H "X-Api-Key: $API_SECRET" http://orchestrator:8000/api/robots/robot-id

   # Check job requirements
   curl -H "X-Api-Key: $API_SECRET" http://orchestrator:8000/api/jobs/pending
   ```

2. **Check Environment**
   ```powershell
   # Robot environment must match job environment
   echo $env:CASARE_ENVIRONMENT  # Should be "production" for production jobs
   ```

3. **Submit Test Job**
   ```bash
   curl -X POST -H "X-Api-Key: $API_SECRET" \
       -H "Content-Type: application/json" \
       -d '{"workflow_id": "test", "target_robot_id": "your-robot-id"}' \
       http://orchestrator:8000/api/jobs
   ```

---

## Workflow Execution Failures

### Symptom: Workflow fails with "Node not found" error

**Error Code:** `ERR_NODE_NOT_FOUND`

**Probable Causes:**
- Workflow references deleted node
- Node type was renamed or removed
- Workflow version mismatch

**Solutions:**

1. **Identify Missing Node**
   ```python
   import json
   with open("workflow.json") as f:
       wf = json.load(f)

   from casare_rpa.nodes.registry_data import NODE_REGISTRY
   registry = set(NODE_REGISTRY.keys())

   for node in wf.get("nodes", []):
       if node["type"] not in registry:
           print(f"Missing: {node['type']} (ID: {node['id']})")
   ```

2. **Update Node References**
   - Open workflow in Canvas
   - Replace missing node with updated version
   - Save workflow

3. **No Auto-Migration**
   - Workflows are not auto-migrated.
   - Replace removed/renamed nodes in Canvas and re-save.

---

### Symptom: Workflow hangs indefinitely

**Probable Causes:**
- Infinite loop in control flow
- Wait node without timeout
- External service not responding
- Deadlock in parallel execution

**Solutions:**

1. **Add Timeouts to Wait Nodes**
   ```json
   {
     "type": "WaitElementNode",
     "properties": {
       "timeout": 30000
     }
   }
   ```

2. **Check for Infinite Loops**
   - Review loop conditions in ForEach/While nodes
   - Ensure exit conditions are reachable

3. **Enable Execution Timeout**
   ```powershell
   $env:CASARE_JOB_TIMEOUT = "1800"  # 30 minutes max
   ```

4. **Monitor Execution**
   - Use debug panel to see current node
   - Check for stuck node in logs

---

### Symptom: Variable not resolved

**Error Code:** `ERR_VARIABLE_NOT_FOUND`

**Probable Causes:**
- Variable name typo
- Variable not set by upstream node
- Scope issue (local vs global)
- Race condition in parallel execution

**Solutions:**

1. **Check Variable Name**
   ```python
   # Variable syntax: ${variable_name}
   # Check for typos, case sensitivity
   ```

2. **Verify Variable Source**
   - Ensure upstream node that sets variable is executed
   - Check execution order in parallel branches

3. **Use Default Values**
   ```json
   {
     "type": "SetVariableNode",
     "properties": {
       "variable_name": "myVar",
       "default_value": "fallback"
     }
   }
   ```

4. **Debug Variables**
   - Open Debug Panel (Ctrl+D)
   - Watch variable values during execution

---

## Browser Automation Errors

### Symptom: Selector not found

**Error Code:** `ERR_SELECTOR_NOT_FOUND`

**Probable Causes:**
- Element not yet loaded
- Selector changed (page update)
- Element in iframe
- Element hidden or off-screen

**Solutions:**

1. **Add Wait Before Action**
   ```json
   {
     "type": "WaitElementNode",
     "properties": {
       "selector": "#my-element",
       "timeout": 30000,
       "state": "visible"
     }
   }
   ```

2. **Use Smart Selector**
   - Enable AI selector healing in preferences
   - Use multiple selector strategies:
   ```json
   {
     "selector": "#unique-id",
     "fallback_selectors": [
       "[data-testid='my-button']",
       "button:has-text('Submit')"
     ]
   }
   ```

3. **Handle Iframes**
   ```json
   {
     "type": "SwitchFrameNode",
     "properties": {
       "frame_selector": "iframe#content-frame"
     }
   }
   ```

4. **Check Element Visibility**
   - Use Selector Picker (F12) to verify element
   - Check if element requires scrolling

---

### Symptom: Browser fails to launch

**Error Code:** `ERR_BROWSER_LAUNCH_FAILED`

**Probable Causes:**
- Playwright not installed
- Browser binaries missing
- Insufficient permissions
- Display not available (headless server)

**Solutions:**

1. **Install Playwright Browsers**
   ```powershell
   python -m playwright install chromium
   python -m playwright install-deps  # Linux only
   ```

2. **Use Headless Mode**
   ```json
   {
     "type": "LaunchBrowserNode",
     "properties": {
       "headless": true
     }
   }
   ```

3. **Check Permissions**
   ```powershell
   # Verify Chrome/Chromium is accessible
   & "$env:LOCALAPPDATA\ms-playwright\chromium-*/chrome-win\chrome.exe" --version
   ```

4. **Configure Display (Linux)**
   ```bash
   # For headless servers
   export DISPLAY=:99
   Xvfb :99 -screen 0 1920x1080x24 &
   ```

---

### Symptom: Page timeout

**Error Code:** `ERR_PAGE_TIMEOUT`

**Probable Causes:**
- Slow network
- Page never finishes loading
- JavaScript errors on page
- Blocked resources

**Solutions:**

1. **Increase Timeout**
   ```json
   {
     "type": "NavigateNode",
     "properties": {
       "url": "https://slow-site.com",
       "timeout": 60000
     }
   }
   ```

2. **Wait for Network Idle**
   ```json
   {
     "properties": {
       "wait_until": "networkidle"
     }
   }
   ```

3. **Check Console Errors**
   - Enable browser console logging
   - Check for JavaScript errors

4. **Block Unnecessary Resources**
   ```json
   {
     "type": "LaunchBrowserNode",
     "properties": {
       "block_resources": ["image", "stylesheet", "font"]
     }
   }
   ```

---

## Desktop Automation Errors

### Symptom: Element not found

**Error Code:** `ERR_DESKTOP_ELEMENT_NOT_FOUND`

**Probable Causes:**
- Application not in foreground
- Element not visible
- Wrong automation ID
- Application not responding

**Solutions:**

1. **Bring Application to Foreground**
   ```json
   {
     "type": "FocusWindowNode",
     "properties": {
       "window_title": "Notepad",
       "wait_timeout": 5000
     }
   }
   ```

2. **Use UI Explorer**
   - Open Selector Picker (F12)
   - Switch to Desktop tab
   - Hover over element to get correct properties

3. **Wait for Element**
   ```json
   {
     "type": "WaitDesktopElementNode",
     "properties": {
       "selector": {"AutomationId": "txtEditor"},
       "timeout": 10000
     }
   }
   ```

4. **Check Application State**
   - Ensure application is responding
   - Check if modal dialog is blocking

---

### Symptom: Cannot interact with elevated application

**Error Code:** `ERR_ACCESS_DENIED`

**Probable Causes:**
- Target application running as Administrator
- UAC blocking access
- Different user session

**Solutions:**

1. **Run Robot as Administrator**
   ```powershell
   # Start robot with elevated privileges
   Start-Process python -ArgumentList "-m casare_rpa.robot.cli start" -Verb RunAs
   ```

2. **Disable UAC for Automation (Not Recommended)**
   - Use only in isolated automation VMs
   - Configure via Group Policy

3. **Use Alternative Automation Method**
   - Keyboard shortcuts instead of UI clicks
   - Use COM automation if available

---

### Symptom: Keyboard input not working

**Error Code:** `ERR_KEYBOARD_FAILED`

**Probable Causes:**
- Window not focused
- Input blocked by security software
- Keyboard layout mismatch
- Virtual keyboard issues

**Solutions:**

1. **Focus Target Window First**
   ```json
   {
     "type": "FocusWindowNode",
     "properties": {"window_title": "Target App"}
   },
   {
     "type": "TypeTextNode",
     "properties": {"text": "Hello World"}
   }
   ```

2. **Use Slower Typing**
   ```json
   {
     "type": "TypeTextNode",
     "properties": {
       "text": "Hello",
       "delay_between_keys": 50
     }
   }
   ```

3. **Check Keyboard Layout**
   ```powershell
   # Verify keyboard layout
   Get-WinUserLanguageList
   ```

4. **Whitelist in Security Software**
   - Add CasareRPA to antivirus exclusions
   - Disable keystroke protection for robot user

---

## Performance Issues

### Symptom: Slow workflow execution

**Probable Causes:**
- Too many sequential operations
- Large data in variables
- Inefficient selectors
- Network latency

**Solutions:**

1. **Use Parallel Execution**
   ```json
   {
     "type": "ParallelNode",
     "branches": [
       {"nodes": [...]},
       {"nodes": [...]}
     ]
   }
   ```

2. **Optimize Selectors**
   - Prefer ID selectors over complex CSS
   - Avoid XPath when possible
   - Use data-testid attributes

3. **Reduce Variable Size**
   - Avoid storing large HTML in variables
   - Process data in chunks

4. **Profile Execution**
   ```python
   # Enable performance logging
   import os
   os.environ["CASARE_PERF_LOG"] = "true"
   ```

---

### Symptom: High CPU usage

**Probable Causes:**
- Busy-wait loops
- Excessive logging
- Browser process accumulation
- Unoptimized image processing

**Solutions:**

1. **Check for Zombie Processes**
   ```powershell
   # Find orphaned browser processes
   Get-Process | Where-Object { $_.ProcessName -like "*chromium*" }

   # Kill if necessary
   Stop-Process -Name "chromium" -Force
   ```

2. **Add Delays in Loops**
   ```json
   {
     "type": "WaitNode",
     "properties": {"duration": 100}
   }
   ```

3. **Reduce Log Level**
   ```powershell
   $env:CASARE_LOG_LEVEL = "WARNING"  # Reduce from DEBUG
   ```

---

## Memory Leaks

### Symptom: Memory usage grows over time

**Probable Causes:**
- Browser pages not closed
- Variables holding large data
- Event listeners not cleaned up
- Circular references

**Solutions:**

1. **Close Browsers Properly**
   ```json
   {
     "type": "CloseBrowserNode",
     "properties": {}
   }
   ```

2. **Clear Variables**
   ```json
   {
     "type": "ClearVariableNode",
     "properties": {"variable_name": "largeData"}
   }
   ```

3. **Monitor Memory**
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

4. **Restart Robot Periodically**
   ```bash
   # Cron job to restart robot daily
   0 2 * * * systemctl restart casare-robot
   ```

---

## Network Connectivity

### Symptom: Cannot reach external APIs

**Error Code:** `ERR_NETWORK_FAILED`

**Probable Causes:**
- Firewall blocking
- Proxy not configured
- DNS resolution failed
- SSL certificate issues

**Solutions:**

1. **Configure Proxy**
   ```powershell
   $env:HTTP_PROXY = "http://proxy.company.com:8080"
   $env:HTTPS_PROXY = "http://proxy.company.com:8080"
   $env:NO_PROXY = "localhost,127.0.0.1,.internal.com"
   ```

2. **Test Connectivity**
   ```powershell
   # Test HTTPS
   Invoke-WebRequest -Uri "https://api.example.com/health" -UseBasicParsing

   # Test DNS
   Resolve-DnsName api.example.com
   ```

3. **Configure Browser Proxy**
   ```json
   {
     "type": "LaunchBrowserNode",
     "properties": {
       "proxy": {
         "server": "http://proxy.company.com:8080"
       }
     }
   }
   ```

4. **Accept Self-Signed Certificates**
   ```json
   {
     "type": "LaunchBrowserNode",
     "properties": {
       "ignore_https_errors": true
     }
   }
   ```

---

## Authentication Failures

### Symptom: API key rejected

**Error Code:** `ERR_AUTHENTICATION_FAILED`

**Probable Causes:**
- Invalid API key format
- Key expired or revoked
- Wrong environment key
- Rate limiting

**Solutions:**

1. **Verify Key Format**
   ```powershell
   # Must be crpa_xxxxxxxx (40+ chars)
   $key = $env:CASARE_API_KEY
   Write-Host "Length: $($key.Length)"
   Write-Host "Prefix: $($key.Substring(0,5))"
   ```

2. **Regenerate API Key**
   ```bash
   # Via Orchestrator API
   curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
       http://orchestrator:8000/api/robots/robot-id/regenerate-key
   ```

3. **Check Rate Limits**
   ```bash
   # Check for 429 responses
   grep "429" /var/log/orchestrator.log
   ```

---

### Symptom: OAuth token expired

**Error Code:** `ERR_TOKEN_EXPIRED`

**Probable Causes:**
- Token not refreshed
- Refresh token expired
- OAuth app permissions changed

**Solutions:**

1. **Re-authenticate**
   - Open Canvas preferences
   - Re-authorize the integration

2. **Check Token Expiry**
   ```python
   import jwt
   token = "your_token"
   decoded = jwt.decode(token, options={"verify_signature": False})
   print(f"Expires: {decoded.get('exp')}")
   ```

3. **Enable Auto-Refresh**
   - Ensure OAuth configuration includes refresh token
   - Check token refresh interval

---

## Database Connection Issues

### Symptom: Database connection failed

**Error Code:** `ERR_DATABASE_CONNECTION`

**Probable Causes:**
- Wrong connection string
- Database server down
- Connection pool exhausted
- SSL requirement

**Solutions:**

1. **Verify Connection String**
   ```bash
   # Test connection
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **Check Database Status**
   ```bash
   # PostgreSQL
   pg_isready -h hostname -p 5432
   ```

3. **Increase Connection Pool**
   ```python
   # In environment
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=10
   ```

4. **Enable SSL**
   ```bash
   DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
   ```

---

### Symptom: Query timeout

**Error Code:** `ERR_QUERY_TIMEOUT`

**Probable Causes:**
- Slow query
- Missing indexes
- Lock contention
- Connection limit reached

**Solutions:**

1. **Add Query Timeout**
   ```python
   # Configure in connection string
   DATABASE_URL="postgresql://...?statement_timeout=30000"
   ```

2. **Check Slow Queries**
   ```sql
   SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '1 minute';
   ```

3. **Analyze and Vacuum**
   ```sql
   VACUUM ANALYZE;
   ```

---

## Error Code Reference

| Error Code | Category | Description |
|------------|----------|-------------|
| `ERR_NODE_NOT_FOUND` | Workflow | Node type not registered |
| `ERR_VARIABLE_NOT_FOUND` | Workflow | Variable not defined |
| `ERR_SELECTOR_NOT_FOUND` | Browser | Element not found |
| `ERR_BROWSER_LAUNCH_FAILED` | Browser | Cannot start browser |
| `ERR_PAGE_TIMEOUT` | Browser | Page load timeout |
| `ERR_DESKTOP_ELEMENT_NOT_FOUND` | Desktop | UI element not found |
| `ERR_ACCESS_DENIED` | Desktop | Insufficient permissions |
| `ERR_KEYBOARD_FAILED` | Desktop | Keyboard input failed |
| `ERR_NETWORK_FAILED` | Network | Request failed |
| `ERR_AUTHENTICATION_FAILED` | Auth | Invalid credentials |
| `ERR_TOKEN_EXPIRED` | Auth | Token needs refresh |
| `ERR_DATABASE_CONNECTION` | Database | Cannot connect |
| `ERR_QUERY_TIMEOUT` | Database | Query took too long |

---

## Getting Help

If you cannot resolve an issue using this guide:

1. **Collect Diagnostic Information**
   ```powershell
   # System info
   systeminfo > diagnostics.txt

   # CasareRPA logs
   Get-Content "$env:APPDATA\CasareRPA\logs\*" >> diagnostics.txt

   # Python environment
   pip freeze >> diagnostics.txt
   ```

2. **Check GitHub Issues**
   - Search existing issues for similar problems
   - Create new issue with diagnostic info

3. **Community Support**
   - Join Discord/Slack community
   - Post with error code and context
