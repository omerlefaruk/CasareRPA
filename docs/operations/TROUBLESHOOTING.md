# CasareRPA Troubleshooting Guide

This guide provides solutions for common issues encountered when using the CasareRPA platform.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Connection Issues](#connection-issues)
3. [Job Execution Issues](#job-execution-issues)
4. [Browser Automation Issues](#browser-automation-issues)
5. [Desktop Automation Issues](#desktop-automation-issues)
6. [Performance Issues](#performance-issues)
7. [Canvas (Designer) Issues](#canvas-designer-issues)
8. [Orchestrator Issues](#orchestrator-issues)
9. [Robot Agent Issues](#robot-agent-issues)
10. [Log Analysis](#log-analysis)

---

## Quick Diagnostics

### System Health Check Script

```powershell
# health_check.ps1
Write-Host "=== CasareRPA Health Check ===" -ForegroundColor Cyan

# Check Python
$pythonVersion = python --version 2>&1
Write-Host "Python: $pythonVersion"

# Check virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Host "Virtual Env: Active ($env:VIRTUAL_ENV)" -ForegroundColor Green
} else {
    Write-Host "Virtual Env: NOT ACTIVE" -ForegroundColor Red
}

# Check ports
$ports = @(8765, 8766)
foreach ($port in $ports) {
    $listener = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($listener) {
        Write-Host "Port $port: LISTENING" -ForegroundColor Green
    } else {
        Write-Host "Port $port: NOT LISTENING" -ForegroundColor Yellow
    }
}

# Check processes
$processes = @("orchestrator", "robot")
foreach ($proc in $processes) {
    $running = Get-Process python -ErrorAction SilentlyContinue |
               Where-Object { $_.CommandLine -like "*$proc*" }
    if ($running) {
        Write-Host "Process $proc: RUNNING" -ForegroundColor Green
    } else {
        Write-Host "Process $proc: NOT RUNNING" -ForegroundColor Yellow
    }
}

# Check disk space
$disk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
if ($freeGB -lt 5) {
    Write-Host "Disk Space: LOW ($freeGB GB free)" -ForegroundColor Red
} else {
    Write-Host "Disk Space: OK ($freeGB GB free)" -ForegroundColor Green
}

Write-Host "=== End Health Check ===" -ForegroundColor Cyan
```

---

## Connection Issues

### Issue: Robot Cannot Connect to Orchestrator

**Symptoms:**
- Robot logs show "Connection failed" or "Connection refused"
- Robot status shows "Disconnected" or "Reconnecting"

**Diagnosis:**
```powershell
# Test connectivity
Test-NetConnection -ComputerName orchestrator-host -Port 8765

# Check if Orchestrator is running
Get-Process python | Where-Object { $_.CommandLine -like "*orchestrator*" }
```

**Solutions:**

1. **Verify Orchestrator is running**
   ```powershell
   python -m casare_rpa.infrastructure.orchestrator.server
   ```

2. **Check firewall rules**
   ```powershell
   # Allow inbound on port 8765
   New-NetFirewallRule -DisplayName "CasareRPA Orchestrator" -Direction Inbound -Port 8765 -Protocol TCP -Action Allow
   ```

3. **Verify network path**
   ```powershell
   # Trace route
   tracert orchestrator-host
   ```

4. **Check Orchestrator bind address**
   - Ensure Orchestrator is bound to `0.0.0.0` not `127.0.0.1`
   ```python
   await engine.start_server(host="0.0.0.0", port=8765)
   ```

---

### Issue: Supabase Connection Timeout

**Symptoms:**
- "Connection timed out after 30.0s"
- "Failed to connect: NetworkError"

**Solutions:**

1. **Verify credentials**
   ```python
   from casare_rpa.robot.config import validate_credentials
   is_valid, error = validate_credentials(url, key)
   print(f"Valid: {is_valid}, Error: {error}")
   ```

2. **Check Supabase status**
   - Visit https://status.supabase.com
   - Check project dashboard

3. **Increase timeout**
   ```yaml
   # robot_config.yaml
   connection:
     connection_timeout: 60.0
   ```

4. **Test direct connection**
   ```python
   from supabase import create_client
   client = create_client(url, key)
   result = client.table("robots").select("id").limit(1).execute()
   print(result)
   ```

---

### Issue: WebSocket Disconnections

**Symptoms:**
- Frequent "Connection closed" messages
- Jobs interrupted mid-execution
- Robot shows as offline intermittently

**Solutions:**

1. **Increase heartbeat timeout**
   ```yaml
   # robot_config.yaml
   connection:
     heartbeat_interval: 30
     heartbeat_timeout: 60
   ```

2. **Check network stability**
   ```powershell
   # Monitor connection
   ping orchestrator-host -t
   ```

3. **Enable keep-alive**
   ```python
   # Already enabled by default in websockets library
   # ping_interval=30, ping_timeout=10
   ```

4. **Check for proxy interference**
   - Disable proxy for internal connections
   - Configure WebSocket-aware proxy if required

---

## Job Execution Issues

### Issue: Job Stuck in "Queued" Status

**Symptoms:**
- Jobs remain in queue indefinitely
- No robots picking up jobs

**Diagnosis:**
```python
# Check queue stats
stats = engine.get_queue_stats()
print(f"Queued: {stats['queued']}, Running: {stats['running']}")

# Check available robots
robots = engine.available_robots
print(f"Available robots: {len(robots)}")
```

**Solutions:**

1. **Verify robots are available**
   ```python
   for robot in engine.get_connected_robots():
       print(f"{robot.name}: {robot.status}, jobs: {robot.current_jobs}/{robot.max_concurrent_jobs}")
   ```

2. **Check environment match**
   - Job environment must match robot environment
   ```python
   # Job
   job.environment = "production"

   # Robot
   robot.environment = "production"  # Must match
   ```

3. **Check robot capacity**
   ```yaml
   # Increase max concurrent jobs
   robot:
     max_concurrent_jobs: 3
   ```

4. **Check dispatch loop**
   ```python
   # Verify dispatcher is running
   stats = engine.get_dispatcher_stats()
   print(stats)
   ```

---

### Issue: Job Fails with Timeout

**Symptoms:**
- Job status changes to "timeout"
- Error: "Job execution timed out"

**Solutions:**

1. **Increase job timeout**
   ```python
   job = await engine.submit_job(
       ...,
       timeout_seconds=7200  # 2 hours
   )
   ```

2. **Check for blocking operations**
   - Look for infinite loops
   - Check for unresponsive elements

3. **Add timeout to individual nodes**
   ```json
   {
     "type": "browser.click",
     "properties": {
       "selector": "#button",
       "timeout": 60000
     }
   }
   ```

4. **Monitor progress**
   - If progress stops at specific node, investigate that node

---

### Issue: Job Fails with "Element Not Found"

**Symptoms:**
- Error: "Element not found: #selector"
- Error: "Timeout waiting for selector"

**Solutions:**

1. **Verify selector is correct**
   - Use browser DevTools to test selector
   - Check if page structure changed

2. **Add wait before action**
   ```json
   {
     "nodes": [
       {
         "type": "browser.wait_for_element",
         "properties": {
           "selector": "#target",
           "timeout": 30000
         }
       },
       {
         "type": "browser.click",
         "properties": {
           "selector": "#target"
         }
       }
     ]
   }
   ```

3. **Use more stable selectors**
   ```
   # Fragile (position-based)
   div > div:nth-child(3) > button

   # Better (attribute-based)
   button[data-testid="submit"]

   # Best (unique ID)
   #submit-button
   ```

4. **Handle dynamic content**
   ```python
   # Wait for network idle
   await page.wait_for_load_state("networkidle")
   ```

---

## Browser Automation Issues

### Issue: Browser Fails to Launch

**Symptoms:**
- Error: "Browser failed to launch"
- Error: "Executable doesn't exist"

**Solutions:**

1. **Install Playwright browsers**
   ```powershell
   playwright install chromium
   playwright install-deps
   ```

2. **Check Playwright installation**
   ```powershell
   playwright --version
   ```

3. **Verify browser path**
   ```python
   from playwright.sync_api import sync_playwright
   with sync_playwright() as p:
       browser = p.chromium.launch()
       print("Browser launched successfully")
       browser.close()
   ```

4. **Run as administrator** (if permission issues)

---

### Issue: Browser Actions Fail Intermittently

**Symptoms:**
- Same workflow sometimes works, sometimes fails
- "Target closed" errors

**Solutions:**

1. **Add explicit waits**
   ```python
   await page.wait_for_load_state("domcontentloaded")
   await page.wait_for_selector("#element", state="visible")
   ```

2. **Handle popups/dialogs**
   ```python
   page.on("dialog", lambda dialog: dialog.accept())
   ```

3. **Increase timeouts**
   ```python
   await page.click("#element", timeout=60000)
   ```

4. **Use retry logic**
   ```python
   for attempt in range(3):
       try:
           await page.click("#element")
           break
       except Exception:
           await asyncio.sleep(1)
   ```

---

### Issue: Screenshots Fail

**Symptoms:**
- Error: "Screenshot failed"
- Empty or corrupted images

**Solutions:**

1. **Check output directory exists**
   ```python
   import os
   os.makedirs("screenshots", exist_ok=True)
   ```

2. **Use absolute paths**
   ```python
   await page.screenshot(path="C:/Screenshots/capture.png")
   ```

3. **Wait for page to render**
   ```python
   await page.wait_for_load_state("networkidle")
   await page.screenshot(path="capture.png", full_page=True)
   ```

---

## Desktop Automation Issues

### Issue: Desktop Element Not Found

**Symptoms:**
- Error: "Control not found"
- Error: "Window not found"

**Solutions:**

1. **Verify window is open**
   ```python
   import uiautomation as auto
   window = auto.WindowControl(searchDepth=1, Name="Application Name")
   print(f"Window exists: {window.Exists()}")
   ```

2. **Check window title exactly**
   ```python
   # Title must match exactly
   window = auto.WindowControl(Name="Notepad")  # Not "Notepad - Untitled"

   # Use regex for partial match
   window = auto.WindowControl(RegexName="Notepad.*")
   ```

3. **Use Inspect.exe to find correct properties**
   - Run Windows SDK Inspect.exe
   - Hover over target element
   - Note AutomationId, Name, ControlType

4. **Increase search depth**
   ```python
   control = auto.ButtonControl(searchDepth=10, Name="OK")
   ```

---

### Issue: Desktop Clicks Not Working

**Symptoms:**
- Click action completes but nothing happens
- Wrong element clicked

**Solutions:**

1. **Ensure window is focused**
   ```python
   window = auto.WindowControl(Name="Application")
   window.SetFocus()
   window.SetTopmost(True)
   ```

2. **Use native click instead of coordinate**
   ```python
   button = window.ButtonControl(Name="Submit")
   button.Click()  # Native click

   # vs coordinate click (less reliable)
   button.Click(x=10, y=10)
   ```

3. **Handle elevated privileges**
   - Run robot as administrator
   - Target app may require elevation

---

## Performance Issues

### Issue: Slow Workflow Execution

**Symptoms:**
- Workflows take longer than expected
- High CPU/memory usage

**Solutions:**

1. **Reduce unnecessary waits**
   ```json
   // Before
   {"type": "wait", "seconds": 5}

   // After - use conditional wait
   {"type": "wait_for_element", "selector": "#loaded"}
   ```

2. **Optimize selectors**
   ```python
   # Slow (searches entire DOM)
   page.locator("text=Submit")

   # Fast (scoped search)
   page.locator("#form").locator("button[type=submit]")
   ```

3. **Reuse browser sessions**
   ```python
   # Don't create new browser for each job
   browser = await playwright.chromium.launch()
   context = await browser.new_context()

   # Reuse context for multiple pages
   page1 = await context.new_page()
   page2 = await context.new_page()
   ```

4. **Enable headless mode in production**
   ```python
   browser = await playwright.chromium.launch(headless=True)
   ```

---

### Issue: High Memory Usage

**Symptoms:**
- Robot memory grows over time
- Out of memory errors

**Solutions:**

1. **Close pages after use**
   ```python
   page = await context.new_page()
   # ... use page ...
   await page.close()
   ```

2. **Clear browser data periodically**
   ```python
   await context.clear_cookies()
   await context.clear_permissions()
   ```

3. **Limit concurrent jobs**
   ```yaml
   robot:
     max_concurrent_jobs: 1  # Reduce if memory issues
   ```

4. **Monitor and restart**
   ```python
   if memory_percent > 90:
       await robot.restart()
   ```

---

## Canvas (Designer) Issues

### Issue: Canvas Crashes on Startup

**Symptoms:**
- Application closes immediately
- Error dialog appears

**Solutions:**

1. **Check Qt installation**
   ```powershell
   pip install --force-reinstall PySide6
   ```

2. **Check for conflicting Qt versions**
   ```powershell
   pip list | Select-String "Qt"
   # Should only have PySide6
   ```

3. **Reset preferences**
   - Delete `%APPDATA%\CasareRPA\preferences.json`

4. **Run from command line to see errors**
   ```powershell
   python -m casare_rpa.presentation.canvas
   ```

---

### Issue: Nodes Not Appearing in Palette

**Symptoms:**
- Node palette is empty
- Some node categories missing

**Solutions:**

1. **Check node registration**
   ```python
   from casare_rpa.presentation.canvas.graph.node_registry import NodeRegistry
   registry = NodeRegistry()
   print(f"Registered nodes: {len(registry.get_all_nodes())}")
   ```

2. **Check for import errors**
   ```python
   # Import all node modules manually to see errors
   from casare_rpa.presentation.canvas.visual_nodes.browser import nodes
   ```

3. **Rebuild node cache**
   - Delete `__pycache__` directories
   - Restart Canvas

---

### Issue: Workflow Won't Save

**Symptoms:**
- Save button does nothing
- Error on save

**Solutions:**

1. **Check file permissions**
   ```powershell
   # Test write access
   New-Item -Path "workflows\test.txt" -ItemType File -Force
   ```

2. **Check disk space**
   ```powershell
   Get-WmiObject Win32_LogicalDisk | Select-Object DeviceID, FreeSpace
   ```

3. **Try Save As to different location**
   - Confirms if specific path is the issue

4. **Check for invalid characters**
   - Workflow name cannot contain: `\ / : * ? " < > |`

---

## Orchestrator Issues

### Issue: Orchestrator High CPU Usage

**Symptoms:**
- CPU at 100%
- Slow response to API calls

**Solutions:**

1. **Check for runaway jobs**
   ```python
   running = engine.get_running_jobs()
   for job in running:
       print(f"{job.id}: {job.progress}% - {job.current_node}")
   ```

2. **Reduce health check frequency**
   ```python
   health_monitor = HealthMonitor(check_interval=60.0)  # Default 30
   ```

3. **Check for connection storms**
   - Robots reconnecting too frequently
   - Increase reconnect delay

4. **Profile the application**
   ```python
   import cProfile
   cProfile.run('asyncio.run(engine.start())')
   ```

---

### Issue: Schedules Not Triggering

**Symptoms:**
- Scheduled jobs don't run
- Next run time in past

**Solutions:**

1. **Verify scheduler is running**
   ```python
   if engine._scheduler:
       jobs = engine._scheduler.get_jobs()
       print(f"Scheduled jobs: {len(jobs)}")
   ```

2. **Check timezone**
   ```python
   # Schedule with explicit timezone
   schedule = await engine.create_schedule(
       ...,
       timezone="America/New_York"
   )
   ```

3. **Verify cron expression**
   ```python
   # Test cron expression
   from croniter import croniter
   cron = croniter("0 9 * * MON-FRI")
   print(f"Next run: {cron.get_next(datetime)}")
   ```

4. **Check APScheduler logs**
   ```python
   import logging
   logging.getLogger('apscheduler').setLevel(logging.DEBUG)
   ```

---

## Robot Agent Issues

### Issue: Robot Offline After Startup

**Symptoms:**
- Robot starts but shows as offline
- Registration fails

**Solutions:**

1. **Check registration message in logs**
   ```
   grep "register" logs/robot_*.log
   ```

2. **Verify robot_id is unique**
   ```yaml
   robot:
     robot_id: "unique-robot-001"
   ```

3. **Check authentication**
   ```yaml
   connection:
     auth_token: "correct-token"
   ```

4. **Test WebSocket connection manually**
   ```python
   import asyncio
   import websockets

   async def test():
       async with websockets.connect("ws://host:8765") as ws:
           print("Connected!")

   asyncio.run(test())
   ```

---

### Issue: Checkpoint Recovery Fails

**Symptoms:**
- Jobs restart from beginning after crash
- "Checkpoint not found" errors

**Solutions:**

1. **Verify checkpointing is enabled**
   ```yaml
   job_execution:
     checkpoint_enabled: true
     checkpoint_on_every_node: true
   ```

2. **Check checkpoint storage**
   ```python
   # List checkpoints
   import sqlite3
   conn = sqlite3.connect("offline_queue.db")
   cursor = conn.execute("SELECT job_id, node_id FROM checkpoints")
   for row in cursor:
       print(row)
   ```

3. **Test checkpoint manually**
   ```python
   checkpoint = await checkpoint_manager.get_checkpoint(job_id)
   print(checkpoint)
   ```

---

## Log Analysis

### Finding Errors

```powershell
# Search all logs for errors
Select-String -Path "logs\*.log" -Pattern "ERROR|CRITICAL|Exception" -Context 2,5

# Search specific time range
Get-Content "logs\orchestrator.log" |
Where-Object { $_ -match "2024-01-15 10:" } |
Select-String "ERROR"
```

### Common Error Patterns

| Pattern | Cause | Solution |
|---------|-------|----------|
| `ConnectionRefusedError` | Service not running | Start the service |
| `TimeoutError` | Network/app slow | Increase timeout |
| `ElementNotFoundError` | Selector invalid | Update selector |
| `CircuitBreakerOpen` | Too many failures | Wait for recovery |
| `AuthenticationError` | Invalid credentials | Check credentials |
| `PermissionError` | Access denied | Check permissions |

### Log Levels

| Level | When Used |
|-------|-----------|
| DEBUG | Detailed diagnostic info |
| INFO | Normal operations |
| WARNING | Recoverable issues |
| ERROR | Operation failures |
| CRITICAL | System failures |

### Enabling Debug Logs

```python
from loguru import logger

# Enable debug logging
logger.add(
    "logs/debug_{time}.log",
    level="DEBUG",
    rotation="100 MB"
)
```

---

## Getting Help

If you cannot resolve an issue:

1. **Collect diagnostic information**
   - Error messages and stack traces
   - Relevant log files
   - Steps to reproduce

2. **Check existing issues**
   - GitHub Issues
   - Documentation

3. **Create detailed bug report**
   - Environment (OS, Python version)
   - Configuration
   - Expected vs actual behavior

---

## Related Documentation

- [Operations Runbook](RUNBOOK.md)
- [System Overview](../architecture/SYSTEM_OVERVIEW.md)
- [API Reference](../api/REST_API_REFERENCE.md)
