# CasareRPA Robot Orchestration Architecture - Complete Roadmap

**Status**: Project Aether Phases 1-3.2 Complete, Phase 4.1 Complete
**Goal**: Transform CasareRPA into enterprise-grade distributed RPA platform
**Last Updated**: 2025-11-28

---

## Executive Summary

This roadmap details the path to a **production-ready robot orchestration architecture** with:
- ✅ Durable execution (DBOS) - automatic crash recovery
- ✅ Distributed job queue (PgQueuer) - 18k+ jobs/sec
- ✅ Self-healing selectors (Tier 1) - automatic UI adaptation
- 🚧 Multi-robot coordination
- 🚧 Enterprise security (Vault)
- 🚧 Real-time monitoring (OpenTelemetry)
- 🚧 Cloud deployment (DBOS Cloud)

---

## Current Architecture State

### ✅ Completed Components

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (Local)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  OrchestratorEngine                                   │  │
│  │    ├─ JobQueue (in-memory) ← needs PgQueuer          │  │
│  │    ├─ JobScheduler (APScheduler)                     │  │
│  │    └─ TriggerManager (manual, scheduled, webhook)   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               WORKFLOW EXECUTION (DBOS)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  @DBOS.workflow()                                     │  │
│  │    ├─ initialize_context_step() [@step]             │  │
│  │    ├─ execute_node_step() × N [@step]               │  │
│  │    └─ cleanup_context_step() [@step]                │  │
│  │                                                       │  │
│  │  Features:                                            │  │
│  │    ✅ Automatic checkpointing                         │  │
│  │    ✅ Crash recovery                                  │  │
│  │    ✅ Exactly-once execution                          │  │
│  │    ✅ workflow_id idempotency                         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            SELF-HEALING SELECTORS (Tier 1)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  HeuristicSelectorHealer                              │  │
│  │    ├─ Multi-attribute fallback (400ms budget)        │  │
│  │    ├─ Fragility scoring                              │  │
│  │    └─ Telemetry collection                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 🚧 Missing Components

```
┌─────────────────────────────────────────────────────────────┐
│                 MISSING: Distributed Queue                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  PgQueuerProducer (Orchestrator)                      │  │
│  │    - Job submission with priority                     │  │
│  │    - Multi-tenancy (RLS)                              │  │
│  │  PgQueuerConsumer (Robots)                            │  │
│  │    - Job claiming (SKIP LOCKED)                       │  │
│  │    - Visibility timeout + heartbeat                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              MISSING: Robot Agent Architecture               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  RobotAgent (runs on worker machines)                 │  │
│  │    ├─ Poll queue for jobs                            │  │
│  │    ├─ Execute workflows (DBOS durable)               │  │
│  │    ├─ Send heartbeats                                │  │
│  │    ├─ Report status                                  │  │
│  │    └─ Handle graceful shutdown                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               MISSING: Security & Secrets                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  HashiCorp Vault / Supabase Vault                    │  │
│  │    - Credential storage                               │  │
│  │    - Dynamic secrets                                  │  │
│  │    - Audit logging                                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            MISSING: Monitoring & Observability               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  OpenTelemetry                                        │  │
│  │    - Distributed tracing                              │  │
│  │    - Metrics (job duration, queue depth)             │  │
│  │    - Logs aggregation                                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase-by-Phase Roadmap

### ✅ Phase 1: DBOS Foundation (COMPLETE)
**Status**: Shipped (`d1f8b5a`)

- ✅ DBOS configuration management
- ✅ Postgres connection handling
- ✅ DBOSWorkflowRunner structure
- ✅ Environment-based config

**Impact**: Foundation for durable execution.

---

### ✅ Phase 2: PgQueuer Infrastructure (COMPLETE)
**Status**: Shipped (`b4e79cd`)

- ✅ PgQueuerProducer (job submission)
- ✅ PgQueuerConsumer (job claiming)
- ✅ QueueAdapter (backward-compatible)
- ✅ Priority mapping (0-20 scale)
- ✅ Dead letter queue
- ✅ Multi-tenancy (RLS)

**Impact**: 18k+ jobs/sec throughput, distributed queue ready.

---

### ✅ Phase 3.1: Step Functions & State (COMPLETE)
**Status**: Shipped (`77e833c`)

- ✅ ExecutionState value object
- ✅ ExecutionContext serialization
- ✅ Step functions structure
- ✅ Fallback mode (no DBOS)

**Impact**: State management for crash recovery.

---

### ✅ Phase 3.2: Workflow Decoration (COMPLETE)
**Status**: Shipped (`d942639`)

- ✅ @DBOS.workflow() decorator
- ✅ @DBOS.step() decorators
- ✅ workflow_id for idempotency
- ✅ start_durable_workflow() helper
- ✅ get_workflow_status() monitoring

**Impact**: Actual durable execution with DBOS runtime.

---

### 🚧 Phase 3.3: Orchestrator Queue Integration (HIGH PRIORITY)
**Status**: Not Started
**Estimated Effort**: 2-3 days
**Dependencies**: Phases 2, 3.1

#### Goals
1. Replace in-memory `JobQueue` with `QueueAdapter` in OrchestratorEngine
2. Support both in-memory (dev) and PgQueuer (prod) modes
3. Maintain backward compatibility

#### Tasks

**3.3.1: Update OrchestratorEngine**
- [ ] Replace `self._job_queue = JobQueue()` with `QueueAdapter`
- [ ] Add `use_pgqueuer` config flag
- [ ] Update `submit_job()` to use async interface
- [ ] Add `start()` and `stop()` lifecycle methods

**Files to Modify**:
```python
# src/casare_rpa/orchestrator/engine.py

class OrchestratorEngine:
    def __init__(self, config: OrchestratorConfig):
        # OLD:
        # self._job_queue = JobQueue()

        # NEW:
        from casare_rpa.orchestrator.queue_adapter import QueueAdapter

        self._queue_adapter = QueueAdapter(
            use_pgqueuer=config.use_pgqueuer,
            postgres_url=config.postgres_url if config.use_pgqueuer else None,
            tenant_id=config.tenant_id
        )

    async def submit_job(self, job: Job) -> str:
        # OLD:
        # self._job_queue.enqueue(job)

        # NEW:
        job_id = await self._queue_adapter.enqueue(job)
        return job_id

    async def start(self):
        """Start orchestrator services."""
        await self._queue_adapter.start()
        self._scheduler.start()

    async def stop(self):
        """Stop orchestrator services."""
        await self._queue_adapter.stop()
        self._scheduler.shutdown()
```

**3.3.2: Configuration**
```yaml
# config/orchestrator.yaml

orchestrator:
  use_pgqueuer: true  # false for in-memory dev mode
  postgres_url: ${POSTGRES_URL}
  tenant_id: "default"

  job_settings:
    default_priority: NORMAL  # LOW, NORMAL, HIGH, URGENT
    default_timeout: 3600
    max_retries: 3
```

**3.3.3: Tests**
- [ ] Test dual backend (in-memory vs PgQueuer)
- [ ] Test job submission with priorities
- [ ] Test concurrent job submission (load test)
- [ ] Test graceful shutdown

**Success Criteria**:
- ✅ Can switch between in-memory and PgQueuer via config
- ✅ Existing workflows work without changes
- ✅ Jobs submitted to PgQueuer can be claimed by Robots
- ✅ Performance: Submit 1000 jobs in <1 second

---

### 🚧 Phase 3.4: Robot Agent Implementation (HIGH PRIORITY)
**Status**: Not Started
**Estimated Effort**: 3-4 days
**Dependencies**: Phase 3.3

#### Goals
1. Create standalone Robot agent for worker machines
2. Poll PgQueuer for jobs
3. Execute workflows with DBOS durability
4. Report status and heartbeat

#### Architecture

```python
# src/casare_rpa/robot/agent.py

class RobotAgent:
    """
    Standalone Robot agent for distributed execution.

    Responsibilities:
    - Poll PgQueuer for jobs
    - Execute workflows with DBOS
    - Send heartbeats to maintain lease
    - Report execution status
    - Handle graceful shutdown
    """

    def __init__(self, config: RobotConfig):
        self.config = config
        self.robot_id = config.robot_id or socket.gethostname()

        # PgQueuer consumer
        self.consumer = PgQueuerConsumer(
            postgres_url=config.postgres_url,
            robot_id=self.robot_id,
            batch_size=config.batch_size,
            visibility_timeout_seconds=30
        )

        # Workflow executor (DBOS)
        self.executor = DBOSWorkflowExecutor()

        # Running state
        self._running = False
        self._current_job: Optional[Job] = None

    async def start(self):
        """Start robot agent."""
        logger.info(f"Starting Robot {self.robot_id}")

        self._running = True

        # Start consumer
        await self.consumer.start()

        # Start polling loop
        asyncio.create_task(self._polling_loop())

        # Start heartbeat loop
        asyncio.create_task(self._heartbeat_loop())

    async def _polling_loop(self):
        """Poll for jobs and execute."""
        while self._running:
            try:
                # Claim job from queue
                job = await self.consumer.claim_job()

                if job:
                    self._current_job = job
                    await self._execute_job(job)
                    self._current_job = None
                else:
                    # No jobs available, sleep
                    await asyncio.sleep(1)

            except Exception as e:
                logger.exception(f"Error in polling loop: {e}")
                await asyncio.sleep(5)

    async def _execute_job(self, job: Job):
        """Execute a job with DBOS durability."""
        logger.info(f"Executing job {job.job_id}: {job.workflow_name}")

        try:
            # Load workflow
            workflow = await load_workflow_by_id(job.workflow_id)

            # Execute with DBOS
            from casare_rpa.infrastructure.dbos.workflow_runner_decorated import (
                start_durable_workflow
            )

            result = await start_durable_workflow(
                workflow=workflow,
                workflow_id=job.job_id,  # Use job_id for idempotency
                initial_variables=job.variables,
                wait_for_result=True
            )

            # Mark job complete
            if result["success"]:
                await self.consumer.complete_job(job.job_id, result)
            else:
                await self.consumer.fail_job(
                    job.job_id,
                    error=result.get("error", "Unknown error")
                )

        except Exception as e:
            logger.exception(f"Job execution failed: {e}")
            await self.consumer.fail_job(job.job_id, error=str(e))

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to extend job lease."""
        while self._running:
            if self._current_job:
                try:
                    await self.consumer.extend_lease(
                        self._current_job.job_id,
                        extension_seconds=30
                    )
                except Exception as e:
                    logger.error(f"Heartbeat failed: {e}")

            await asyncio.sleep(10)  # Heartbeat every 10s

    async def stop(self):
        """Graceful shutdown."""
        logger.info(f"Stopping Robot {self.robot_id}")

        self._running = False

        # Wait for current job to complete (with timeout)
        if self._current_job:
            logger.info("Waiting for current job to complete...")
            await asyncio.sleep(60)  # Grace period

        await self.consumer.stop()
```

#### Configuration

```yaml
# config/robot.yaml

robot:
  robot_id: null  # Auto-generated from hostname if null
  postgres_url: ${POSTGRES_URL}

  polling:
    batch_size: 1  # Jobs to claim at once
    poll_interval_seconds: 1

  execution:
    max_concurrent_jobs: 1  # Run one job at a time per robot
    job_timeout_seconds: 3600

  heartbeat:
    interval_seconds: 10
    lease_extension_seconds: 30

  graceful_shutdown:
    grace_period_seconds: 60
```

#### CLI

```bash
# Start robot agent
python -m casare_rpa.robot.cli start --config config/robot.yaml

# Stop robot agent (graceful)
python -m casare_rpa.robot.cli stop --robot-id worker-01

# Show robot status
python -m casare_rpa.robot.cli status
```

#### Tasks

**3.4.1: Robot Agent Core**
- [ ] Implement `RobotAgent` class
- [ ] Polling loop with PgQueuerConsumer
- [ ] Job execution with DBOS
- [ ] Heartbeat mechanism
- [ ] Graceful shutdown

**3.4.2: Robot CLI**
- [ ] `robot start` command
- [ ] `robot stop` command
- [ ] `robot status` command
- [ ] Configuration loading

**3.4.3: Tests**
- [ ] Test job claiming
- [ ] Test workflow execution
- [ ] Test heartbeat extension
- [ ] Test graceful shutdown
- [ ] Test crash recovery (kill robot mid-job)

**Success Criteria**:
- ✅ Robot can claim jobs from PgQueuer
- ✅ Robot executes workflows with DBOS durability
- ✅ Heartbeats extend job lease
- ✅ Graceful shutdown waits for job completion
- ✅ Crashed robots don't lose jobs (visibility timeout)

---

### ✅ Phase 4.1: Self-Healing Selectors Tier 1 (COMPLETE)
**Status**: Shipped (PR #27)

- ✅ SmartSelector value object
- ✅ Multi-attribute fallback (8 strategies)
- ✅ Fragility scoring
- ✅ HeuristicSelectorHealer (<400ms)
- ✅ HealingTelemetryService

**Impact**: Workflows adapt to UI changes automatically.

---

### 🚧 Phase 4.2: Anchor-Based Healing (MEDIUM PRIORITY)
**Status**: Not Started
**Estimated Effort**: 2-3 days
**Dependencies**: Phase 4.1

#### Goals
1. Navigate from stable "anchor" elements to target
2. Auto-detect stable anchors during recording
3. Provide spatial relationship selectors

#### Architecture

```python
# src/casare_rpa/domain/value_objects/anchor.py

class SpatialRelationship(str, Enum):
    """Spatial relationship between anchor and target."""
    ABOVE = "above"
    BELOW = "below"
    LEFT_OF = "left_of"
    RIGHT_OF = "right_of"
    INSIDE = "inside"

class AnchoredSelector(BaseModel):
    """Selector using anchor-based navigation."""
    id: str
    target: SmartSelector  # Target element
    anchor: SmartSelector  # Stable anchor element
    relationship: SpatialRelationship
    max_distance: int = 200  # pixels
```

```python
# src/casare_rpa/infrastructure/browser/anchor_healer.py

class AnchorBasedHealer:
    """Tier 2 healing using anchor-based navigation."""

    async def find_element(
        self,
        page: Page,
        selector: AnchoredSelector,
        workflow_name: str
    ) -> Optional[tuple[Locator, HealingEvent]]:
        """
        Find element by navigating from anchor.

        Steps:
        1. Find anchor element (usually stable header/label)
        2. Get anchor bounding box
        3. Search for target in spatial region
        4. Return closest match
        """
        # Find anchor
        anchor_locator = await self.heuristic_healer.find_element(
            page, selector.anchor, workflow_name
        )

        if not anchor_locator:
            return None

        # Get anchor position
        anchor_box = await anchor_locator.bounding_box()

        # Define search region based on relationship
        search_region = self._compute_search_region(
            anchor_box,
            selector.relationship,
            selector.max_distance
        )

        # Find target in region
        target_locator = await self._find_in_region(
            page,
            selector.target,
            search_region
        )

        if target_locator:
            # Create healing event
            event = create_healing_event(
                selector_id=selector.id,
                tier=HealingTier.TIER_2_ANCHOR,
                # ...
            )
            return (target_locator, event)

        return None
```

#### Tasks

**4.2.1: Domain Models**
- [ ] `SpatialRelationship` enum
- [ ] `AnchoredSelector` value object
- [ ] Serialization support

**4.2.2: Anchor Healer**
- [ ] Implement `AnchorBasedHealer`
- [ ] Spatial region computation
- [ ] Find-in-region logic
- [ ] Bounding box handling

**4.2.3: Canvas Integration**
- [ ] Update visual node recorder to detect anchors
- [ ] UI for defining anchor relationships
- [ ] Anchor visualization in canvas

**4.2.4: Tests**
- [ ] Test anchor detection
- [ ] Test spatial navigation
- [ ] Test with dynamic layouts

**Success Criteria**:
- ✅ Can navigate from stable header to dynamic button
- ✅ Handles layout changes (responsive design)
- ✅ <400ms tier 2 healing budget

---

### 🚧 Phase 4.3: Computer Vision Fallback (LOW PRIORITY)
**Status**: Not Started
**Estimated Effort**: 3-4 days
**Dependencies**: Phase 4.2

#### Goals
1. Template matching as last resort
2. Perceptual hashing for fast similarity
3. Template caching with TTL

#### Dependencies
```bash
pip install opencv-python>=4.9.0 pillow>=10.2.0 imagehash>=4.3.1
```

#### Architecture

```python
# src/casare_rpa/infrastructure/browser/cv_healer.py

class ComputerVisionHealer:
    """Tier 3 healing using template matching."""

    async def find_element(
        self,
        page: Page,
        template_path: str,
        threshold: float = 0.8
    ) -> Optional[tuple[Coordinates, HealingEvent]]:
        """
        Find element by template matching.

        Steps:
        1. Screenshot page
        2. Load template image
        3. cv2.matchTemplate()
        4. Return best match if confidence > threshold
        """
        # Capture screenshot
        screenshot = await page.screenshot(type="png")

        # Load template
        template = cv2.imread(template_path)

        # Match
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # Found match
            x, y = max_loc
            w, h = template.shape[1], template.shape[0]

            return ((x + w//2, y + h//2), healing_event)

        return None
```

**Tasks**:
- [ ] OpenCV integration
- [ ] Template storage strategy
- [ ] Perceptual hashing cache
- [ ] Performance optimization

**Success Criteria**:
- ✅ Can find elements when selectors fail
- ✅ <200ms tier 3 healing budget
- ✅ >80% match confidence

---

### 🚧 Phase 5: Security & Vault (HIGH PRIORITY)
**Status**: Not Started
**Estimated Effort**: 2-3 days
**Dependencies**: None

#### Goals
1. Secure credential storage (HashiCorp Vault or Supabase Vault)
2. Dynamic secrets for database connections
3. Audit logging for credential access

#### Architecture

```python
# src/casare_rpa/infrastructure/security/vault_adapter.py

class VaultAdapter:
    """Adapter for HashiCorp Vault or Supabase Vault."""

    async def get_secret(self, key: str) -> str:
        """Retrieve secret from vault."""
        pass

    async def set_secret(self, key: str, value: str) -> None:
        """Store secret in vault."""
        pass

    async def delete_secret(self, key: str) -> None:
        """Delete secret from vault."""
        pass
```

#### Tasks

**5.1: Vault Integration**
- [ ] HashiCorp Vault client
- [ ] Supabase Vault client
- [ ] VaultAdapter interface
- [ ] Configuration

**5.2: Credential Resolution**
- [ ] Update ExecutionContext to resolve credentials
- [ ] Inject secrets into node execution
- [ ] Audit logging

**5.3: Canvas Integration**
- [ ] Credential field type in properties panel
- [ ] Secure credential input (password fields)
- [ ] Never serialize credentials in workflow JSON

**Success Criteria**:
- ✅ Credentials never stored in workflow JSON
- ✅ Dynamic secrets from Vault
- ✅ Audit log for all credential access

---

### 🚧 Phase 6: Monitoring & Observability (MEDIUM PRIORITY)
**Status**: Not Started
**Estimated Effort**: 3-4 days
**Dependencies**: Phase 3.4

#### Goals
1. OpenTelemetry integration
2. Distributed tracing across Orchestrator → Robot → Workflow
3. Metrics (job duration, queue depth, success rate)

#### Architecture

```python
# src/casare_rpa/infrastructure/telemetry/otel.py

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize tracer
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="otel-collector:4317"))
)
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

# Instrument workflow execution
@tracer.start_as_current_span("execute_workflow")
async def execute_workflow(workflow_id: str):
    span = trace.get_current_span()
    span.set_attribute("workflow.id", workflow_id)
    span.set_attribute("workflow.name", workflow.metadata.name)

    # Execute workflow
    result = await workflow.execute()

    span.set_attribute("workflow.success", result.success)
    return result
```

#### Metrics to Collect

- **Queue Metrics**:
  - `queue.depth` - Current queue size
  - `queue.age` - Oldest job age
  - `jobs.submitted` - Jobs submitted per minute
  - `jobs.claimed` - Jobs claimed per minute

- **Workflow Metrics**:
  - `workflow.duration` - Workflow execution time
  - `workflow.success_rate` - Success percentage
  - `node.duration` - Per-node execution time
  - `healing.events` - Selector healing occurrences

- **Robot Metrics**:
  - `robot.active` - Active robot count
  - `robot.idle_time` - Time since last job
  - `robot.utilization` - Job execution percentage

#### Tasks

**6.1: OpenTelemetry Setup**
- [ ] Install OpenTelemetry SDK
- [ ] Configure OTLP exporter
- [ ] Tracer and meter providers

**6.2: Instrumentation**
- [ ] Instrument OrchestratorEngine
- [ ] Instrument RobotAgent
- [ ] Instrument workflow execution
- [ ] Instrument self-healing selectors

**6.3: Dashboards**
- [ ] Grafana dashboard for queue metrics
- [ ] Grafana dashboard for workflow metrics
- [ ] Alerts for queue depth, failure rate

**Success Criteria**:
- ✅ End-to-end trace from job submission to completion
- ✅ Real-time metrics in Grafana
- ✅ Alerts for anomalies

---

### 🚧 Phase 7: Orchestrator API (MEDIUM PRIORITY)
**Status**: Not Started
**Estimated Effort**: 2-3 days
**Dependencies**: Phase 3.3

#### Goals
1. REST API for job submission
2. WebSocket for real-time updates
3. API documentation (OpenAPI)

#### Architecture

```python
# src/casare_rpa/orchestrator/api/main.py

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

app = FastAPI(title="CasareRPA Orchestrator API")

@app.post("/api/v1/jobs")
async def submit_job(request: SubmitJobRequest):
    """Submit a job to the orchestrator."""
    job_id = await orchestrator.submit_job(
        workflow_id=request.workflow_id,
        variables=request.variables,
        priority=request.priority
    )

    return {"job_id": job_id, "status": "submitted"}

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status."""
    status = await orchestrator.get_job_status(job_id)
    return status

@app.websocket("/ws/jobs/{job_id}")
async def job_updates(websocket: WebSocket, job_id: str):
    """Real-time job updates via WebSocket."""
    await websocket.accept()

    # Subscribe to job events
    async for event in orchestrator.subscribe_job_events(job_id):
        await websocket.send_json(event.to_dict())
```

#### Tasks

**7.1: FastAPI Setup**
- [ ] Create FastAPI app
- [ ] Define API routes
- [ ] Request/response models

**7.2: WebSocket Support**
- [ ] WebSocket endpoint for job updates
- [ ] Event bus integration
- [ ] Connection management

**7.3: Documentation**
- [ ] OpenAPI schema generation
- [ ] Swagger UI
- [ ] API usage guide

**Success Criteria**:
- ✅ Can submit jobs via REST API
- ✅ Real-time updates via WebSocket
- ✅ OpenAPI documentation generated

---

### 🚧 Phase 8: Cloud Deployment (DBOS Cloud)
**Status**: Not Started
**Estimated Effort**: 1-2 days
**Dependencies**: All previous phases

#### Goals
1. Deploy to DBOS Cloud
2. Managed Postgres and queue
3. Auto-scaling robots

#### Steps

**8.1: DBOS Cloud Setup**
```bash
# Install DBOS CLI
npm install -g @dbos-inc/dbos-cloud

# Login
dbos-cloud login

# Deploy
dbos-cloud deploy
```

**8.2: Configuration**
```yaml
# dbos-cloud.yaml

name: casare-rpa
runtime: python
version: 3.0.0

database:
  provider: dbos-managed  # Managed Postgres

compute:
  orchestrator:
    instances: 1
    memory: 2Gi

  robots:
    instances: 3
    memory: 4Gi
    auto_scaling:
      min_instances: 1
      max_instances: 10
      target_queue_depth: 10
```

**8.3: CI/CD**
```yaml
# .github/workflows/deploy.yml

name: Deploy to DBOS Cloud

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        run: |
          dbos-cloud deploy --env production
```

**Success Criteria**:
- ✅ Orchestrator running on DBOS Cloud
- ✅ Robots auto-scale based on queue depth
- ✅ CI/CD pipeline deploys automatically

---

## Priority Matrix

### Immediate (Next 1-2 Weeks)

| Phase | Priority | Impact | Effort |
|-------|----------|--------|--------|
| **3.3** Orchestrator Queue Integration | 🔴 CRITICAL | Enables distributed execution | 2-3 days |
| **3.4** Robot Agent Implementation | 🔴 CRITICAL | Core distributed architecture | 3-4 days |
| **5** Security & Vault | 🟠 HIGH | Production security requirement | 2-3 days |

### Short-Term (1-2 Months)

| Phase | Priority | Impact | Effort |
|-------|----------|--------|--------|
| **6** Monitoring & Observability | 🟡 MEDIUM | Operations visibility | 3-4 days |
| **7** Orchestrator API | 🟡 MEDIUM | External integration | 2-3 days |
| **4.2** Anchor-Based Healing | 🟡 MEDIUM | Improved resilience | 2-3 days |

### Long-Term (3+ Months)

| Phase | Priority | Impact | Effort |
|-------|----------|--------|--------|
| **8** Cloud Deployment | 🟢 LOW | Managed hosting | 1-2 days |
| **4.3** Computer Vision Fallback | 🟢 LOW | Last-resort healing | 3-4 days |

---

## Success Metrics

### Technical Metrics

- **Queue Throughput**: 18,000+ jobs/sec (PgQueuer capability)
- **Workflow Durability**: 100% crash recovery (DBOS guarantees)
- **Selector Healing**: >90% success rate (Tier 1)
- **Robot Utilization**: >80% (efficient job distribution)
- **API Latency**: <100ms (job submission)

### Business Metrics

- **Deployment Time**: <5 minutes (single command)
- **Robot Provisioning**: <30 seconds (auto-scaling)
- **Workflow Maintenance**: 50% reduction (self-healing)
- **Mean Time to Recovery**: <1 minute (crash recovery)

---

## Technical Debt & Future Enhancements

### Post-MVP Enhancements

1. **ML-Based Selector Healing**
   - Train model on healing patterns
   - Predict best fallback strategy
   - Auto-generate selector improvements

2. **Workflow Version Control**
   - Git-like versioning for workflows
   - Rollback to previous versions
   - A/B testing workflows

3. **Cross-Platform Robots**
   - Linux robot agents
   - macOS robot agents
   - Container-based robots (Docker)

4. **Advanced Scheduling**
   - Cron expressions
   - Dependency-based scheduling (DAGs)
   - Priority queues per tenant

5. **Multi-Tenancy**
   - Tenant isolation (RLS)
   - Per-tenant quotas
   - Billing integration

---

## Getting Started

### For Developers

**Next Task**: Implement Phase 3.3 (Orchestrator Queue Integration)

```bash
cd /c/Users/Rau/Desktop/casare-aether
git checkout feature/aether-v3

# Create new branch for Phase 3.3
git checkout -b feature/phase3-3-orchestrator-queue

# Start implementation
# See Phase 3.3 section above for detailed tasks
```

### For Project Managers

**Critical Path**:
1. Phase 3.3 (Orchestrator Queue) → 2-3 days
2. Phase 3.4 (Robot Agent) → 3-4 days
3. Phase 5 (Security) → 2-3 days

**Total Time to Production MVP**: ~2 weeks

**Resource Requirements**:
- 1 Senior Backend Developer (distributed systems)
- 1 DevOps Engineer (DBOS Cloud deployment)
- 1 QA Engineer (integration testing)

---

## Conclusion

This roadmap transforms CasareRPA from a local automation tool into an **enterprise-grade distributed RPA platform** with:

- ✅ **Durable execution** (DBOS) - workflows never lose progress
- ✅ **Distributed queue** (PgQueuer) - 18k+ jobs/sec throughput
- ✅ **Self-healing** (Tier 1) - adapts to UI changes automatically
- 🚧 **Multi-robot coordination** - horizontal scaling
- 🚧 **Enterprise security** (Vault) - secure credential management
- 🚧 **Real-time monitoring** (OpenTelemetry) - full observability
- 🚧 **Cloud deployment** (DBOS Cloud) - managed infrastructure

**Next Step**: Implement Phase 3.3 (Orchestrator Queue Integration)

---

**Last Updated**: 2025-11-28
**Maintained By**: Project Aether Team
**Status**: 5/8 phases complete (62.5%)
