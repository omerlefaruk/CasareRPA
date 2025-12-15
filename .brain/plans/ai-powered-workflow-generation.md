# AI-Powered Workflow Generation Research

**Research Date**: 2025-12-11
**Research Type**: Technical Analysis and Competitive Research
**Status**: Complete

---

## Executive Summary

This research analyzes how AI can be used to CREATE and DESIGN workflows in CasareRPA through natural language interfaces. CasareRPA already has a solid foundation with `SmartWorkflowAgent` and `AIAssistantDock`, but there are significant opportunities to enhance capabilities to match and exceed industry leaders like UiPath Autopilot and Power Automate Copilot.

---

## Part 1: Current CasareRPA AI Workflow Generation

### Existing Implementation

CasareRPA already has a functional AI workflow generation system:

#### Core Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `SmartWorkflowAgent` | `infrastructure/ai/smart_agent.py` | LLM + validation generation loop |
| `AIAssistantDock` | `presentation/canvas/ui/widgets/ai_assistant/dock.py` | Chat UI for workflow requests |
| `GenerateWorkflowUseCase` | `application/use_cases/generate_workflow.py` | Application layer orchestration |
| `WorkflowAISchema` | `domain/schemas/workflow_ai.py` | Pydantic validation for AI output |
| `PromptBuilder` | `domain/ai/prompts.py` | System prompt construction |
| `registry_dumper` | `infrastructure/ai/registry_dumper.py` | Node manifest for context |
| `HeadlessWorkflowSandbox` | `infrastructure/ai/smart_agent.py` | Validation without UI |

#### Current Flow

```
User Prompt -> SmartWorkflowAgent -> LLM Call -> JSON Response
                    |
                    v
              Parse JSON -> WorkflowAISchema Validation
                    |
                    v
              HeadlessWorkflowSandbox Qt Validation
                    |
                    +-- Valid: Return Workflow
                    |
                    +-- Invalid: Build Repair Prompt -> Retry (up to 3x)
```

#### Strengths

1. **Generate + Validate + Repair Loop**: Robust "paranoid engineering" approach
2. **Multi-provider Support**: Google AI, OpenAI via LiteLLM
3. **Node Manifest Context**: Compact markdown fed to LLM with all available nodes
4. **Schema Validation**: Pydantic models prevent malformed workflows
5. **Security**: Dangerous pattern detection (eval, exec, subprocess, etc.)
6. **Edit Detection**: Distinguishes between edit requests and new generation
7. **Canvas Context**: Provides current canvas state to LLM for context
8. **Configurable Agent**: `AgentConfig` for customizing generation behavior

#### Gaps Identified

1. **No Multi-turn Refinement**: Single-shot generation only
2. **No Workflow Suggestions**: Cannot suggest completions for partial designs
3. **No Auto-completion**: No intelligent port connection suggestions
4. **No Intent Templates**: No pre-built workflow templates by intent
5. **No Visual Preview**: Preview card shows text summary only
6. **No Streaming**: Full response required before display
7. **No Conversation Memory**: Each request is independent

---

## Part 2: Competitor Analysis

### UiPath Autopilot

**Source**: [UiPath Autopilot Documentation](https://docs.uipath.com/autopilot/other/latest/overview/text-to-workflow)

#### Key Features

| Feature | Description | CasareRPA Status |
|---------|-------------|------------------|
| **Text to Workflow** | Natural language to workflow with 70%+ acceptance | Implemented (SmartWorkflowAgent) |
| **Text to Code** | Generate coded logic from description | Not implemented |
| **Text to Expression** | Generate workflow expressions in NL | Not implemented |
| **Visual Preview** | See workflow structure before building | Basic (text summary only) |
| **Predefined Templates** | Example prompts to start from | Not implemented |
| **Non-conversational** | Single prompt generation | Implemented |
| **Multi-model Backend** | Gemini 2.5 Flash/Pro, Gemini 2.0 Flash | LiteLLM multi-provider |

#### UiPath Workflow Generation Approach

1. User describes automation idea in natural language
2. Autopilot identifies relevant activities from its activity library
3. Generates logical sequence of activities
4. Provides visual preview before building
5. Developer refines and deploys

**Key Insight**: UiPath uses a mix of proprietary models and third-party LLMs (Google Gemini) for optimal performance.

### Power Automate Copilot

**Source**: [Power Automate Copilot Overview](https://learn.microsoft.com/en-us/power-automate/copilot-overview)

#### Key Features

| Feature | Description | CasareRPA Status |
|---------|-------------|------------------|
| **Multi-step Conversation** | Refine through conversation | Not implemented |
| **Auto Setup Connections** | Automatically configure connectors | Not implemented |
| **Copilot-assisted Expressions** | NL to WDL/Power Fx expressions | Not implemented |
| **Flow Analysis** | Analyze existing flows | Not implemented |
| **Error Repair** | AI-driven error identification | Implemented (repair prompts) |
| **Agent Flows** | Create agent flows via NL | Not implemented |
| **Generative Actions** | AI-driven steps (summarize, enrich) | Implemented (LLM nodes) |

#### Power Automate Workflow Generation Approach

1. User describes what they need in everyday language
2. Copilot interprets intent and creates flow
3. Automatically sets up connections
4. Applies parameters based on prompt
5. Responds to change requests conversationally
6. Can modify existing flows

**Key Insight**: Power Automate emphasizes multi-turn conversation for iterative refinement.

### Comparison Matrix

| Capability | UiPath Autopilot | Power Automate Copilot | CasareRPA |
|------------|------------------|------------------------|-----------|
| NL to Workflow | Yes (70%+ acceptance) | Yes | Yes |
| Multi-turn Conversation | No | Yes | No |
| Visual Preview | Yes | Yes | Basic |
| Template Library | Yes | Yes | No |
| Auto-connections | Limited | Yes | No |
| Expression Generation | Yes | Yes | No |
| Error Repair | Yes | Yes | Yes |
| Edit Existing | Limited | Yes | Detected only |
| Streaming Response | Unknown | Yes | No |
| Self-healing | Yes (Healing Agent) | Yes | No |

---

## Part 3: Technical Approaches for Enhancement

### 3.1 LLM Prompting Strategies

#### Current Strategy (CasareRPA)

The current `GENIUS_SYSTEM_PROMPT` follows a structured approach:
- PLAN -> BUILD -> VALIDATE -> REPAIR -> OUTPUT protocol
- Node manifest in compact markdown format
- JSON schema template embedded
- Control flow port documentation (critical for valid connections)

#### Recommended Enhancements

**1. Chain-of-Thought (CoT) Prompting**

```python
ENHANCED_PROMPT = """
Before generating the workflow JSON, think through these steps:

1. UNDERSTAND: What is the user trying to accomplish?
   - Primary goal
   - Input data sources
   - Expected output

2. DECOMPOSE: Break into atomic operations
   - List each distinct action needed
   - Identify dependencies between actions
   - Note any conditional logic required

3. MAP: Match operations to CasareRPA nodes
   - Search the manifest for exact matches
   - Consider node composition for complex operations
   - Identify any gaps requiring new nodes

4. SEQUENCE: Determine execution order
   - Which operations can run in parallel?
   - Which must be sequential?
   - Where are error boundaries needed?

5. GENERATE: Output the JSON workflow

Now apply this process to: {user_prompt}
"""
```

**2. Few-Shot Examples**

Include curated workflow examples for common patterns:

```python
FEW_SHOT_EXAMPLES = {
    "web_scraping": {
        "prompt": "Scrape product prices from example.com",
        "workflow": {...}  # Complete valid workflow
    },
    "file_processing": {
        "prompt": "Read CSV, filter rows, write Excel",
        "workflow": {...}
    },
    "api_integration": {
        "prompt": "Call REST API and save response",
        "workflow": {...}
    }
}
```

**3. Structured Output Enforcement**

**Source**: [JSON Schema for LLM Structured Outputs](https://blog.promptlayer.com/how-json-schema-works-for-structured-outputs-and-tool-integration/)

Use OpenAI/Anthropic structured output mode:

```python
# OpenAI example
response = client.chat.completions.create(
    model="gpt-4o",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "workflow",
            "schema": WorkflowAISchema.model_json_schema()
        }
    },
    messages=[...]
)
```

**Benefits**:
- Guaranteed valid JSON structure
- No need for JSON extraction regex
- Reduced repair cycles

### 3.2 Workflow DSL Generation

#### Current Approach

CasareRPA generates JSON directly matching the workflow schema:

```json
{
  "metadata": {"name": "...", "description": "..."},
  "nodes": {
    "node_id": {
      "node_id": "...",
      "node_type": "...",
      "config": {...},
      "position": [x, y]
    }
  },
  "connections": [...]
}
```

#### Proposed: Intermediate DSL

Introduce a simpler intermediate representation that's easier for LLMs to generate correctly:

```
# CasareRPA Workflow DSL (CRPA-DSL)
@workflow "Download Email Attachments"
@description "Downloads attachments from unread emails"

# Variables
$folder = "C:/downloads"
$sender_filter = "invoices@company.com"

# Flow
START
  -> ConnectIMAPNode(host="imap.gmail.com", cred="email_cred")
  -> ListEmailsNode(folder="INBOX", unread_only=true)
  -> ForEach(email in $emails)
      -> IF(email.has_attachments)
          -> DownloadAttachmentNode(save_to=$folder)
      -> ENDIF
  -> EndForEach
END
```

**DSL Compiler**:

```python
class DSLCompiler:
    """Compiles CRPA-DSL to workflow JSON."""

    def compile(self, dsl_text: str) -> Dict[str, Any]:
        tokens = self._tokenize(dsl_text)
        ast = self._parse(tokens)
        workflow = self._generate_workflow(ast)
        return workflow
```

**Benefits**:
- Simpler syntax = fewer LLM errors
- Easier to validate incrementally
- Human-readable intermediate form
- Can be edited manually before compilation

### 3.3 Node Graph Synthesis

#### Graph-Based Generation

**Source**: [LangGraph Multi-Agent Workflows](https://blog.langchain.com/langgraph-multi-agent-workflows/)

Instead of generating complete JSON, generate incrementally:

```python
class IncrementalGraphBuilder:
    """Builds workflow graph node-by-node with LLM guidance."""

    def __init__(self, llm_client, node_registry):
        self.llm = llm_client
        self.registry = node_registry
        self.graph = WorkflowGraph()

    async def build_from_prompt(self, user_prompt: str):
        # Step 1: Identify required operations
        operations = await self._identify_operations(user_prompt)

        # Step 2: For each operation, select best node
        for op in operations:
            node_type = await self._select_node(op)
            config = await self._configure_node(node_type, op)
            node_id = self.graph.add_node(node_type, config)

        # Step 3: Connect nodes intelligently
        await self._auto_connect_nodes()

        return self.graph.to_workflow_dict()

    async def _auto_connect_nodes(self):
        """Use LLM to determine optimal connections."""
        # Analyze data flow requirements
        # Match output types to input types
        # Infer execution order from semantics
```

#### Auto-Connection Logic

```python
class PortMatcher:
    """Intelligent port matching for auto-connections."""

    def suggest_connections(
        self,
        source_node: NodeSchema,
        target_node: NodeSchema
    ) -> List[ConnectionSuggestion]:
        suggestions = []

        # Match by data type
        for out_port in source_node.outputs:
            for in_port in target_node.inputs:
                if self._types_compatible(out_port.data_type, in_port.data_type):
                    score = self._calculate_match_score(out_port, in_port)
                    suggestions.append(ConnectionSuggestion(
                        source_port=out_port.name,
                        target_port=in_port.name,
                        confidence=score
                    ))

        # Special handling for exec ports
        if source_node.has_exec_out and target_node.has_exec_in:
            suggestions.append(ConnectionSuggestion(
                source_port="exec_out",
                target_port="exec_in",
                confidence=1.0,
                is_exec=True
            ))

        return sorted(suggestions, key=lambda s: -s.confidence)
```

---

## Part 4: Implementation Recommendations

### 4.1 Multi-Turn Conversation System

**Priority**: High | **Effort**: Medium

```python
class ConversationalWorkflowAgent:
    """
    Maintains conversation history for iterative refinement.
    """

    def __init__(self, smart_agent: SmartWorkflowAgent):
        self.agent = smart_agent
        self.conversation_history: List[Message] = []
        self.current_workflow: Optional[Dict] = None
        self.intent_stack: List[Intent] = []

    async def process_message(self, user_input: str) -> AgentResponse:
        # Classify intent
        intent = await self._classify_intent(user_input)

        if intent == Intent.NEW_WORKFLOW:
            return await self._handle_new_workflow(user_input)
        elif intent == Intent.MODIFY_WORKFLOW:
            return await self._handle_modification(user_input)
        elif intent == Intent.CLARIFICATION:
            return await self._request_clarification(user_input)
        elif intent == Intent.CONFIRMATION:
            return await self._confirm_and_finalize()
        else:
            return await self._handle_general_query(user_input)

    async def _handle_modification(self, request: str) -> AgentResponse:
        """Handle workflow modification requests."""
        if not self.current_workflow:
            return AgentResponse(
                message="No workflow to modify. Would you like to create one?",
                needs_input=True
            )

        # Parse modification intent
        mod_intent = await self._parse_modification_intent(request)

        # Apply modification
        modified = await self.agent.generate_workflow(
            user_prompt=f"Modify this workflow: {request}",
            existing_workflow=self.current_workflow,
            canvas_state=self._workflow_to_canvas_state(),
            is_edit=True
        )

        if modified.success:
            # Show diff
            diff = self._compute_workflow_diff(
                self.current_workflow,
                modified.workflow
            )
            self.current_workflow = modified.workflow
            return AgentResponse(
                message=f"I've made these changes:\n{diff}",
                workflow=modified.workflow,
                show_preview=True
            )
        else:
            return AgentResponse(
                message=f"I couldn't make that change: {modified.error}",
                needs_input=True
            )
```

**UI Integration**:

```python
# In AIAssistantDock
class AIAssistantDock(QDockWidget):

    def __init__(self, ...):
        ...
        self._conversational_agent = ConversationalWorkflowAgent(...)
        self._conversation_mode = True  # Enable multi-turn

    async def _on_send_clicked(self):
        prompt = self._input_field.text()

        if self._conversation_mode:
            response = await self._conversational_agent.process_message(prompt)
            self._handle_agent_response(response)
        else:
            # Single-shot mode (current behavior)
            self._start_generation(prompt)
```

### 4.2 Intent Recognition and Templates

**Priority**: High | **Effort**: Low

```python
@dataclass
class WorkflowIntent:
    """Recognized user intent with confidence."""
    category: str  # web_automation, file_processing, data_transform, etc.
    action: str    # scrape, download, upload, convert, etc.
    entities: Dict[str, str]  # url, file_path, format, etc.
    confidence: float

class IntentClassifier:
    """Classifies user requests into workflow intents."""

    INTENT_PATTERNS = {
        "web_scraping": [
            r"scrape\s+(?:data|content|prices?|products?)\s+from\s+(.+)",
            r"extract\s+(?:data|information)\s+from\s+(?:website|page)\s+(.+)",
            r"get\s+(?:all)?\s*(.+)\s+from\s+(.+\.com|.+\.org|.+\.net)",
        ],
        "file_download": [
            r"download\s+(?:all)?\s*(?:attachments?|files?)\s+from\s+(.+)",
            r"save\s+(.+)\s+to\s+(.+)",
        ],
        "data_transform": [
            r"convert\s+(.+)\s+to\s+(.+)",
            r"transform\s+(.+)\s+into\s+(.+)",
            r"read\s+(.+)\s+and\s+(?:write|save|export)\s+(?:as|to)\s+(.+)",
        ],
        "api_call": [
            r"call\s+(?:the)?\s*(.+)\s+api",
            r"(?:get|post|send)\s+(?:data\s+)?(?:to|from)\s+(.+)",
        ],
        "email_automation": [
            r"(?:read|check|get|download)\s+(?:new|unread)?\s*emails?\s+from\s+(.+)",
            r"send\s+email\s+to\s+(.+)",
        ],
        "form_fill": [
            r"fill\s+(?:out|in)?\s*(?:the)?\s*form\s+(?:on|at)\s+(.+)",
            r"login\s+to\s+(.+)",
            r"submit\s+(?:data|form)\s+to\s+(.+)",
        ],
    }

    async def classify(self, user_input: str) -> WorkflowIntent:
        # First try pattern matching
        for category, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    return WorkflowIntent(
                        category=category,
                        action=self._extract_action(pattern),
                        entities=self._extract_entities(match),
                        confidence=0.8
                    )

        # Fall back to LLM classification
        return await self._llm_classify(user_input)
```

**Template Library**:

```python
WORKFLOW_TEMPLATES = {
    "web_scraping": {
        "name": "Web Scraping Template",
        "description": "Extract data from websites",
        "required_inputs": ["url", "selector"],
        "nodes": [
            {"type": "LaunchBrowserNode", "config": {}},
            {"type": "GoToURLNode", "config": {"url": "{{url}}"}},
            {"type": "WaitForElementNode", "config": {"selector": "{{selector}}"}},
            {"type": "ExtractTextNode", "config": {"selector": "{{selector}}"}},
            {"type": "CloseBrowserNode", "config": {}},
        ]
    },
    "email_download": {
        "name": "Email Attachment Download",
        "description": "Download attachments from emails",
        "required_inputs": ["email_credential", "save_folder"],
        "nodes": [
            {"type": "IMAPConnectNode", "config": {}},
            {"type": "ListEmailsNode", "config": {"folder": "INBOX", "unread_only": True}},
            {"type": "ForLoopStartNode", "config": {}},
            {"type": "DownloadAttachmentsNode", "config": {"save_to": "{{save_folder}}"}},
            {"type": "ForLoopEndNode", "config": {}},
        ]
    },
    # ... more templates
}
```

### 4.3 Workflow Suggestions and Auto-Completion

**Priority**: Medium | **Effort**: Medium

```python
class WorkflowSuggestionEngine:
    """Suggests next nodes and connections based on partial workflow."""

    def __init__(self, node_registry, llm_client):
        self.registry = node_registry
        self.llm = llm_client
        self._connection_patterns = self._load_connection_patterns()

    async def suggest_next_nodes(
        self,
        current_workflow: Dict,
        cursor_node_id: str
    ) -> List[NodeSuggestion]:
        """Suggest what nodes to add next based on context."""

        cursor_node = current_workflow["nodes"].get(cursor_node_id)
        if not cursor_node:
            return []

        # Get output types from cursor node
        node_def = self.registry.get(cursor_node["node_type"])
        output_types = [p.data_type for p in node_def.outputs]

        suggestions = []

        # Find nodes that can consume these output types
        for node_type, node_def in self.registry.items():
            compatibility = self._check_input_compatibility(
                output_types,
                node_def.inputs
            )
            if compatibility > 0:
                suggestions.append(NodeSuggestion(
                    node_type=node_type,
                    reason=f"Can process {output_types[0]} output",
                    confidence=compatibility,
                    suggested_config=self._suggest_config(node_def)
                ))

        # Use LLM for semantic suggestions
        semantic_suggestions = await self._get_semantic_suggestions(
            cursor_node,
            current_workflow
        )
        suggestions.extend(semantic_suggestions)

        return sorted(suggestions, key=lambda s: -s.confidence)[:10]

    async def suggest_connections(
        self,
        current_workflow: Dict,
        source_node_id: str,
        target_node_id: str
    ) -> List[ConnectionSuggestion]:
        """Suggest which ports to connect between two nodes."""

        source = current_workflow["nodes"][source_node_id]
        target = current_workflow["nodes"][target_node_id]

        source_def = self.registry.get(source["node_type"])
        target_def = self.registry.get(target["node_type"])

        suggestions = []

        # Type-based matching
        for out_port in source_def.outputs:
            for in_port in target_def.inputs:
                if self._types_compatible(out_port.data_type, in_port.data_type):
                    suggestions.append(ConnectionSuggestion(
                        source_port=out_port.name,
                        target_port=in_port.name,
                        confidence=0.9 if out_port.data_type == in_port.data_type else 0.7
                    ))

        # Pattern-based matching (common combinations)
        pattern_suggestions = self._apply_connection_patterns(
            source["node_type"],
            target["node_type"]
        )
        suggestions.extend(pattern_suggestions)

        return suggestions
```

**UI Integration - Autocomplete Popup**:

```python
class NodeSuggestionPopup(QWidget):
    """Shows node suggestions while editing."""

    node_selected = Signal(str, dict)  # node_type, suggested_config

    def show_suggestions(self, suggestions: List[NodeSuggestion]):
        self._suggestion_list.clear()
        for suggestion in suggestions:
            item = QListWidgetItem(
                f"{suggestion.node_type} - {suggestion.reason}"
            )
            item.setData(Qt.UserRole, suggestion)
            self._suggestion_list.addItem(item)

        self.show()
```

### 4.4 Streaming Response UI

**Priority**: Medium | **Effort**: Low

```python
class StreamingWorkflowGenerator:
    """Generates workflows with streaming feedback."""

    async def generate_with_streaming(
        self,
        prompt: str,
        on_token: Callable[[str], None],
        on_node: Callable[[Dict], None],
        on_complete: Callable[[Dict], None]
    ):
        # Phase 1: Stream planning thoughts
        on_token("Analyzing your request...\n")

        async for token in self._stream_plan(prompt):
            on_token(token)

        on_token("\n\nGenerating workflow nodes...\n")

        # Phase 2: Generate and emit nodes incrementally
        nodes = await self._generate_nodes_incrementally(prompt)
        for node in nodes:
            on_node(node)
            on_token(f"+ Added {node['node_type']}\n")

        # Phase 3: Connect and validate
        on_token("\nConnecting nodes and validating...\n")
        workflow = await self._connect_and_validate(nodes)

        on_complete(workflow)
```

**PySide6 Integration**:

```python
class StreamingChatArea(ChatArea):
    """Chat area with streaming response support."""

    def start_streaming_response(self):
        """Prepare for streaming response."""
        self._streaming_bubble = self._create_ai_bubble()
        self._streaming_text = ""

    def append_stream_token(self, token: str):
        """Append token to streaming response."""
        self._streaming_text += token
        self._streaming_bubble.setText(self._streaming_text)
        self._scroll_to_bottom()

    def finish_streaming_response(self):
        """Finalize streaming response."""
        self._streaming_bubble = None
```

### 4.5 Visual Workflow Preview

**Priority**: Medium | **Effort**: High

```python
class WorkflowPreviewWidget(QWidget):
    """Mini node graph preview of generated workflow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene()
        self._view = QGraphicsView(self._scene)
        self._nodes: Dict[str, QGraphicsItem] = {}
        self._connections: List[QGraphicsLineItem] = []

    def set_workflow(self, workflow: Dict):
        """Render workflow as mini graph."""
        self._scene.clear()
        self._nodes.clear()
        self._connections.clear()

        # Create node rectangles
        for node_id, node_data in workflow.get("nodes", {}).items():
            item = self._create_node_item(node_id, node_data)
            self._scene.addItem(item)
            self._nodes[node_id] = item

        # Create connection lines
        for conn in workflow.get("connections", []):
            line = self._create_connection_line(conn)
            self._scene.addItem(line)
            self._connections.append(line)

        # Fit view
        self._view.fitInView(
            self._scene.itemsBoundingRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

    def _create_node_item(self, node_id: str, data: Dict) -> QGraphicsItem:
        """Create visual representation of a node."""
        node_type = data.get("node_type", "Unknown")
        pos = data.get("position", [0, 0])

        # Create rectangle with label
        rect = QGraphicsRectItem(0, 0, 80, 30)
        rect.setPos(pos[0] / 5, pos[1] / 5)  # Scale down
        rect.setBrush(self._get_node_color(node_type))

        # Add label
        label = QGraphicsTextItem(node_type[:12], rect)
        label.setFont(QFont("Arial", 6))

        return rect
```

---

## Part 5: Python/PySide6 Integration Architecture

### Proposed Architecture

```
+------------------------------------------------------------------+
|                     PRESENTATION LAYER                            |
|  +-------------------+  +--------------------+  +----------------+ |
|  | AIAssistantDock   |  | WorkflowPreviewWgt |  | NodeSuggestPop | |
|  | (Chat UI)         |  | (Mini Graph)       |  | (Autocomplete) | |
|  +-------------------+  +--------------------+  +----------------+ |
|           |                      |                     |          |
|           v                      v                     v          |
|  +-----------------------------------------------------------+   |
|  |              ConversationalWorkflowController             |   |
|  +-----------------------------------------------------------+   |
+------------------------------------------------------------------+
                              |
+------------------------------------------------------------------+
|                     APPLICATION LAYER                             |
|  +--------------------+  +-------------------+  +---------------+ |
|  | ConversationalAgent|  | IntentClassifier  |  | TemplateLib   | |
|  +--------------------+  +-------------------+  +---------------+ |
|           |                      |                     |          |
|           v                      v                     v          |
|  +-----------------------------------------------------------+   |
|  |                    SmartWorkflowAgent                     |   |
|  |    (Generate -> Validate -> Repair -> Return)             |   |
|  +-----------------------------------------------------------+   |
|           |                                                       |
|           v                                                       |
|  +-----------------------------------------------------------+   |
|  |              SuggestionEngine + DSLCompiler               |   |
|  +-----------------------------------------------------------+   |
+------------------------------------------------------------------+
                              |
+------------------------------------------------------------------+
|                     INFRASTRUCTURE LAYER                          |
|  +------------------+  +------------------+  +------------------+ |
|  | LLMResourceMgr   |  | HeadlessValidator|  | RegistryDumper  | |
|  | (Multi-provider) |  | (Qt + Domain)    |  | (Node Manifest) | |
|  +------------------+  +------------------+  +------------------+ |
+------------------------------------------------------------------+
```

### Key Classes

```python
# Controller for managing conversation and workflow generation
class ConversationalWorkflowController(QObject):
    """
    Main controller bridging UI and workflow generation.

    Signals:
        workflow_updated: Emitted when workflow changes
        suggestion_available: Emitted when suggestions ready
        streaming_token: Emitted for each streaming token
    """

    workflow_updated = Signal(dict)
    suggestion_available = Signal(list)  # List[NodeSuggestion]
    streaming_token = Signal(str)
    generation_progress = Signal(str, int)  # stage, progress

    def __init__(self, parent=None):
        super().__init__(parent)
        self._agent = ConversationalWorkflowAgent(SmartWorkflowAgent())
        self._suggestion_engine = WorkflowSuggestionEngine()
        self._intent_classifier = IntentClassifier()

    async def handle_user_input(self, text: str):
        """Process user input and generate appropriate response."""
        # Classify intent
        intent = await self._intent_classifier.classify(text)

        # If we have a template for this intent, offer it
        if intent.category in WORKFLOW_TEMPLATES:
            template = WORKFLOW_TEMPLATES[intent.category]
            self.template_suggested.emit(template)

        # Generate workflow
        response = await self._agent.process_message(text)

        if response.workflow:
            self.workflow_updated.emit(response.workflow)

        return response

    async def request_suggestions(self, cursor_node_id: str):
        """Get suggestions for next nodes."""
        workflow = self._agent.current_workflow
        if workflow:
            suggestions = await self._suggestion_engine.suggest_next_nodes(
                workflow,
                cursor_node_id
            )
            self.suggestion_available.emit(suggestions)
```

### Thread Safety

```python
class WorkflowGenerationThread(QThread):
    """
    Background thread for AI workflow generation.

    Handles async LLM calls without blocking Qt event loop.
    Emits signals for progress and completion.
    """

    # Signals
    progress = Signal(str, int)  # stage_name, percentage
    streaming_token = Signal(str)
    node_generated = Signal(dict)
    workflow_complete = Signal(object)  # WorkflowGenerationResult
    error = Signal(str)

    def __init__(
        self,
        controller: ConversationalWorkflowController,
        prompt: str,
        mode: str = "generate",  # generate, edit, suggest
        parent=None
    ):
        super().__init__(parent)
        self._controller = controller
        self._prompt = prompt
        self._mode = mode

    def run(self):
        """Execute generation in background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            if self._mode == "generate":
                result = loop.run_until_complete(
                    self._controller.handle_user_input(self._prompt)
                )
            elif self._mode == "suggest":
                result = loop.run_until_complete(
                    self._controller.request_suggestions(self._prompt)
                )

            self.workflow_complete.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
```

---

## Part 6: Implementation Roadmap

### Phase 1: Foundation (2-3 weeks)

| Task | Priority | Effort | Description |
|------|----------|--------|-------------|
| Structured Output Mode | P1 | Low | Use OpenAI/Anthropic JSON Schema mode |
| Intent Classifier | P1 | Low | Pattern + LLM-based intent recognition |
| Template Library | P1 | Low | 10-15 common workflow templates |
| Few-Shot Examples | P1 | Low | Add examples to prompts |

### Phase 2: Conversation (3-4 weeks)

| Task | Priority | Effort | Description |
|------|----------|--------|-------------|
| Conversation History | P1 | Medium | Maintain multi-turn context |
| Modification Intent | P1 | Medium | Detect and handle edit requests |
| Clarification Requests | P2 | Low | Ask for missing parameters |
| Workflow Diff Display | P2 | Medium | Show changes in UI |

### Phase 3: Suggestions (4-6 weeks)

| Task | Priority | Effort | Description |
|------|----------|--------|-------------|
| Node Suggestions | P2 | Medium | Suggest next nodes |
| Port Auto-Connect | P2 | Medium | Intelligent port matching |
| Suggestion Popup UI | P2 | Medium | PySide6 autocomplete widget |
| Connection Patterns DB | P3 | Low | Learn common connections |

### Phase 4: Advanced (6-8 weeks)

| Task | Priority | Effort | Description |
|------|----------|--------|-------------|
| CRPA-DSL | P3 | High | Intermediate workflow language |
| Visual Preview | P3 | High | Mini graph preview widget |
| Streaming Responses | P2 | Medium | Token-by-token display |
| Self-Healing Agent | P3 | High | Auto-fix broken workflows |

---

## Part 7: Metrics and Success Criteria

### Key Performance Indicators

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Generation Success Rate | ~70% | 90% | Valid workflow / attempts |
| Average Attempts | 1.5-2 | 1.2 | Retries before success |
| Time to First Node | ~3s | <1s | Streaming first response |
| Intent Recognition | N/A | 85% | Correct template suggested |
| User Modification Rate | N/A | <30% | Workflows needing edits |

### Testing Strategy

```python
# Test suite for AI workflow generation
class TestAIWorkflowGeneration:

    @pytest.mark.parametrize("prompt,expected_nodes", [
        ("Login to example.com", ["GoToURLNode", "TypeTextNode", "ClickElementNode"]),
        ("Download PDF from email", ["IMAPConnectNode", "ListEmailsNode", "DownloadAttachmentNode"]),
        ("Convert CSV to Excel", ["ReadCSVNode", "WriteExcelNode"]),
    ])
    async def test_basic_generation(self, prompt, expected_nodes):
        agent = SmartWorkflowAgent()
        result = await agent.generate_workflow(prompt)
        assert result.success
        node_types = [n["node_type"] for n in result.workflow["nodes"].values()]
        for expected in expected_nodes:
            assert any(expected in nt for nt in node_types)

    async def test_multi_turn_modification(self):
        agent = ConversationalWorkflowAgent()

        # Initial generation
        r1 = await agent.process_message("Create a web scraping workflow")
        assert r1.workflow is not None

        # Modification
        r2 = await agent.process_message("Add error handling")
        assert "TryNode" in str(r2.workflow)

        # Another modification
        r3 = await agent.process_message("Save results to Excel instead of JSON")
        assert "WriteExcelNode" in str(r3.workflow)
```

---

## Part 8: References and Sources

### Competitor Documentation
- [UiPath Autopilot - Text to Workflow](https://docs.uipath.com/autopilot/other/latest/overview/text-to-workflow)
- [UiPath Autopilot - Generating Automations](https://docs.uipath.com/autopilot/other/latest/user-guide/autopilot-for-developers)
- [Power Automate Copilot Overview](https://learn.microsoft.com/en-us/power-automate/copilot-overview)
- [Power Automate 2025 Release Wave 1](https://learn.microsoft.com/en-us/power-platform/release-plan/2025wave1/power-automate/)

### Technical Resources
- [JSON Schema for Structured Outputs](https://blog.promptlayer.com/how-json-schema-works-for-structured-outputs-and-tool-integration/)
- [Structured Output from LLMs](https://medium.com/@twardziak.p/structured-output-from-llms-more-than-just-prompt-engineering-b47408a0f8d3)
- [LangGraph Multi-Agent Workflows](https://blog.langchain.com/langgraph-multi-agent-workflows/)
- [Building Agentic Workflows with LangGraph](https://www.upnxtblog.com/index.php/2025/11/18/building-agentic-ai-systems-with-langchain-and-langgraph/)
- [Mastering JSON Prompting for LLMs](https://machinelearningmastery.com/mastering-json-prompting-for-llms/)

### CasareRPA Current Implementation
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\infrastructure\ai\smart_agent.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\ai\prompts.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\ai\config.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\application\use_cases\generate_workflow.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\domain\schemas\workflow_ai.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\presentation\canvas\ui\widgets\ai_assistant\dock.py`

---

## Conclusion

CasareRPA has a solid foundation for AI-powered workflow generation with the `SmartWorkflowAgent` and `AIAssistantDock`. The primary opportunities for enhancement are:

1. **Multi-turn Conversation**: Allow iterative refinement of workflows
2. **Intent Templates**: Speed up common use cases with pre-built templates
3. **Auto-Suggestions**: Intelligent node and connection recommendations
4. **Structured Output**: Use provider JSON Schema mode for reliability
5. **Visual Preview**: Show mini graph of generated workflow

The recommended implementation prioritizes high-impact, lower-effort improvements first (structured output, intent templates) before tackling more complex features (DSL, visual preview).

Key success metrics should focus on:
- Generation success rate (target: 90%+)
- Average retry attempts (target: <1.5)
- User modification rate (target: <30%)
