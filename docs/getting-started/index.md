# Getting Started

Welcome to CasareRPA! This guide will help you get up and running quickly with enterprise-grade RPA automation.

## Quick Start

1. **[Installation](installation.md)** - Set up your environment
2. **[First Workflow](first-workflow.md)** - Create your first automation
3. **[Core Concepts](concepts.md)** - Understand the basics

## Prerequisites

- Windows 10/11 (Linux/Mac for development)
- Python 3.12+
- Node.js 18+ (for monitoring dashboard)
- 8GB RAM (16GB recommended)
- PostgreSQL 15+ (optional, in-memory fallback available)

## Platform Components

| Component | Purpose | Port |
|-----------|---------|------|
| **Canvas Designer** | Visual workflow editor | Desktop app |
| **Orchestrator API** | REST/WebSocket backend | 8000 |
| **Monitoring Dashboard** | Real-time monitoring | 5173 |
| **Robot Agent** | Distributed execution | - |

## Quick Platform Start

```bash
# Windows
start_platform.bat

# Linux/Mac
./start_dev.sh

# Start Canvas Designer
python run.py
```

## Execution Modes

| Mode | Shortcut | Description |
|------|----------|-------------|
| **Run Local** | F8 | Execute in Canvas process |
| **Run on Robot** | Ctrl+F5 | Submit to LAN robot |
| **Submit** | Ctrl+Shift+F5 | Queue for internet robots |

## Next Steps

After completing the getting started guide:

- Explore the [Node Reference](../nodes/index.md) - 405 automation nodes
- Check the [User Guides](../guides/index.md) - Step-by-step tutorials
- Review the [API Reference](../api/index.md) - Architecture layers
- See the [Orchestrator API](../api/infrastructure/orchestrator-api.md) - REST endpoints
