# AI Assistant Guide

The CasareRPA AI Assistant enables natural language workflow generation. Describe what you want to automate in plain English, and the AI will generate a complete, executable workflow.

---

## Overview

The AI Assistant uses large language models to:

- Interpret natural language automation requests
- Select appropriate nodes from the 413+ node library
- Generate properly connected workflows
- Validate and refine generated workflows

---

## Accessing the AI Assistant

### In Canvas

1. Press `Ctrl+Shift+G` to open AI Assistant panel
2. Or click **View > AI Assistant** in the menu

### Via API

```python
from casare_rpa.application.use_cases import generate_workflow_from_text

workflow = await generate_workflow_from_text(
    "Open Google and search for weather in New York"
)
```

---

## Using the AI Assistant

### Basic Workflow Generation

1. Open the AI Assistant panel
2. Type your automation request in natural language
3. Click "Generate" or press Enter
4. Review the generated workflow
5. Click "Apply" to add to canvas

### Example Requests

**Web Automation:**
```
Open Chrome, go to amazon.com, search for "laptop", and extract the first 5 product titles and prices
```

**Data Processing:**
```
Read all CSV files from the Downloads folder, merge them into one file, and save as merged_data.xlsx
```

**Email Automation:**
```
Check Gmail for unread emails with "invoice" in the subject, download attachments, and save them to the Invoices folder
```

**Desktop Automation:**
```
Open Excel, create a new workbook, enter "Monthly Report" in cell A1, and save as report.xlsx on the Desktop
```

---

## Generation Features

### Multi-Turn Conversation

The AI remembers context for refinement:

```
User: Create a workflow to scrape product prices from amazon.com
AI: [Generates workflow]

User: Add error handling for when products aren't found
AI: [Adds TryCatch node around scraping logic]

User: Also send an email notification when it completes
AI: [Adds SendEmail node at the end]
```

### Workflow Refinement

Request specific changes:

```
User: Make the browser run in headless mode
User: Add a 2 second delay between clicking products
User: Change the output format from JSON to CSV
```

### Node Suggestions

Ask for capabilities:

```
User: What nodes can I use for PDF processing?
AI: Available PDF nodes:
- ReadPDFNode - Extract text from PDF files
- ExtractPDFTablesNode - Extract tables from PDFs
- MergePDFsNode - Combine multiple PDFs
- SplitPDFNode - Split PDF into pages
- PDFToImagesNode - Convert PDF pages to images
```

---

## Best Practices

### 1. Be Specific

```
# Less specific (may produce unexpected results)
"Automate Excel"

# More specific (better results)
"Open the file sales_q4.xlsx, calculate the sum of column C, and write the result to cell C100"
```

### 2. Break Down Complex Tasks

```
# Instead of one complex request:
"Scrape 1000 products, process them, save to database, and email report"

# Break into steps:
1. "Create a workflow to scrape product listings from example.com"
2. "Add data transformation to clean the product data"
3. "Add database insertion for the processed products"
4. "Add email notification at the end with summary"
```

### 3. Specify Data Handling

```
# Unclear data handling
"Get the data and save it"

# Clear data handling
"Extract the table data as JSON and save to output.json in the project folder"
```

### 4. Include Error Handling

```
"Create a web scraping workflow with retry logic for failed requests and skip products that don't have prices"
```

---

## Workflow Validation

Generated workflows are automatically validated:

1. **Schema Validation** - Node configurations match expected types
2. **Connection Validation** - Port types are compatible
3. **Loop Validation** - Control flow structures are properly formed
4. **Reference Validation** - All referenced nodes and variables exist

### Validation Feedback

If validation fails, the AI automatically attempts to fix issues:

```
Generation attempt 1/3: Invalid connection between nodes
Auto-fixing: Adjusting port connections...
Generation attempt 2/3: Success!
```

---

## Configuration

### Model Selection

Configure the LLM model used for generation:

| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| `gpt-4o-mini` | Fast | Good | Low |
| `gpt-4o` | Medium | Better | Medium |
| `claude-3-sonnet` | Medium | Better | Medium |
| `claude-3-opus` | Slow | Best | High |

Set via environment variable:

```bash
CASARE_AI_MODEL=gpt-4o
```

Or in configuration:

```yaml
ai:
  model: gpt-4o
  temperature: 0.2
  max_tokens: 4000
```

### Performance Settings

```yaml
ai:
  performance:
    wait_strategy: "no_hardcoded_waits"  # Use dynamic waits
    parallelism: "moderate"              # Allow parallel operations
    timeout_handling: "dynamic"          # Adjust timeouts dynamically

  error_handling:
    mode: "paranoid"                     # Wrap all operations in try-catch
```

### Retry Settings

```yaml
ai:
  retry:
    max_generation_retries: 3
    retry_delay_seconds: 1
```

---

## API Reference

### generate_workflow_from_text

```python
async def generate_workflow_from_text(
    query: str,
    model: str = "gpt-4o-mini",
    llm_manager: Optional[LLMResourceManager] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Generate a workflow from natural language.

    Args:
        query: Natural language description of desired automation
        model: LLM model to use
        llm_manager: Optional custom LLM manager
        validate: Whether to validate generated workflow

    Returns:
        Workflow JSON dictionary

    Raises:
        WorkflowGenerationError: If generation fails
    """
```

### SmartWorkflowAgent

```python
from casare_rpa.infrastructure.ai import SmartWorkflowAgent

agent = SmartWorkflowAgent(
    max_retries=3,
    config=agent_config  # Optional AgentConfig
)

# Generate workflow
result = await agent.generate(
    prompt="Scrape weather data from weather.com"
)

# Access results
workflow_json = result.workflow_data
attempts = result.attempts
validation = result.validation_result
```

### WorkflowGenerationResult

```python
@dataclass
class WorkflowGenerationResult:
    workflow_data: Dict[str, Any]      # Generated workflow JSON
    attempts: List[GenerationAttempt]  # All generation attempts
    validation_result: ValidationResult  # Validation status
    total_time_seconds: float          # Total generation time
```

---

## Error Handling

### Common Errors

**LLMCallError**
```
Error: Failed to call LLM: API rate limit exceeded
```
- Wait and retry
- Check API key quotas
- Try different model

**JSONParseError**
```
Error: Failed to parse LLM response as JSON
```
- Automatic retry with clearer prompt
- Usually resolves within max_retries

**ValidationError**
```
Error: Generated workflow validation failed
```
- AI automatically attempts to fix
- Review error details if persists

**MaxRetriesExceededError**
```
Error: Failed to generate valid workflow after 3 attempts
```
- Simplify the request
- Break into smaller steps
- Provide more specific details

### Handling Errors in Code

```python
from casare_rpa.infrastructure.ai import (
    generate_smart_workflow,
    WorkflowGenerationError,
    LLMCallError,
    ValidationError,
)

try:
    workflow = await generate_smart_workflow(prompt)
except LLMCallError as e:
    print(f"LLM error: {e.details}")
except ValidationError as e:
    print(f"Validation failed: {e.validation_errors}")
except WorkflowGenerationError as e:
    print(f"Generation failed: {e}")
```

---

## Advanced Features

### RAG (Retrieval-Augmented Generation)

The AI uses RAG to find relevant nodes:

1. Query is analyzed for intent
2. Relevant nodes are retrieved from vector store
3. Node documentation is included in prompt
4. More accurate node selection

### Custom Prompts

Configure prompt customization:

```python
from casare_rpa.domain.ai.config import AgentConfig, PromptCustomization

config = AgentConfig(
    prompts=PromptCustomization(
        custom_rules=[
            "Always use headless browser mode",
            "Prefer CSS selectors over XPath",
            "Add logging after each major step",
        ]
    )
)

agent = SmartWorkflowAgent(config=config)
```

### Intent Classification

The AI classifies request intent:

| Intent | Description | Handling |
|--------|-------------|----------|
| `generate` | Create new workflow | Full generation |
| `edit` | Modify existing workflow | Targeted changes |
| `append` | Add to workflow | Add nodes at end |
| `question` | Ask about capabilities | Informational response |

---

## Limitations

1. **Complex Logic** - Very complex conditional logic may need manual adjustment
2. **Domain Knowledge** - Industry-specific terms may need clarification
3. **Visual Layout** - Node positioning may need manual arrangement
4. **Custom Nodes** - Custom nodes require explicit naming

---

## Examples

### Web Data Extraction

**Request:**
```
Go to news.ycombinator.com, extract the top 10 article titles and URLs, and save them to a JSON file
```

**Generated Workflow:**
```
[Launch Browser] -> [Navigate] -> [Extract Elements] -> [Transform to JSON] -> [Write File]
                        |
                        v
                  news.ycombinator.com
```

### Automated Reporting

**Request:**
```
Every Monday at 9 AM, read sales data from Google Sheets, generate a summary, and email it to the sales team
```

**Generated Workflow:**
```
[Schedule Trigger] -> [Read Sheets] -> [Aggregate Data] -> [Format Report] -> [Send Email]
      |
      v
  Mon 9:00 AM
```

### File Processing

**Request:**
```
Watch the Downloads folder for new PDF files, extract text, and save as text files with the same name
```

**Generated Workflow:**
```
[File Watch Trigger] -> [Read PDF] -> [Extract Text] -> [Write File]
         |
         v
    Downloads/*.pdf
```

---

## Related Documentation

- [First Workflow](../getting-started/first-workflow.md) - Manual workflow creation
- [Node Reference](../../reference/nodes/index.md) - All available nodes
- [Best Practices](best-practices.md) - Workflow design guidelines
- [Debugging](debugging.md) - Troubleshooting workflows
