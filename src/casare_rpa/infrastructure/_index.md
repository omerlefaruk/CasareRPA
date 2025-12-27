# Infrastructure Index

```xml
<infra_index>
  <!-- Quick reference for infrastructure layer. Framework integrations and external adapters. -->

  <dirs>
    <d name="caching/">      <p>LRU caches for workflows, schemas</p>         <e>WorkflowCache, get_workflow_cache</e></d>
    <d name="agent/">        <p>Robot agent for headless execution</p>         <e>RobotAgent, JobExecutor, HeartbeatService</e></d>
    <d name="ai/">           <p>AI-powered workflow generation</p>            <e>SmartWorkflowAgent, dump_node_manifest</e></d>
    <d name="analytics/">    <p>Metrics aggregation, process mining</p>        <e>MetricsAggregator, ProcessMiner</e></d>
    <d name="auth/">         <p>Robot API key management</p>                  <e>RobotApiKeyService, RobotApiKey</e></d>
    <d name="browser/">      <p>Playwright lifecycle, healing</p>             <e>PlaywrightManager, SelectorHealingChain</e></d>
    <d name="coordination/"> <p>Parallel agent state coordination</p>         <e>StateCoordinator, ResourceCoordinator</e></d>
    <d name="database/">     <p>Database migrations, schema</p>               <i>(migrations only)</i></d>
    <d name="events/">       <p>Real-time monitoring events</p>               <e>MonitoringEventBus, MonitoringEvent</e></d>
    <d name="execution/">    <p>Execution context runtime</p>                 <e>ExecutionContext, ConcurrentResourceManager</e></d>
    <d name="http/">         <p>Resilient HTTP client</p>                     <e>UnifiedHttpClient, get_unified_http_client</e></d>
    <d name="observability/"> <p>OpenTelemetry integration</p>                <e>Observability, TelemetryProvider</e></d>
    <d name="orchestrator/"> <p>Distributed robot orchestration</p>           <e>OrchestratorClient, OrchestratorConfig</e></d>
    <d name="persistence/">  <p>File system repositories</p>                  <e>ProjectStorage, FolderStorage, JsonUnitOfWork</e></d>
    <d name="queue/">        <p>PostgreSQL job queue</p>                      <e>PgQueuerConsumer, PgQueuerProducer, DLQManager</e></d>
    <d name="realtime/">     <p>Supabase Realtime integration</p>             <e>RealtimeClient, SubscriptionManager</e></d>
    <d name="resources/">    <p>External resource managers</p>                <e>LLMResourceManager, GoogleAPIClient</e></d>
    <d name="security/">     <p>Vault, RBAC, OAuth, tenancy</p>               <e>VaultClient, AuthorizationService</e></d>
    <d name="tunnel/">       <p>Secure WebSocket tunnel</p>                   <e>AgentTunnel, MTLSConfig</e></d>
    <d name="updater/">      <p>TUF auto-update</p>                           <e>TUFUpdater, UpdateManager</e></d>
  </dirs>

  <key_files>
    <f>__init__.py</f>                  <d>Top-level exports (26 items)</d></f>
    <f>ai/smart_agent.py</f>             <d>SmartWorkflowAgent (54KB)</d></f>
    <f>browser/playwright_manager.py</f> <d>Singleton browser lifecycle</d></f>
    <f>execution/execution_context.py</f> <d>ExecutionContext class</d></f>
    <f>http/unified_http_client.py</f>   <d>Circuit breaker, retry logic</d></f>
    <f>security/vault_client.py</f>      <d>Credential management</d></f>
    <f>security/rbac.py</f>              <d>Role-based access control</d></f>
    <f>persistence/unit_of_work.py</f>   <d>JsonUnitOfWork - Unit of Work pattern</d></f>
  </key_files>

  <entry_points>
    <code>
# Workflow Caching
from casare_rpa.infrastructure.caching import WorkflowCache, get_workflow_cache

# Robot Agent (headless execution)
from casare_rpa.infrastructure import RobotAgent, RobotConfig

# Browser Management
from casare_rpa.infrastructure.browser import PlaywrightManager, get_playwright_singleton

# HTTP Client (resilient) - MANDATORY for all HTTP
from casare_rpa.infrastructure import UnifiedHttpClient, get_unified_http_client

# AI Workflow Generation
from casare_rpa.infrastructure.ai import SmartWorkflowAgent, dump_node_manifest

# Security (Vault + RBAC)
from casare_rpa.infrastructure.security import (
    VaultClient, AuthorizationService, create_vault_provider
)

# Observability
from casare_rpa.infrastructure.observability import Observability, configure_observability

# Analytics
from casare_rpa.infrastructure.analytics import MetricsAggregator, ProcessMiner

# Queue (PostgreSQL)
from casare_rpa.infrastructure.queue import PgQueuerConsumer, PgQueuerProducer

# Resources (LLM, Google, Messaging)
from casare_rpa.infrastructure.resources import (
    LLMResourceManager, GoogleAPIClient, TelegramClient
)
    </code>
  </entry_points>

  <patterns>
    <p>Adapters - Wrap external libraries (Playwright, UIAutomation, aiohttp)</p>
    <p>Repository Pattern - Persistence abstraction for workflows, credentials</p>
    <p>Factory Pattern - Create complex objects (HTTP clients, browser contexts)</p>
    <p>Singleton - Shared resources (HTTP client, credential cache)</p>
    <p>Circuit Breaker - Resilience for external API calls</p>
    <p>mTLS - Mutual TLS for secure robot-orchestrator communication</p>
    <p>Unit of Work - Transactional operations with domain event publishing</p>
  </patterns>

  <exports>
    <m>__init__.py</m>      <n>24</n>
    <m>security/</m>        <n>91</n>
    <m>queue/</m>           <n>57</n>
    <m>observability/</m>   <n>75</n>
    <m>analytics/</m>       <n>81</n>
    <m>resources/</m>       <n>46</n>
    <m>browser/</m>         <n>12</n>
    <m>ai/</m>              <n>25</n>
  </exports>

  <related>
    <r>ai/_index.md</r>      <d>AI workflow generation</d></r>
    <r>../domain/_index.md</r> <d>Domain entities and services</d></r>
    <r>../application/_index.md</r> <d>Use cases layer</d></r>
    <r>../nodes/_index.md</r> <d>Node implementations</d></r>
  </related>
</infra_index>
```
