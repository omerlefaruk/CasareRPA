"""
Fallback Pattern - Alternative Strategies

When primary operation fails, try alternatives before giving up.

Use cases:
- Multiple data sources (API -> database -> cache)
- Alternative selectors (CSS -> XPath -> text search)
- Degraded functionality (high-res image -> thumbnail)
- Multiple authentication methods
"""

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType


@properties(
    PropertyDef("primary_selector", PropertyType.STRING, required=True),
    PropertyDef("fallback_selectors", PropertyType.JSON, default=[]),
)
@node(category="browser")
class FallbackSelectorNode(BaseNode):
    """
    Click element using primary selector, falling back to alternatives.

    Tries each selector in order until one succeeds or all fail.
    Logs which selector worked for future optimization.
    """

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_exec_output("success")  # Click succeeded
        self.add_exec_output("failed")  # All selectors failed
        self.add_input_port("primary_selector", DataType.STRING)
        self.add_output_port("selector_used", DataType.STRING)

    async def execute(self, context) -> dict:
        primary = self.get_parameter("primary_selector")
        fallbacks = self.get_parameter("fallback_selectors", [])

        # Build selector chain: primary first, then fallbacks
        selectors = [primary] + fallbacks

        for idx, selector in enumerate(selectors):
            try:
                page = context.get_active_page()
                await page.click(selector, timeout=5000)

                selector_type = "primary" if idx == 0 else f"fallback[{idx}]"
                logger.info(f"Element clicked using {selector_type} selector: {selector}")

                self.set_output_value("selector_used", selector)
                return {"success": True, "next_nodes": ["success"]}

            except Exception as exc:
                is_last = idx >= len(selectors) - 1
                if not is_last:
                    logger.warning(
                        f"Selector {idx + 1}/{len(selectors)} failed, " f"trying next: {exc}"
                    )
                else:
                    logger.error(f"All {len(selectors)} selectors failed: {exc}")

        return {
            "success": False,
            "error": "All selectors failed",
            "next_nodes": ["failed"],
        }


@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("cache_path", PropertyType.STRING, required=False),
)
@node(category="data")
class DataSourceFallbackNode(BaseNode):
    """
    Fetch data from API, falling back to cache or static file.

    Implements graceful degradation:
    1. Try live API (fresh data)
    2. Try cache file (stale but available)
    3. Try static fallback (minimal functionality)
    """

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_exec_output()
        self.add_input_port("url", DataType.STRING)
        self.add_output_port("data", DataType.ANY)

    async def execute(self, context) -> dict:
        url = self.get_parameter("url")
        cache_path = self.get_parameter("cache_path")

        # Strategy 1: Live API
        data = await self._try_api(url)
        if data is not None:
            logger.info("Retrieved data from live API")
            self.set_output_value("data", data)
            self.set_output_value("source", "api")
            return {"success": True}

        # Strategy 2: Cache file
        if cache_path:
            data = await self._try_cache(cache_path)
            if data is not None:
                logger.warning("API unavailable, using cached data")
                self.set_output_value("data", data)
                self.set_output_value("source", "cache")
                return {"success": True}

        # Strategy 3: Static fallback
        data = await self._try_fallback()
        if data is not None:
            logger.warning("API and cache unavailable, using fallback data")
            self.set_output_value("data", data)
            self.set_output_value("source", "fallback")
            return {"success": True}

        # All strategies failed
        return {
            "success": False,
            "error": "All data sources unavailable",
            "error_code": "RESOURCE_EXHAUSTED",
        }

    async def _try_api(self, url: str) -> object | None:
        """Try to fetch from live API."""
        try:
            # Simulate API call
            return {"status": "ok", "data": "api_result"}
        except Exception as exc:
            logger.debug(f"API fetch failed: {exc}")
            return None

    async def _try_cache(self, path: str) -> object | None:
        """Try to read from cache file."""
        try:
            # Simulate file read
            return {"status": "stale", "data": "cached_result"}
        except Exception as exc:
            logger.debug(f"Cache read failed: {exc}")
            return None

    async def _try_fallback(self) -> object | None:
        """Return minimal fallback data."""
        return {"status": "fallback", "data": []}


__all__ = ["FallbackSelectorNode", "DataSourceFallbackNode"]
