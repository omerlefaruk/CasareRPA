<rules category="nodes">
  <registration>
    <domain_node>
      <file_location>src/casare_rpa/nodes/{category}/</file_location>
      <steps>
        <step order="1">Define class with @properties</step>
        <step order="2">Add to category/__init__.py exports</step>
        <step order="3">Register in registry_data.py</step>
      </steps>
    </domain_node>

    <visual_node>
      <file_location>src/casare_rpa/presentation/canvas/visual_nodes/{category}/</file_location>
      <steps>
        <step order="1">Create VisualXNode extending BaseVisualNode</step>
        <step order="2">Add to visual_nodes/__init__.py _VISUAL_NODE_REGISTRY</step>
        <step order="3">Set icon, category, ports</step>
      </steps>
    </visual_node>

    <node_registry>
      <file>src/casare_rpa/nodes/registry_data.py</file>
      <format>
        <entry>
          <key>"node_category.NodeName"</key>
          <schema>NodeSchema(...)</schema>
        </entry>
      </format>
    </node_registry>

    <node_type_map>
      <file>src/casare_rpa/presentation/canvas/visual_nodes/__init__.py</file>
      <purpose>Map node_type to visual class</purpose>
    </node_type_map>
  </registration>

  <example_full_flow>
    <step>Create domain node in nodes/category/</step>
    <step>Export in category/__init__.py</step>
    <step>Register in registry_data.py</step>
    <step>Create visual node in visual_nodes/category/</step>
    <step>Register in _VISUAL_NODE_REGISTRY</step>
    <step>Update NODE_TYPE_MAP</step>
    <step>Write tests using test-generator skill</step>
  </example_full_flow>
</rules>
