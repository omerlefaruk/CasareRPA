<rule id="async-patterns" priority="critical">
  <name>Async Patterns</name>

  <node_execution>
    <rule>All node execute methods must be async</rule>

    <correct><![CDATA[
class MyNode(BaseNode):
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        # Always use async/await for I/O operations
        page = await self.get_page(context)

        # Use retry wrapper for external calls
        result = await retry_async(
            page.click,
            self.get_parameter("selector"),
            config=self.retry_config,
        )
        return {"success": True, "data": result}
]]></correct>
  </node_execution>

  <testing_async>
    <use>@pytest.mark.asyncio for async tests</use>

    <correct><![CDATA[
import pytest

@pytest.mark.asyncio
async def test_node_execution_success(mock_context, mock_page):
    node = MyNode("test")
    result = await node.execute(mock_context)
    assert result["success"] is True
]]></correct>
  </testing_async>

  <qt_integration>
    <library>qasync for Qt integration</library>
    <file>@src/casare_rpa/infrastructure/async_utils.py</file>

    <correct><![CDATA[
import qasync

class MyController(QObject):
    @qasync.asyncSlot()
    async def handle_action(self):
        result = await self.async_operation()
        self.update_ui(result)
]]></correct>
  </qt_integration>

  <context_rules>
    <rule>Never mix blocking and async I/O in same context</rule>
    <rule>Use retry_async for all external calls</rule>
    <rule>Proper event loop management in tests</rule>
    <rule>Handle async context cleanup with try/finally or async with</rule>
  </context_rules>

  <anti_patterns>
    <wrong><![CDATA[
# WRONG: Blocking I/O in async context
async def execute(self, context):
    time.sleep(5)  # NO - use asyncio.sleep

# WRONG: Not awaiting async operations
async def execute(self, context):
    result = self.do_async_work()  # NO - missing await

# WRONG: Mixing sync and async
async def execute(self, context):
    requests.get(url)  # NO - blocking
]]></wrong>
  </anti_patterns>
</rule>
