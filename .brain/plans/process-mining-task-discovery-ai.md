# Process Mining and Task Discovery with AI for CasareRPA

**Research Date**: 2025-12-11
**Research Type**: Competitive Analysis, Technical Research, Implementation Planning
**Status**: Complete

---

## Executive Summary

This document provides comprehensive research on integrating Process Mining and AI-driven Task Discovery capabilities into CasareRPA. These features enable automatic discovery of automation candidates by analyzing user desktop activity, recognizing patterns in repetitive tasks, and optimizing existing workflows.

**Key Finding**: CasareRPA already has a solid foundation with the existing `DesktopRecorder` class that captures mouse clicks, keyboard input, and UI element information. This provides the raw data collection infrastructure needed for process mining.

---

## Part 1: Competitive Analysis

### 1.1 UiPath Task Mining

**How It Works**:
- Collects employee desktop data (screenshots + action logs) upon each user action
- Uses AI to analyze data and identify automation opportunities
- Captures variations of specific tasks by recording mouse clicks, keystrokes, and hotkeys
- Merges variations into comprehensive task picture for end-to-end understanding
- Generates PDD (Process Definition Document) and XAML files for automation implementation

**Key Features**:
| Feature | Description |
|---------|-------------|
| Desktop Data Collection | Screenshots + logs for each user action |
| AI Analysis | Pattern recognition across multiple recordings |
| Variation Merging | Consolidates different user approaches |
| ROI Metrics | Prioritizes automation opportunities |
| GDPR Compliance | Privacy-first consent model |
| Asset Generation | Auto-creates PDD and XAML automation skeletons |

**Integration with Process Mining**:
- Zoom from macro-level business processes to micro-level desktop activities
- Start task mining projects from bottlenecks identified in process graphs
- Unified view of processes at both organizational and individual levels

**Important Note**: UiPath is discontinuing "Unassisted Task Mining" in December 2025, consolidating into "Assisted Task Mining" which requires active user participation.

**Sources**:
- [UiPath Task Mining Product](https://www.uipath.com/product/task-mining)
- [UiPath Task Mining Documentation](https://docs.uipath.com/task-mining/automation-cloud/latest/user-guide/introduction-as)
- [UiPath Process Mining 2025](https://docs.uipath.com/process-mining/automation-cloud/latest/user-guide/2025)

---

### 1.2 Microsoft Process Advisor (Power Automate)

**How It Works**:
- Task mining analyzes recorded user actions to gain insights
- Identifies common mistakes and tasks suitable for automation
- Process mining extracts data from business applications
- Combines both for comprehensive process understanding

**Key Features**:
| Feature | Description |
|---------|-------------|
| Activity Analysis | Identifies longest activities and process variations |
| Application Analytics | Shows time spent in applications per activity |
| Automation Recommendations | Suggests connectors based on analysis |
| UIA + MSAA Support | Records both selector types |
| Rework Detection | Identifies repeated work patterns |
| Root Cause Analysis | AI-powered bottleneck identification |
| Process Comparison | Compare process variations |
| Custom Metrics | Define business-specific KPIs |

**2025 Release Wave Features**:
- AI-First approach with dynamic, multimodal automations
- Generative actions and intelligent document processing
- Self-healing automations with built-in AI
- Deep insights with custom Power BI reports

**Sources**:
- [Power Automate Process Advisor Overview](https://learn.microsoft.com/en-us/power-automate/process-advisor-overview)
- [Task Mining Overview](https://learn.microsoft.com/en-us/power-automate/task-mining-overview)
- [Power Automate 2025 Release Wave 1](https://learn.microsoft.com/en-us/power-platform/release-plan/2025wave1/power-automate/)

---

### 1.3 Automation Anywhere Discovery Bot

**How It Works**:
- Uses AI and ML to automatically capture and analyze user actions
- Identifies common, repetitive process steps as employees navigate applications
- Consolidates multiple workflow recordings from different users
- Prioritizes automation opportunities by ROI

**Six-Step Process**:
1. **Capture**: Record user desktop interactions
2. **Map**: Create workflow diagrams with screenshots
3. **Identify**: Find automation candidates with AI
4. **Prioritize**: Rank by ROI potential
5. **Generate**: Create bot automation skeleton
6. **Deploy**: Push to production

**Key Features**:
| Feature | Description |
|---------|-------------|
| Computer Vision | Captures from mainframes, VDI, Windows, web apps |
| Workflow Visualization | Screenshots attached to each action |
| Multi-User Analysis | Merges recordings from different users |
| Bot Generation | Creates automation skeletons automatically |
| Zero-Client | Web-based interface for collaboration |

**Important Note**: Automation Anywhere is discontinuing Discovery Bot in November 2025, transitioning to Process Discovery Cloud.

**Sources**:
- [Discovery Bot Introduction](https://docs.automationanywhere.com/bundle/enterprise-v2019/page/discovery-bot/topics/discovery-bot-intro.html)
- [Process Discovery vs Process Mining](https://www.automationanywhere.com/company/blog/company-news/how-process-discovery-drives-automation)
- [Automation Anywhere Press Release](https://www.automationanywhere.com/company/press-room/automation-anywhere-announces-worlds-first-integrated-process-discovery-solution)

---

### 1.4 Feature Comparison Matrix

| Feature | UiPath | Power Automate | AA Discovery | CasareRPA (Current) |
|---------|--------|----------------|--------------|---------------------|
| Desktop Recording | Yes | Yes | Yes | **Yes (DesktopRecorder)** |
| Screenshot Capture | Yes | Yes | Yes | Partial |
| UI Element Detection | Yes | Yes (UIA/MSAA) | Yes | **Yes (UIAutomation)** |
| Pattern Recognition | AI | AI | AI/ML | Not Yet |
| Multi-User Analysis | Yes | Yes | Yes | Not Yet |
| ROI Prioritization | Yes | Yes | Yes | Not Yet |
| Bot/Workflow Generation | Yes | Yes | Yes | **Yes (WorkflowGenerator)** |
| Process Mining Integration | Yes | Yes | Yes | Not Yet |
| Event Log Analysis | Yes | Yes | Limited | Not Yet |
| Bottleneck Detection | Yes | Yes | Yes | Not Yet |

---

## Part 2: CasareRPA Current Capabilities

### 2.1 Existing Infrastructure

**DesktopRecorder** (`src/casare_rpa/desktop/desktop_recorder.py`):
- Records mouse clicks (single, double, right-click)
- Captures keyboard input (typing, hotkeys)
- Detects UI elements using UIAutomation
- Supports drag operations and window activations
- Provides callbacks for real-time recording feedback
- Global hotkey support (F9 start/stop, F10 pause, Escape cancel)

**Recorded Action Data**:
```python
@dataclass
class DesktopRecordedAction:
    action_type: DesktopActionType
    timestamp: datetime
    x: int, y: int  # Coordinates
    text: str, keys: List[str]  # Keyboard data
    element_name: str  # UI element name
    element_type: str  # Control type
    element_automation_id: str
    element_class_name: str
    window_title: str
    selector: Dict[str, Any]  # Replay selector
```

**WorkflowGenerator**:
- Converts recorded actions to workflow JSON
- Creates appropriate node types (DesktopClickElementNode, DesktopTypeTextNode, etc.)
- Builds execution flow connections
- Generates named workflows with timestamps

**Desktop Managers**:
- `MouseController`: Async mouse operations (click, drag, scroll)
- `KeyboardController`: Key sending, hotkeys, text typing
- `WindowManager`: Window activation, enumeration
- `ScreenCapture`: Screenshot functionality

### 2.2 Gap Analysis for Process Mining

| Capability | Status | Gap |
|------------|--------|-----|
| Action Recording | Complete | None |
| UI Element Capture | Complete | Add screenshot per action |
| Event Log Format | Missing | Need XES/standard format export |
| Pattern Recognition | Missing | Need ML analysis |
| Process Visualization | Missing | Need graph generation |
| Bottleneck Detection | Missing | Need timing analysis |
| Multi-Session Analysis | Missing | Need recording aggregation |
| Optimization Suggestions | Missing | Need AI recommendations |

---

## Part 3: Python Libraries for Process Mining

### 3.1 PM4Py - Primary Recommendation

**Overview**: Open-source Python library for process mining algorithms, developed by Fraunhofer FIT / Process Intelligence Solutions.

**Key Features**:
| Feature | Description |
|---------|-------------|
| Event Log Formats | XES, CSV, pandas DataFrames |
| Process Discovery | Alpha Miner, Inductive Miner, Heuristic Miner |
| Conformance Checking | Token replay, alignments |
| Process Enhancement | Performance analysis, bottlenecks |
| Visualization | Petri nets, BPMN, DFG graphs |
| GPU Acceleration | NVIDIA RAPIDS integration |

**Installation**:
```bash
pip install pm4py
```

**Basic Usage**:
```python
import pm4py

# Load event log
log = pm4py.read_xes("event_log.xes")
# Or from DataFrame
log = pm4py.convert_to_event_log(df)

# Process Discovery - Alpha Miner
net, im, fm = pm4py.discover_petri_net_alpha(log)

# Process Discovery - Inductive Miner (recommended)
net, im, fm = pm4py.discover_petri_net_inductive(log)

# Visualization
pm4py.view_petri_net(net, im, fm)

# Conformance Checking
alignments = pm4py.conformance_diagnostics_alignments(log, net, im, fm)

# Bottleneck Analysis
from pm4py.statistics.sojourn_time.log import get as sojourn_get
sojourn = sojourn_get.apply(log, parameters={"aggregationMeasure": "median"})
```

**Licensing**: AGPL-3.0 (open source)

**Sources**:
- [PM4Py Official Documentation](https://pm4py.fit.fraunhofer.de/documentation)
- [PM4Py GitHub Repository](https://github.com/process-intelligence-solutions/pm4py)
- [PM4Py Academic Paper](https://www.sciencedirect.com/science/article/pii/S2665963823000933)

---

### 3.2 Desktop Recording Libraries

**pynput** (Already in CasareRPA):
```python
from pynput import mouse, keyboard

# Mouse listener
mouse.Listener(on_click=on_click, on_scroll=on_scroll).start()

# Keyboard listener
keyboard.Listener(on_press=on_press, on_release=on_release).start()
```

**PyAutoGUI** (Supplementary):
```python
import pyautogui

# Screenshot capture
screenshot = pyautogui.screenshot(region=(x, y, width, height))

# Mouse/keyboard automation for replay
pyautogui.click(x, y)
pyautogui.typewrite('text')
```

**Sources**:
- [pynput Recording Guide](https://github.com/george-jensen/record-and-play-pynput)
- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/en/latest/)
- [Desktop RPA Recording Guide](https://www.laminarrun.com/post/recording-desktop-rpa-scripts-from-manual-clicks-to-python-automation)

---

### 3.3 Machine Learning Libraries for Pattern Recognition

**scikit-learn** (Pattern Detection):
```python
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler

# Cluster similar action sequences
scaler = StandardScaler()
features = scaler.fit_transform(action_features)
clusters = DBSCAN(eps=0.5, min_samples=5).fit_predict(features)
```

**TensorFlow/PyTorch** (Deep Learning):
- LSTM for sequence pattern recognition
- Transformer models for action prediction
- Autoencoders for anomaly detection

**Reinforcement Learning** (Process Optimization):
```python
# OpenAI Gym environment for process optimization
import gymnasium as gym

# Q-learning for optimal path finding
# DQN for bottleneck avoidance
```

**Sources**:
- [Process Mining ML Integration](https://www.processmining.org/ml.html)
- [RL for Process Mining](https://www.sciencedirect.com/science/article/pii/S1110866524001580)
- [AI Agent Frameworks for ML](https://machinelearningmastery.com/7-ai-agent-frameworks-for-machine-learning-workflows-in-2025/)

---

## Part 4: Implementation Architecture

### 4.1 Proposed System Architecture

```
+-------------------+     +----------------------+     +-------------------+
|  Desktop Recorder |---->|   Event Log Storage  |---->|   Process Mining  |
|   (Existing)      |     |   (XES Format)       |     |   Engine (PM4Py)  |
+-------------------+     +----------------------+     +-------------------+
        |                          |                           |
        v                          v                           v
+-------------------+     +----------------------+     +-------------------+
| Screenshot Engine |     | Session Aggregator   |     | Pattern Analyzer  |
|   (New)           |     |   (Multi-user)       |     |   (ML/AI)         |
+-------------------+     +----------------------+     +-------------------+
        |                          |                           |
        v                          v                           v
+-------------------+     +----------------------+     +-------------------+
|  UI Integrations  |<----|  Recommendation      |<----|  Visualization    |
|  (Canvas Display) |     |  Engine (AI)         |     |  (Process Graphs) |
+-------------------+     +----------------------+     +-------------------+
```

### 4.2 Data Flow

1. **Recording Phase**:
   - User starts recording session
   - DesktopRecorder captures actions with timestamps
   - Screenshots captured for each click action
   - UI element information extracted via UIAutomation
   - Raw events stored with session metadata

2. **Event Log Generation**:
   - Convert recorded actions to XES format
   - Map action types to standard activities
   - Generate case IDs for process instances
   - Include timing information for duration analysis

3. **Process Discovery**:
   - Apply Inductive Miner for process model
   - Generate Petri net / BPMN visualization
   - Calculate process metrics (variants, frequency, duration)

4. **Analysis & Recommendations**:
   - Identify bottlenecks (longest durations)
   - Detect repetitive patterns (automation candidates)
   - Calculate ROI estimates
   - Generate optimization suggestions

5. **Workflow Generation**:
   - Convert identified patterns to CasareRPA workflows
   - Create node sequences from action patterns
   - Add error handling and waits
   - Present suggestions in UI

---

## Part 5: Specific Implementation Recommendations

### 5.1 Phase 1: Enhanced Recording (2-3 weeks)

**Objective**: Extend existing DesktopRecorder with process mining requirements

**New Components**:

#### 1. Screenshot Enhancement
```python
# Add to DesktopRecordedAction
screenshot_path: str = ""  # Path to captured screenshot
screenshot_region: Tuple[int, int, int, int] = (0, 0, 0, 0)  # Crop region
```

#### 2. Session Management
```python
@dataclass
class RecordingSession:
    session_id: str
    user_id: str
    process_name: str
    start_time: datetime
    end_time: Optional[datetime]
    actions: List[DesktopRecordedAction]
    metadata: Dict[str, Any]  # Application, window context
```

#### 3. XES Event Log Export
```python
class EventLogExporter:
    """Exports recorded actions to XES format for PM4Py."""

    def export_to_xes(self, sessions: List[RecordingSession]) -> str:
        """Generate XES XML from recording sessions."""
        # Map action types to activity names
        # Create trace per session
        # Include timestamps as event attributes
```

**Files to Create**:
- `src/casare_rpa/process_mining/__init__.py`
- `src/casare_rpa/process_mining/session_manager.py`
- `src/casare_rpa/process_mining/event_log_exporter.py`
- `src/casare_rpa/process_mining/screenshot_capture.py`

---

### 5.2 Phase 2: Process Mining Integration (3-4 weeks)

**Objective**: Integrate PM4Py for process discovery and analysis

**New Components**:

#### 1. Process Mining Service
```python
class ProcessMiningService:
    """Service for process mining operations."""

    def discover_process(self, log_path: str, algorithm: str = "inductive"):
        """Discover process model from event log."""
        import pm4py
        log = pm4py.read_xes(log_path)

        if algorithm == "inductive":
            net, im, fm = pm4py.discover_petri_net_inductive(log)
        elif algorithm == "alpha":
            net, im, fm = pm4py.discover_petri_net_alpha(log)
        elif algorithm == "heuristic":
            net, im, fm = pm4py.discover_petri_net_heuristics(log)

        return ProcessModel(net, im, fm)

    def analyze_bottlenecks(self, log_path: str) -> List[Bottleneck]:
        """Identify process bottlenecks."""
        log = pm4py.read_xes(log_path)
        sojourn = pm4py.statistics.sojourn_time.log.get.apply(log)
        # Return activities with highest average duration

    def get_process_variants(self, log_path: str) -> List[ProcessVariant]:
        """Get process execution variants."""
        log = pm4py.read_xes(log_path)
        variants = pm4py.get_variants(log)
        return variants
```

#### 2. Visualization Generator
```python
class ProcessVisualization:
    """Generates process visualizations."""

    def generate_petri_net_svg(self, process_model) -> str:
        """Generate SVG visualization of process model."""

    def generate_dfg_image(self, log_path: str) -> bytes:
        """Generate Directly-Follows Graph image."""

    def generate_bpmn(self, process_model) -> str:
        """Export process model as BPMN XML."""
```

**Files to Create**:
- `src/casare_rpa/process_mining/mining_service.py`
- `src/casare_rpa/process_mining/visualization.py`
- `src/casare_rpa/process_mining/models.py`

---

### 5.3 Phase 3: Pattern Recognition & AI (4-6 weeks)

**Objective**: Add ML-based pattern recognition for automation candidates

**New Components**:

#### 1. Pattern Recognition Engine
```python
class PatternRecognitionEngine:
    """AI-powered pattern recognition for repetitive tasks."""

    def find_repetitive_patterns(
        self,
        sessions: List[RecordingSession],
        min_frequency: int = 3
    ) -> List[AutomationCandidate]:
        """Identify repetitive action sequences."""
        # Extract action sequences as features
        # Apply sequence alignment/clustering
        # Identify frequently repeated patterns

    def calculate_automation_roi(
        self,
        pattern: AutomationCandidate
    ) -> AutomationROI:
        """Estimate ROI of automating a pattern."""
        # Time saved per execution
        # Error reduction potential
        # Implementation complexity estimate
```

#### 2. LLM-based Analysis
```python
class AIProcessAnalyzer:
    """Uses LLM for process analysis and recommendations."""

    async def analyze_process(
        self,
        process_data: ProcessModel,
        bottlenecks: List[Bottleneck]
    ) -> ProcessInsights:
        """Generate AI insights about the process."""
        prompt = self._build_analysis_prompt(process_data, bottlenecks)
        # Use existing LLM infrastructure
        response = await self.llm_service.complete(prompt)
        return self._parse_insights(response)

    async def suggest_optimizations(
        self,
        process_data: ProcessModel
    ) -> List[OptimizationSuggestion]:
        """AI-generated optimization suggestions."""
```

**ML Approaches**:

| Technique | Use Case | Library |
|-----------|----------|---------|
| Sequence Clustering | Group similar action patterns | scikit-learn DBSCAN |
| DTW (Dynamic Time Warping) | Match action sequences | dtaidistance |
| N-gram Analysis | Find common subsequences | NLTK, custom |
| LSTM Networks | Predict next actions | PyTorch/TensorFlow |
| Anomaly Detection | Find unusual executions | Isolation Forest |

**Files to Create**:
- `src/casare_rpa/process_mining/pattern_engine.py`
- `src/casare_rpa/process_mining/ai_analyzer.py`
- `src/casare_rpa/process_mining/ml_models.py`

---

### 5.4 Phase 4: UI Integration (2-3 weeks)

**Objective**: Add process mining UI to CasareRPA canvas

**New UI Components**:

#### 1. Process Mining Panel
- Recording session management
- Session list with metadata
- Record/Stop/Pause controls
- Progress indicators

#### 2. Process Visualization View
- Interactive process graph display
- Bottleneck highlighting
- Variant comparison
- Activity statistics

#### 3. Automation Candidates Panel
- List of discovered patterns
- ROI estimates per pattern
- "Generate Workflow" button
- Preview of suggested automation

#### 4. Insights Dashboard
- Process metrics summary
- Time saved estimates
- Automation coverage
- Trend analysis

**Integration Points**:
- Add "Process Mining" tab to bottom panel
- Add "Discover" button to toolbar
- Connect to existing WorkflowGenerator

---

### 5.5 New Node Types

**Recording Nodes**:
| Node | Purpose |
|------|---------|
| StartRecordingNode | Begin desktop recording session |
| StopRecordingNode | End recording and return actions |
| RecordToWorkflowNode | Convert recording to workflow |

**Analysis Nodes**:
| Node | Purpose |
|------|---------|
| ImportEventLogNode | Load XES/CSV event log |
| DiscoverProcessNode | Run process discovery algorithm |
| AnalyzeBottlenecksNode | Identify process bottlenecks |
| GetProcessVariantsNode | Extract process variants |

**Visualization Nodes**:
| Node | Purpose |
|------|---------|
| VisualizePetriNetNode | Generate Petri net image |
| VisualizeDFGNode | Generate DFG visualization |
| ExportBPMNNode | Export process as BPMN |

---

## Part 6: Dependencies and Configuration

### 6.1 New Dependencies

```
# Process Mining
pm4py>=2.7.0

# Already present
pynput>=1.7.0  # Desktop recording
uiautomation>=2.0.0  # UI element detection
Pillow>=10.0.0  # Screenshot handling

# ML (optional, for advanced features)
scikit-learn>=1.3.0
dtaidistance>=2.3.0  # DTW for sequence matching

# Visualization
graphviz>=0.20.0  # Process graph rendering
```

### 6.2 Configuration Schema

```json
{
  "process_mining": {
    "recording": {
      "capture_screenshots": true,
      "screenshot_quality": 85,
      "screenshot_max_size": [1920, 1080],
      "auto_detect_ui_elements": true,
      "text_flush_delay_ms": 500,
      "double_click_threshold_ms": 300
    },
    "analysis": {
      "default_algorithm": "inductive",
      "min_pattern_frequency": 3,
      "bottleneck_threshold_seconds": 30,
      "enable_ai_analysis": true
    },
    "visualization": {
      "graph_format": "svg",
      "highlight_bottlenecks": true,
      "show_frequencies": true,
      "max_variants_shown": 10
    },
    "storage": {
      "session_directory": "~/.casare_rpa/recordings",
      "event_log_directory": "~/.casare_rpa/event_logs",
      "max_sessions_retained": 100
    }
  }
}
```

---

## Part 7: Event Log Format Specification

### 7.1 XES Format for CasareRPA Actions

```xml
<?xml version="1.0" encoding="UTF-8"?>
<log xes.version="1.0" xes.features="nested-attributes">
  <extension name="Concept" prefix="concept" uri="http://www.xes-standard.org/concept.xesext"/>
  <extension name="Time" prefix="time" uri="http://www.xes-standard.org/time.xesext"/>
  <extension name="Lifecycle" prefix="lifecycle" uri="http://www.xes-standard.org/lifecycle.xesext"/>

  <trace>
    <string key="concept:name" value="session_001"/>
    <string key="user" value="user@example.com"/>
    <string key="process" value="Invoice Processing"/>

    <event>
      <string key="concept:name" value="Click Button"/>
      <date key="time:timestamp" value="2025-12-11T10:30:00.000+00:00"/>
      <string key="lifecycle:transition" value="complete"/>
      <string key="action_type" value="mouse_click"/>
      <string key="element_name" value="Submit"/>
      <string key="element_type" value="ButtonControl"/>
      <string key="window_title" value="Invoice Entry"/>
      <int key="x" value="500"/>
      <int key="y" value="300"/>
    </event>

    <event>
      <string key="concept:name" value="Type Text"/>
      <date key="time:timestamp" value="2025-12-11T10:30:05.000+00:00"/>
      <string key="lifecycle:transition" value="complete"/>
      <string key="action_type" value="keyboard_type"/>
      <string key="text" value="INV-2025-001"/>
      <string key="window_title" value="Invoice Entry"/>
    </event>
  </trace>
</log>
```

### 7.2 Activity Mapping

| Action Type | XES Activity Name | Category |
|-------------|-------------------|----------|
| mouse_click | Click {element_name} | UI Interaction |
| mouse_double_click | Double-Click {element_name} | UI Interaction |
| mouse_right_click | Right-Click {element_name} | UI Interaction |
| keyboard_type | Type "{text[:20]}..." | Data Entry |
| keyboard_hotkey | Hotkey {keys} | Navigation |
| mouse_drag | Drag to ({end_x}, {end_y}) | UI Interaction |
| window_activate | Activate {window_title} | Application Switch |

---

## Part 8: Bottleneck Detection Approach

### 8.1 Metrics for Bottleneck Identification

1. **Sojourn Time**: Total time spent on each activity
2. **Waiting Time**: Time between activities
3. **Service Time**: Actual activity duration
4. **Frequency**: How often each activity occurs
5. **Variance**: Inconsistency in activity duration

### 8.2 Detection Algorithm

```python
def detect_bottlenecks(event_log, threshold_percentile=90):
    """
    Identify bottlenecks using multiple metrics.

    Returns activities where:
    1. Average duration > threshold_percentile of all durations
    2. High variance indicates inconsistent execution
    3. Frequent rework (activity repeated in same trace)
    """
    # Calculate sojourn times per activity
    sojourn_times = pm4py.statistics.sojourn_time.log.get.apply(event_log)

    # Calculate threshold
    all_durations = list(sojourn_times.values())
    threshold = np.percentile(all_durations, threshold_percentile)

    bottlenecks = []
    for activity, duration in sojourn_times.items():
        if duration > threshold:
            bottlenecks.append(Bottleneck(
                activity=activity,
                avg_duration=duration,
                severity=duration / threshold,
                recommendation=generate_recommendation(activity, duration)
            ))

    return sorted(bottlenecks, key=lambda b: b.severity, reverse=True)
```

### 8.3 AI-Powered Root Cause Analysis

Using LLM to generate human-readable root cause analysis:

```python
async def analyze_bottleneck_root_cause(bottleneck: Bottleneck, context: ProcessContext):
    prompt = f"""
    Analyze this process bottleneck and suggest root causes:

    Activity: {bottleneck.activity}
    Average Duration: {bottleneck.avg_duration} seconds
    Expected Duration: {context.expected_duration} seconds
    Process: {context.process_name}
    Window: {context.window_title}

    Previous Activity: {context.previous_activity}
    Next Activity: {context.next_activity}

    Suggest:
    1. Likely root causes (3-5)
    2. Optimization recommendations
    3. Automation potential (high/medium/low)
    """
    return await llm_service.complete(prompt)
```

---

## Part 9: Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)
- [ ] Add screenshot capture to DesktopRecorder
- [ ] Implement RecordingSession management
- [ ] Create XES EventLogExporter
- [ ] Add session storage/retrieval

### Phase 2: Process Mining Core (Weeks 4-7)
- [ ] Integrate PM4Py library
- [ ] Implement ProcessMiningService
- [ ] Create visualization generators
- [ ] Add bottleneck detection

### Phase 3: Pattern Recognition (Weeks 8-13)
- [ ] Implement pattern recognition engine
- [ ] Add sequence clustering
- [ ] Create automation candidate scoring
- [ ] Integrate LLM for analysis

### Phase 4: UI Integration (Weeks 14-16)
- [ ] Create Process Mining panel
- [ ] Add visualization view
- [ ] Implement automation candidates panel
- [ ] Connect to workflow generation

### Phase 5: Advanced Features (Weeks 17-20)
- [ ] Multi-user session aggregation
- [ ] Advanced ML models
- [ ] ROI calculator
- [ ] Insights dashboard

---

## Part 10: Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Recording Accuracy | >95% | Actions correctly captured |
| Process Discovery | >90% | Correct process models from logs |
| Pattern Detection | >80% | Repetitive patterns identified |
| Bottleneck Identification | >85% | True bottlenecks found |
| Workflow Generation | >70% | Usable workflows from patterns |
| User Satisfaction | >4/5 | Survey ratings |

---

## References

### Competitor Documentation
- [UiPath Task Mining](https://www.uipath.com/product/task-mining)
- [Power Automate Process Advisor](https://learn.microsoft.com/en-us/power-automate/process-advisor-overview)
- [Automation Anywhere Discovery Bot](https://docs.automationanywhere.com/bundle/enterprise-v2019/page/discovery-bot/topics/discovery-bot-intro.html)

### Process Mining Resources
- [PM4Py Documentation](https://pm4py.fit.fraunhofer.de/documentation)
- [PM4Py GitHub](https://github.com/process-intelligence-solutions/pm4py)
- [Process Mining Algorithms Explained](https://www.processmaker.com/blog/process-mining-algorithms-simply-explained/)

### ML and AI Resources
- [RL for Process Mining](https://www.sciencedirect.com/science/article/pii/S1110866524001580)
- [Bottleneck Detection Methods](https://link.springer.com/chapter/10.1007/978-3-031-36840-0_7)
- [AI Workflow Automation 2025](https://www.cflowapps.com/ai-workflow-automation-trends-for-2025/)

### Python Libraries
- [pynput](https://github.com/george-jensen/record-and-play-pynput)
- [PyAutoGUI](https://pyautogui.readthedocs.io/en/latest/)
- [Windows UIAutomation](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview)

### CasareRPA Current Implementation
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\desktop\desktop_recorder.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\desktop\managers\mouse_controller.py`
- `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\desktop\managers\keyboard_controller.py`

---

*Research completed: 2025-12-11*
