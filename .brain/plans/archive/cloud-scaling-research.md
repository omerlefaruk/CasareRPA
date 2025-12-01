# Cloud & Scaling Research for CasareRPA

**Date**: 2025-12-01
**Status**: COMPLETE
**Focus**: Enterprise-scale cloud deployment strategies
**Summary**: Windows RPA requires hybrid architecture - cloud control plane with on-prem Windows robots. Kubernetes with KEDA for orchestrator scaling; Windows VMs/physical machines for desktop automation. Cost optimization via spot instances, reserved capacity, and intelligent job routing.

---

## Executive Summary

CasareRPA has strong foundations for cloud scaling:
- DistributedRobotAgent with PostgreSQL-based job queue (SKIP LOCKED)
- Supabase Realtime for hybrid poll+subscribe
- UnifiedResourceManager with pooling/quotas
- FastAPI orchestrator API with health checks
- Robot registration with capability-based routing

This research identifies cloud deployment models, container orchestration, serverless options, and scaling strategies for 1000+ robots.

---

## 1. Deployment Models

### 1.1 SaaS (Software-as-a-Service)

**Architecture**:
```
[CasareRPA Cloud]
    |
    +-- Control Plane (Managed)
    |   +-- Orchestrator API (FastAPI)
    |   +-- Job Queue (PostgreSQL/Supabase)
    |   +-- Dashboard (React)
    |   +-- Workflow Designer (Web Canvas)
    |
    +-- Data Plane (Per-Tenant)
        +-- Isolated Robot Pools
        +-- Tenant-specific DB schemas
        +-- Encrypted credential stores
```

**Pros**:
- No infrastructure for customers
- Centralized updates
- Usage-based billing
- Fastest time-to-value

**Cons**:
- Data residency concerns (GDPR, HIPAA)
- Limited customization
- Internet dependency
- Per-seat licensing complexity

**Tech Stack**:
- AWS/Azure/GCP multi-tenant deployment
- Supabase for PostgreSQL + Realtime
- Row-Level Security (RLS) for tenant isolation
- Kubernetes for robot orchestration

### 1.2 Hybrid (On-Prem Robots, Cloud Control)

**Architecture**:
```
[Cloud Control Plane]          [On-Prem Data Plane]
    |                               |
    +-- Orchestrator API            +-- DistributedRobotAgent
    +-- Job Queue                   +-- Local Browser/Desktop
    +-- Dashboard                   +-- Credential Vault
    +-- Workflow Storage            +-- Audit Logs
    |                               |
    +----- TLS Tunnel (WebSocket) --+
```

**Current CasareRPA Support**:
- DistributedRobotAgent already supports remote orchestration
- Supabase Realtime provides WebSocket connectivity
- Robot capability advertisement enables intelligent routing

**Pros**:
- Data stays on-prem
- Desktop automation works (UIAutomation)
- Firewall-friendly (outbound only)
- Centralized workflow management

**Cons**:
- On-prem infrastructure required
- Network latency for job assignment
- Split ops responsibility

**Recommended Additions**:
```python
# tunnel/agent_tunnel.py
class SecureTunnel:
    """
    Establishes outbound-only secure connection to cloud control plane.
    Uses WebSocket with mTLS for authentication.
    """
    async def connect(self, control_plane_url: str, client_cert: Path) -> None:
        """Connect to control plane with mutual TLS."""
        pass

    async def register(self, robot_capabilities: RobotCapabilities) -> str:
        """Register robot and receive robot_id."""
        pass
```

### 1.3 On-Premises (Self-Hosted)

**Architecture**:
```
[Customer Datacenter]
    |
    +-- CasareRPA Orchestrator (Docker/K8s)
    |   +-- FastAPI (existing)
    |   +-- PostgreSQL (existing)
    |   +-- React Dashboard (existing)
    |
    +-- Robot Pool (Windows VMs/Physical)
        +-- DistributedRobotAgent (existing)
        +-- Local resources
```

**Current Support**: Nearly complete
- FastAPI orchestrator exists
- DistributedRobotAgent exists
- PostgreSQL queue exists
- Missing: Installer/deployment packaging

**Deployment Options**:
1. **Docker Compose** - Single server, dev/small deployments
2. **Kubernetes Helm Chart** - Production, HA deployment
3. **Windows Installer** - Desktop robot installation

**Recommended Additions**:
```yaml
# deploy/docker-compose.yml
version: '3.8'
services:
  orchestrator:
    image: casarerpa/orchestrator:latest
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:pass@db:5432/casare

  db:
    image: postgres:16
    volumes: ["pgdata:/var/lib/postgresql/data"]

  dashboard:
    image: casarerpa/dashboard:latest
    ports: ["3000:3000"]

volumes:
  pgdata:
```

### 1.4 Deployment Model Comparison

| Criteria | SaaS | Hybrid | On-Prem |
|----------|------|--------|---------|
| Time to Value | Fast | Medium | Slow |
| Data Control | Low | High | Full |
| Desktop Automation | Limited | Full | Full |
| Maintenance Burden | None | Split | Full |
| Customization | Low | Medium | Full |
| Scaling Ease | Easy | Medium | Hard |
| Enterprise Compliance | Challenging | Good | Full |
| Cost (Small) | Low | Medium | High |
| Cost (Large) | High | Medium | Medium |

**Recommendation**: Prioritize Hybrid model first
- Matches existing architecture
- Enables desktop automation
- Addresses enterprise security concerns
- Lower development effort than full SaaS

---

## 2. Container Orchestration

### 2.1 Kubernetes for Robot Orchestration

**Challenge**: RPA robots need:
- Persistent browser contexts (stateful)
- Desktop access (Windows containers limited)
- GPU for vision AI
- High resource isolation

**Solution**: Kubernetes with specialized node pools

```yaml
# k8s/robot-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: casare-robot-pool
spec:
  replicas: 10  # Managed by HPA
  selector:
    matchLabels:
      app: casare-robot
  template:
    metadata:
      labels:
        app: casare-robot
    spec:
      nodeSelector:
        casare.io/robot-capable: "true"
        kubernetes.io/os: linux  # or windows
      containers:
      - name: robot
        image: casarerpa/robot:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: casare-db
              key: url
        - name: CASARE_ROBOT_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        volumeMounts:
        - name: browser-cache
          mountPath: /home/robot/.cache
      volumes:
      - name: browser-cache
        emptyDir:
          sizeLimit: 2Gi
```

### 2.2 Horizontal Pod Autoscaler

```yaml
# k8s/robot-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: casare-robot-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: casare-robot-pool
  minReplicas: 2
  maxReplicas: 100
  metrics:
  - type: External
    external:
      metric:
        name: casare_queue_depth
      target:
        type: AverageValue
        averageValue: 5  # 5 pending jobs per robot
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 10
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### 2.3 KEDA for Queue-Based Scaling

```yaml
# k8s/keda-scaledobject.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: casare-robot-scaler
spec:
  scaleTargetRef:
    name: casare-robot-pool
  minReplicaCount: 2
  maxReplicaCount: 1000
  triggers:
  - type: postgresql
    metadata:
      connectionFromEnv: POSTGRES_URL
      query: "SELECT COUNT(*) FROM job_queue WHERE status = 'pending'"
      targetQueryValue: "5"
  - type: cron
    metadata:
      timezone: America/New_York
      start: "0 8 * * *"    # Scale up at 8 AM
      end: "0 18 * * *"     # Scale down at 6 PM
      desiredReplicas: "50"
```

### 2.4 Docker Strategies

**Robot Dockerfile**:
```dockerfile
# Dockerfile.robot
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install CasareRPA
COPY . /app
RUN pip install -e .

# Pre-install browsers
RUN playwright install chromium firefox

# Non-root user for security
RUN useradd -m robot && chown -R robot:robot /app
USER robot

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
  CMD python -c "import httpx; httpx.get('http://localhost:8080/health')"

CMD ["python", "-m", "casare_rpa.robot.cli", "run"]
```

**Windows Container (for Desktop Automation)**:
```dockerfile
# Dockerfile.robot.windows
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Install Python
RUN powershell -Command \
    Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe -OutFile python.exe; \
    Start-Process python.exe -Wait -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1'

WORKDIR C:\\app
COPY . C:\\app

RUN pip install -e .

CMD ["python", "-m", "casare_rpa.robot.cli", "run"]
```

### 2.5 Kubernetes Operators (Future)

Custom operator for intelligent robot management:

```yaml
# k8s/crds/robot-pool.yaml
apiVersion: casare.io/v1
kind: RobotPool
metadata:
  name: production-pool
spec:
  environment: production
  minRobots: 5
  maxRobots: 100
  capabilities:
    browser: [chromium, firefox]
    desktop: false
    tags: [high-memory, gpu]
  scaling:
    metric: queue-depth
    targetPerRobot: 3
  scheduling:
    businessHours:
      timezone: America/New_York
      start: "08:00"
      end: "18:00"
      minRobots: 50
    offHours:
      minRobots: 5
```

---

## 3. Serverless Options

### 3.1 AWS Lambda for Lightweight Automation

**Use Cases**:
- API-only workflows (no browser/desktop)
- Webhook handlers
- Data transformation
- Notification triggers

**Limitations**:
- 15 min max execution
- No persistent state
- No desktop/GUI
- Cold start latency

**Implementation**:
```python
# serverless/lambda_handler.py
import json
from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase

def handler(event: dict, context) -> dict:
    """AWS Lambda handler for CasareRPA workflows."""
    workflow_json = event.get("workflow")
    variables = event.get("variables", {})

    # Only allow API-compatible nodes
    executor = ExecuteWorkflowUseCase(
        browser_enabled=False,
        desktop_enabled=False,
        timeout_seconds=min(event.get("timeout", 60), 840)  # Max 14 min
    )

    result = executor.execute_sync(workflow_json, variables)

    return {
        "statusCode": 200 if result.success else 500,
        "body": json.dumps(result.to_dict())
    }
```

**SAM Template**:
```yaml
# serverless/template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  CasareRPAFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: lambda_handler.handler
      Runtime: python3.12
      Timeout: 900
      MemorySize: 3008  # Max for compute-intensive
      Environment:
        Variables:
          POSTGRES_URL: !Ref DatabaseUrl
      Events:
        WorkflowApi:
          Type: Api
          Properties:
            Path: /execute
            Method: POST
```

### 3.2 Azure Functions

Similar to Lambda but with:
- Durable Functions for long-running workflows
- Better Windows support
- Premium plan for VNet integration

```python
# serverless/azure_function.py
import azure.functions as func
import azure.durable_functions as df

async def orchestrator_function(context: df.DurableOrchestrationContext):
    """Durable orchestrator for multi-step workflows."""
    workflow = context.get_input()

    # Fan-out parallel nodes
    parallel_tasks = []
    for node in workflow.get("parallel_nodes", []):
        parallel_tasks.append(
            context.call_activity("execute_node", node)
        )

    results = await context.task_all(parallel_tasks)
    return {"success": all(r["success"] for r in results)}
```

### 3.3 Google Cloud Run

Best for:
- Container-based serverless
- Long-running jobs (up to 60 min)
- Custom runtime environments

```yaml
# serverless/cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: casare-worker
spec:
  template:
    spec:
      containers:
      - image: gcr.io/project/casare-robot:latest
        resources:
          limits:
            memory: 4Gi
            cpu: "2"
        env:
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
      timeoutSeconds: 3600
      containerConcurrency: 1  # One job per instance
```

### 3.4 Serverless Comparison

| Feature | AWS Lambda | Azure Functions | Cloud Run |
|---------|------------|-----------------|-----------|
| Max Timeout | 15 min | 10 min (Consumption) | 60 min |
| Max Memory | 10 GB | 14 GB (Premium) | 32 GB |
| Browser Support | Layer (limited) | Premium plan | Full |
| Desktop Support | No | No | No |
| Cold Start | 1-5s | 1-5s | 0-30s |
| Pricing Model | Per invocation | Per execution | Per request |
| VNet Support | VPC | VNet | VPC Connector |

**Recommendation**: Serverless for API/data workflows only
- Use AWS Lambda + SQS for lightweight tasks
- Use Cloud Run for browser-based workflows (Linux only)
- Keep DistributedRobotAgent for desktop automation

---

## 4. Multi-Region Deployment

### 4.1 Architecture

```
                    +------------------+
                    |   Global Load    |
                    |    Balancer      |
                    +--------+---------+
                             |
        +--------------------+--------------------+
        |                    |                    |
+-------v--------+  +--------v-------+  +---------v------+
|   US-East      |  |    EU-West     |  |   APAC         |
|  (Primary)     |  |   (Replica)    |  |  (Replica)     |
+----------------+  +----------------+  +----------------+
| Orchestrator   |  | Orchestrator   |  | Orchestrator   |
| PostgreSQL     |  | PostgreSQL     |  | PostgreSQL     |
| Robot Pool     |  | Robot Pool     |  | Robot Pool     |
+----------------+  +----------------+  +----------------+
        |                    |                    |
        +-------- Cross-Region Replication -------+
```

### 4.2 Database Replication

**Option A: Supabase with Read Replicas**
```sql
-- Primary (US-East)
-- Supabase automatically handles replication

-- Application routing
SELECT * FROM job_queue WHERE region = 'us-east' FOR UPDATE SKIP LOCKED;
```

**Option B: CockroachDB (Globally Distributed)**
```sql
-- Geo-partitioned table
CREATE TABLE job_queue (
    id UUID PRIMARY KEY,
    region STRING NOT NULL,
    workflow_json STRING,
    ...
) PARTITION BY LIST (region) (
    PARTITION us_east VALUES IN ('us-east'),
    PARTITION eu_west VALUES IN ('eu-west'),
    PARTITION apac VALUES IN ('apac')
);

ALTER PARTITION us_east CONFIGURE ZONE USING constraints='[+region=us-east-1]';
ALTER PARTITION eu_west CONFIGURE ZONE USING constraints='[+region=eu-west-1]';
ALTER PARTITION apac CONFIGURE ZONE USING constraints='[+region=ap-southeast-1]';
```

### 4.3 Job Routing

```python
# infrastructure/routing/geo_router.py
from typing import Optional

class GeoRouter:
    """Routes jobs to nearest region based on data residency."""

    REGION_MAPPINGS = {
        # Country -> Preferred Region
        "US": "us-east",
        "CA": "us-east",
        "GB": "eu-west",
        "DE": "eu-west",
        "FR": "eu-west",
        "JP": "apac",
        "AU": "apac",
        "SG": "apac",
    }

    def route_job(
        self,
        workflow_id: str,
        tenant_country: str,
        data_residency: Optional[str] = None,
    ) -> str:
        """
        Determine target region for job execution.

        Priority:
        1. Explicit data residency requirement
        2. Tenant country mapping
        3. Default region
        """
        if data_residency:
            return data_residency
        return self.REGION_MAPPINGS.get(tenant_country, "us-east")
```

### 4.4 Multi-Region Challenges

| Challenge | Solution |
|-----------|----------|
| Data consistency | Eventually consistent with conflict resolution |
| Latency | Edge routing, regional robot pools |
| Failover | Active-passive with DNS failover |
| Cost | Reserved capacity per region |
| Compliance | Region-locked data partitions |

---

## 5. Scaling Strategies for 1000+ Robots

### 5.1 Job Queue Optimization

**Current**: PostgreSQL with SKIP LOCKED (good for ~100 robots)

**Scaling Options**:

**Option A: Partitioned Queue**
```sql
-- Partition by priority for faster high-priority claims
CREATE TABLE job_queue_partitioned (
    id UUID,
    priority INTEGER,
    status TEXT,
    ...
) PARTITION BY RANGE (priority);

CREATE TABLE job_queue_p1 PARTITION OF job_queue_partitioned
    FOR VALUES FROM (1) TO (4);
CREATE TABLE job_queue_p2 PARTITION OF job_queue_partitioned
    FOR VALUES FROM (4) TO (7);
CREATE TABLE job_queue_p3 PARTITION OF job_queue_partitioned
    FOR VALUES FROM (7) TO (10);
```

**Option B: Redis Streams (High Throughput)**
```python
# infrastructure/queue/redis_queue.py
import redis.asyncio as redis

class RedisJobQueue:
    """High-throughput job queue using Redis Streams."""

    async def enqueue(self, job: Job) -> str:
        """Add job to stream."""
        return await self.redis.xadd(
            f"jobs:{job.environment}",
            {
                "workflow_id": job.workflow_id,
                "workflow_json": job.workflow_json,
                "priority": str(job.priority),
            },
        )

    async def claim(self, robot_id: str, count: int = 1) -> list[Job]:
        """Claim jobs using consumer group."""
        messages = await self.redis.xreadgroup(
            groupname="robots",
            consumername=robot_id,
            streams={f"jobs:{self.environment}": ">"},
            count=count,
            block=5000,
        )
        return [self._parse_job(m) for m in messages]
```

**Option C: Apache Kafka (Extreme Scale)**
- For 10,000+ robots
- Partitioned by workflow_id for ordering
- Consumer groups for load balancing

### 5.2 Capacity Planning

| Robots | PostgreSQL | Redis Streams | Kafka |
|--------|------------|---------------|-------|
| 100 | Optimal | Overkill | Overkill |
| 500 | Good | Optimal | Overkill |
| 1000 | Possible | Optimal | Good |
| 5000 | Bottleneck | Good | Optimal |
| 10000+ | Not recommended | Possible | Optimal |

### 5.3 Connection Pooling at Scale

```python
# infrastructure/scaling/connection_manager.py
from pgbouncer import PgBouncer

class ScaledConnectionManager:
    """
    Connection management for 1000+ robots.
    Uses PgBouncer for connection pooling.
    """

    def __init__(self):
        # Each robot needs ~3 connections
        # 1000 robots = 3000 connections
        # PostgreSQL max_connections = 100-500 typically
        # Solution: PgBouncer in transaction mode
        self.bouncer = PgBouncer(
            pool_mode="transaction",
            max_client_conn=10000,
            default_pool_size=100,
            reserve_pool_size=50,
        )
```

### 5.4 Metrics for Scaling

```python
# infrastructure/observability/scaling_metrics.py
from prometheus_client import Gauge, Counter, Histogram

# Queue metrics
queue_depth = Gauge(
    "casare_queue_depth",
    "Number of pending jobs",
    ["environment", "priority"]
)

# Robot metrics
robot_count = Gauge(
    "casare_robot_count",
    "Number of registered robots",
    ["environment", "status"]
)

# Job latency
job_wait_time = Histogram(
    "casare_job_wait_seconds",
    "Time from job creation to start",
    ["environment"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

# Utilization
robot_utilization = Gauge(
    "casare_robot_utilization",
    "Ratio of busy to total robots",
    ["environment"]
)
```

### 5.5 Auto-Scaling Decision Matrix

```python
# infrastructure/scaling/autoscaler.py
from dataclasses import dataclass

@dataclass
class ScalingDecision:
    action: str  # "scale_up", "scale_down", "none"
    target_count: int
    reason: str

class RobotAutoscaler:
    """Intelligent auto-scaling based on queue metrics."""

    def decide(
        self,
        current_robots: int,
        pending_jobs: int,
        avg_job_duration_seconds: float,
        time_of_day: int,
    ) -> ScalingDecision:
        """
        Scaling algorithm:
        1. Calculate jobs per robot capacity
        2. Factor in business hours
        3. Apply min/max constraints
        """
        # Target: 3 pending jobs per robot
        ideal_robots = pending_jobs / 3

        # Business hours multiplier (1.5x during peak)
        if 9 <= time_of_day <= 17:
            ideal_robots *= 1.5

        # Smooth scaling (max 20% change)
        if ideal_robots > current_robots * 1.2:
            return ScalingDecision(
                action="scale_up",
                target_count=int(current_robots * 1.2),
                reason=f"Queue depth {pending_jobs} exceeds capacity"
            )
        elif ideal_robots < current_robots * 0.8:
            return ScalingDecision(
                action="scale_down",
                target_count=max(2, int(current_robots * 0.9)),
                reason="Queue depth low, reducing capacity"
            )

        return ScalingDecision(
            action="none",
            target_count=current_robots,
            reason="Capacity adequate"
        )
```

---

## 6. Recommended Cloud Roadmap

### Phase 1: Containerization (2-4 weeks) - COMPLETE
- [x] DistributedRobotAgent exists
- [x] Create Dockerfile for robot (`deploy/docker/Dockerfile.browser-robot`)
- [x] Create docker-compose for local development (`deploy/docker/docker-compose.yml`)
- [x] Add health check endpoints to robot (existing `/health/live`, `/health/ready`)
- [x] Document deployment process (`.brain/activeContext.md`, `.env.example`)

### Phase 2: Kubernetes Deployment (4-6 weeks) - COMPLETE
- [x] Create K8s manifests for orchestrator (`deploy/kubernetes/orchestrator-*.yaml`)
- [x] Create K8s manifests for robot pool (`deploy/kubernetes/browser-robot-deployment.yaml`)
- [x] Implement HPA with queue depth metric (`deploy/kubernetes/hpa.yaml`)
- [x] Add KEDA for advanced scaling (`deploy/kubernetes/keda-scaledobject.yaml`)
- [x] Set up Prometheus/Grafana monitoring (`deploy/docker/prometheus.yml`)

### Phase 3: Hybrid Cloud (4-6 weeks) - COMPLETE
- [x] Implement secure tunnel for on-prem robots (`infrastructure/tunnel/agent_tunnel.py`)
- [x] Add mTLS authentication (`infrastructure/tunnel/mtls.py`)
- [x] Create agent installer for Windows (`deploy/windows/install-robot.ps1`)
- [x] Document hybrid deployment (`docs/HYBRID_DEPLOYMENT.md`)

### Phase 4: Multi-Tenancy (6-8 weeks)
- [ ] Implement Row-Level Security in PostgreSQL
- [ ] Add tenant isolation for robot pools
- [ ] Create tenant provisioning API
- [ ] Add usage metering

### Phase 5: Serverless Integration (4-6 weeks)
- [ ] Create Lambda handler for API workflows
- [ ] Add Cloud Run support for browser workflows
- [ ] Implement serverless job router
- [ ] Add cost optimization logic

### Phase 6: Multi-Region (8-12 weeks)
- [ ] Set up regional deployments
- [ ] Implement geo-routing
- [ ] Add cross-region replication
- [ ] Create failover automation

### Phase 7: Enterprise Scale (Ongoing)
- [ ] Migrate to Redis Streams (if needed)
- [ ] Implement advanced auto-scaling
- [ ] Add Kubernetes Operator
- [ ] Enterprise compliance certifications

---

## 7. Windows Container Deep Dive

### 7.1 Windows Container Limitations for RPA

**Critical Constraint**: Windows containers have severe limitations for desktop automation:

| Feature | Linux Container | Windows Container | Impact |
|---------|-----------------|-------------------|--------|
| GUI Access | X11/Xvfb works | No desktop session | Desktop automation impossible |
| UIAutomation | N/A | Requires desktop | Cannot use in container |
| RDP | N/A | Not supported | No remote desktop |
| Container Size | ~100MB base | ~5GB+ base | Slow startup, high storage |
| Node Affinity | Any node | Windows nodes only | Limited cluster flexibility |

**Conclusion**: Windows containers are NOT suitable for desktop automation nodes.

### 7.2 Recommended Architecture: Split Workloads

```
[Kubernetes Cluster (Linux)]              [Windows Robot Fleet]
+-------------------------+               +------------------------+
| Orchestrator (FastAPI)  |               | Windows VM/Physical    |
| Job Queue (PostgreSQL)  |   WebSocket   | DistributedRobotAgent  |
| Dashboard (React)       | <-----------> | UIAutomation nodes     |
| Browser Robots (Linux)  |               | Win32 API access       |
+-------------------------+               +------------------------+
         |                                          |
         +--- Browser automation (Playwright)       +--- Desktop automation
         +--- API workflows                         +--- Excel/Outlook COM
         +--- Data processing                       +--- Native Windows apps
```

### 7.3 Windows VM Auto-Scaling (Azure/AWS)

**Azure VMSS (Virtual Machine Scale Sets)**:
```yaml
# azure/vmss-robots.bicep
resource robotVMSS 'Microsoft.Compute/virtualMachineScaleSets@2023-03-01' = {
  name: 'casare-robot-vmss'
  location: location
  sku: {
    name: 'Standard_D4s_v5'  # 4 vCPU, 16GB RAM
    capacity: 5
  }
  properties: {
    virtualMachineProfile: {
      osProfile: {
        computerNamePrefix: 'robot'
        adminUsername: 'casareadmin'
        windowsConfiguration: {
          enableAutomaticUpdates: false
          provisionVMAgent: true
        }
      }
      storageProfile: {
        imageReference: {
          publisher: 'MicrosoftWindowsServer'
          offer: 'WindowsServer'
          sku: '2022-datacenter'
          version: 'latest'
        }
      }
      extensionProfile: {
        extensions: [{
          name: 'robot-install'
          properties: {
            publisher: 'Microsoft.Compute'
            type: 'CustomScriptExtension'
            settings: {
              commandToExecute: 'powershell -File install-robot.ps1'
            }
          }
        }]
      }
    }
  }
}

resource autoscale 'Microsoft.Insights/autoscaleSettings@2022-10-01' = {
  name: 'robot-autoscale'
  properties: {
    targetResourceUri: robotVMSS.id
    profiles: [{
      name: 'queue-based'
      capacity: {
        minimum: '2'
        maximum: '50'
        default: '5'
      }
      rules: [{
        metricTrigger: {
          metricName: 'casare_queue_depth'
          metricResourceUri: applicationInsights.id
          timeGrain: 'PT1M'
          statistic: 'Average'
          timeWindow: 'PT5M'
          operator: 'GreaterThan'
          threshold: 10
        }
        scaleAction: {
          direction: 'Increase'
          type: 'ChangeCount'
          value: '2'
          cooldown: 'PT5M'
        }
      }]
    }]
  }
}
```

**AWS Auto Scaling Group**:
```yaml
# aws/robot-asg.yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  RobotLaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: casare-robot-template
      LaunchTemplateData:
        ImageId: !Ref WindowsAMI
        InstanceType: m5.xlarge  # 4 vCPU, 16GB
        UserData:
          Fn::Base64: |
            <powershell>
            # Install Python 3.12
            # Install CasareRPA robot
            # Register with orchestrator
            </powershell>

  RobotASG:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      LaunchTemplate:
        LaunchTemplateId: !Ref RobotLaunchTemplate
        Version: !GetAtt RobotLaunchTemplate.LatestVersionNumber
      MinSize: 2
      MaxSize: 50
      DesiredCapacity: 5
      VPCZoneIdentifier: !Ref PrivateSubnets

  QueueDepthScalingPolicy:
    Type: AWS::AutoScaling::ScalingPolicy
    Properties:
      AutoScalingGroupName: !Ref RobotASG
      PolicyType: TargetTrackingScaling
      TargetTrackingConfiguration:
        CustomizedMetricSpecification:
          MetricName: QueueDepthPerRobot
          Namespace: CasareRPA
          Statistic: Average
        TargetValue: 3  # 3 jobs per robot target
```

### 7.4 Kubernetes Node Affinity for Mixed Workloads

```yaml
# k8s/mixed-workload-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: casare-browser-robots
spec:
  replicas: 20
  template:
    spec:
      nodeSelector:
        kubernetes.io/os: linux
        casare.io/workload: browser
      tolerations:
      - key: "casare.io/browser-only"
        operator: "Exists"
        effect: "NoSchedule"
      containers:
      - name: browser-robot
        image: casarerpa/robot:browser-only
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
---
# Windows robots managed externally (VMSS/ASG)
# Kubernetes manages Linux workloads only
apiVersion: v1
kind: ConfigMap
metadata:
  name: robot-routing-config
data:
  routing.yaml: |
    workload_routing:
      browser_only:
        target: kubernetes
        node_types: [NavigateNode, ClickElementNode, ScrapeDataNode]
      desktop_required:
        target: windows_fleet
        node_types: [ClickDesktopNode, TypeTextNode, ReadExcelNode]
      mixed:
        strategy: split
        # Browser nodes -> K8s, Desktop nodes -> Windows
```

---

## 8. Cost Optimization Strategies

### 8.1 Compute Cost Optimization

| Strategy | Savings | Complexity | Best For |
|----------|---------|------------|----------|
| Reserved Instances (1yr) | 30-40% | Low | Baseline capacity |
| Reserved Instances (3yr) | 50-60% | Medium | Stable workloads |
| Spot/Preemptible | 60-80% | High | Batch processing |
| Savings Plans | 20-30% | Low | Flexible workloads |
| Right-sizing | 10-30% | Medium | All workloads |

### 8.2 Spot Instance Strategy for Robots

```python
# infrastructure/scaling/spot_manager.py
from dataclasses import dataclass
from enum import Enum

class InstanceType(Enum):
    ON_DEMAND = "on_demand"
    SPOT = "spot"
    RESERVED = "reserved"

@dataclass
class SpotConfig:
    """Configuration for spot instance robot pools."""
    max_spot_percentage: float = 0.7  # 70% spot max
    fallback_on_demand: bool = True
    interruption_behavior: str = "terminate"  # or "stop"
    spot_price_limit: float = 0.5  # 50% of on-demand price

class RobotFleetManager:
    """
    Manages mixed fleet of on-demand, spot, and reserved robots.

    Cost optimization strategy:
    1. Reserved instances for baseline (always-on robots)
    2. On-demand for guaranteed capacity during peak
    3. Spot for burst capacity and batch processing
    """

    def calculate_fleet_composition(
        self,
        target_robots: int,
        reserved_capacity: int,
        spot_available: bool,
    ) -> dict:
        """
        Calculate optimal fleet composition.

        Priority:
        1. Use all reserved capacity (already paid for)
        2. Fill with spot instances (cheapest)
        3. On-demand for remainder
        """
        reserved = min(reserved_capacity, target_robots)
        remaining = target_robots - reserved

        if spot_available:
            spot = int(remaining * 0.7)  # 70% spot
            on_demand = remaining - spot
        else:
            spot = 0
            on_demand = remaining

        return {
            "reserved": reserved,
            "spot": spot,
            "on_demand": on_demand,
            "estimated_hourly_cost": self._calculate_cost(reserved, spot, on_demand),
        }

    def handle_spot_interruption(self, robot_id: str) -> None:
        """
        Handle 2-minute spot interruption warning.

        Actions:
        1. Stop accepting new jobs
        2. Checkpoint current job (if supported)
        3. Re-queue unfinished work
        4. Request replacement instance
        """
        pass
```

### 8.3 Database Cost Optimization

| Database | Monthly Cost (est.) | Robots Supported | Notes |
|----------|---------------------|------------------|-------|
| Supabase Free | $0 | 10-20 | Dev only |
| Supabase Pro | $25 | 100-200 | Small production |
| RDS PostgreSQL db.t3.medium | $50 | 200-500 | Self-managed |
| RDS PostgreSQL db.r5.large | $200 | 500-1000 | High performance |
| Aurora Serverless v2 | $50-500 | 100-2000 | Auto-scaling |

**Recommendation**: Start with Supabase Pro, migrate to Aurora Serverless for enterprise scale.

### 8.4 Storage Cost Optimization

```python
# infrastructure/storage/tiered_storage.py
from datetime import datetime, timedelta
from enum import Enum

class StorageTier(Enum):
    HOT = "hot"      # SSD, frequent access
    WARM = "warm"    # HDD, occasional access
    COLD = "cold"    # Archive, rare access
    DELETED = "deleted"

class WorkflowStorageManager:
    """
    Tiered storage for workflow artifacts.

    Tier Policy:
    - Hot: Last 7 days of logs, active workflow versions
    - Warm: 7-90 days, compressed
    - Cold: 90+ days, archived (S3 Glacier/Azure Archive)
    - Deleted: After retention period
    """

    TIER_RULES = {
        "execution_logs": {
            StorageTier.HOT: timedelta(days=7),
            StorageTier.WARM: timedelta(days=90),
            StorageTier.COLD: timedelta(days=365),
        },
        "screenshots": {
            StorageTier.HOT: timedelta(days=1),
            StorageTier.WARM: timedelta(days=30),
            StorageTier.COLD: timedelta(days=90),
        },
        "workflow_versions": {
            StorageTier.HOT: None,  # Current version always hot
            StorageTier.WARM: timedelta(days=30),
            StorageTier.COLD: timedelta(days=365),
        },
    }

    def calculate_storage_costs(self, data_gb: float) -> dict:
        """Calculate monthly storage costs by tier."""
        return {
            "hot": data_gb * 0.10 * 0.4,    # 40% in hot tier @ $0.10/GB
            "warm": data_gb * 0.025 * 0.35,  # 35% in warm @ $0.025/GB
            "cold": data_gb * 0.004 * 0.25,  # 25% in cold @ $0.004/GB
            "total": data_gb * 0.10 * 0.4 + data_gb * 0.025 * 0.35 + data_gb * 0.004 * 0.25,
        }
```

### 8.5 Network Cost Optimization

| Traffic Type | Cost | Optimization |
|--------------|------|--------------|
| Ingress | Free | N/A |
| Egress (same region) | Free | Keep robots in same region as orchestrator |
| Egress (cross-region) | $0.02-0.09/GB | Minimize cross-region job routing |
| Egress (internet) | $0.05-0.12/GB | Cache external API responses |

**Key Optimizations**:
1. Regional affinity - route jobs to local robots
2. Compression - gzip workflow payloads (70-90% reduction)
3. Delta sync - only send changed workflow portions
4. CDN for dashboard - reduce orchestrator load

### 8.6 Cost Monitoring Dashboard

```python
# infrastructure/observability/cost_metrics.py
from prometheus_client import Gauge, Counter

# Cost tracking metrics
hourly_compute_cost = Gauge(
    "casare_hourly_compute_cost_dollars",
    "Estimated hourly compute cost",
    ["instance_type", "region"]
)

monthly_storage_cost = Gauge(
    "casare_monthly_storage_cost_dollars",
    "Estimated monthly storage cost",
    ["tier", "data_type"]
)

cost_per_execution = Gauge(
    "casare_cost_per_execution_dollars",
    "Average cost per workflow execution",
    ["workflow_id", "environment"]
)

spot_savings = Counter(
    "casare_spot_savings_dollars_total",
    "Total savings from spot instances",
    ["region"]
)
```

### 8.7 Cost Comparison: CasareRPA vs Competitors

| Metric | UiPath | Automation Anywhere | Power Automate | CasareRPA (Self-Hosted) |
|--------|--------|---------------------|----------------|-------------------------|
| Per Robot/Year | $8,000-15,000 | $5,000-12,000 | $1,800 (attended) | $0 (license) + infra |
| Orchestrator | Included | Included | Included | $200-500/mo (K8s) |
| 10 Robots/Year | $80,000+ | $50,000+ | $18,000 | ~$6,000 infra |
| 100 Robots/Year | $800,000+ | $500,000+ | $180,000 | ~$30,000 infra |

**CasareRPA Value Proposition**: 80-95% cost reduction at scale vs commercial alternatives.

---

## 9. Technology Recommendations

### Immediate (Current Sprint)
| Component | Current | Keep/Replace | Reason |
|-----------|---------|--------------|--------|
| Job Queue | PostgreSQL SKIP LOCKED | Keep | Works well for <500 robots |
| Realtime | Supabase | Keep | Excellent for hybrid model |
| API | FastAPI | Keep | Production-ready |
| Robots | DistributedRobotAgent | Keep | Well-designed |

### Short-Term (3-6 months)
| Need | Technology | Notes |
|------|------------|-------|
| Container Orchestration | Kubernetes + KEDA | Queue-based scaling |
| Secrets Management | HashiCorp Vault | Enterprise credentials |
| Observability | Prometheus + Grafana | Existing metrics compatible |
| CI/CD | GitHub Actions | Already in use |
| Windows Auto-Scaling | Azure VMSS or AWS ASG | Queue-depth based |

### Long-Term (6-12 months)
| Need | Technology | Notes |
|------|------------|-------|
| High-Scale Queue | Redis Streams | If >500 robots needed |
| Multi-Region DB | CockroachDB or Supabase | Geo-distributed |
| Service Mesh | Istio | mTLS, traffic management |
| Serverless | Cloud Run | Browser automation only |

---

## 10. Open Questions

1. **Target Scale**: What is the target robot count for first enterprise customers? (Affects queue technology choice)

2. **Data Residency**: Which regions are required for compliance? (EU, US, APAC?)

3. **Desktop Automation Priority**: Is Windows desktop automation required for cloud deployments, or can it be on-prem only?

4. **Pricing Model**: Usage-based (per execution) or subscription (per robot)? (Affects metering design)

5. **Multi-Tenancy Model**: Shared infrastructure with RLS or isolated deployments per tenant?

---

## 11. Key Findings Summary

### Windows RPA Cloud Constraints
1. **Windows containers cannot run desktop automation** - No GUI/UIAutomation access
2. **Hybrid architecture is mandatory** - Cloud control plane + on-prem Windows robots
3. **Split workloads** - Browser/API on Kubernetes, Desktop on Windows VMs

### Auto-Scaling Recommendations
| Workload | Technology | Metric | Target |
|----------|------------|--------|--------|
| Orchestrator | Kubernetes HPA | CPU/Memory | 70% utilization |
| Browser Robots | Kubernetes + KEDA | Queue depth | 3-5 jobs/robot |
| Windows Robots | Azure VMSS / AWS ASG | Queue depth | 3-5 jobs/robot |
| Serverless | Cloud Run / Lambda | Requests | Auto-managed |

### Multi-Region Strategy
1. **Primary region** - Full deployment (US-East recommended)
2. **Secondary regions** - Read replicas + robot pools
3. **Data routing** - Job affinity to tenant region for compliance
4. **Failover** - DNS-based with 5-minute TTL

### Cost Optimization Priorities
1. **Reserved capacity** - 30-40% savings for baseline robots
2. **Spot instances** - 60-80% savings for burst capacity
3. **Tiered storage** - 50-70% savings on logs/artifacts
4. **Regional affinity** - Eliminate cross-region egress costs

### CasareRPA vs Competitors
- **80-95% cost reduction** at 100+ robots vs UiPath/Automation Anywhere
- **Open-source advantage** - No per-robot licensing
- **Hybrid-first** - Built for enterprise security requirements

---

## 12. References

### Competitor Approaches

**UiPath**:
- Orchestrator: Kubernetes-based, SQL Server
- Robots: On-prem agents with cloud connection
- Scaling: Per-robot licensing, capacity pools

**Automation Anywhere**:
- Control Room: Cloud-first SaaS
- Bot Agents: On-prem Windows
- Scaling: Device pools, auto-scaling

**Power Automate Desktop**:
- Cloud-first with Dataverse
- Desktop flows require attended/unattended licensing
- Scaling: Per-flow run pricing

### CasareRPA Advantages
1. Open-source/self-hostable option
2. PostgreSQL (vs proprietary DB)
3. Python-native (easy to extend)
4. Hybrid-first architecture
5. Clean DDD architecture for maintainability

---

*Research completed by: rpa-research-specialist*
*Date: 2025-12-01*
