<rules category="nodes">
  <schema_driven>
    <pattern>Modern Node Standard 2025 - Schema-Driven</pattern>

    <decorator>
      <use>@properties decorator for schema definition</use>
      <use>@node decorator for metadata</use>

      <correct><![CDATA[
from casare_rpa.domain.decorators import properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.nodes.registry import node

# Property constants for reusability
BROWSER_TIMEOUT = PropertyDef(
    "timeout",
    PropertyType.INTEGER,
    default=30000,
    description="Timeout in milliseconds"
)

@properties(
    PropertyDef("selector", PropertyType.SELECTOR, required=True),
    PropertyDef("text", PropertyType.STRING, default=""),
    BROWSER_TIMEOUT,  # Reusable constant
)
@node(category="browser")
class TypeTextNode(BrowserBaseNode):
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        selector = self.get_parameter("selector")
        text = self.get_parameter("text")
        timeout = self.get_parameter("timeout", 30000)
        return {"success": True}
]]></correct>
    </decorator>

    <parameter_access>
      <rule>Use self.get_parameter(name, default) for access</rule>
      <forbidden>NO self.config.get() calls</forbidden>

      <correct><![CDATA[
selector = self.get_parameter("selector")
timeout = self.get_parameter("timeout", 30000)
]]></correct>

      <wrong><![CDATA[
selector = self.config.get("selector")  # NO
timeout = self.config.get("timeout", 30000)  # NO
]]></wrong>
    </parameter_access>

    <property_types>
      <type name="SELECTOR">CSS/XPath selector string</type>
      <type name="STRING">Text string</type>
      <type name="INTEGER">Whole number</type>
      <type name="BOOLEAN">True/False</type>
      <type name="DICT">Dictionary/object</type>
      <type name="LIST">Array/list</type>
      <type name="ANY">Any type</type>
    </property_types>
  </schema_driven>

  <ports>
    <pattern>Port definition with _define_ports()</pattern>

    <correct><![CDATA[
def _define_ports(self):
    # Input ports
    self.add_input_port("url", DataType.STRING, required=True)
    self.add_input_port("headers", DataType.DICT, required=False)

    # Output ports
    self.add_output_port("result", DataType.DICT)
    self.add_output_port("status_code", DataType.INTEGER)

    # Execution ports (flow control)
    self.add_exec_input("exec_in")
    self.add_exec_output("exec_out")
    self.add_exec_output("error")
]]></correct>

    <page_passthrough>
      <use>add_page_passthrough_ports() for browser nodes</use>
      <correct>self.add_page_passthrough_ports()</correct>
    </page_passthrough>
  </ports>

  <execution_result>
    <pattern>Standard ExecutionResult dict format</pattern>

    <correct><![CDATA[
# Success
return {
    "success": True,
    "next_nodes": ["exec_out"],
    "data": {"result": value}
}

# Error
return {
    "success": False,
    "next_nodes": ["error"],
    "error": "Failed to click element",
    "error_code": "CLICK_FAILED"
}
]]></correct>
  </execution_result>

  <rules>
    <rule>Always call super().__init__() in custom __init__</rule>
    <rule>Call self._define_ports() in __init__</rule>
    <rule>Use @properties decorator for all nodes</rule>
    <rule>Use self.get_parameter() not self.config.get()</rule>
    <rule>Return dict with success/data/error keys</rule>
    <rule>Don't raise exceptions in execute() - return error result</rule>
  </rules>
</rules>
