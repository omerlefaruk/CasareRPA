# Infrastructure Index

Quick reference for infrastructure layer. Framework integrations and external adapters.

## Directory Structure

| Directory | Description | Key Exports |
|-----------|-------------|-------------|
| `caching/` | LRU caches for workflows, schemas | WorkflowCache, get_workflow_cache |
| `agent/` | Robot agent for headless execution | RobotAgent, JobExecutor, HeartbeatService |
| `ai/` | AI-powered workflow generation | SmartWorkflowAgent, dump_node_manifest |
| `analytics/` | Metrics aggregation, process mining | MetricsAggregator, ProcessMiner |
| `auth/` | Robot API key management | RobotApiKeyService, RobotApiKey |
| `browser/` | Playwright lifecycle, healing | PlaywrightManager, SelectorHealingChain |
| `config/` | External service configuration | CloudflareConfig |
| `coordination/` | Parallel agent state coordination | StateCoordinator, ResourceCoordinator |
| `database/` | Database migrations, schema | (migrations only) |
| `events/` | Real-time monitoring events | MonitoringEventBus, MonitoringEvent |
| `execution/` | Execution context runtime | ExecutionContext, ConcurrentResourceManager |
| `http/` | Resilient HTTP client | UnifiedHttpClient, get_unified_http_client |
| `logging/` | Log streaming, cleanup | LogStreamingService, LogCleanupJob |
| `observability/` | OpenTelemetry integration | Observability, TelemetryProvider |
| `orchestrator/` | Distributed robot orchestration | OrchestratorClient, OrchestratorConfig |
| `persistence/` | File system repositories | ProjectStorage, FolderStorage, JsonUnitOfWork |
| `queue/` | PostgreSQL job queue | PgQueuerConsumer, PgQueuerProducer, DLQManager |
| `realtime/` | Supabase Realtime integration | RealtimeClient, SubscriptionManager |
| `resources/` | External resource managers | LLMResourceManager, GoogleAPIClient |
| `security/` | Vault, RBAC, OAuth, tenancy | VaultClient, AuthorizationService |
| `tunnel/` | Secure WebSocket tunnel | AgentTunnel, MTLSConfig |
| `updater/` | TUF auto-update | TUFUpdater, UpdateManager |

## Key Files

| File | Contains |
|------|----------|
| `__init__.py` | Top-level exports (26 items) |
| `caching/workflow_cache.py` | WorkflowCache LRU cache |
| `agent/robot_agent.py` | RobotAgent class |
| `ai/smart_agent.py` | SmartWorkflowAgent (54KB) |
| `ai/registry_dumper.py` | Node manifest generation |
| `browser/playwright_manager.py` | Singleton browser lifecycle |
| `execution/execution_context.py` | ExecutionContext class |
| `http/unified_http_client.py` | Circuit breaker, retry logic |
| `security/vault_client.py` | Credential management |
| `security/rbac.py` | Role-based access control |
| `persistence/unit_of_work.py` | JsonUnitOfWork - Unit of Work pattern implementation |

## Entry Points

```python
# Workflow Caching
from casare_rpa.infrastructure.caching import (
    WorkflowCache,
    get_workflow_cache,
)

# Robot Agent (headless execution)
from casare_rpa.infrastructure import RobotAgent, RobotConfig

# Browser Management
from casare_rpa.infrastructure.browser import (
    PlaywrightManager,
    get_playwright_singleton,
)

# HTTP Client (resilient)
from casare_rpa.infrastructure import (
    UnifiedHttpClient,
    get_unified_http_client,
)

# AI Workflow Generation
from casare_rpa.infrastructure.ai import (
    SmartWorkflowAgent,
    dump_node_manifest,
)

# Security (Vault + RBAC)
from casare_rpa.infrastructure.security import (
    VaultClient,
    AuthorizationService,
    create_vault_provider,
)

# Observability
from casare_rpa.infrastructure.observability import (
    Observability,
    configure_observability,
)

# Analytics
from casare_rpa.infrastructure.analytics import (
    MetricsAggregator,
    ProcessMiner,
)

# Queue (PostgreSQL)
from casare_rpa.infrastructure.queue import (
    PgQueuerConsumer,
    PgQueuerProducer,
)

# Resources (LLM, Google, Messaging)
from casare_rpa.infrastructure.resources import (
    LLMResourceManager,
    GoogleAPIClient,
    TelegramClient,
)
```

## Key Patterns

- **Adapters**: Wrap external libraries (Playwright, UIAutomation, aiohttp)
- **Repository Pattern**: Persistence abstraction for workflows, credentials
- **Factory Pattern**: Create complex objects (HTTP clients, browser contexts)
- **Singleton**: Shared resources (HTTP client, credential cache)
- **Circuit Breaker**: Resilience for external API calls
- **mTLS**: Mutual TLS for secure robot-orchestrator communication
- **Unit of Work**: Transactional operations across repositories with domain event publishing

## Export Counts

| Module | Exports |
|--------|---------|
| `__init__.py` | 24 |
| `security/` | 91 |
| `queue/` | 57 |
| `observability/` | 75 |
| `analytics/` | 81 |
| `resources/` | 46 |
| `browser/` | 12 |
| `ai/` | 25 |

## Related Indexes

- `infrastructure/ai/_index.md` - AI workflow generation
- `domain/_index.md` - Domain entities and services
- `application/_index.md` - Use cases layer
- `nodes/_index.md` - Node implementations
