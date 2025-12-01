# AI/ML Integration Research for CasareRPA

**Date**: 2025-12-01 | **Status**: Research Complete

---

## Competitor AI Features

### UiPath AI Center
| Feature | Description | CasareRPA Gap |
|---------|-------------|---------------|
| AI Center | ML model deployment, training, management | No ML model management |
| Document Understanding | AI-powered OCR + classification + extraction | Basic OCR only |
| AI Computer Vision | ML-based element detection without selectors | Selector-based only |
| Generative AI (Claude 3.5) | LLM integration for Autopilot, Clipboard AI | No LLM integration |
| ML Skills | Consume ML models in workflows | No ML skill nodes |
| Auto-healing | AI fixes broken selectors | Manual selector repair |

**Sources**: [UiPath AI Center Docs](https://docs.uipath.com/ai-center/automation-cloud/latest/user-guide/about-ai-center), [UiPath Document Understanding](https://docs.uipath.com/document-understanding/automation-cloud/latest/release-notes/release-notes-cloud-june-2025)

### Microsoft Power Automate AI Builder
| Feature | Description | CasareRPA Gap |
|---------|-------------|---------------|
| Generative Actions | LLM-driven steps in cloud flows | No LLM nodes |
| GPT Prompts | Reusable prompt components | No prompt system |
| Document Intelligence | Azure AI for document processing | Basic OCR |
| Copilot Expression Editing | NLP for workflow expressions | Code-only |
| Form Recognizer | Pre-built document models | Manual extraction |

**Sources**: [AI Builder 2025](https://learn.microsoft.com/en-us/power-platform/release-plan/2025wave1/ai-builder/), [Power Automate 2025](https://learn.microsoft.com/en-us/power-platform/release-plan/2025wave1/power-automate/)

### Automation Anywhere
| Feature | Description | CasareRPA Gap |
|---------|-------------|---------------|
| IQ Bot (until 2026) | Cognitive document processing | Basic OCR |
| Document Automation | Replacement for IQ Bot | No equivalent |
| Self-learning extraction | Learns from human corrections | Static extraction |
| Multi-language OCR | 190 languages | Limited languages |

**Note**: IQ Bot sunset March 2026, transitioning to Document Automation.

**Sources**: [IQ Bot Sunset](https://community.automationanywhere.com/product-updates/iq-bot-will-officially-sunset-in-march-2026-89560)

---

## LLM Integration Opportunities

### Integration Patterns

#### 1. LLM Action Nodes
```
LLMCompletionNode       - Send prompt, get response
LLMChatNode             - Multi-turn conversation
LLMExtractDataNode      - Extract structured data from text
LLMSummarizeNode        - Summarize long content
LLMTranslateNode        - Language translation
LLMClassifyNode         - Text classification
```

#### 2. Supported Providers
| Provider | Model | Use Case | Python Package |
|----------|-------|----------|----------------|
| OpenAI | GPT-4o | General, fast | `openai` |
| Anthropic | Claude 3.5 | Complex reasoning, 200k context | `anthropic` |
| Google | Gemini Pro | Multimodal, long context | `google-generativeai` |
| Local | LLaMA, Mistral | Privacy, offline | `ollama`, `llama-cpp-python` |

#### 3. LangChain Integration
```python
# Benefits for CasareRPA:
- Unified API for multiple LLMs
- Chain composition (prompt -> LLM -> output)
- Memory/context management
- Tool/function calling
- Agent orchestration
```

**Architecture Fit**:
```
nodes/ai/
  llm_nodes.py          - LLM completion nodes
  prompt_nodes.py       - Prompt template nodes
  chain_nodes.py        - LangChain integration

infrastructure/resources/
  llm_resource_manager.py  - API key management, rate limiting
```

**Sources**: [LangChain OpenAI](https://python.langchain.com/docs/integrations/llms/openai/), [Best LLMs for Agents 2025](https://visionvix.com/best-llm-for-agents/)

---

## Computer Vision Opportunities

### Current State in CasareRPA
- `OCRExtractTextNode` - Basic text extraction
- `CaptureScreenshotNode` - Screen capture
- `CompareImagesNode` - Image comparison
- Selector-based element detection

### AI Computer Vision Features to Add

#### 1. ML-Based Element Detection
| Feature | Description | Benefit |
|---------|-------------|---------|
| Element Detection | Find buttons, fields by visual appearance | Works on any UI |
| Anchor System | Multi-anchor element identification | Reliable targeting |
| Fuzzy Text Matching | Find text with OCR tolerance | Handle OCR errors |
| Icon Recognition | Match icons/images | Visual UI automation |

#### 2. Implementation Approach
```python
# Use pre-trained models:
- YOLO/Faster R-CNN for UI element detection
- Tesseract + EasyOCR for text
- CLIP for icon/image matching

# Node structure:
nodes/ai/vision/
  element_detector_node.py    - Find UI elements by vision
  visual_click_node.py        - Click by visual recognition
  visual_wait_node.py         - Wait for visual element
  image_search_node.py        - Find image in screen
```

#### 3. VDI/Citrix Support
ML-based detection enables automation on:
- Citrix virtual desktops
- VMware environments
- Remote desktop sessions
- Legacy applications without DOM

**Market**: 68% of RPA enterprises use computer vision AI modules (2025).

**Sources**: [UiPath AI Computer Vision](https://www.uipath.com/product/ai-computer-vision-for-rpa), [RPA Computer Vision](https://research.aimultiple.com/rpa-computer-vision/)

---

## Document Processing (IDP)

### IDP Market Context
- Market: $7.89B (2024) -> $66.68B (2032)
- CAGR: 30.1%
- 50%+ solutions incorporate AI/NLP (2024)

### Features to Implement

#### 1. Document Classification
```python
ClassifyDocumentNode:
  - Invoice, Receipt, Contract, Form detection
  - Multi-page document splitting
  - Pre-trained + custom models
```

#### 2. Intelligent Extraction
```python
ExtractDocumentDataNode:
  inputs:
    - document: Image/PDF
    - template: Optional schema
  outputs:
    - structured_data: Dict
    - confidence: Float
    - validation_flags: List
```

#### 3. Document Types to Support
| Document Type | Fields to Extract |
|---------------|-------------------|
| Invoice | vendor, date, amount, line_items |
| Receipt | store, date, total, items |
| Contract | parties, dates, terms, signatures |
| ID/Passport | name, dob, number, expiry |
| Form | field_name -> value mapping |

#### 4. Technology Stack
```
Primary: Azure AI Document Intelligence or Google Document AI
Fallback: Open-source (LayoutLM, Donut model)
OCR: Tesseract, RapidOCR (already supported), EasyOCR
```

#### 5. Architecture
```
nodes/document/
  classify_document_node.py
  extract_document_node.py
  validate_document_node.py

infrastructure/resources/
  document_ai_manager.py  - Provider abstraction
```

**Sources**: [IDP Market Report](https://www.fortunebusinessinsights.com/intelligent-document-processing-market-108590), [AWS Document Processing](https://aws.amazon.com/ai/generative-ai/use-cases/document-processing/)

---

## Natural Language Automation

### Voice/Text Workflow Creation

#### 1. Natural Language to Workflow
```
User: "Every day at 9am, check email for invoices and save attachments to shared drive"

System generates:
  - ScheduleTrigger (cron: "0 9 * * *")
  - ReadEmailNode (filter: "attachment:pdf")
  - ForEachNode (emails)
    - SaveAttachmentNode (path: "shared_drive/invoices")
```

#### 2. Implementation Levels

| Level | Feature | Complexity |
|-------|---------|------------|
| 1 | Text description -> workflow JSON | Medium |
| 2 | Voice input -> text -> workflow | Medium+ |
| 3 | Conversational refinement | High |
| 4 | Self-healing workflows | Very High |

#### 3. Technical Approach
```python
# Step 1: LLM prompt engineering
prompt = f"""
Convert this automation request to CasareRPA workflow JSON:
Request: {user_input}
Available nodes: {node_catalog}
Output format: {workflow_schema}
"""

# Step 2: Validation layer
- Schema validation
- Node existence check
- Connection compatibility

# Step 3: Optional voice
- Speech-to-text (Whisper, Azure Speech)
- Text-to-workflow
```

#### 4. Agent SOPs Pattern
Following AWS Strands pattern:
```markdown
# SOP: Invoice Processing Agent

## Trigger
- Email received with PDF attachment

## Steps
1. Extract sender email address
2. Download PDF attachment
3. Classify document type
4. If invoice:
   a. Extract vendor, amount, date
   b. Save to database
   c. Notify accounting
5. If not invoice:
   a. Forward to general inbox
```

**Sources**: [AWS Strands Agent SOPs](https://aws.amazon.com/blogs/opensource/introducing-strands-agent-sops-natural-language-workflows-for-ai-agents/), [n8n AI Workflow](https://n8n.io)

---

## Recommended AI Roadmap

### Phase 1: Foundation (2-3 months)
**Priority**: HIGH | **Effort**: Medium

| Task | Description |
|------|-------------|
| LLM Nodes | Basic OpenAI/Claude completion nodes |
| API Key Management | Secure credential storage for AI providers |
| Prompt Templates | Reusable prompt node with variables |

**Deliverables**:
- `LLMCompletionNode`, `LLMChatNode`
- `LLMResourceManager` in infrastructure
- Provider abstraction (OpenAI, Anthropic, local)

```
nodes/ai/
  __init__.py
  llm_nodes.py
  prompt_nodes.py
infrastructure/resources/
  llm_resource_manager.py
```

### Phase 2: Document Intelligence (2-3 months)
**Priority**: HIGH | **Effort**: High

| Task | Description |
|------|-------------|
| Document Classification | Auto-detect document type |
| Smart Extraction | LLM-powered data extraction |
| Validation Nodes | Confidence scoring, human review |

**Deliverables**:
- `ClassifyDocumentNode`
- `ExtractDocumentDataNode` (LLM-based)
- `ValidateExtractionNode`
- Integration with existing OCR nodes

### Phase 3: Visual AI (3-4 months)
**Priority**: MEDIUM | **Effort**: High

| Task | Description |
|------|-------------|
| Element Detection Model | Train/use YOLO for UI elements |
| Visual Click Node | Click by appearance, not selector |
| Anchor System | Multi-anchor element identification |
| Icon Matching | Find elements by icon |

**Deliverables**:
- `VisualElementDetectorNode`
- `VisualClickNode`, `VisualTypeNode`
- `ImageSearchNode`
- VDI/Citrix compatibility

### Phase 4: NL Workflow Creation (3-4 months)
**Priority**: MEDIUM | **Effort**: Very High

| Task | Description |
|------|-------------|
| Workflow Generator | LLM prompt -> workflow JSON |
| Node Catalog Export | Auto-generate node descriptions for LLM |
| Validation Layer | Ensure generated workflows are valid |
| UI Integration | Text input in canvas for quick automation |

**Deliverables**:
- `WorkflowGeneratorService`
- Natural language input panel in UI
- Workflow validation and preview

### Phase 5: Agentic Automation (4-6 months)
**Priority**: LOW (future) | **Effort**: Very High

| Task | Description |
|------|-------------|
| Self-healing | AI fixes broken selectors/workflows |
| Decision Agents | LLM decides next action |
| SOP Execution | Natural language procedure execution |
| Voice Commands | Speech-to-automation |

---

## Python Libraries to Integrate

### Required Dependencies
```toml
# pyproject.toml additions

[project.optional-dependencies]
ai = [
    "openai>=1.0.0",
    "anthropic>=0.7.0",
    "langchain>=0.1.0",
    "langchain-openai>=0.0.5",
    "langchain-anthropic>=0.0.5",
]
vision = [
    "ultralytics>=8.0.0",  # YOLO
    "opencv-python>=4.8.0",
    "easyocr>=1.7.0",
]
document = [
    "azure-ai-documentintelligence>=1.0.0",
    # OR
    "google-cloud-documentai>=2.0.0",
]
voice = [
    "openai-whisper>=20230918",
    # OR
    "azure-cognitiveservices-speech>=1.30.0",
]
```

### Existing Compatible Stack
- `pillow` - Image processing (already used)
- `aiohttp` - Async HTTP (already used)
- `pydantic` - Schema validation (already used)

---

## CasareRPA Advantages for AI Integration

| Advantage | Impact |
|-----------|--------|
| Python-native | Direct LLM library integration |
| Async architecture | Non-blocking AI API calls |
| Node-based | Easy AI node composition |
| Clean DDD | AI in infrastructure layer |
| JSON workflows | LLM-friendly format |

---

## Open Questions

1. **Provider Strategy**: Single provider (OpenAI) or multi-provider from start?
2. **Cost Model**: How to handle AI API costs for users?
3. **Offline Support**: Priority for local LLM (Ollama) support?
4. **Training**: Allow users to fine-tune models?
5. **Privacy**: On-premise AI for sensitive data?

---

## Summary

| Category | Competitor Lead | CasareRPA Opportunity |
|----------|-----------------|----------------------|
| LLM Integration | UiPath (Claude), Power Automate (GPT) | Add LLM nodes with LangChain |
| Document AI | All majors | LLM-based extraction (simpler) |
| Computer Vision | UiPath (strongest) | YOLO-based element detection |
| NL Automation | Power Automate Copilot | Workflow generation via LLM |
| Voice | Emerging (n8n, aiOla) | Future consideration |

**Recommendation**: Start with Phase 1 (LLM Nodes) - highest ROI, lowest risk, enables Phases 2-4.

---

*Research conducted: 2025-12-01*
*Sources: UiPath, Microsoft, Automation Anywhere, industry reports*
