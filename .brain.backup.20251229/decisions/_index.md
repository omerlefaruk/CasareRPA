# Decision Trees Index

```xml
<decisions_index>
  <!-- Quick navigation for common development tasks. -->

  <trees>
    <t name="add-node.md">     <p>Creating new automation nodes</p></t>
    <t name="add-feature.md">  <p>Adding UI, API, or business logic</p></t>
    <t name="fix-bug.md">       <p>Debugging crashes, wrong output, UI issues</p></t>
    <t name="modify-execution.md"> <p>Changing workflow execution flow</p></t>
  </trees>

  <decision_matrix>
    <q>What do you need to do?</q>
    <branch>
      <b>Add something new?</b>
      <l>New node for automation → add-node.md</l>
      <l>New UI widget/panel → add-feature.md#step-1</l>
      <l>New API integration → add-feature.md#step-2</l>
      <l>New business rule → add-feature.md#step-3</l>
    </branch>
    <branch>
      <b>Fix something broken?</b>
      <l>App crashes → fix-bug.md#step-1</l>
      <l>Wrong output → fix-bug.md#step-2</l>
      <l>UI not updating → fix-bug.md#step-3</l>
      <l>Slow performance → fix-bug.md#step-4</l>
    </branch>
    <branch>
      <b>Modify existing behavior?</b>
      <l>Change execution order → modify-execution.md</l>
      <l>Add retry/error handling → modify-execution.md#error-handling</l>
      <l>Change event flow → modify-execution.md#events</l>
    </branch>
    <branch>
      <b>Refactor/cleanup?</b>
      <l>See .brain/projectRules.md for standards</l>
    </branch>
  </decision_matrix>

  <common_start>
    <task>
      <q>I need to add a new node that...</q>
      <s>1. Read add-node.md</s>
      <s>2. Check nodes/_index.md for similar nodes</s>
      <s>3. Use template from .brain/docs/node-templates-core.md</s>
    </task>
    <task>
      <q>I need to fix a bug where...</q>
      <s>1. Read fix-bug.md</s>
      <s>2. Find the error type in the decision tree</s>
      <s>3. Follow debugging steps</s>
    </task>
    <task>
      <q>I need to integrate with external API...</q>
      <s>1. Read add-feature.md#step-2</s>
      <s>2. Create infrastructure client</s>
      <s>3. Create domain protocol</s>
      <s>4. Create node that uses client</s>
    </task>
    <task>
      <q>I need to change how workflows execute...</q>
      <s>1. Read modify-execution.md</s>
      <s>2. Understand current flow in domain/services/</s>
      <s>3. Check event handlers in application/handlers/</s>
    </task>
  </common_start>

  <related>
    <r>Symbol lookup</r>     <f>.brain/symbols.md</f>
    <r>System patterns</r>   <f>.brain/systemPatterns.md</f>
    <r>Coding standards</r>   <f>.brain/projectRules.md</f>
    <r>Error catalog</r>      <f>.brain/errors.md</f>
    <r>Dependencies</r>      <f>.brain/dependencies.md</f>
  </related>

  <used_by>
    <u>/implement-feature</u> <t>add-feature.md</t>
    <u>/implement-node</u>    <t>add-node.md</t>
    <u>/fix-feature</u>       <t>fix-bug.md</t>
    <u>architect agent</u>    <t>All trees for planning</t>
    <u>explore agent</u>      <t>Navigation reference</t>
  </used_by>
</decisions_index>
```
