<rules category="testing">
  <organization>
    <structure>
      <directory>tests/ mirrors src/ structure</directory>
      <example>
        <src>src/casare_rpa/domain/</src>
        <test>tests/domain/</test>
      </example>
      <example>
        <src>src/casare_rpa/presentation/canvas/</src>
        <test>tests/presentation/canvas/</test>
      </example>
    </structure>

    <naming>
      <pattern>test_{module_name}.py</pattern>
      <example>test_workflow.py for workflow.py</example>
      <class_pattern>Test{ClassName}</class_pattern>
      <method_pattern>test_{scenario}_{expected_result}</method_pattern>
    </naming>
  </organization>

  <standards>
    <framework>pytest</framework>
    <run_command>pytest tests/ -v</run_command>

    <given_when_then>
      <pattern>Use Given-When-Then for test clarity</pattern>
      <example>
        <code><![CDATA[
def test_node_execution_with_valid_input():
    # Given: A node with valid input
    node = AddNumbersNode()
    node.set_input("a", 5)
    node.set_input("b", 3)

    # When: Executing the node
    result = node.execute()

    # Then: Result is correct
    assert result.output_value == 8
]]></code>
      </example>
    </given_when_then>

    <fixtures>
      <use>conftest.py for shared fixtures</use>
      <fixtures>
        <fixture>node_graph_fixture</fixture>
        <fixture>workflow_fixture</fixture>
        <fixture>mock_browser_fixture</fixture>
      </fixtures>
      <location>@tests/conftest.py</location>
    </fixtures>
  </standards>

  <node_testing>
    <use_skill>test-generator skill</use>
    <file>@tests/presentation/canvas/node_chains/</file>
    <pattern>Chain testing for multi-node workflows</pattern>
    <tier_based>Test tiers (basic, intermediate, advanced)</tier_based>
  </node_testing>

  <references>
    <ref>@docs/agent/testing-standards.md</ref>
    <ref>@.claude/skills/test-generator/SKILL.md</ref>
    <ref>@.claude/skills/chain-tester/SKILL.md</ref>
  </references>
</rules>
