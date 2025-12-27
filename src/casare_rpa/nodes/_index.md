# Nodes Package Index

```xml
<nodes>
<!--
430+ automation nodes across 18 categories.
Modern Node Standard 2025 - Schema-Driven Logic.
-->
<std>
  <r>@properties(PropertyDef(...))</r>
  <r>self.get_parameter(name, default)</r>
  <r>add_input_port(name, DataType.X)</r>
  <r>NO self.config.get() calls</r>
</std>
<workflow>
  <s>1</s> <d>PLAN: Define atomic operation</d>
  <s>2</s> <d>SEARCH: Check _index.md, registry_data.py</d>
  <s>3</s> <d>IMPLEMENT: Use existing → Modify → Create</d>
</workflow>
<register>
  <s>1. Export in @{category}/__init__.py</s>
  <s>2. Register in @registry_data.py</s>
  <s>3. Add to NODE_TYPE_MAP</s>
  <s>4. Create visual node</s>
  <s>5. Register in visual_nodes/__init__.py</s>
</register>
<cats>
  <c>browser</c>      <b>BrowserBaseNode</b>   <x>PlaywrightPage</x>
  <c>desktop</c>      <b>DesktopNodeBase</b>   <x>DesktopContext</x>
  <c>data</c>         <b>BaseNode</b>          <x>None</x>
  <c>http</c>         <b>BaseNode</b>          <x>UnifiedHttpClient</x>
  <c>system</c>       <b>BaseNode</b>          <x>None</x>
  <c>control_flow</c> <b>BaseNode</b>          <x>None</x>
  <c>variable</c>     <b>BaseNode</b>          <x>ExecutionContext</x>
</cats>
<audit>
  <c>python scripts/audit_node_modernization.py</c>
  <t>Target 98%+ modern</t>
</audit>
</nodes>
```
