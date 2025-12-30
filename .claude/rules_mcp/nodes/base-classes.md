<rules category="nodes">
  <base_classes>
    <category_base_classes>
      <category name="browser">
        <base>BrowserBaseNode</base>
        <file>@src/casare_rpa/nodes/browser/browser_base.py</file>
        <helpers>get_page(), get_normalized_selector(), safe_click()</helpers>
      </category>

      <category name="desktop">
        <base>DesktopNodeBase</base>
        <file>@src/casare_rpa/nodes/desktop_automation/desktop_base.py</file>
        <helpers>get_desktop_context(), wait_for_element()</helpers>
      </category>

      <category name="data">
        <base>BaseNode</base>
        <context>ExecutionContext for variable access</context>
      </category>
    </category_base_classes>

    <browser_pattern>
      <correct><![CDATA[
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode

class MyBrowserNode(BrowserBaseNode):
    @properties(
        PropertyDef("selector", PropertyType.SELECTOR, required=True),
    )
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        # Get page with error handling
        page = await self.get_page(context)

        # Get normalized selector
        selector = self.get_normalized_selector(context)

        # Safe click with retry
        success = await self.safe_click(page, selector)

        return {"success": success}
]]></correct>
    </browser_pattern>

    <desktop_pattern>
      <correct><![CDATA[
from casare_rpa.nodes.desktop_automation.desktop_base import DesktopNodeBase

class MyDesktopNode(DesktopNodeBase):
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        # Get desktop context
        desktop = self.get_desktop_context(context)

        # Wait for element
        found = await self.wait_for_element(
            context,
            self.get_parameter("selector"),
            timeout=self.get_parameter("timeout", 30000)
        )

        return {"success": found}
]]></correct>
    </desktop_pattern>

    <context_access>
      <rule>Always check resource availability before use</rule>
      <rule>Use helper methods instead of direct context access</rule>
      <wrong>page = context.page  # Don't access directly</wrong>
      <correct>page = await self.get_page(context)  # Use helper</correct>
    </context_access>

    <selector_handling>
      <rule>Use normalized selectors through selector facade</rule>
      <rule>Support variable interpolation ({{variable}})</rule>

      <correct><![CDATA[
def get_normalized_selector(self, context: ExecutionContext) -> str:
    selector = self.get_parameter("selector")
    if selector.startswith("{{"):
        selector = context.resolve_value(selector)
    return normalize_selector(selector)
]]></correct>
    </selector_handling>
  </base_classes>

  <retry_patterns>
    <rule>Add retry logic for flaky operations</rule>

    <correct><![CDATA[
from casare_rpa.utils.resilience.retry import retry_async, RetryConfig

async def safe_click(self, page: Page, selector: str) -> bool:
    try:
        await retry_async(
            page.click,
            selector,
            config=RetryConfig(
                max_attempts=3,
                initial_delay=1.0,
                retry_on=[TimeoutError, ConnectionError]
            )
        )
        return True
    except Exception as e:
        logger.error(f"Failed to click {selector}: {e}")
        return False
]]></correct>
  </retry_patterns>
</rules>
