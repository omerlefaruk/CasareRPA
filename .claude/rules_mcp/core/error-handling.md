<rule id="error-handling" priority="critical">
  <name>Error Handling Patterns</name>

  <decorator_pattern>
    <use>@error_handler() decorator on node execute methods</use>
    <file>@src/casare_rpa/domain/decorators/error_handler.py</file>

    <correct><![CDATA[
@error_handler()
async def execute(self, context: ExecutionContext) -> ExecutionResult:
    result = await self.do_work()
    return {"success": True, "data": result}

# With custom options
@error_handler(
    log_format="{class_name} failed on selector: {error}",
    include_traceback=True,
    error_outputs={"success": False},
)
async def execute(self, context: ExecutionContext) -> ExecutionResult:
    result = await self.do_work()
    return {"success": True, "data": result}
]]></correct>
  </decorator_pattern>

  <result_pattern>
    <domain_nodes>Return ExecutionResult dict, don't raise exceptions</domain_nodes>
    <format>{"success": bool, "data": any, "error": str|None}</format>

    <correct>return {"success": True, "data": value}</correct>
    <correct>return {"success": False, "error": "Message", "error_code": "CODE"}</correct>
    <wrong>raise Exception("Don't raise in nodes")</wrong>
  </result_pattern>

  <logging_pattern>
    <library>loguru (imported from casare_rpa.domain.interfaces.logger)</library>

    <correct><![CDATA[
from loguru import logger

# Error logging with context
logger.error(f"Node {self.node_id} failed: {error}",
            node_type=self.node_type,
            operation="execute")

# Structured logging
logger.bind(component="browser", action="click").debug(
    f"Clicked element {selector}")
]]></correct>

    <wrong>print(f"Error: {error}")  # NO print statements</wrong>
    <wrong>logger.error(error)  # Always include context</wrong>
  </logging_pattern>

  <retry_pattern>
    <use>retry_async for all external calls</use>
    <file>@src/casare_rpa/utils/resilience/retry.py</file>

    <correct><![CDATA[
from casare_rpa.utils.resilience.retry import retry_async, RetryConfig

result = await retry_async(
    page.click,
    selector,
    config=RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=30.0,
        backoff_multiplier=2.0,
        jitter=True,
    )
)
]]></correct>
  </retry_pattern>

  <classification>
    <categorize>Classify errors as transient or permanent</categorize>
    <transient>TimeoutError, ConnectionError (retry)</transient>
    <permanent>ValueError, KeyError (don't retry)</permanent>

    <correct><![CDATA[
def should_retry(exception: Exception) -> bool:
    category = classify_error(exception)
    return category == ErrorCategory.TRANSIENT
]]></correct>
  </classification>

  <universal_rules>
    <rule>Wrap ALL external calls in try/except</rule>
    <rule>Log context: what attempted, failed, recovery</rule>
    <rule>Never let external failures be silent</rule>
    <rule>Use structured logging with meaningful keys</rule>
    <rule>Implement proper cleanup after timeout/failure</rule>
  </universal_rules>
</rule>
