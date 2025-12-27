# Application Index

```xml
<app_index>
  <!-- Quick reference for application layer. Use cases, services, and orchestration. -->

  <purpose>
    <p>Orchestrates domain operations via use cases</p>
    <dep>Domain only. Never import from Infrastructure or Presentation</dep>
  </purpose>

  <dirs>
    <d name="use_cases/">      <p>Core business use cases</p>         <e>ExecuteWorkflowUseCase, NodeExecutor</e></d>
    <d name="services/">       <p>Cross-cutting services</p>          <e>ExecutionLifecycleManager, BrowserRecordingService</e></d>
    <d name="queries/">        <p>CQRS read-optimized queries</p>     <e>WorkflowQueryService, ExecutionQueryService</e></d>
    <d name="dependency_injection/"> <p>DI container</p>             <e>DIContainer, Singleton</e></d>
    <d name="orchestrator/">   <p>Job execution use cases</p>        <e>SubmitJobUseCase, ExecuteLocalUseCase</e></d>
    <d name="execution/">      <p>Trigger execution</p>              <e>CanvasTriggerRunner</e></d>
    <d name="workflow/">       <p>Import/export, recent files</p>     <e>WorkflowImporter, RecentFilesManager</e></d>
  </dirs>

  <key_files>
    <f>use_cases/__init__.py</f>       <d>32 exports</d></f>
    <f>use_cases/execute_workflow.py</f> <d>Main workflow executor</d></f>
    <f>use_cases/node_executor.py</f>   <d>Node execution engine</d></f>
    <f>use_cases/variable_resolver.py</f> <d>Variable interpolation</d></f>
    <f>use_cases/generate_workflow.py</f> <d>AI workflow generation</d></f>
    <f>services/__init__.py</f>          <d>9 exports</d></f>
    <f>queries/__init__.py</f>           <d>6 exports</d></f>
    <f>dependency_injection/__init__.py</d> <d>9 exports</d></f>
  </key_files>

  <entry_points>
    <code>
# Workflow Execution
from casare_rpa.application import (
    ExecuteWorkflowUseCase, NodeExecutor, VariableResolver
)

# Use Cases
from casare_rpa.application.use_cases import (
    ExecuteWorkflowUseCase, ExecutionStateManager, ExecutionSettings,
    NodeExecutor, NodeExecutorWithTryCatch, NodeExecutionResult,
    VariableResolver, TryCatchErrorHandler,
)

# Workflow Validation
from casare_rpa.application.use_cases import (
    ValidateWorkflowUseCase, ValidationResult, ValidationIssue
)

# Project Management
from casare_rpa.application.use_cases import (
    CreateProjectUseCase, LoadProjectUseCase, SaveProjectUseCase,
    ListProjectsUseCase, DeleteProjectUseCase, ProjectResult
)

# Scenario Management
from casare_rpa.application.use_cases import (
    CreateScenarioUseCase, LoadScenarioUseCase, SaveScenarioUseCase,
    DeleteScenarioUseCase, ListScenariosUseCase, ScenarioResult
)

# Subflow Execution
from casare_rpa.application.use_cases import (
    Subflow, SubflowExecutor, SubflowInputDefinition,
    SubflowOutputDefinition, SubflowExecutionResult
)

# AI Workflow Generation
from casare_rpa.application.use_cases import (
    GenerateWorkflowUseCase, WorkflowGenerationError, generate_workflow_from_text
)

# Services
from casare_rpa.application.services import (
    ExecutionLifecycleManager, ExecutionState, ExecutionSession,
    OrchestratorClient, WorkflowSubmissionResult,
    BrowserRecordingService, get_browser_recording_service
)

# Dependency Injection
from casare_rpa.application.dependency_injection import (
    DIContainer, Lifecycle, Singleton, LazySingleton, create_singleton_accessor
)

# Orchestrator Use Cases
from casare_rpa.application.orchestrator import (
    ExecuteJobUseCase, SubmitJobUseCase, ExecuteLocalUseCase,
    ExecutionResult, AssignRobotUseCase, ListRobotsUseCase
)

# Trigger Execution
from casare_rpa.application.execution import CanvasTriggerRunner, TriggerEventHandler

# Workflow Import/Export
from casare_rpa.application.workflow import WorkflowImporter, RecentFilesManager

# CQRS Query Services (read-optimized)
from casare_rpa.application.queries import (
    WorkflowQueryService, WorkflowListItemDTO, WorkflowFilter,
    ExecutionQueryService, ExecutionLogDTO, ExecutionFilter
)
    </code>
  </entry_points>

  <use_cases>
    <cat name="Workflow Execution">
      <u>ExecuteWorkflowUseCase</u>      <d>Main workflow execution orchestrator</d>
      <u>ExecutionStateManager</u>       <d>Manage execution state and pause/resume</d>
      <u>NodeExecutor</u>                <d>Execute individual nodes</d>
      <u>NodeExecutorWithTryCatch</u>    <d>Node execution with error recovery</d>
      <u>VariableResolver</u>            <d>Resolve variables in node properties</d>
      <u>SubflowExecutor</u>             <d>Execute subflow nodes</d>
    </cat>
    <cat name="Project Management">
      <u>CreateProjectUseCase</u>        <d>Create new RPA project</d>
      <u>LoadProjectUseCase</u>          <d>Load existing project</d>
      <u>SaveProjectUseCase</u>          <d>Save project to disk</d>
      <u>DeleteProjectUseCase</u>        <d>Delete project</d>
      <u>ListProjectsUseCase</u>         <d>List all projects</d>
    </cat>
    <cat name="Scenario Management">
      <u>CreateScenarioUseCase</u>       <d>Create workflow scenario</d>
      <u>LoadScenarioUseCase</u>         <d>Load scenario JSON</d>
      <u>SaveScenarioUseCase</u>         <d>Save scenario to disk</d>
      <u>DeleteScenarioUseCase</u>       <d>Delete scenario</d>
      <u>ListScenariosUseCase</u>        <d>List project scenarios</d>
    </cat>
    <cat name="Orchestrator">
      <u>SubmitJobUseCase</u>            <d>Submit job to queue</d>
      <u>ExecuteJobUseCase</u>            <d>Execute job from queue</d>
      <u>ExecuteLocalUseCase</u>          <d>Local execution (no orchestrator)</d>
      <u>AssignRobotUseCase</u>          <d>Assign robot to workflow</d>
      <u>ListRobotsUseCase</u>           <d>List available robots</d>
    </cat>
  </use_cases>

  <exports>
    <m>__init__.py</m>      <n>4</n>
    <m>use_cases/</m>       <n>29</n>
    <m>services/</m>        <n>9</n>
    <m>dependency_injection/</m> <n>9</n>
    <m>orchestrator/</m>    <n>6</n>
    <m>execution/</m>       <n>4</n>
    <m>workflow/</m>        <n>2</n>
    <m>queries/</m>         <n>6</n>
  </exports>

  <patterns>
    <p>Use Cases - Single-responsibility operations (Command side of CQRS)</p>
    <p>Query Services - Read-optimized queries bypassing domain model (Query side)</p>
    <p>Services - Cross-cutting concerns (lifecycle, recording)</p>
    <p>DI Container - Thread-safe dependency management</p>
    <p>Result Types - Explicit success/failure returns</p>
    <p>DTOs - Data Transfer Objects for read operations</p>
  </patterns>

  <related>
    <r>../infrastructure/_index.md</r> <d>External adapters</d></r>
    <r>../domain/_index.md</r>         <d>Domain entities</d></r>
    <r>../nodes/_index.md</r>          <d>Node implementations</d></r>
    <r>presentation/canvas/_index.md</r> <d>UI layer</d></r>
  </related>
</app_index>
```
