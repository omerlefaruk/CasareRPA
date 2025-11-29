# Getting Started with CasareRPA

Welcome to CasareRPA! This guide will help you install, configure, and create your first automation workflow.

## Table of Contents

1. [What is CasareRPA?](#what-is-casarerpa)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Creating Your First Workflow](#creating-your-first-workflow)
6. [Running Workflows](#running-workflows)
7. [Next Steps](#next-steps)

---

## What is CasareRPA?

CasareRPA is a Windows Desktop RPA (Robotic Process Automation) platform that enables you to automate repetitive tasks through a visual, drag-and-drop workflow editor.

### Key Features

- **Visual Workflow Editor** - Create automation workflows without coding
- **Web Automation** - Automate browser interactions with Playwright
- **Desktop Automation** - Control Windows applications via UIAutomation
- **Scheduling** - Schedule workflows to run automatically
- **Triggers** - Start workflows from webhooks, file changes, emails, and more
- **Scalable** - Run multiple robots for parallel execution

### Architecture Overview

```
+-------------+     +---------------+     +--------+
|   Canvas    | --> | Orchestrator  | --> | Robot  |
|  (Designer) |     |   (Manager)   |     |(Runner)|
+-------------+     +---------------+     +--------+
       |                   |                   |
       v                   v                   v
   Create              Schedule           Execute
   Workflows           & Queue            Automation
```

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11 (64-bit) |
| Python | 3.12 or higher |
| RAM | 4 GB |
| Disk | 500 MB free space |
| Display | 1280x720 resolution |

### Recommended

| Component | Recommendation |
|-----------|----------------|
| RAM | 8 GB or more |
| CPU | Multi-core processor |
| Disk | SSD storage |
| Display | 1920x1080 resolution |

---

## Installation

### Step 1: Install Python

1. Download Python 3.12+ from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH"
4. Click "Install Now"

Verify installation:
```powershell
python --version
# Expected: Python 3.12.x
```

### Step 2: Get CasareRPA

Option A: Clone from Git
```powershell
git clone https://github.com/omerlefaruk/CasareRPA.git
cd CasareRPA
```

Option B: Download ZIP
1. Download the repository ZIP
2. Extract to desired location
3. Open PowerShell in extracted folder

### Step 3: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` in your prompt.

### Step 4: Install Dependencies

```powershell
# Install CasareRPA in development mode
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### Step 5: Verify Installation

```powershell
# Run the Canvas application
python run.py
```

If you see the CasareRPA window, installation is complete!

---

## Quick Start

### Starting the Canvas (Designer)

```powershell
# Navigate to CasareRPA directory
cd C:\path\to\CasareRPA

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start Canvas
python run.py
```

### Canvas Interface Overview

```
+------------------------------------------------------------------+
|  File   Edit   View   Workflow   Tools   Help                    |
+------------------------------------------------------------------+
|  +----------------+  +-----------------------------------+  +---+|
|  |  Node Palette  |  |                                   |  | P ||
|  |                |  |          Canvas Area              |  | r ||
|  |  [Basic]       |  |                                   |  | o ||
|  |  [Browser]     |  |    Drag nodes here to build       |  | p ||
|  |  [Desktop]     |  |    your workflow                  |  | e ||
|  |  [Control]     |  |                                   |  | r ||
|  |  [Data]        |  |                                   |  | t ||
|  |  [File]        |  |                                   |  | i ||
|  |  ...           |  |                                   |  | e ||
|  +----------------+  +-----------------------------------+  | s ||
|                                                              +---+|
+------------------------------------------------------------------+
|  Output Console                                                  |
+------------------------------------------------------------------+
```

### Key Areas

| Area | Purpose |
|------|---------|
| Node Palette | Browse and search for automation nodes |
| Canvas Area | Build workflows by connecting nodes |
| Properties Panel | Configure selected node settings |
| Output Console | View execution logs and debug info |

---

## Creating Your First Workflow

Let's create a simple workflow that opens a browser, navigates to a website, and takes a screenshot.

### Step 1: Create New Workflow

1. Click **File > New Workflow** (or press `Ctrl+N`)
2. You'll see an empty canvas with a Start node

### Step 2: Add Browser Nodes

1. In the Node Palette, expand **Browser** category
2. Drag **Open Browser** to the canvas
3. Drag **Navigate** to the canvas
4. Drag **Screenshot** to the canvas
5. Drag **Close Browser** to the canvas

### Step 3: Connect the Nodes

1. Click on the **output port** (right side) of Start node
2. Drag to the **input port** (left side) of Open Browser node
3. Continue connecting:
   - Open Browser -> Navigate
   - Navigate -> Screenshot
   - Screenshot -> Close Browser

Your workflow should look like:

```
[Start] --> [Open Browser] --> [Navigate] --> [Screenshot] --> [Close Browser]
```

### Step 4: Configure Node Properties

Click on each node and set properties in the Properties Panel:

**Open Browser:**
- Browser: `chromium`
- Headless: `false` (to see the browser)

**Navigate:**
- URL: `https://example.com`

**Screenshot:**
- Path: `C:\Screenshots\example.png`
- Full Page: `true`

### Step 5: Save Your Workflow

1. Click **File > Save** (or press `Ctrl+S`)
2. Choose location and filename
3. Click Save

### Step 6: Run the Workflow

1. Click the **Run** button in the toolbar (or press `F5`)
2. Watch the execution in the Output Console
3. Check the screenshot in your specified path

Congratulations! You've created and run your first workflow!

---

## Running Workflows

### Run Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Run** | Execute entire workflow | Normal execution |
| **Debug** | Step-by-step execution | Troubleshooting |
| **Selected** | Run only selected nodes | Testing parts |

### Running in Debug Mode

1. Click **Debug** button (or press `F6`)
2. Use step controls:
   - **Step Over** (`F10`) - Execute current node
   - **Continue** (`F5`) - Run to next breakpoint
   - **Stop** (`Shift+F5`) - Stop execution

### Setting Breakpoints

1. Right-click on a node
2. Select **Toggle Breakpoint**
3. Node will show a red indicator
4. Execution pauses at breakpoints in debug mode

### Viewing Results

After execution:
- **Output Console** shows logs
- **Variables Panel** shows variable values
- **Properties Panel** shows node results

---

## Common Tasks

### Web Automation

```
Example: Login to a website

[Start]
    |
[Open Browser]
    |
[Navigate] (URL: https://example.com/login)
    |
[Type] (Selector: #username, Value: myuser)
    |
[Type] (Selector: #password, Value: ${password})
    |
[Click] (Selector: #login-button)
    |
[Wait For Element] (Selector: .dashboard)
    |
[Close Browser]
```

### File Operations

```
Example: Process files in a folder

[Start]
    |
[List Files] (Path: C:\Input, Pattern: *.xlsx)
    |
[For Each] (Variable: file)
    |   |
    |   [Read Excel] (Path: ${file})
    |   |
    |   [Transform Data] (...)
    |   |
    |   [Write Excel] (Path: C:\Output\${filename})
    |
[End For Each]
```

### Desktop Automation

```
Example: Automate Notepad

[Start]
    |
[Launch App] (Path: notepad.exe)
    |
[Wait For Window] (Title: Untitled - Notepad)
    |
[Type Text] (Text: Hello, World!)
    |
[Send Keys] (Keys: Ctrl+S)
    |
[Wait For Window] (Title: Save As)
    |
[Type Text] (Text: output.txt)
    |
[Click] (Name: Save)
```

---

## Using Variables

### Creating Variables

1. Open **Variables Panel** (View > Variables)
2. Click **Add Variable**
3. Set name, type, and value

### Variable Types

| Type | Example | Use Case |
|------|---------|----------|
| String | `"Hello"` | Text values |
| Integer | `42` | Numbers |
| Boolean | `true/false` | Conditions |
| List | `["a", "b", "c"]` | Collections |
| Credential | `(secure)` | Passwords |

### Using Variables in Nodes

Reference variables with `${variable_name}`:

```
Navigate URL: ${base_url}/login
Type Value: ${username}
File Path: ${output_folder}/report_${date}.xlsx
```

### Special Variables

| Variable | Description |
|----------|-------------|
| `${workflow_id}` | Current workflow ID |
| `${job_id}` | Current job ID |
| `${timestamp}` | Current timestamp |
| `${date}` | Current date (YYYY-MM-DD) |

---

## Scheduling Workflows

### Creating a Schedule

1. Click **Workflow > Schedule**
2. Configure schedule:
   - **Name**: Descriptive name
   - **Frequency**: Daily, Weekly, Cron
   - **Time**: When to run
   - **Timezone**: Your timezone
3. Click **Create Schedule**

### Schedule Types

| Type | Example | Description |
|------|---------|-------------|
| Once | Jan 15, 2024 9:00 AM | Run once |
| Hourly | Every 2 hours | Regular intervals |
| Daily | Every day at 9:00 AM | Daily execution |
| Weekly | Mon, Wed, Fri at 8:00 AM | Specific days |
| Cron | `0 9 * * MON-FRI` | Advanced scheduling |

### Cron Expression Examples

| Expression | Meaning |
|------------|---------|
| `0 9 * * *` | Every day at 9:00 AM |
| `0 */2 * * *` | Every 2 hours |
| `0 9 * * MON-FRI` | Weekdays at 9:00 AM |
| `0 0 1 * *` | First day of month |

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Browser won't open | Run `playwright install chromium` |
| Element not found | Check selector, add wait |
| Workflow won't save | Check file permissions |
| Canvas won't start | Check Python version |

### Getting Help

1. Check **Output Console** for error messages
2. Review [Troubleshooting Guide](../operations/TROUBLESHOOTING.md)
3. Search existing issues on GitHub
4. Create new issue with:
   - Error message
   - Steps to reproduce
   - Workflow file (if possible)

---

## Next Steps

### Learn More

- [System Architecture](../architecture/SYSTEM_OVERVIEW.md) - Understand the platform
- [API Reference](../api/REST_API_REFERENCE.md) - Integration options
- [Contributing Guide](../development/CONTRIBUTING.md) - Extend the platform

### Advanced Topics

1. **Triggers** - Start workflows from external events
2. **Error Handling** - Build robust workflows
3. **Robot Deployment** - Scale with multiple robots
4. **Custom Nodes** - Create your own automation nodes

### Example Workflows

Look in the `examples/` folder for sample workflows:
- `web_scraping.json` - Extract data from websites
- `file_processing.json` - Batch file operations
- `desktop_automation.json` - Windows app automation
- `data_entry.json` - Form filling automation

---

## Quick Reference

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New workflow |
| `Ctrl+O` | Open workflow |
| `Ctrl+S` | Save workflow |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `F5` | Run workflow |
| `F6` | Debug workflow |
| `F10` | Step over (debug) |
| `Delete` | Delete selected |
| `Ctrl+A` | Select all |
| `Ctrl+C` | Copy |
| `Ctrl+V` | Paste |
| `Ctrl+F` | Find node |

### Node Categories

| Category | Contains |
|----------|----------|
| Basic | Start, End, Log, Comment |
| Browser | Open, Navigate, Click, Type, Wait |
| Desktop | Find, Click, Type, Send Keys |
| Control | If, For Each, While, Try/Catch |
| Data | Variables, Transform, Filter |
| File | Read, Write, Copy, Delete |
| Email | Send, Read, Download |
| Database | Query, Insert, Update |
| REST API | GET, POST, PUT, DELETE |

---

Happy automating with CasareRPA!
