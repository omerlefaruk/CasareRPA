<rules category="domain">
  <aggregates>
    <pattern>Aggregate Root Pattern</pattern>
    <file>@src/casare_rpa/domain/aggregates/</file>

    <structure>
      <rule>Aggregate root is the only entry point for modifications</rule>
      <rule>Entity IDs are value objects (NodeId, WorkflowId, etc.)</rule>
      <rule>State changes generate domain events</rule>

      <correct><![CDATA[
from casare_rpa.domain.entities import Workflow, NodeId
from casare_rpa.domain.value_objects import NodeStatus

class Workflow:
    def __init__(self, workflow_id: WorkflowId):
        self._workflow_id = workflow_id
        self._nodes: dict[NodeId, BaseNode] = {}
        self._events: list[DomainEvent] = []

    def add_node(self, node: BaseNode) -> None:
        """Add node - aggregate root controls state."""
        self._nodes[node.node_id] = node
        self._events.append(NodeAddedEvent(node_id=str(node.node_id)))

    def get_events(self) -> list[DomainEvent]:
        """Get pending events to publish."""
        return self._events.copy()

    def mark_events_published(self):
        """Clear events after publishing."""
        self._events.clear()
]]></correct>
    </structure>

    <value_objects>
      <rule>Value objects are immutable</rule>
      <rule>Use dataclass with frozen=True</rule>
      <rule>Implement __eq__ and __hash__</rule>

      <correct><![CDATA[
@dataclass(frozen=True)
class DataType:
    name: str
    underlying_type: type

    def __str__(self) -> str:
        return self.name

# Predefined instances
DataType.STRING = DataType("string", str)
DataType.INTEGER = DataType("integer", int)
DataType.DICT = DataType("dict", dict)
]]></correct>
    </value_objects>

    <rules>
      <rule>Don't bypass aggregate root to modify entities</rule>
      <rule>Aggregate controls invariants and validation</rule>
      <rule>Use value objects for type safety</rule>
      <rule>Never expose internal collections directly</rule>
    </rules>
  </aggregates>
</rules>
