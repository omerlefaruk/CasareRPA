---
description: Create a Notepad Automation Workflow using AI Infrastructure
---

# Create a Notepad Workflow using /infrastructure/ai

This workflow demonstrates how to use the CasareRPA AI infrastructure to generate desktop automation workflows.

## Prerequisites

1. Ensure you have the CasareRPA environment set up
2. Have LLM API credentials configured in `.env` (for AI generation)
3. Python virtual environment activated

## Method 1: Using the AI Generator Script

// turbo
1. Navigate to the project root:
```bash
cd c:\Users\Rau\Desktop\CasareRPA
```

2. Activate the virtual environment:
```bash
.venv\Scripts\activate
```

// turbo
3. Run the AI workflow generator:
```bash
python scripts/generate_notepad_workflow.py
```

4. The script will:
   - Use `SmartWorkflowAgent` from `infrastructure/ai`
   - Send a natural language prompt to the LLM
   - Validate the generated workflow using `HeadlessWorkflowSandbox`
   - Save the result to `workflows/ai_notepad_workflow.json`

## Method 2: Using Pre-built Template

If AI generation isn't available (no API credentials), use the pre-built template:

1. Copy the template:
```bash
copy templates\simple_notepad_workflow.json workflows\my_notepad_workflow.json
```

2. Open the workflow in CasareRPA Canvas

## Key Components Used

### From `/infrastructure/ai`:

| Component | Purpose |
|-----------|---------|
| `SmartWorkflowAgent` | Main AI agent for workflow generation |
| `WorkflowGenerationResult` | Result dataclass with validation info |
| `HeadlessWorkflowSandbox` | Validates generated workflows |
| `dump_node_manifest` | Provides available nodes to the LLM |

### From `/domain/ai`:

| Component | Purpose |
|-----------|---------|
| `SIMPLE_FAST_CONFIG` | Fast generation configuration |
| `PERFORMANCE_OPTIMIZED_CONFIG` | For optimized workflows |
| `PromptBuilder` | Builds prompts with node context |

### Desktop Nodes Used:

| Node | Purpose |
|------|---------|
| `LaunchApplicationNode` | Opens notepad.exe |
| `WaitNode` | Delays for window loading |
| `SendKeysNode` | Types text into Notepad |
| `SendHotKeyNode` | Sends Enter key |
| `CloseApplicationNode` | Closes the application |

## Customizing the Prompt

Edit `scripts/generate_notepad_workflow.py` to modify the prompt. The AI will:

1. **Parse** your natural language description
2. **Match** requested actions to available nodes
3. **Generate** valid JSON workflow structure
4. **Validate** against Qt-based workflow validator
5. **Repair** any issues found during validation

## Example Prompts

### Simple Notepad Workflow:
```
Create a workflow that opens Notepad, types "Hello World", and closes it.
```

### Advanced Notepad Workflow:
```
Create a Notepad workflow that:
1. Launches Notepad in maximized window
2. Types a multi-line poem with proper Enter keys
3. Saves the file using Ctrl+S hotkey
4. Closes the application gracefully
```

### With Error Handling:
```
Create a robust Notepad workflow with TryCatchNode that:
1. Tries to launch Notepad
2. Types a greeting message
3. Catches any errors and logs them
4. Always closes the application in finally block
```

## Troubleshooting

### API Key Issues
Ensure your `.env` file has valid LLM credentials:
```
OPENAI_API_KEY=sk-...
# or
GOOGLE_API_KEY=...
```

### Validation Errors
If the AI generates invalid workflows, check:
- Node types match exactly (case-sensitive)
- Port names are correct (exec_in, exec_out)
- Config properties match node schemas

### Import Errors
Ensure you're running from the project root with virtual environment activated.
