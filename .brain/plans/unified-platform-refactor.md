# Unified Platform Refactoring Plan

## Overview
Consolidate monitoring, orchestration, robot, installer, deploy, config, kubernetes, migrations, supabase, and fleet management into a cohesive, production-ready system.

## Current State Analysis

### Problems Identified
1. **Scattered .env files** - 9 different locations with overlapping variables
2. **Fragmented migrations** - 4+ migration paths (deploy/supabase, infrastructure/database, infrastructure/persistence, infrastructure/queue)
3. **Monitoring disconnect** - React dashboard separate from Python observability, no unified metrics pipeline
4. **Config duplication** - config/, deploy/*, root level configs with inconsistent patterns
5. **Build fragmentation** - Multiple build scripts, no unified CI/CD pipeline
6. **Orchestrator complexity** - Client/server separation unclear, persistence split between local/cloud
7. **Robot lifecycle gaps** - Installer, agent, CLI not fully integrated
8. **Fleet management partial** - Canvas UI exists but not connected to real-time backend

## 10 Refactor Agent Assignments

### Agent 1: Monitoring Unification
**Scope**: `src/casare_rpa/infrastructure/observability/`, `monitoring-dashboard/`
**Goals**:
- Unify Python telemetry with React dashboard via WebSocket
- Create MetricsExporter that pushes to both Prometheus and dashboard
- Add OpenTelemetry traces for full distributed tracing
- Consolidate stdout_capture, system_metrics, logging into single observability facade

### Agent 2: Orchestrator API Refactor
**Scope**: `src/casare_rpa/infrastructure/orchestrator/api/`
**Goals**:
- Consolidate routers into cohesive CRUD patterns
- Unify auth middleware (JWT + API key)
- Add rate limiting per-tenant
- Create unified error responses
- Add OpenAPI schema generation

### Agent 3: Robot Agent Consolidation
**Scope**: `src/casare_rpa/robot/`
**Goals**:
- Merge distributed_agent + coordination into single robust agent
- Add proper lifecycle management (start/stop/pause/resume)
- Integrate circuit_breaker + checkpoint into main loop
- Add proper signal handling for Windows service mode
- Unify metrics collection with observability layer

### Agent 4: Installer Consolidation
**Scope**: `deploy/installer/`
**Goals**:
- Create unified build pipeline (PyInstaller -> NSIS)
- Add version injection from pyproject.toml
- Create single-command build: `python -m deploy.build`
- Add code signing preparation
- Create MSI alternative to NSIS

### Agent 5: Deploy/Docker Unification
**Scope**: `deploy/docker/`, `deploy/orchestrator/`
**Goals**:
- Consolidate duplicate docker-compose files
- Create multi-stage Dockerfile for minimal images
- Add docker-compose profiles (dev, prod, full)
- Unify port mappings and networking
- Add healthcheck standardization

### Agent 6: Config Consolidation
**Scope**: `config/`, `.env*`, `deploy/*/.env*`
**Goals**:
- Create single `.env.template` with ALL variables documented
- Create `config/` as source of truth with per-environment overrides
- Add config validation on startup
- Create config loader that works for both dev and production
- Remove duplicate .env files, use symlinks where needed

### Agent 7: Kubernetes Modernization
**Scope**: `deploy/kubernetes/`
**Goals**:
- Add Kustomize overlays (base, dev, staging, prod)
- Create proper Helm chart alternative
- Add KEDA scaler config for job-based autoscaling
- Add proper resource limits and requests
- Create ingress with TLS termination

### Agent 8: Migrations Consolidation
**Scope**: All `**/migrations/**/*.sql`
**Goals**:
- Single migration source: `deploy/migrations/`
- Create migration runner script
- Add rollback support (up/down migrations)
- Version migrations with semver
- Add migration verification tests

### Agent 9: Supabase Integration
**Scope**: `deploy/supabase/`
**Goals**:
- Consolidate setup scripts (setup.py, quickstart.py, auto_setup.py)
- Create single `supabase_setup.py` with all operations
- Add edge function deployment automation
- Create RLS policy documentation
- Add Supabase type generation for Python

### Agent 10: Fleet Management Integration
**Scope**: `src/casare_rpa/presentation/canvas/ui/dialogs/fleet*`, `controllers/robot_controller.py`
**Goals**:
- Connect FleetDashboard to live orchestrator WebSocket
- Add real-time robot status updates
- Integrate with unified metrics system
- Add drag-and-drop job assignment to robots
- Create robot group management UI

## Architecture Target

```
deploy/
├── migrations/           # Single source of truth for ALL migrations
│   ├── 001_initial.sql
│   ├── 002_robots.sql
│   └── migrate.py        # Migration runner
├── docker/
│   ├── Dockerfile        # Multi-stage, multi-target
│   └── docker-compose.yml # Unified with profiles
├── kubernetes/
│   ├── base/             # Kustomize base
│   └── overlays/         # dev, staging, prod
├── installer/
│   ├── build.py          # Single build script
│   └── casarerpa.nsi     # NSIS installer
├── supabase/
│   ├── setup.py          # Unified setup
│   └── functions/        # Edge functions
└── config/
    ├── .env.template     # Documented template
    └── schema.py         # Pydantic config validation

src/casare_rpa/
├── infrastructure/
│   ├── observability/    # Unified monitoring facade
│   │   ├── metrics.py    # Prometheus + custom
│   │   ├── traces.py     # OpenTelemetry
│   │   └── facade.py     # Single entry point
│   └── orchestrator/
│       ├── api/          # Refactored routers
│       └── client.py     # Unified client
├── robot/
│   ├── agent.py          # Consolidated agent
│   └── service.py        # Windows service wrapper
└── presentation/
    └── canvas/
        └── ui/dialogs/fleet/  # Integrated fleet UI
```

## Execution Order

1. Config (Agent 6) - Foundation for all other work
2. Migrations (Agent 8) - Database foundation
3. Orchestrator API (Agent 2) - Core backend
4. Robot (Agent 3) - Worker nodes
5. Monitoring (Agent 1) - Observability
6. Fleet Management (Agent 10) - UI integration
7. Deploy/Docker (Agent 5) - Containerization
8. Kubernetes (Agent 7) - Orchestration
9. Installer (Agent 4) - Distribution
10. Supabase (Agent 9) - Cloud integration

## Success Criteria

- [ ] Single `python -m deploy.setup` command sets up entire platform
- [ ] Single docker-compose up starts full stack
- [ ] Migrations run from single source with rollback
- [ ] Config loads from single .env with validation
- [ ] Fleet dashboard shows real-time robot/job status
- [ ] Robot installer builds from single command
- [ ] Kubernetes deploys with `kubectl apply -k deploy/kubernetes/overlays/prod`
- [ ] All tests pass with >80% coverage on refactored code
