<rules category="domain">
  <events>
    <pattern>DDD 2025 Domain Events Pattern</pattern>
    <file>@src/casare_rpa/domain/events/base.py</file>

    <structure>
      <use>Frozen dataclasses for immutability</use>
      <extend>DomainEvent base class with event_id and occurred_on</extend>
      <method>Implement to_dict() for serialization</method>

      <correct><![CDATA[
from dataclasses import dataclass
from casare_rpa.domain.events.base import DomainEvent

@dataclass(frozen=True)
class WorkflowStartedEvent(DomainEvent):
    workflow_id: str = ""
    user_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["workflow_id"] = self.workflow_id
        result["user_id"] = self.user_id
        return result
]]></correct>
    </structure>

    <aggregate_events>
      <extend>AggregateEvent for aggregate-related events</extend>
      <include>aggregate_id field</include>

      <correct><![CDATA[
@dataclass(frozen=True)
class NodeCompletedEvent(AggregateEvent):
    node_id: str = ""
    output_data: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["node_id"] = self.node_id
        result["output_data"] = self.output_data or {}
        return result
]]></correct>
    </aggregate_events>

    <rules>
      <rule>Never mutate event fields after creation</rule>
      <rule>Always call super().to_dict() in custom to_dict()</rule>
      <rule>Use frozen=True to ensure immutability</rule>
      <rule>Include all custom fields in to_dict()</rule>
    </rules>

    <anti_patterns>
      <wrong>@dataclass  # Missing frozen=True</wrong>
      <wrong>def to_dict(self):  # Missing super().to_dict() call</wrong>
      <wrong>self.field = new_value  # Mutating frozen event</wrong>
    </anti_patterns>

    <references>
      <ref>@src/casare_rpa/domain/events/</ref>
      <ref>@.claude/rules/12-ddd-events.md</ref>
    </references>
  </events>
</rules>
