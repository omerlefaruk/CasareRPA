# CasareRPA Next Priorities Research

**Date**: 2025-12-01 | **Status**: COMPLETE
**Researcher**: rpa-research-specialist

---

## Executive Summary

After analyzing:
- Current codebase (v3.0, 3344+ tests, Clean DDD architecture)
- Archived research (AI/ML, Cloud Scaling, Enterprise Security)
- Competitor features (UiPath 2025, Power Automate 2025, Automation Anywhere 2025)
- Existing TODOs in codebase

**Key Finding**: The RPA market in 2025 is dominated by **Agentic AI** capabilities. All major competitors have pivoted to AI-first automation with natural language workflow creation, self-healing, and autonomous agents. CasareRPA has strong foundations but lacks these differentiating features.

---

## Competitor Analysis Summary (2025)

| Feature | UiPath | Power Automate | Automation Anywhere | CasareRPA |
|---------|--------|----------------|---------------------|-----------|
| AI Agent Builder | Agent Builder (50+ templates) | Copilot | PRE + Reasoning Agents | NONE |
| Natural Language Automation | ScreenPlay | Copilot NL | Process Reasoning Engine | NONE |
| Self-Healing Selectors | Adaptive selectors | AI-first healing | Near-real-time | Selector healing (basic) |
| Process Mining | Dashboards | Full suite | APA discovery | NONE |
| Document AI | Document Understanding | IDP (90%+ accuracy) | Advanced IDP | Basic OCR |
| LLM Integration | Claude 3.5, GPT-4 | Azure OpenAI | Multi-LLM | NONE |

**Sources**:
- [UiPath FUSION 2025 Announcements](https://www.uipath.com/blog/product-and-updates/fusion-2025-agentic-ai-biggest-product-announcements)
- [Power Automate 2025 Release Wave](https://learn.microsoft.com/en-us/power-platform/release-plan/2025wave1/power-automate/)
- [Automation Anywhere Process Reasoning Engine](https://www.globenewswire.com/news-release/2025/05/13/3080186/0/en/Automation-Anywhere-Takes-a-Step-Towards-Artificial-General-Intelligence-for-Work-with-Industry-s-First-Process-Reasoning-Engine.html)

---

## Prioritized Recommendations

### 1. LLM Integration Nodes (HIGHEST PRIORITY)

**Feature Name**: AI/LLM Action Nodes

**Why It Matters**:
- Every major competitor has LLM integration in 2025
- Enables intelligent document processing, data extraction, decision-making
- Foundation for all other AI features (agents, NL automation)
- Users expect AI capabilities in modern automation tools

**Technical Complexity**: MEDIUM
- Direct Python library integration (openai, anthropic)
- Follows existing node patterns
- Already researched in `.brain/plans/archive/ai-ml-integration.md`

**Dependencies/Prerequisites**:
- None - can start immediately
- Requires API key management (use existing SecretsManager)

**Scope** (files/components affected):
```
NEW FILES:
- src/casare_rpa/nodes/ai/__init__.py
- src/casare_rpa/nodes/ai/llm_nodes.py (4-6 nodes)
- src/casare_rpa/nodes/ai/prompt_nodes.py (2-3 nodes)
- src/casare_rpa/infrastructure/resources/llm_resource_manager.py
- src/casare_rpa/presentation/canvas/visual_nodes/ai/__init__.py
- tests/nodes/ai/test_llm_nodes.py

MODIFIED:
- pyproject.toml (add openai, anthropic dependencies)
- src/casare_rpa/nodes/__init__.py
```

**Nodes to Implement**:
1. `LLMCompletionNode` - Basic prompt completion
2. `LLMChatNode` - Multi-turn conversation
3. `LLMExtractDataNode` - Extract structured JSON from text
4. `LLMSummarizeNode` - Text summarization
5. `LLMClassifyNode` - Text classification
6. `PromptTemplateNode` - Reusable prompt with variables

**Estimated LOC**: ~1,500 (nodes) + ~500 (resource manager) + ~800 (tests)

---

### 2. Intelligent Document Processing (IDP)

**Feature Name**: Document AI Nodes

**Why It Matters**:
- 30%+ CAGR market growth for IDP
- Invoice/receipt/form processing is top RPA use case
- Competitors offer 90%+ extraction accuracy with AI
- Current CasareRPA has basic OCR only

**Technical Complexity**: MEDIUM-HIGH
- LLM-based approach (GPT-4 Vision, Claude) simplifies implementation
- Can leverage LLM nodes from Priority 1
- Multiple document types to support

**Dependencies/Prerequisites**:
- LLM nodes (Priority 1) - for LLM-based extraction
- Or: Azure Document Intelligence SDK (cloud approach)

**Scope**:
```
NEW FILES:
- src/casare_rpa/nodes/document/__init__.py
- src/casare_rpa/nodes/document/classification_nodes.py
- src/casare_rpa/nodes/document/extraction_nodes.py
- src/casare_rpa/nodes/document/validation_nodes.py
- src/casare_rpa/infrastructure/resources/document_ai_manager.py
- tests/nodes/document/test_document_nodes.py

MODIFIED:
- pyproject.toml (optional: azure-ai-documentintelligence)
```

**Nodes to Implement**:
1. `ClassifyDocumentNode` - Detect document type (invoice, receipt, etc.)
2. `ExtractInvoiceNode` - Structured invoice data extraction
3. `ExtractFormNode` - Generic form field extraction
4. `ValidateExtractionNode` - Confidence scoring, validation
5. `OCRWithLayoutNode` - Enhanced OCR preserving structure

**Estimated LOC**: ~2,000 (nodes) + ~400 (manager) + ~600 (tests)

---

### 3. Enhanced Selector Self-Healing

**Feature Name**: AI-Powered Selector Healing

**Why It Matters**:
- UiPath, AA have "near-real-time" self-healing
- Broken selectors are #1 maintenance burden in RPA
- CasareRPA has basic selector healing but not AI-powered
- Differentiator for reliability

**Technical Complexity**: MEDIUM
- Build on existing `selector_healing.py`
- Add ML/fuzzy matching for similar elements
- Use LLM for semantic element understanding

**Dependencies/Prerequisites**:
- LLM nodes (optional, for advanced healing)
- Current selector infrastructure exists

**Scope**:
```
MODIFIED FILES:
- src/casare_rpa/utils/selectors/selector_healing.py (extend)
- src/casare_rpa/utils/selectors/selector_manager.py
- src/casare_rpa/nodes/browser_nodes.py (integrate healing)
- src/casare_rpa/nodes/desktop_nodes/element_nodes.py

NEW FILES:
- src/casare_rpa/utils/selectors/ai_selector_healer.py
- tests/utils/selectors/test_ai_selector_healer.py
```

**Capabilities to Add**:
1. Fuzzy attribute matching (threshold-based)
2. Structural similarity scoring
3. Visual element matching (screenshot comparison)
4. LLM-based semantic matching ("Find the login button")
5. Healing suggestions with confidence scores
6. Auto-heal mode for attended bots

**Estimated LOC**: ~800 (new) + ~400 (modifications) + ~500 (tests)

---

### 4. Process Recording & Discovery

**Feature Name**: Action Recorder

**Why It Matters**:
- Power Automate has recorder with AI detection
- UiPath Clipboard AI records actions
- CasareRPA has desktop_recorder.py but incomplete
- Reduces workflow creation time by 50-70%

**Technical Complexity**: MEDIUM-HIGH
- Windows hook integration (already partial in desktop_recorder.py)
- UI detection and node generation
- Browser action recording via Playwright

**Dependencies/Prerequisites**:
- Existing desktop_recorder.py infrastructure
- Browser DevTools protocol (Playwright)

**Scope**:
```
MODIFIED FILES:
- src/casare_rpa/desktop/desktop_recorder.py (complete implementation)
- src/casare_rpa/presentation/canvas/main_window.py (UI integration)

NEW FILES:
- src/casare_rpa/utils/recording/browser_recorder.py
- src/casare_rpa/utils/recording/recording_processor.py
- src/casare_rpa/utils/recording/action_to_node_converter.py
- src/casare_rpa/presentation/canvas/ui/panels/recording_panel.py
- tests/utils/recording/test_recorder.py
```

**Features**:
1. Desktop action capture (click, type, key press)
2. Browser action capture (navigation, clicks, input)
3. Smart element detection (generate robust selectors)
4. Action deduplication and optimization
5. One-click "generate workflow" from recording
6. Recording playback preview

**Estimated LOC**: ~2,500 (implementation) + ~800 (tests)

---

### 5. Workflow Analytics & Insights

**Feature Name**: Execution Analytics Dashboard

**Why It Matters**:
- Process mining is major 2025 trend
- Identifies bottlenecks, failure patterns
- Enables data-driven optimization
- Competitors include analytics in orchestrator

**Technical Complexity**: LOW-MEDIUM
- Uses existing execution history data
- Add aggregation queries
- Dashboard UI in orchestrator

**Dependencies/Prerequisites**:
- Orchestrator API exists
- Execution history stored in database

**Scope**:
```
MODIFIED FILES:
- src/casare_rpa/infrastructure/orchestrator/api/database.py
- src/casare_rpa/orchestrator/api/static/ (React dashboard)

NEW FILES:
- src/casare_rpa/infrastructure/analytics/__init__.py
- src/casare_rpa/infrastructure/analytics/execution_analyzer.py
- src/casare_rpa/infrastructure/analytics/bottleneck_detector.py
- src/casare_rpa/infrastructure/orchestrator/api/routers/analytics.py
- tests/infrastructure/analytics/test_execution_analyzer.py
```

**Features**:
1. Workflow success/failure rates over time
2. Average execution duration by workflow
3. Node-level timing breakdown
4. Bottleneck identification (slowest nodes)
5. Failure pattern clustering
6. Optimization suggestions

**Estimated LOC**: ~1,200 (backend) + ~800 (frontend) + ~400 (tests)

---

## Priority Matrix

| Priority | Feature | User Impact | Complexity | Competitive Gap | Recommended |
|----------|---------|-------------|------------|-----------------|-------------|
| 1 | LLM Nodes | HIGH | MEDIUM | CRITICAL | START NOW |
| 2 | Document AI | HIGH | MEDIUM-HIGH | HIGH | After #1 |
| 3 | Selector Healing | MEDIUM-HIGH | MEDIUM | MEDIUM | Parallel |
| 4 | Action Recorder | HIGH | MEDIUM-HIGH | HIGH | Q1 2025 |
| 5 | Analytics | MEDIUM | LOW-MEDIUM | LOW | Q1 2025 |

---

## Implementation Roadmap

### Phase 1: AI Foundation (2-3 weeks)
- Implement LLM nodes (Priority 1)
- Add openai/anthropic to dependencies
- Create LLM resource manager with rate limiting
- Visual nodes for canvas

### Phase 2: Document Intelligence (3-4 weeks)
- Leverage LLM nodes for extraction
- Add document classification
- Invoice/receipt/form templates
- Validation and confidence scoring

### Phase 3: Self-Healing & Recording (4-6 weeks)
- Enhanced selector healing
- Desktop recorder completion
- Browser recorder
- Action-to-node conversion

### Phase 4: Analytics (2-3 weeks)
- Execution analyzer service
- Bottleneck detection
- Dashboard integration

---

## Codebase TODOs Analysis

Found 22 TODOs in current codebase, mostly in orchestrator API:

| Location | TODO | Priority |
|----------|------|----------|
| `routers/schedules.py` | APScheduler integration (5 TODOs) | HIGH |
| `routers/workflows.py` | Database operations (4 TODOs) | MEDIUM |
| `database.py` | Node execution breakdown, self-healing tracking | MEDIUM |
| `canvas_workflow_runner.py` | Project context support | LOW |

**Recommendation**: Address schedules.py TODOs during normal development (not a separate initiative).

---

## Recommended Next Plan

**Create**: `.brain/plans/llm-integration.md`

This should be the next feature plan as it:
1. Addresses critical competitive gap
2. Has medium complexity (achievable in 2-3 weeks)
3. Enables subsequent AI features (document processing, NL automation)
4. Uses existing patterns (nodes, resource managers)
5. Already researched in detail (see archive/ai-ml-integration.md)

---

## Summary

**Top 5 Next Features (Prioritized)**:

1. **LLM Integration Nodes** - CRITICAL gap, foundation for AI features
2. **Intelligent Document Processing** - High-value use case, leverages LLM
3. **AI-Powered Selector Healing** - Reliability improvement, competitive parity
4. **Action Recorder** - Productivity boost, reduces time-to-automation
5. **Execution Analytics** - Operational visibility, optimization insights

**Recommendation**: Start with LLM nodes immediately. This is the highest-impact, lowest-risk feature that enables all subsequent AI capabilities.

---

*Research completed: 2025-12-01*
*Sources: UiPath FUSION 2025, Microsoft Power Platform 2025, Automation Anywhere PRE, CasareRPA codebase analysis*
