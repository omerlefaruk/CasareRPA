# Execution Modes

CasareRPA provides multiple ways to run workflows, each suited to different use cases. Understanding execution modes helps you choose the right approach for development, testing, and production scenarios.

## Overview of Execution Modes

| Mode | Environment | Use Case |
|------|-------------|----------|
| Local (Canvas) | Designer UI | Development and testing |
| Robot | Headless agent | Production execution |
| Orchestrated | Queued jobs | Enterprise scheduling |
| Debug | Canvas with breakpoints | Troubleshooting |
| Validate | Pre-run check | Configuration verification |

## Local Execution (Canvas Preview)

Local execution runs workflows directly within the Canvas designer interface.

### When to Use

- Developing and testing new workflows
- Quick verification of changes
- Interactive debugging
- Learning and experimentation

### How to Run Locally

1. Open your workflow in Canvas
2. Click the **Play** button or press `F5`
3. Watch execution progress in real-time
4. View results in the Log panel

### Characteristics

| Aspect | Behavior |
|--------|----------|
| UI | Full Canvas interface visible |
| Browser | Opens visible browser windows (unless headless) |
| Speed | Normal execution speed |
| Logs | Real-time in Log panel |
| Variables | Visible in Variables panel |
| Interaction | Can interact during execution |

### Local Execution Flow

```
[Canvas UI]
     |
     v
[Click Play] --> [Initialize Context] --> [Execute Nodes] --> [Show Results]
                        |                       |
                   [Load Variables]        [Update UI]
                   [Setup Resources]       [Log Progress]
```

### Stopping Execution

- Click the **Stop** button
- Press `Shift+F5`
- Close the Canvas window

## Robot Execution (Headless Agent)

The Robot is a standalone agent that executes workflows without the Canvas UI.

### When to Use

- Production deployments
- Scheduled automations
- Server-based execution
- Unattended automation

### Running with Robot

**Command line:**
```bash
python -m casare_rpa.robot run workflow.json
```

**With variables:**
```bash
python -m casare_rpa.robot run workflow.json --var username=admin --var env=production
```

### Characteristics

| Aspect | Behavior |
|--------|----------|
| UI | No GUI (headless) |
| Browser | Headless by default |
| Speed | Optimized for throughput |
| Logs | Written to files/stdout |
| Variables | Passed via command line or config |
| Interaction | None (unattended) |

### Robot Architecture

```
[Robot Agent]
     |
     +-- [Job Executor] --> [Workflow Engine]
     |                            |
     +-- [Heartbeat Service]      +-- [Node Executor]
     |                            |
     +-- [Log Handler]            +-- [Resource Manager]
```

### Robot Configuration

Configure the Robot via environment variables or config file:

| Setting | Description | Default |
|---------|-------------|---------|
| `CASARE_LOG_LEVEL` | Log verbosity | INFO |
| `CASARE_HEADLESS` | Browser headless mode | true |
| `CASARE_TIMEOUT` | Default node timeout | 30000 |
| `CASARE_RETRY_COUNT` | Retry attempts on failure | 3 |

## Orchestrated Execution (Queued Jobs)

The Orchestrator manages multiple Robots and queues jobs for execution.

### When to Use

- Enterprise deployments
- Multiple concurrent workflows
- Job scheduling and prioritization
- Centralized management

### How It Works

1. **Submit Job**: Upload workflow to Orchestrator
2. **Queue**: Job enters the execution queue
3. **Assign**: Orchestrator assigns job to available Robot
4. **Execute**: Robot runs the workflow
5. **Report**: Results sent back to Orchestrator

### Orchestrator Components

```
[Orchestrator Server]
     |
     +-- [API Endpoints] --> /jobs, /robots, /workflows
     |
     +-- [Job Queue] --> Priority-based scheduling
     |
     +-- [Robot Registry] --> Track available Robots
     |
     +-- [Results Store] --> Job outcomes and logs
```

### Job States

| State | Description |
|-------|-------------|
| PENDING | Job submitted, waiting for Robot |
| ASSIGNED | Robot selected, preparing to run |
| RUNNING | Workflow actively executing |
| COMPLETED | Workflow finished successfully |
| FAILED | Workflow encountered error |
| CANCELLED | Job cancelled by user |

### Submitting Jobs

**Via API:**
```bash
curl -X POST http://orchestrator:8765/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "my-workflow", "priority": 1}'
```

**Via Canvas:**
1. Select **Run > Run on Orchestrator**
2. Choose target Robot or let Orchestrator assign
3. Monitor job status in the Fleet panel

## Debug Mode

Debug mode provides step-by-step execution with breakpoints for troubleshooting.

### When to Use

- Investigating unexpected behavior
- Understanding data flow
- Verifying conditional logic
- Learning how nodes work

### Enabling Debug Mode

1. Click the **Debug** button (bug icon) or press `F6`
2. Execution starts and pauses at the first node
3. Step through nodes one at a time
4. Inspect variables and outputs at each step

### Debug Controls

| Control | Action | Shortcut |
|---------|--------|----------|
| **Step Over** | Execute current node, move to next | `F10` |
| **Step Into** | Enter subflow (if applicable) | `F11` |
| **Continue** | Run until next breakpoint | `F5` |
| **Stop** | End debug session | `Shift+F5` |

### Breakpoints

Breakpoints pause execution at specific nodes:

**Setting Breakpoints:**
1. Click the left margin of a node (red dot appears)
2. Or right-click node and select **Toggle Breakpoint**

**Breakpoint Types:**

| Type | Behavior |
|------|----------|
| Standard | Always pauses |
| Conditional | Pauses when condition is true |
| Hit Count | Pauses after N executions |

### Debug Panel

When paused, the Debug panel shows:

- **Call Stack**: Current execution path
- **Variables**: All variables and their current values
- **Watch**: Custom expressions to monitor
- **Output**: Current node's output values

### Inspecting Data

While paused:
1. Hover over variables in the Variables panel
2. Expand objects to see nested properties
3. Add expressions to the Watch list
4. Check output ports of completed nodes

## Validate Mode

Validate mode checks workflow configuration without executing.

### When to Use

- Before deploying to production
- After making changes
- Verifying connections and settings
- Pre-flight checks

### Running Validation

1. Select **Run > Validate Workflow** or press `Ctrl+Shift+V`
2. Validator checks all nodes and connections
3. Issues appear in the Problems panel

### What Gets Validated

| Check | Description |
|-------|-------------|
| Required properties | All required fields have values |
| Connection validity | Ports are compatible and connected |
| Type compatibility | Data types match between connections |
| Missing dependencies | Required resources are available |
| Circular references | No infinite loops in execution flow |
| Syntax errors | Expressions and selectors are valid |

### Validation Results

| Severity | Meaning |
|----------|---------|
| Error | Cannot execute, must fix |
| Warning | May cause issues, review |
| Info | Suggestion for improvement |

## Execution States

During any execution mode, nodes transition through states:

| State | Description | Visual |
|-------|-------------|--------|
| IDLE | Not yet executed | Gray |
| RUNNING | Currently executing | Blue/animated |
| SUCCESS | Completed successfully | Green |
| ERROR | Failed with error | Red |
| SKIPPED | Bypassed (conditional) | Yellow |
| CANCELLED | Stopped by user | Gray strikethrough |

### State Transitions

```
IDLE --> RUNNING --> SUCCESS
              |
              +--> ERROR (with retry) --> RUNNING
              |
              +--> ERROR (final) --> [Workflow fails or continues]
              |
              +--> SKIPPED (condition false)
```

### Viewing Execution State

- **Canvas**: Nodes highlight with state colors
- **Log Panel**: Timestamped state changes
- **API**: Query job/execution status

## Execution Context

All modes share a common execution context that provides:

| Resource | Description |
|----------|-------------|
| Variables | Storage for workflow data |
| Browser Resources | Playwright browsers, contexts, pages |
| Desktop Context | Windows automation handles |
| Credentials | Secure credential access |
| Logging | Execution event recording |

### Context Lifecycle

```
[Start Execution]
     |
     v
[Create Context] --> [Initialize Variables]
     |
     v
[Execute Nodes] --> [Context available to all nodes]
     |
     v
[Cleanup Resources] --> [Close browsers, release handles]
     |
     v
[End Execution]
```

## Choosing the Right Mode

| Scenario | Recommended Mode |
|----------|------------------|
| Building new workflow | Local (Canvas) |
| Testing changes | Local with Debug |
| Finding bugs | Debug with breakpoints |
| Production deployment | Robot (headless) |
| Scheduled tasks | Orchestrated |
| Enterprise scale | Orchestrated |
| Pre-deployment check | Validate |

## Best Practices

### Development

1. **Use Debug mode liberally**: Step through new logic
2. **Set breakpoints at decision points**: Verify conditions
3. **Watch key variables**: Monitor data transformation
4. **Validate before committing**: Catch configuration errors

### Production

1. **Test locally first**: Ensure workflow works in Canvas
2. **Run in Robot mode**: Verify headless behavior
3. **Use Orchestrator for scale**: Manage multiple workflows
4. **Monitor job status**: Track success/failure rates
5. **Review logs**: Investigate failures promptly

### Debugging Tips

1. **Start with breakpoints at inputs**: Verify incoming data
2. **Check variable values**: Ensure correct data flow
3. **Verify conditional logic**: Step through branches
4. **Test error paths**: Trigger errors intentionally
5. **Use the Log node**: Add explicit logging statements

## Error Handling Across Modes

| Mode | Error Behavior |
|------|----------------|
| Local | Shows error dialog, workflow stops |
| Debug | Pauses at error node, allows inspection |
| Robot | Logs error, continues or stops per config |
| Orchestrated | Reports failure to Orchestrator, job marked FAILED |

### Retry Configuration

Configure retry behavior for transient failures:

```python
# In node configuration
retry_count: 3
retry_delay_ms: 1000
retry_on_error_codes: ["TIMEOUT", "CONNECTION_REFUSED"]
```

## Next Steps

- [Workflows](workflows.md): Understand workflow structure
- [Nodes and Ports](nodes-and-ports.md): Learn about execution ports
- [Triggers](triggers.md): See how triggered workflows execute
- [Variables](variables.md): Manage execution context data
