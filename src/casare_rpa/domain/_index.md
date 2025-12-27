# Domain Layer Index

```xml
<dom>
<!--
Quick reference for domain layer components.
Pure business logic with zero external dependencies.
Framework-agnostic and testable in isolation.
-->
<struct>
  <d>aggregates/</d>   <e>Workflow, WorkflowId, Position</e>
  <d>entities/</d>     <e>BaseNode, WorkflowSchema, Variable, Project</e>
  <d>events/</d>       <e>NodeAdded, WorkflowStarted, etc.</e>
  <d>value_objects/</d> <e>DataType, NodeStatus, Port, Connection</e>
  <d>services/</d>     <e>ExecutionOrchestrator, Validator, Resolver</e>
  <d>schemas/</d>      <e>PropertyDef, NodeSchema, PropertyType</e>
  <d>protocols/</d>    <e>IExecutionContext, IFolderStorage</e>
  <d>interfaces/</d>   <e>INode, AbstractUnitOfWork</e>
  <d>ai/</d>          <e>AI config, prompt templates</e>
  <d>validation/</d>   <e>ValidationResult, validate_workflow</e>
  <d>errors/</d>      <e>ErrorCode, exceptions, handlers</e>
</struct>
<principles>
  <p>No external imports (Infrastructure, Presentation)</p>
  <p>No I/O operations (file, network, database)</p>
  <p>Framework agnostic (No PySide6, Playwright, aiohttp)</p>
  <p>Testable in isolation (no mocks needed)</p>
</principles>
<events>
  <ex>bus = get_event_bus()</ex>
  <ex>bus.publish(NodeCompleted(node_id="x", ...))</ex>
  <ex>bus.subscribe(NodeCompleted, handler)</ex>
</events>
</dom>
```
