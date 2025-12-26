"""
Skip Pattern - Non-Critical Nodes

For optional operations where failure shouldn't stop the workflow.

Use cases:
- Optional data enrichment
- Nice-to-have notifications
- Secondary UI elements
- Cache warming
- Analytics/logging
"""

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType


@properties(
    PropertyDef("recipient", PropertyType.STRING, required=True),
    PropertyDef("subject", PropertyType.STRING, required=True),
    PropertyDef("is_critical", PropertyType.BOOLEAN, default=False),
)
@node(category="google")
class OptionalEmailNode(BaseNode):
    """
    Send optional notification email.

    If is_critical=False, failures are logged but don't stop workflow.
    Uses separate output ports for success/failure routing.
    """

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_exec_output("sent")  # Email sent successfully
        self.add_exec_output("skipped")  # Email failed but not critical
        self.add_exec_output("failed")  # Critical email failed

        self.add_input_port("recipient", DataType.STRING)
        self.add_input_port("subject", DataType.STRING)
        self.add_output_port("error_message", DataType.STRING)

    async def execute(self, context) -> dict:
        recipient = self.get_parameter("recipient")
        subject = self.get_parameter("subject")
        is_critical = self.get_parameter("is_critical", False)

        try:
            # Attempt to send email
            await self._send_email(recipient, subject)
            logger.info(f"Notification email sent to {recipient}")

            return {"success": True, "next_nodes": ["sent"]}

        except Exception as exc:
            error_msg = f"Email failed: {exc}"
            self.set_output_value("error_message", error_msg)

            if is_critical:
                # Critical notification - fail the workflow
                logger.error(f"Critical notification failed: {exc}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": "API_ERROR",
                    "next_nodes": ["failed"],
                }
            else:
                # Optional notification - log and continue
                logger.warning(f"Optional notification skipped: {exc}")
                return {"success": True, "next_nodes": ["skipped"]}

    async def _send_email(self, recipient: str, subject: str) -> None:
        """Send email via Gmail client (simplified)."""
        # In production, use GmailClient from infrastructure layer
        await asyncio.sleep(0.1)  # Simulate async operation


@properties(
    PropertyDef("cache_key", PropertyType.STRING, required=True),
    PropertyDef("data", PropertyType.ANY, required=True),
)
@node(category="data")
class CacheWriteNode(BaseNode):
    """
    Write to cache - optional operation.

    Cache writes are nice-to-have. If cache is unavailable,
    log a warning but continue with main workflow.
    """

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_exec_output("done")
        self.add_input_port("cache_key", DataType.STRING)
        self.add_input_port("data", DataType.ANY)

    async def execute(self, context) -> dict:
        cache_key = self.get_parameter("cache_key")
        data = self.get_input_value("data")

        try:
            await self._write_to_cache(cache_key, data)
            logger.debug(f"Cached data under key: {cache_key}")

        except Exception as exc:
            # Cache failure is not critical
            logger.warning(f"Cache write failed (continuing): {exc}")

        # Always succeed - cache is optional
        return {"success": True, "next_nodes": ["done"]}

    async def _write_to_cache(self, key: str, value: object) -> None:
        """Write to cache storage (simplified)."""
        # Simulate cache write
        pass


@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("primary_selector", PropertyType.STRING, required=True),
    PropertyDef("secondary_selectors", PropertyType.JSON, default=[]),
    PropertyDef("required", PropertyType.BOOLEAN, default=False),
)
@node(category="browser")
class OptionalScrapeNode(BaseNode):
    """
    Scrape optional data from page.

    If required=False and scraping fails, returns empty result
    instead of failing the workflow.
    """

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_exec_output()

        self.add_input_port("url", DataType.STRING)
        self.add_output_port("scraped_data", DataType.DICT)
        self.add_output_port("was_successful", DataType.BOOLEAN)

    async def execute(self, context) -> dict:
        url = self.get_parameter("url")
        primary_selector = self.get_parameter("primary_selector")
        secondary_selectors = self.get_parameter("secondary_selectors", [])
        is_required = self.get_parameter("required", False)

        page = context.get_active_page()
        scraped_data = {}
        success = False

        # Try primary selector
        try:
            element = await page.query_selector(primary_selector)
            if element:
                scraped_data["primary"] = await element.text_content()
                success = True
        except Exception as exc:
            logger.debug(f"Primary selector failed: {exc}")

        # Try secondary selectors
        if not success:
            for idx, selector in enumerate(secondary_selectors):
                try:
                    element = await page.query_selector(selector)
                    if element:
                        scraped_data[f"secondary_{idx}"] = await element.text_content()
                        success = True
                        break
                except Exception:
                    continue

        self.set_output_value("scraped_data", scraped_data)
        self.set_output_value("was_successful", success)

        if not success and is_required:
            return {
                "success": False,
                "error": "Required data could not be scraped",
                "error_code": "ELEMENT_NOT_FOUND",
            }

        logger.info(f"Scrape {'succeeded' if success else 'failed (optional)'}")
        return {"success": True, "next_nodes": ["exec_out"]}


__all__ = ["OptionalEmailNode", "CacheWriteNode", "OptionalScrapeNode"]
