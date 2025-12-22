# CasareRPA

**Windows RPA Platform | Python 3.12 | PySide6 | Playwright**

CasareRPA is a professional-grade Robotic Process Automation platform for Windows. Build visual workflows to automate web browsers, desktop applications, files, emails, APIs, and more.

## Quick Install

```bash
pip install casare-rpa
```

## Quick Run

```bash
# Launch the visual designer
python run.py

# Run a workflow from CLI
casare-rpa run workflow.json

# Run with specific robot agent
casare-rpa agent start --name my-robot
```

## Features

- **413+ Automation Nodes** - Browser, desktop, data, HTTP, email, and system automation
- **20+ Trigger Types** - Schedule, webhook, file watch, email, messaging integrations
- **Visual Canvas Designer** - Drag-and-drop workflow editor with real-time execution
- **AI Workflow Generation** - Generate workflows from natural language
- **Multi-Robot Orchestration** - Distribute execution across multiple agents
- **Self-Healing Selectors** - Automatic recovery when web elements change

## Quick Example

```python
from casare_rpa.application import ExecuteWorkflowUseCase
from casare_rpa.infrastructure.execution import ExecutionContext

# Load and execute a workflow
use_case = ExecuteWorkflowUseCase()
result = await use_case.execute("my_workflow.json")

print(f"Workflow completed: {result.success}")
```

## System Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.12+ |
| OS | Windows 10/11 |
| Memory | 8GB+ recommended |

## Documentation

Full documentation available at [docs/index.md](index.md):

- [User Guide](user-guide/index.md) - Getting started, tutorials, and guides
- [Developer Guide](developer-guide/index.md) - Architecture and extending the platform
- [Reference](reference/index.md) - Complete node and trigger reference
- [Security](security/index.md) - Authentication and credentials
- [Operations](operations/index.md) - Deployment and troubleshooting

## Project Structure

```
casare-rpa/
    src/casare_rpa/
        domain/           # Business logic, entities, events
        application/      # Use cases, queries, services
        infrastructure/   # External adapters, persistence
        presentation/     # Canvas UI, CLI
        nodes/            # 413+ automation nodes
        triggers/         # 20+ trigger implementations
    docs/                 # Documentation
    examples/             # Sample workflows
```

## License

Proprietary - All rights reserved.

## Support

- GitHub Issues for bug reports and feature requests
- See documentation for troubleshooting guides
