# .brain/docs Index

```xml<brain_docs_index>
  <!-- Technical documentation and development guides. -->

  <node_dev>
    <f name="node-templates-core.md">  <p>Browser, Desktop, Control Flow templates</p></f>
    <f name="node-templates-data.md">   <p>File, String, List, Variable templates</p></f>
    <f name="node-templates-services.md"> <p>HTTP, Google, System, Dialog templates</p></f>
    <f name="node-checklist.md">        <p>Step-by-step node checklist</p></f>
    <f name="super-node-pattern.md">    <p>Super Node consolidation pattern</p></f>
    <f name="trigger-checklist.md">     <p>Trigger node checklist</p></f>
  </node_dev>

  <ui_dev>
    <f name="ui-standards.md">   <p>UI/UX standards and patterns</p></f>
    <f name="widget-rules.md">   <p>Widget implementation rules</p></f>
  </ui_dev>

  <testing>
    <f name="tdd-guide.md">     <p>Test-driven development guide</p></f>
  </testing>

  <search>
    <p>Semantic search uses local ChromaDB index</p>
    <cmd>python scripts/index_codebase.py</cmd> <d>Build/update index</d>
    <mcp>python scripts/chroma_search_mcp.py</mcp> <t>search_codebase</t>
  </search>

  <quick_ref>
    <for>Node Developers</for>
    <s>1. Start with node-checklist.md</s>
    <s>2. Use templates (core/data/services)</s>
    <s>3. For multi-action nodes, see super-node-pattern.md</s>
  </quick_ref>

  <quick_ref>
    <for>UI Developers</for>
    <s>1. Read ui-standards.md first</s>
    <s>2. Follow widget-rules.md</s>
    <s>3. Check .claude/rules/ui/theme-rules.md for theming</s>
  </quick_ref>

  <quick_ref>
    <for>Test Writers</for>
    <s>1. Follow tdd-guide.md</s>
    <s>2. Run: pytest tests/ -v</s>
  </quick_ref>

  <xref>
    <r>Node creation workflow</r> <l>../decisions/add-node.md</l>
    <r>UI patterns</r>            <l>.claude/rules/ui/</l>
    <r>Testing patterns</r>        <l>agent-rules/agents/quality.md</l>
    <r>Architecture</r>           <l>../systemPatterns.md</l>
  </xref>
</brain_docs_index>
```
