# Infrastructure Layer API

**Modules:** 128 | **Classes:** 576 | **Functions:** 276

The infrastructure layer provides adapters for external systems, persistence, security, and resources.

## Module Categories

### Agent & Robot

| Module | Description |
|--------|-------------|
| `infrastructure.agent.heartbeat_service` | Heartbeat service for robot health monitoring |
| `infrastructure.agent.job_executor` | Job execution on robot agents |
| `infrastructure.agent.robot_agent` | Main robot agent entry point |
| `infrastructure.agent.robot_config` | Robot configuration management |

### Analytics & Observability

| Module | Description |
|--------|-------------|
| `infrastructure.analytics.bottleneck_detector` | Performance bottleneck detection |
| `infrastructure.analytics.execution_analyzer` | Workflow execution analysis |
| `infrastructure.analytics.process_mining` | Process mining and discovery |
| `infrastructure.analytics.metrics_aggregator` | Metrics aggregation engine |
| `infrastructure.observability.telemetry` | OpenTelemetry integration |
| `infrastructure.observability.metrics` | RPA-specific metrics collection |

### Orchestrator API

| Module | Description |
|--------|-------------|
| `infrastructure.orchestrator.api.main` | FastAPI application (port 8000) |
| `infrastructure.orchestrator.api.routers.workflows` | Workflow management endpoints |
| `infrastructure.orchestrator.api.routers.jobs` | Job queue endpoints |
| `infrastructure.orchestrator.api.routers.robots` | Robot management endpoints |
| `infrastructure.orchestrator.api.routers.schedules` | Schedule management endpoints |
| `infrastructure.orchestrator.api.routers.analytics` | Analytics endpoints |
| `infrastructure.orchestrator.api.routers.websockets` | WebSocket real-time updates |

### Queue System

| Module | Description |
|--------|-------------|
| `infrastructure.queue.pgqueuer_producer` | PgQueuer job producer (18k+ jobs/sec) |
| `infrastructure.queue.pgqueuer_consumer` | PgQueuer job consumer |
| `infrastructure.queue.memory_queue` | In-memory fallback for development |
| `infrastructure.queue.dlq_manager` | Dead letter queue management |

### Persistence

| Module | Description |
|--------|-------------|
| `infrastructure.persistence.repositories.job_repository` | Job persistence |
| `infrastructure.persistence.repositories.robot_repository` | Robot persistence |
| `infrastructure.persistence.repositories.workflow_assignment_repository` | Workflow assignments |
| `infrastructure.persistence.project_storage` | Project file storage |

### Security

| Module | Description |
|--------|-------------|
| `infrastructure.security.credential_store` | Unified credential management |
| `infrastructure.security.vault_client` | Vault integration (HashiCorp, SQLite, Supabase) |
| `infrastructure.security.rbac` | Role-based access control |
| `infrastructure.security.tenancy` | Multi-tenancy support |
| `infrastructure.security.validators` | Input sanitization |

### Resources

| Module | Description |
|--------|-------------|
| `infrastructure.resources.browser_resource_manager` | Playwright browser pool |
| `infrastructure.resources.unified_resource_manager` | Robot resource lifecycle |
| `infrastructure.resources.google_client` | Google API authentication |
| `infrastructure.resources.gmail_client` | Gmail API client |
| `infrastructure.resources.google_sheets_client` | Sheets API client |
| `infrastructure.resources.telegram_client` | Telegram Bot API |
| `infrastructure.resources.whatsapp_client` | WhatsApp Business API |
| `infrastructure.resources.llm_resource_manager` | LLM provider integration |

### Browser Healing

| Module | Description |
|--------|-------------|
| `infrastructure.browser.healing.healing_chain` | Self-healing selector chain |
| `infrastructure.browser.healing.anchor_healer` | Anchor-based healing (Tier 2) |
| `infrastructure.browser.healing.cv_healer` | Computer vision healing (Tier 3) |

### Tunnel & Updates

| Module | Description |
|--------|-------------|
| `infrastructure.tunnel.agent_tunnel` | Secure tunnel for on-prem robots |
| `infrastructure.tunnel.mtls` | mTLS certificate management |
| `infrastructure.updater.tuf_updater` | TUF secure updates |

## Key Classes

### Orchestrator

- **FastAPI App** - REST API with Swagger docs at `/docs`
- **WebSocket Server** - Real-time job/robot status updates
- **PgQueuer** - High-performance PostgreSQL job queue

### Robot Agent

- **RobotAgent** - Distributed workflow executor
- **HeartbeatService** - Connection health monitoring
- **JobExecutor** - Workflow execution engine

### Security

- **CredentialStore** - Encrypted credential storage
- **VaultClient** - Multi-provider vault integration
- **RBACManager** - Permission management

## Related

- [Orchestrator API Reference](orchestrator-api.md)
- [Domain Layer](../domain/index.md)
- [Application Layer](../application/index.md)
- [Presentation Layer](../presentation/index.md)
