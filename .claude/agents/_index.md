# Agents Index

```xml
<agents_index>
  <!-- Agent definitions for CasareRPA. Primary specs in this directory. -->

  <agents>
    <agent name="architect">System design - Implementation plans</agent>
    <agent name="builder">Code implementation - Writing features</agent>
    <agent name="docs">Documentation - API docs, guides</agent>
    <agent name="explore">Codebase navigation - Finding files</agent>
    <agent name="integrations">External services - APIs, databases</agent>
    <agent name="quality">Testing & QA - Unit tests, performance</agent>
    <agent name="refactor">Code improvement - DRY, patterns</agent>
    <agent name="researcher">Investigation - Library comparison</agent>
    <agent name="reviewer">Code review - Quality gate</agent>
    <agent name="ui">UI development - PySide6/Qt widgets</agent>
  </agents>

  <workflows>
    <task name="Feature">explore → architect → builder → quality → reviewer</task>
    <task name="Bug fix">explore → builder → quality → reviewer</task>
    <task name="Refactor">explore → refactor → quality → reviewer</task>
    <task name="Research">explore → researcher → docs</task>
  </workflows>

  <usage_examples>
    <example>Task(subagent_type="explore", prompt="Find authentication code")</example>
    <example>Task(subagent_type="architect", prompt="Design login feature")</example>
    <example>Task(subagent_type="builder", prompt="Implement login per plan")</example>
  </usage_examples>

  <references>
    <ref type="summaries">agent-rules/agents/</ref>
    <ref type="workflow">agent-rules/rules/04-agents.md</ref>
    <ref type="commands">../commands/</ref>
  </references>
</agents_index>
```

*Parent: [../_index.md](../_index.md)*
