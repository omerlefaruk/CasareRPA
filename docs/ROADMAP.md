# CasareRPA Roadmap

**Version**: 3.3
**Last Updated**: 2025-12-09

---

## Current State

CasareRPA is a Windows Desktop RPA platform with:
- Visual node-based workflow editor (413 nodes)
- Web automation (Playwright) + Desktop automation (UIAutomation)
- Clean DDD Architecture (Domain, Application, Infrastructure, Presentation)
- Orchestrator API with distributed robot execution
- Google Workspace integration (Gmail, Drive, Sheets, Calendar, Docs)

---

## Phase 1: Stability & Polish

### 1.1 Architecture Cleanup
- [ ] Fix remaining 20 layer violations (Application → Infrastructure imports)
- [ ] Complete Dependency Inversion for all use cases
- [ ] Remove deprecated `core/` compatibility layer

### 1.2 Performance
- [ ] Canvas rendering optimization (target: <100ms for 100 nodes)
- [ ] Lazy loading for node library panel
- [ ] Connection pooling audit for all external integrations

### 1.3 Testing
- [ ] Increase test coverage to 80%
- [ ] Add E2E workflow tests
- [ ] Performance regression test suite

---

## Phase 2: Enterprise Features

### 2.1 Security & Compliance
- [ ] RBAC (Role-Based Access Control)
- [ ] Audit logging for all workflow executions
- [ ] Credential vault integration (Azure Key Vault, HashiCorp Vault)
- [ ] SOC 2 compliance preparation

### 2.2 Multi-Tenancy
- [ ] Tenant isolation for Orchestrator
- [ ] Per-tenant quotas and rate limiting
- [ ] Tenant-scoped credentials and variables

### 2.3 Monitoring & Observability
- [ ] OpenTelemetry integration
- [ ] Prometheus metrics endpoint
- [ ] Grafana dashboard templates
- [ ] Alerting (PagerDuty, Slack, Teams)

---

## Phase 3: AI & Intelligence

### 3.1 LLM Integration
- [ ] AI-powered node suggestions
- [ ] Natural language workflow generation
- [ ] Intelligent error recovery suggestions

### 3.2 Computer Vision
- [ ] OCR nodes (Tesseract, Azure AI Vision)
- [ ] Image classification nodes
- [ ] Visual element detection

### 3.3 Self-Healing
- [ ] Selector healing Tier 2+ (ML-based)
- [ ] Automatic retry strategies
- [ ] Anomaly detection in workflow execution

---

## Phase 4: Integrations

### 4.1 Enterprise Connectors
- [ ] Salesforce
- [ ] SAP
- [ ] Microsoft Dynamics 365
- [ ] ServiceNow

### 4.2 Communication
- [ ] Slack integration
- [ ] Microsoft Teams integration
- [ ] Discord integration

### 4.3 Cloud Services
- [ ] AWS SDK nodes (S3, Lambda, SQS)
- [ ] Azure SDK nodes (Blob, Functions, Service Bus)
- [ ] GCP SDK nodes (Cloud Storage, Pub/Sub)

### 4.4 Data & Messaging
- [ ] Kafka nodes
- [ ] RabbitMQ nodes
- [ ] Redis nodes
- [ ] MongoDB nodes

---

## Phase 5: Platform Expansion

### 5.1 Cross-Platform
- [ ] macOS support (Playwright + accessibility APIs)
- [ ] Linux support (Playwright + AT-SPI)

### 5.2 Mobile Automation
- [ ] Appium integration for mobile testing
- [ ] iOS/Android device farm support

### 5.3 API Automation
- [ ] GraphQL nodes
- [ ] gRPC nodes
- [ ] WebSocket nodes

---

## Phase 6: Developer Experience

### 6.1 SDK & Extensibility
- [ ] Plugin system for custom nodes
- [ ] Python SDK for programmatic workflow creation
- [ ] REST API for workflow management

### 6.2 IDE Integration
- [ ] VS Code extension for workflow editing
- [ ] IntelliSense for workflow JSON
- [ ] Debugging from IDE

### 6.3 Documentation
- [ ] Interactive tutorials
- [ ] Video walkthroughs
- [ ] API reference generator

---

## Backlog (Unprioritized)

- Process mining visualization
- Workflow versioning and rollback
- A/B testing for workflows
- Workflow marketplace
- Custom node marketplace
- Batch job scheduling
- Webhook triggers with signature validation
- SSH/SFTP nodes
- Windows Registry nodes
- PDF form filling nodes
- Email attachment processing
- Browser popup/dialog handling
- IFrame support in browser automation

---

## Completed (v3.3)

- [x] Clean DDD Architecture migration
- [x] 413 nodes registered in single registry
- [x] UnifiedHttpClient with resilience patterns
- [x] SignalCoordinator + PanelManager extraction
- [x] Unified theme system (VSCode Dark+ aligned)
- [x] SSRF protection for HTTP client
- [x] Domain interfaces (IExecutionContext, repositories)
- [x] Google Workspace integration (5 services)
- [x] Telegram & WhatsApp messaging nodes
- [x] FastAPI Orchestrator with PostgreSQL queue
- [x] Debug panel with breakpoints

---

## Contributing

See [CONTRIBUTING.md](development/CONTRIBUTING.md) for guidelines on proposing roadmap items.
