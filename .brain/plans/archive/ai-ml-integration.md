# AI/ML Integration Research for CasareRPA

**Date**: 2025-12-01 | **Status**: COMPLETE

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

---

## Detailed Library/Service Recommendations

### Document AI (OCR, Form Extraction, Invoice Processing)

#### Cloud Services (Production-Ready)

| Service | Best For | Pricing | Integration |
|---------|----------|---------|-------------|
| **Azure Document Intelligence** | Enterprise, high accuracy | $1.50/1000 pages | `azure-ai-documentintelligence` |
| **Google Document AI** | Multi-language, custom models | $1.50/1000 pages | `google-cloud-documentai` |
| **AWS Textract** | AWS ecosystem, forms/tables | $1.50/1000 pages | `boto3` |
| **OpenAI Vision (GPT-4o)** | Flexible extraction, complex layouts | Per-token | `openai` |

#### Open Source Alternatives

| Library | Use Case | Pros | Cons |
|---------|----------|------|------|
| **Tesseract 5.x** | General OCR | Free, offline, 100+ languages | Setup required, accuracy varies |
| **EasyOCR** | Multi-language | Easy setup, GPU support | Slower on CPU |
| **RapidOCR** | Chinese/Japanese | Very fast, lightweight | Limited languages |
| **PaddleOCR** | Production OCR | State-of-art accuracy | Large model |
| **LayoutLMv3** | Document understanding | Structural analysis | Complex setup |
| **Donut** | End-to-end extraction | No OCR needed | GPU required |

#### CasareRPA Integration Pattern

```python
# nodes/document/document_ai_nodes.py

@executable_node
class IntelligentOCRNode(BaseNode):
    """Multi-engine OCR with automatic engine selection."""

    def __init__(self, config: Dict = None):
        default_config = {
            "engine": "auto",  # auto, tesseract, easyocr, rapidocr, cloud
            "cloud_provider": None,  # azure, google, aws
            "languages": ["en"],
            "detect_layout": True,
        }
        super().__init__(config=default_config | (config or {}))

    async def execute(self, context) -> Dict[str, Any]:
        image = self.get_input_value("image")
        engine = self.config["engine"]

        # Auto-select best engine based on content
        if engine == "auto":
            engine = await self._detect_best_engine(image)

        text = await self._extract_with_engine(image, engine)
        return {"text": text, "engine_used": engine, "success": True}


@executable_node
class ExtractInvoiceNode(BaseNode):
    """Extract structured data from invoices using AI."""

    INVOICE_SCHEMA = {
        "vendor_name": str,
        "invoice_number": str,
        "date": str,
        "due_date": str,
        "total_amount": float,
        "currency": str,
        "line_items": list,
        "tax_amount": float,
    }

    async def execute(self, context) -> Dict[str, Any]:
        document = self.get_input_value("document")
        provider = self.config.get("provider", "openai")

        if provider == "azure":
            result = await self._azure_invoice_extract(document)
        elif provider == "openai":
            result = await self._openai_vision_extract(document)
        else:
            result = await self._local_extract(document)

        return {"invoice_data": result, "success": True}
```

### Computer Vision (UI Element Detection, Image Classification)

#### Existing CasareRPA Capabilities
- `CVHealer` - Template matching, OCR text detection (cv_healer.py)
- `CompareImagesNode` - Histogram, pixel, SSIM comparison
- `OCRExtractTextNode` - Multi-engine OCR support

#### Recommended Additions

| Feature | Library | Use Case |
|---------|---------|----------|
| **UI Element Detection** | `ultralytics` (YOLO) | Find buttons, inputs by appearance |
| **Icon Matching** | `opencv-python` + SIFT/ORB | Match icons across resolutions |
| **Screen Change Detection** | `imagehash` | Detect UI changes for automation triggers |
| **Text in Images** | `paddleocr` or `easyocr` | Extract text from screenshots |
| **Semantic Similarity** | `clip-interrogator` | Match elements by description |

#### Pre-trained Models for RPA

```python
# Available YOLO-trained models for UI elements
UI_DETECTION_MODELS = {
    "icon-detect": "https://huggingface.co/nickmuchi/icon-detect",  # 30 icon classes
    "rico-layout": "https://github.com/nickmuchi/RICO-UI-Detection",  # Android UI
    "uied": "https://github.com/nickmuchi/UIED",  # General UI elements
}

# CasareRPA node implementation
@executable_node
class VisualElementDetectorNode(BaseNode):
    """Detect UI elements by visual appearance using YOLO."""

    def __init__(self, config: Dict = None):
        default_config = {
            "model": "yolov8n",  # nano model for speed
            "confidence": 0.5,
            "element_types": ["button", "input", "checkbox", "dropdown"],
        }
        super().__init__(config=default_config | (config or {}))

    async def execute(self, context) -> Dict[str, Any]:
        from ultralytics import YOLO

        image = self.get_input_value("image")
        model = YOLO(self.config["model"])
        results = model(image, conf=self.config["confidence"])

        elements = []
        for r in results[0].boxes:
            elements.append({
                "type": model.names[int(r.cls)],
                "confidence": float(r.conf),
                "bbox": r.xyxy.tolist()[0],
                "center": self._get_center(r.xyxy),
            })

        return {"elements": elements, "count": len(elements), "success": True}
```

### NLP (Text Extraction, Sentiment, Entity Recognition)

#### Library Comparison

| Library | Speed | Accuracy | Size | Use Case |
|---------|-------|----------|------|----------|
| **spaCy** | Fast | Good | 50MB-500MB | Production NER, parsing |
| **Hugging Face Transformers** | Slow | Best | 500MB+ | SOTA accuracy needed |
| **Flair** | Medium | Good | 200MB | Sequence labeling |
| **TextBlob** | Fast | Basic | 10MB | Simple sentiment |
| **LLM (GPT/Claude)** | API | Best | Cloud | Complex extraction |

#### CasareRPA NLP Nodes

```python
# nodes/ai/nlp_nodes.py

@executable_node
class ExtractEntitiesNode(BaseNode):
    """Extract named entities using spaCy or LLM."""

    ENTITY_TYPES = ["PERSON", "ORG", "GPE", "DATE", "MONEY", "EMAIL", "PHONE"]

    async def execute(self, context) -> Dict[str, Any]:
        text = self.get_input_value("text")
        engine = self.config.get("engine", "spacy")

        if engine == "spacy":
            import spacy
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(text)
            entities = [{"text": ent.text, "type": ent.label_} for ent in doc.ents]
        elif engine == "llm":
            entities = await self._llm_extract(text)

        return {"entities": entities, "success": True}


@executable_node
class ClassifyTextNode(BaseNode):
    """Classify text into categories."""

    async def execute(self, context) -> Dict[str, Any]:
        text = self.get_input_value("text")
        categories = self.get_input_value("categories")  # ["positive", "negative", "neutral"]

        # Use zero-shot classification
        from transformers import pipeline
        classifier = pipeline("zero-shot-classification")
        result = classifier(text, categories)

        return {
            "category": result["labels"][0],
            "confidence": result["scores"][0],
            "all_scores": dict(zip(result["labels"], result["scores"])),
            "success": True,
        }


@executable_node
class SummarizeTextNode(BaseNode):
    """Summarize long text using LLM."""

    async def execute(self, context) -> Dict[str, Any]:
        text = self.get_input_value("text")
        max_length = self.config.get("max_length", 100)
        provider = self.config.get("provider", "openai")

        llm = context.resources.get("llm_client")
        summary = await llm.summarize(text, max_length=max_length)

        return {"summary": summary, "original_length": len(text), "success": True}
```

### Process Mining (Workflow Optimization)

#### Approach for CasareRPA

| Feature | Implementation |
|---------|----------------|
| **Execution Analytics** | Track node execution times, success rates |
| **Bottleneck Detection** | Identify slow nodes, suggest parallelization |
| **Failure Pattern Mining** | Cluster errors, suggest fixes |
| **Workflow Similarity** | Compare workflows, suggest reusable components |

```python
# infrastructure/analytics/process_mining.py

class WorkflowAnalyzer:
    """Analyze workflow execution patterns for optimization."""

    async def analyze_execution_history(self, workflow_id: str, days: int = 30) -> Dict:
        executions = await self.repo.get_executions(workflow_id, days)

        return {
            "total_runs": len(executions),
            "success_rate": self._calculate_success_rate(executions),
            "avg_duration": self._avg_duration(executions),
            "bottleneck_nodes": self._find_bottlenecks(executions),
            "failure_patterns": self._cluster_failures(executions),
            "optimization_suggestions": self._generate_suggestions(executions),
        }

    def _find_bottlenecks(self, executions) -> List[Dict]:
        """Find nodes that consistently take longest."""
        node_times = defaultdict(list)
        for ex in executions:
            for node_id, timing in ex.node_timings.items():
                node_times[node_id].append(timing)

        bottlenecks = []
        for node_id, times in node_times.items():
            avg_time = sum(times) / len(times)
            if avg_time > self.threshold_ms:
                bottlenecks.append({
                    "node_id": node_id,
                    "avg_time_ms": avg_time,
                    "suggestion": self._suggest_optimization(node_id, avg_time),
                })

        return sorted(bottlenecks, key=lambda x: -x["avg_time_ms"])[:5]
```

### Intelligent Automation (Decision Making, Anomaly Detection)

#### AI-Powered Decision Nodes

```python
# nodes/ai/decision_nodes.py

@executable_node
class AIDecisionNode(BaseNode):
    """Make decisions using LLM reasoning."""

    async def execute(self, context) -> Dict[str, Any]:
        data = self.get_input_value("data")
        options = self.get_input_value("options")  # ["approve", "reject", "escalate"]
        criteria = self.config.get("criteria", "")

        prompt = f"""
        Based on the following data and criteria, choose the best option.

        Data: {data}
        Criteria: {criteria}
        Options: {options}

        Respond with JSON: {{"decision": "option", "confidence": 0.0-1.0, "reasoning": "..."}}
        """

        llm = context.resources.get("llm_client")
        response = await llm.complete(prompt, json_mode=True)

        return {
            "decision": response["decision"],
            "confidence": response["confidence"],
            "reasoning": response["reasoning"],
            "success": True,
        }


@executable_node
class AnomalyDetectorNode(BaseNode):
    """Detect anomalies in data patterns."""

    async def execute(self, context) -> Dict[str, Any]:
        data = self.get_input_value("data")
        baseline = self.get_input_value("baseline")  # Historical data
        threshold = self.config.get("threshold", 2.0)  # Std deviations

        from sklearn.ensemble import IsolationForest
        import numpy as np

        model = IsolationForest(contamination=0.1)
        model.fit(np.array(baseline).reshape(-1, 1))

        predictions = model.predict(np.array(data).reshape(-1, 1))
        anomalies = [d for d, p in zip(data, predictions) if p == -1]

        return {
            "is_anomaly": len(anomalies) > 0,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "success": True,
        }
```

---

## Recommended Dependencies

### pyproject.toml Additions

```toml
[project.optional-dependencies]
# LLM Integration (Phase 1)
ai = [
    "openai>=1.12.0",
    "anthropic>=0.18.0",
    "langchain>=0.1.5",
    "langchain-openai>=0.0.5",
    "langchain-anthropic>=0.1.0",
    "tiktoken>=0.5.0",
]

# Computer Vision (Phase 3)
vision = [
    "ultralytics>=8.1.0",       # YOLO models
    "opencv-python>=4.9.0",     # Image processing
    "easyocr>=1.7.0",           # Multi-language OCR
    "imagehash>=4.3.0",         # Perceptual hashing
]

# Document AI (Phase 2)
document = [
    "azure-ai-documentintelligence>=1.0.0b1",
    "pytesseract>=0.3.10",
    "pdf2image>=1.17.0",
    "python-docx>=1.1.0",
    "openpyxl>=3.1.0",
]

# NLP (Phase 2)
nlp = [
    "spacy>=3.7.0",
    "transformers>=4.37.0",
    "sentence-transformers>=2.3.0",
]

# Analytics (Phase 4)
analytics = [
    "scikit-learn>=1.4.0",
    "pandas>=2.2.0",
]

# All AI features
ai-full = [
    "casare-rpa[ai,vision,document,nlp,analytics]",
]
```

---

## Architecture Integration

### File Structure

```
src/casare_rpa/
  nodes/
    ai/
      __init__.py
      llm_nodes.py          # LLMCompletionNode, LLMChatNode
      prompt_nodes.py       # PromptTemplateNode
      nlp_nodes.py          # ExtractEntitiesNode, ClassifyTextNode
      decision_nodes.py     # AIDecisionNode, AnomalyDetectorNode
    document/
      __init__.py
      ocr_nodes.py          # IntelligentOCRNode
      extraction_nodes.py   # ExtractInvoiceNode, ExtractFormNode
      classification_nodes.py  # ClassifyDocumentNode
    vision/
      __init__.py
      detection_nodes.py    # VisualElementDetectorNode
      matching_nodes.py     # IconMatchNode, TemplateMatchNode
  infrastructure/
    resources/
      llm_resource_manager.py    # API key management, provider switching
      document_ai_manager.py     # Cloud document AI abstraction
    analytics/
      process_mining.py          # Execution analytics
```

### Resource Manager Pattern

```python
# infrastructure/resources/llm_resource_manager.py

class LLMResourceManager:
    """Manage LLM API connections with rate limiting and fallback."""

    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "local": OllamaProvider,
    }

    def __init__(self, config: Dict):
        self.primary = config.get("primary_provider", "openai")
        self.fallback = config.get("fallback_provider", "anthropic")
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.get("rpm", 60)
        )

    async def complete(self, prompt: str, **kwargs) -> str:
        await self.rate_limiter.acquire()

        try:
            return await self._providers[self.primary].complete(prompt, **kwargs)
        except Exception as e:
            if self.fallback:
                return await self._providers[self.fallback].complete(prompt, **kwargs)
            raise
```

---

## Implementation Priority Matrix

| Phase | Features | Dependencies | Effort | Impact |
|-------|----------|--------------|--------|--------|
| 1 | LLM nodes (GPT/Claude) | openai, anthropic | Low | High |
| 1 | Prompt templates | None | Low | Medium |
| 2 | Document extraction (LLM-based) | openai | Low | High |
| 2 | NLP entity extraction | spacy | Medium | Medium |
| 3 | Visual element detection | ultralytics, opencv | High | High |
| 3 | Enhanced OCR | easyocr | Medium | Medium |
| 4 | Process mining | pandas, sklearn | Medium | Low |
| 5 | Agentic automation | langchain | High | High |

---

## Quick Start Implementation

### Minimal LLM Integration (1-2 days)

```python
# 1. Add dependency
# pip install openai anthropic

# 2. Create simple LLM node
@executable_node
class LLMCompletionNode(BaseNode):
    """Simple LLM completion node."""

    async def execute(self, context) -> Dict[str, Any]:
        from openai import AsyncOpenAI

        prompt = self.get_input_value("prompt")
        api_key = context.secrets.get("OPENAI_API_KEY")

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "response": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens,
            "success": True,
        }
```

---

## Open Questions (Resolved)

1. **Provider Strategy**: Start with OpenAI (most common), add Anthropic as fallback. Support local via Ollama.
2. **Cost Model**: Implement usage tracking in LLMResourceManager, show in UI.
3. **Offline Support**: Ollama support in Phase 1 for local LLM.
4. **Training**: Defer to Phase 5+ (fine-tuning complexity).
5. **Privacy**: On-premise via Ollama; enterprise customers can use Azure Private Endpoints.
