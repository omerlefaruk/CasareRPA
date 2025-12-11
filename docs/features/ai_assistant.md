# CasareRPA Genius AI Assistant

The AI Assistant is a dockable widget that generates validated workflow JSON from natural language descriptions.

## Overview

The Genius Assistant uses a "Paranoid Engineering" approach:
1. **Generate** - LLM creates workflow JSON from user prompt
2. **Validate** - HeadlessWorkflowSandbox validates structure
3. **Repair** - If validation fails, LLM fixes errors (up to 3 attempts)
4. **Output** - Only verified workflows are presented to user

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRESENTATION                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               AIAssistantDock (dock.py)                   │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │  │
│  │  │ ChatArea    │  │ PreviewCard  │  │ CredentialSelect│   │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        INFRASTRUCTURE                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               SmartWorkflowAgent (smart_agent.py)         │  │
│  │    ┌──────────────┐         ┌─────────────────────────┐   │  │
│  │    │ LLM Client   │ ←──────→│ HeadlessWorkflowSandbox │   │  │
│  │    └──────────────┘         └─────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                           DOMAIN                                │
│  ┌─────────────────────┐  ┌────────────────────────────────┐   │
│  │  prompts.py         │  │  headless_validator.py          │   │
│  │  - System prompts   │  │  - ValidationResult            │   │
│  │  - Repair templates │  │  - Port validation             │   │
│  └─────────────────────┘  └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. AI Assistant Dock (`presentation/canvas/ui/widgets/ai_assistant/dock.py`)

Main dockable widget with:
- **Credential Selector** - Dropdown for AI provider selection (Google AI, OpenAI)
- **Model Selector** - Choose specific model (Gemini, GPT-4o, etc.)
- **Chat Area** - Conversation display with user/AI message bubbles
- **Input Field** - User prompt entry with send button
- **Preview Card** - Workflow summary with Append/Regenerate actions

**Thread-Safe Generation:**
The dock uses `WorkflowGenerationThread` to run async LLM calls without blocking the Qt event loop:

```python
# Credentials are retrieved from the secure credential store
thread = WorkflowGenerationThread(
    prompt="Create a login workflow",
    model_id="gemini/gemini-flash-latest",
    credential_id="my-google-ai-cred",
)
thread.finished.connect(self._on_generation_complete)
thread.start()
```

**Signals:**
```python
workflow_ready = Signal(dict)      # Valid workflow generated
append_requested = Signal(dict)    # User clicked "Append to Canvas"
generation_started = Signal()      # Show loading state
generation_finished = Signal(bool) # Hide loading, show result
credential_changed = Signal(str)   # Credential selection changed
```

### 2. Smart Workflow Agent (`infrastructure/ai/smart_agent.py`)

Integrates LLM generation with validation:

```python
agent = SmartWorkflowAgent(llm_client, max_retries=3)

result = await agent.generate_workflow(
    user_prompt="Create a web scraping workflow",
    existing_workflow=None  # Or pass existing for append mode
)

if result.success:
    workflow_json = result.workflow
    print(f"Generated in {result.attempts} attempts")
else:
    print(f"Failed: {result.error}")
```

### 3. Headless Workflow Sandbox (`domain/services/headless_validator.py`)

Validates workflow JSON without UI:

```python
validator = HeadlessWorkflowSandbox()
result = validator.validate_workflow(workflow_json)

if result.success:
    print(f"Valid: {result.validated_nodes} nodes, {result.validated_connections} connections")
else:
    for error in result.errors:
        print(f"{error.error_type}: {error.message}")
        print(f"  Suggestion: {error.suggestion}")
```

**Error Types:**
- `REGISTRY_ERROR` - Node type not found
- `INIT_ERROR` - Node initialization failed
- `PORT_ERROR` - Invalid port reference
- `TYPE_MISMATCH` - Incompatible port types
- `SCHEMA_ERROR` - JSON schema validation failed

### 4. AI Prompts (`domain/ai/prompts.py`)

System prompts and templates:
- `GENIUS_SYSTEM_PROMPT` - AI character definition
- `ROBUSTNESS_INSTRUCTIONS` - Paranoid engineering guidelines
- `MISSING_NODE_PROTOCOL` - Node creation/modification protocol
- `JSON_SCHEMA_TEMPLATE` - Expected JSON structure
- `REPAIR_PROMPT_TEMPLATE` - Error correction template

## Usage

### Adding to Main Window

```python
from casare_rpa.presentation.canvas.ui.widgets.ai_assistant import AIAssistantDock
from PySide6.QtCore import Qt

# Create dock
assistant = AIAssistantDock(parent=main_window)
main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, assistant)

# Connect signals
assistant.append_requested.connect(self._on_append_workflow)

def _on_append_workflow(self, workflow: dict):
    # Add nodes to canvas
    self.canvas.load_workflow_fragment(workflow)
```

### Standalone Generation

```python
from casare_rpa.infrastructure.ai import generate_smart_workflow

result = await generate_smart_workflow(
    prompt="Create a workflow that reads a CSV and sends emails",
    credential_id="my-openai-key"
)
```

## Missing Node Protocol

When a workflow requires functionality that **no existing node provides**, the AI Assistant can request node creation or modification.

### Request Node Creation

```json
{
  "action": "create_node",
  "reason": "No existing node supports PDF table extraction",
  "node_spec": {
    "name": "ExtractPDFTableNode",
    "category": "file",
    "description": "Extract tables from PDF files as structured data",
    "inputs": [
      {"name": "exec_in", "type": "EXEC"},
      {"name": "file_path", "type": "STRING", "required": true},
      {"name": "page_number", "type": "INTEGER", "required": false}
    ],
    "outputs": [
      {"name": "exec_out", "type": "EXEC"},
      {"name": "tables", "type": "LIST"}
    ],
    "config": {
      "extraction_method": {"type": "string", "default": "auto", "description": "Method: auto, lattice, stream"}
    },
    "execute_logic": "Use camelot or tabula to extract tables from PDF"
  }
}
```

### Request Node Modification

```json
{
  "action": "modify_node",
  "existing_node": "ReadCSVNode",
  "reason": "Need to handle multiple delimiters",
  "modifications": {
    "new_config": {"delimiter": {"type": "string", "default": ",", "description": "Field delimiter character"}}
  }
}
```

After node creation approval, the AI continues generating the workflow using the new node type.

## Robustness Protocol

All AI-generated workflows follow these patterns:

### 1. TryCatchNode Wrapper
Logic clusters are wrapped in error handling:
```
TryNode → [Business Logic] → CatchNode → [Error Handler] → FinallyNode
```

### 2. IfElseNode Sanity Checks
Critical variables are validated before use:
```
IfNode (condition: "{{data}} != null") → True Branch / False Branch
```

### 3. DebugNode Logging
Entry/exit points include logging:
```
DebugNode (message: "Starting data processing...")
```

## Testing

### Test Invalid Node Type
```python
# User prompt: "Create a workflow with a FakeNode"
# Expected: Validator catches RegistryError, LLM substitutes valid node
```

### Test Invalid Port
```python
# Connection references non-existent port
# Expected: Validator catches PortError with suggestion
```

## Files

| File | Purpose |
|------|---------|
| `domain/ai/prompts.py` | System prompts and templates |
| `domain/services/headless_validator.py` | Workflow validation |
| `infrastructure/ai/smart_agent.py` | LLM + validation loop |
| `presentation/canvas/ui/widgets/ai_assistant/dock.py` | Main widget |
| `presentation/canvas/ui/widgets/ai_assistant/chat_area.py` | Chat display |
| `presentation/canvas/ui/widgets/ai_assistant/preview_card.py` | Workflow preview |
| `docs/ai_context/workflow_standards.md` | LLM context documentation |

## Related Documentation

- [Workflow Standards](../ai_context/workflow_standards.md) - Complete node reference
- [Node Registration](../../src/casare_rpa/nodes/_index.md) - Node development guide
