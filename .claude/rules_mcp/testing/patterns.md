<rules category="testing">
  <organization>
    <structure>
      <tests>tests/domain/</tests>
      <tests>tests/application/</tests>
      <tests>tests/infrastructure/</tests>
      <tests>tests/presentation/</tests>
      <tests>tests/integration/</tests>
    </structure>

    <fixtures>
      <location>@tests/conftest.py</location>

      <use>Always use fixtures from conftest.py</use>

      <correct><![CDATA[
import pytest

@pytest.mark.asyncio
async def test_node_execution(mock_context, mock_page):
    """Use fixtures instead of creating mocks manually."""
    node = MyNode("test")
    result = await node.execute(mock_context)
    assert result["success"] is True
]]></correct>

      <common_fixtures>
        <fixture name="execution_context">REAL ExecutionContext for node testing</fixture>
        <fixture name="mock_context">MOCK ExecutionContext for controlled testing</fixture>
        <fixture name="mock_page">Mock Playwright Page with common methods</fixture>
        <fixture name="mock_http_client">Mock UnifiedHttpClient for HTTP testing</fixture>
      </common_fixtures>
    </fixtures>

    <naming>
      <pattern>test_method_scenario</pattern>

      <correct>
        <test>test_execute_simple_script_success</test>
        <test>test_execute_with_missing_selector_fails</test>
        <test>test_execute_empty_result_returns_none</test>
      </correct>
    </naming>
  </organization>

  <test_paths>
    <rule>Test all three paths: happy, sad, edge</rule>

    <correct><![CDATA[
@pytest.mark.asyncio
async def test_node_execution_success(mock_context, mock_page):
    """HAPPY PATH: Node executes successfully"""
    mock_page.evaluate.return_value = "My Title"
    node = BrowserEvaluateNode("test")
    result = await node.execute(mock_context)
    assert result["success"] is True

@pytest.mark.asyncio
async def test_node_execution_error(mock_context, mock_page):
    """SAD PATH: Node fails due to exception"""
    mock_page.evaluate.side_effect = Exception("Script error")
    node = BrowserEvaluateNode("test")
    result = await node.execute(mock_context)
    assert result["success"] is False

@pytest.mark.asyncio
async def test_node_empty_result(mock_context, mock_page):
    """EDGE CASE: Empty result handling"""
    mock_page.evaluate.return_value = None
    node = BrowserEvaluateNode("test")
    result = await node.execute(mock_context)
    assert result["success"] is True
    assert node.get_output_value("result") is None
]]></correct>
  </test_paths>

  <async_tests>
    <use>@pytest.mark.asyncio for all async tests</use>

    <correct><![CDATA[
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    result = await my_async_function()
    assert result is not None
]]></correct>
  </async_tests>

  <chain_testing>
    <location>@tests/domain/services/chain/conftest.py</location>
    <pattern>MockAgentOrchestrator for chain execution testing</pattern>

    <correct><![CDATA[
from tests.domain.services.chain.conftest import MockAgentOrchestrator

def test_chain_execution():
    orchestrator = MockAgentOrchestrator()
    orchestrator.set_result(AgentType.EXPLORE, AgentResult(success=True))
    orchestrator.set_result(AgentType.PLAN, AgentResult(success=True))

    result = orchestrator.execute_chain([AgentType.EXPLORE, AgentType.PLAN])
    assert result.success
]]></correct>
  </chain_testing>

  <rules>
    <rule>Use fixtures from conftest.py instead of creating mocks manually</rule>
    <rule>Separate real vs mock contexts</rule>
    <rule>Use @pytest.mark.asyncio for async tests</rule>
    <rule>Test happy, sad, and edge cases</rule>
    <rule>Use descriptive test names: test_method_scenario</rule>
    <rule>Parametrize common scenarios to avoid duplication</rule>
  </rules>

  <references>
    <ref>@.claude/skills/test-generator/SKILL.md</ref>
    <ref>@.claude/skills/chain-tester/SKILL.md</ref>
    <ref>@docs/agent/testing-standards.md</ref>
  </references>
</rules>
