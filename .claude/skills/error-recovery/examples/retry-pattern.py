"""
Retry Pattern - Exponential Backoff with Jitter

For transient errors that may succeed on retry: timeouts, stale elements,
network hiccups, resource locks.

Key points:
- Max retries prevents infinite loops
- Exponential backoff reduces server load
- Jitter prevents retry thundering herd
- Log each retry attempt for debugging
"""

import asyncio
import random

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType


@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("max_retries", PropertyType.INTEGER, default=3),
    PropertyDef("base_delay_ms", PropertyType.INTEGER, default=1000),
)
@node(category="http")
class RetryHTTPRequestNode(BaseNode):
    """
    HTTP request with automatic retry on transient failures.

    Retries on: connection timeout, 5xx server errors, network errors
    No retry on: 4xx client errors, invalid URLs
    """

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_exec_output()
        self.add_input_port("url", DataType.STRING)
        self.add_output_port("response", DataType.DICT)

    async def execute(self, context) -> dict:
        url = self.get_parameter("url")
        max_retries = self.get_parameter("max_retries", 3)
        base_delay = self.get_parameter("base_delay_ms", 1000)

        last_error = None

        for attempt in range(max_retries):
            try:
                # Simulate HTTP request
                result = await self._make_request(url)

                if attempt > 0:
                    logger.info(f"Request succeeded on retry {attempt + 1}")

                self.set_output_value("response", result)
                return {"success": True, "next_nodes": ["exec_out"]}

            except TimeoutError as exc:
                last_error = exc
                is_last_attempt = attempt >= max_retries - 1

                if is_last_attempt:
                    logger.error(f"Request failed after {max_retries} retries: {exc}")
                    break

                # Calculate delay with exponential backoff + jitter
                delay_ms = self._calculate_retry_delay(attempt, base_delay)
                logger.warning(
                    f"Request timeout, retry {attempt + 1}/{max_retries} " f"after {delay_ms}ms"
                )
                await asyncio.sleep(delay_ms / 1000)

            except ConnectionError as exc:
                # Connection errors are usually transient
                last_error = exc
                if attempt < max_retries - 1:
                    delay_ms = self._calculate_retry_delay(attempt, base_delay)
                    logger.warning(f"Connection failed, retry {attempt + 1}/{max_retries}: {exc}")
                    await asyncio.sleep(delay_ms / 1000)
                else:
                    logger.error(f"Connection failed after {max_retries} retries: {exc}")
                    break

        # All retries exhausted
        return {
            "success": False,
            "error": f"Request failed: {last_error}",
            "error_code": "TIMEOUT",
        }

    def _calculate_retry_delay(self, attempt: int, base_delay: int) -> int:
        """
        Calculate retry delay with exponential backoff and jitter.

        Pattern: base * 2^attempt + random(10-30%)
        Prevents retry thundering herd while keeping delays reasonable.

        Args:
            attempt: Current retry attempt (0-based)
            base_delay: Base delay in milliseconds

        Returns:
            Delay in milliseconds
        """
        max_delay = 30000  # Cap at 30 seconds

        # Exponential backoff: 1s, 2s, 4s, 8s...
        exponential_delay = base_delay * (2**attempt)

        # Add jitter: 10-30% of delay
        jitter_percent = random.uniform(0.1, 0.3)
        jitter = int(exponential_delay * jitter_percent)

        delay = exponential_delay + jitter
        return min(delay, max_delay)

    async def _make_request(self, url: str) -> dict:
        """
        Make HTTP request (simplified example).

        In production, use UnifiedHttpClient from infrastructure layer.
        """
        # Placeholder for actual HTTP call
        await asyncio.sleep(0.1)
        return {"status": 200, "data": "response"}


__all__ = ["RetryHTTPRequestNode"]
