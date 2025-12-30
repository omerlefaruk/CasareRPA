<rules category="nodes">
  <standard name="Modern Node Standard 2025" version="2.0">

    <schema_driven>
      <rule>Use @properties decorator for node properties</rule>
      <rule>Access values via self.get_parameter(name, default)</rule>
      <forbidden>NO self.config.get() calls</forbidden>

      <example>
        <code><![CDATA[
@properties(PropertyDef(name="url", type=DataType.STRING, default=""))
class MyNode(BaseNode):
    async def execute(self):
        url = self.get_parameter("url", "")
]]></code>
      </example>
    </schema_driven>

    <ports>
      <input>Use add_input_port(name, DataType.X)</input>
      <output>Define in schema, return in execute()</output>
    </ports>

    <category_patterns>
      <category name="browser">
        <base>BrowserBaseNode</base>
        <context>PlaywrightPage</context>
        <file>@src/casare_rpa/nodes/browser/</file>
      </category>

      <category name="desktop">
        <base>DesktopNodeBase</base>
        <context>DesktopContext</context>
        <file>@src/casare_rpa/nodes/desktop_automation/</file>
      </category>

      <category name="data">
        <base>BaseNode</base>
        <context>ExecutionContext</context>
        <file>@src/casare_rpa/nodes/data_operations/</file>
      </category>

      <category name="http">
        <base>BaseNode</base>
        <context>UnifiedHttpClient</context>
        <forbidden>No raw httpx/aiohttp</forbidden>
      </category>

      <category name="variable">
        <base>BaseNode</base>
        <context>ExecutionContext</context>
        <file>@src/casare_rpa/nodes/variable_management/</file>
      </category>
    </category_patterns>

    <workflow>
      <step>1. PLAN: Define atomic operation</step>
      <step>2. SEARCH: Check _index.md, registry_data.py</step>
      <step>3. IMPLEMENT: Use existing → Modify → Create</step>
    </workflow>

    <registration>
      <step>1. Export in category/__init__.py</step>
      <step>2. Register in registry_data.py</step>
      <step>3. Add to NODE_TYPE_MAP</step>
      <step>4. Create visual node</step>
      <step>5. Register in visual_nodes/__init__.py</step>
    </registration>

    <testing>
      <use>test-generator skill</use>
      <pattern>Given-When-Then with node_graph_fixture</pattern>
      <file>@tests/presentation/canvas/node_chains/</file>
    </testing>

    <references>
      <ref>@src/casare_rpa/nodes/_index.md</ref>
      <ref>@docs/agent/nodes.md</ref>
      <ref>@.claude/skills/node-template-generator/SKILL.md</ref>
    </references>
  </standard>
</rules>
