# CasareRPA Documentation Index

Welcome to the CasareRPA documentation. This index provides quick access to all documentation resources.

## Documentation Structure

```
docs/
    INDEX.md                    <- You are here
    architecture/
        SYSTEM_OVERVIEW.md      - High-level architecture (C4 diagrams)
        DATA_FLOW.md            - Data flow diagrams
        COMPONENT_DIAGRAM.md    - Component interactions
    api/
        REST_API_REFERENCE.md   - Complete API documentation
    operations/
        RUNBOOK.md              - Operational procedures
        TROUBLESHOOTING.md      - Common issues and solutions
    development/
        CONTRIBUTING.md         - Development guidelines
        TESTING_GUIDE.md        - Testing strategy
    security/
        SECURITY_ARCHITECTURE.md - Security model and practices
    user-guide/
        GETTING_STARTED.md      - User quickstart guide
```

---

## Quick Links

### For Users

| Document | Description |
|----------|-------------|
| [Getting Started](user-guide/GETTING_STARTED.md) | Installation and first workflow |
| [Troubleshooting](operations/TROUBLESHOOTING.md) | Common issues and solutions |

### For Operators

| Document | Description |
|----------|-------------|
| [Operations Runbook](operations/RUNBOOK.md) | Startup, shutdown, scaling, backup |
| [Troubleshooting](operations/TROUBLESHOOTING.md) | Diagnostic procedures |
| [Security Architecture](security/SECURITY_ARCHITECTURE.md) | Security best practices |

### For Developers

| Document | Description |
|----------|-------------|
| [System Overview](architecture/SYSTEM_OVERVIEW.md) | Architecture and design |
| [Data Flow](architecture/DATA_FLOW.md) | Sequence and flow diagrams |
| [Component Diagram](architecture/COMPONENT_DIAGRAM.md) | Component structure |
| [API Reference](api/REST_API_REFERENCE.md) | WebSocket and REST APIs |
| [Contributing Guide](development/CONTRIBUTING.md) | Development guidelines |
| [Testing Guide](development/TESTING_GUIDE.md) | Testing strategies |

### For Security/Compliance

| Document | Description |
|----------|-------------|
| [Security Architecture](security/SECURITY_ARCHITECTURE.md) | Threat model and controls |

---

## Documentation by Topic

### Architecture

- [System Overview](architecture/SYSTEM_OVERVIEW.md) - C4 model diagrams, layer descriptions
- [Data Flow](architecture/DATA_FLOW.md) - Job submission, execution, failover flows
- [Component Diagram](architecture/COMPONENT_DIAGRAM.md) - Canvas, Robot, Orchestrator internals

### API & Integration

- [REST API Reference](api/REST_API_REFERENCE.md) - WebSocket protocol, message types, endpoints

### Operations

- [Runbook](operations/RUNBOOK.md) - Procedures for startup, shutdown, scaling, backup
- [Troubleshooting](operations/TROUBLESHOOTING.md) - Diagnostic scripts, common issues

### Development

- [Contributing](development/CONTRIBUTING.md) - Architecture guidelines, coding standards, PR process
- [Testing](development/TESTING_GUIDE.md) - Unit, integration, E2E testing

### Security

- [Security Architecture](security/SECURITY_ARCHITECTURE.md) - Auth, encryption, threat model, compliance

### User Guide

- [Getting Started](user-guide/GETTING_STARTED.md) - Installation, first workflow, common tasks

---

## Diagram Reference

All documentation uses Mermaid.js diagrams. Key diagram types:

### C4 Model Diagrams
- Context diagram (system boundaries)
- Container diagram (applications)
- Component diagram (internal structure)

### Sequence Diagrams
- Job submission flow
- Robot execution flow
- Failover and recovery
- Trigger event flow

### State Diagrams
- Job state machine
- Trigger lifecycle
- Connection states

### Flowcharts
- Self-healing flow
- Incident response
- Decision trees

---

## Version Information

| Item | Version |
|------|---------|
| Documentation | 1.0.0 |
| CasareRPA | 3.0.0-dev |
| Last Updated | 2024-01 |

---

## Contributing to Documentation

Documentation improvements are welcome! See [Contributing Guide](development/CONTRIBUTING.md) for:
- Documentation style guidelines
- How to update diagrams
- Review process

---

## Support

- GitHub Issues: Bug reports and feature requests
- Discussions: Questions and community support
- Documentation: This documentation set
