# CasareRPA Project Context & Architecture

## Overview
CasareRPA is a comprehensive Robotic Process Automation platform featuring a visual workflow designer, a distributed robot execution engine, and a centralized orchestrator with a web dashboard.

## Architecture
The project follows **Clean Architecture** principles.

### Directory Structure
- **`src/casare_rpa/`**: Core Python source code.
  - **`domain/`**: Pure business logic and entities. No external dependencies.
  - **`application/`**: Use cases and application logic.
  - **`infrastructure/`**: Adapters for DB, APIs, File System, etc.
    - **`orchestrator/`**: The FastAPI backend for the Orchestrator.
    - **`agent/`**: Robot agent infrastructure implementations.
  - **`presentation/`**: UI and Interface layers.
    - **`canvas/`**: The Qt-based Visual Workflow Designer (Desktop App).
  - **`robot/`**: Robot agent logic (likely Domain/Application mix, currently refactoring).
  - **`nodes/`**: Implementation of workflow nodes (Browser, Excel, etc.).
- **`monitoring-dashboard/`**: React + Vite frontend for the Orchestrator.
- **`deploy/`**: Kubernetes manifests, Docker files, and deployment scripts.
- **`tests/`**: Pytest suite matching the source structure.
- **`scripts/`**: Utility scripts.
- **`docs/`**: Documentation.

## Unified CLI (`manage.py`)
The project now uses a unified CLI entry point: `manage.py`.

### Common Commands
- **Start Canvas (Designer):**
  ```bash
  python manage.py canvas
  ```
- **Start Orchestrator (API):**
  ```bash
  python manage.py orchestrator start
  ```
- **Start Robot Agent:**
  ```bash
  python manage.py robot start
  ```
- **Start Dashboard:**
  ```bash
  python manage.py dashboard
  ```

## Key Components

### 1. Orchestrator
- **Stack:** FastAPI, PostgreSQL.
- **Location:** `src/casare_rpa/infrastructure/orchestrator/api/main.py`
- **Role:** Manages robots, jobs, schedules, and serves the dashboard API.

### 2. Robot Agent
- **Stack:** Python (asyncio), Playwright, UIAutomation.
- **Location:** `src/casare_rpa/robot/` & `src/casare_rpa/infrastructure/agent/`
- **Role:** Connects to Orchestrator (via WebSocket/HTTP) and executes assigned workflows.

### 3. Monitoring Dashboard
- **Stack:** React, Vite, Tailwind.
- **Location:** `monitoring-dashboard/`
- **Role:** Web UI for managing the fleet, viewing logs, and scheduling jobs.

### 4. Canvas Designer
- **Stack:** PySide6 (Qt), NodeGraphQt.
- **Location:** `src/casare_rpa/presentation/canvas/`
- **Role:** Desktop application for visually building automation workflows.

## Development Guidelines
- **Refactoring:** When moving code, strictly adhere to Clean Architecture boundaries.
- **Cleanup:** Legacy scripts are in `scripts/legacy_launchers/`. Prefer using `manage.py`.
- **Testing:** Run `pytest` for all backend tests.

## Copilot/AI Instructions
This file serves as the primary context for AI assistants. When creating plans or modifying code, refer to the structure defined here to ensure consistency.
