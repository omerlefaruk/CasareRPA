<rule id="type-safety" priority="normal">
  <name>Type Safety Patterns</name>

  <signatures>
    <rule>All method signatures must have type hints</rule>
    <rule>Return types must be explicit</rule>
    <rule>Use TYPE_CHECKING for circular imports</rule>

    <correct><![CDATA[
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from casare_rpa.domain.entities import BaseNode

def my_function(node: BaseNode) -> str:
    return node.node_id
]]></correct>

    <wrong><![CDATA[
def my_function(node):  # NO type hints
    return node.id
]]></wrong>
  </signatures>

  <protocols>
    <use>Protocols for interface definitions</use>
    <location>@src/casare_rpa/domain/protocols/</location>

    <correct><![CDATA[
from typing import Protocol

class ExecutionContext(Protocol):
    async def resolve_value(self, value: str) -> str: ...
    def get_variable(self, name: str) -> Any: ...
]]></correct>
  </protocols>

  <result_types>
    <domain>Return ExecutionResult dict with success/data/error</domain>
    <application>Use Result[Ok, Err] pattern or explicit result classes</application>

    <correct><![CDATA[
# Domain nodes
return {"success": True, "data": value}
return {"success": False, "error": "message"}

# Application use cases
from casare_rpa.domain.errors import Ok, Err
return Ok(Response(...))
return Err(WorkflowError("message"))
]]></correct>
  </result_types>
</rule>
