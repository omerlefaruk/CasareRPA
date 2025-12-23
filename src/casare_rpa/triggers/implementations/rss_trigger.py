"""
CasareRPA - RSS Feed Trigger

Trigger that fires when new items appear in an RSS/Atom feed.
Polls the feed at configurable intervals and emits events for new entries.
"""

import asyncio
from collections import deque
from hashlib import sha256
from typing import Any, Dict, List, Optional, Set

import aiohttp
from loguru import logger

# Use defusedxml to prevent XXE attacks
try:
    import defusedxml.ElementTree as ET
except ImportError:
    # Fallback with security mitigations
    import xml.etree.ElementTree as ET

    logger.warning("defusedxml not installed - using stdlib XML parser with limited XXE protection")

from casare_rpa.triggers.base import BaseTrigger, TriggerStatus, TriggerType
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class RSSFeedTrigger(BaseTrigger):
    """
    Trigger that monitors RSS/Atom feeds for new entries.

    Configuration options:
        feed_url: URL of the RSS or Atom feed
        poll_interval: How often to check the feed (seconds)
        max_items: Maximum items to process per poll (0 = unlimited)
        filter_title: Only trigger on items containing this string in title
        filter_category: Only trigger on items in this category
        include_content: Include full content in payload (default: False)
        track_by: How to identify unique items (id, link, guid, title_hash)

    Outputs:
        title: Item title
        link: Item link/URL
        description: Item description/summary
        published: Publication timestamp
        author: Item author
        categories: List of categories
        content: Full content (if include_content=True)
    """

    trigger_type = TriggerType.RSS_FEED
    display_name = "RSS Feed"
    description = "Trigger when new items appear in RSS/Atom feed"
    icon = "rss"
    category = "External"

    # Maximum number of seen items to track (prevents unbounded memory growth)
    MAX_SEEN_ITEMS = 10000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen_items: set[str] = set()
        self._seen_items_order: deque = deque(maxlen=self.MAX_SEEN_ITEMS)
        self._poll_task: asyncio.Task | None = None
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> bool:
        """Start monitoring the RSS feed."""
        try:
            # Validate config first
            is_valid, error = self.validate_config()
            if not is_valid:
                self._error_message = error
                self._status = TriggerStatus.ERROR
                return False

            self._status = TriggerStatus.STARTING

            # Create HTTP session
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))

            # Do initial fetch to populate seen items (avoid triggering on old items)
            await self._initial_fetch()

            # Start polling task
            self._poll_task = asyncio.create_task(self._poll_loop())
            self._status = TriggerStatus.ACTIVE

            logger.info(
                f"RSS trigger started: {self.config.name} "
                f"(feed: {self.config.config.get('feed_url')})"
            )
            return True

        except Exception as e:
            self._error_message = str(e)
            self._status = TriggerStatus.ERROR
            logger.error(f"Failed to start RSS trigger: {e}")
            return False

    async def stop(self) -> bool:
        """Stop monitoring the RSS feed."""
        try:
            # Cancel poll task
            if self._poll_task and not self._poll_task.done():
                self._poll_task.cancel()
                try:
                    await self._poll_task
                except asyncio.CancelledError:
                    pass

            # Close session
            if self._session:
                await self._session.close()
                self._session = None

            self._status = TriggerStatus.INACTIVE
            logger.info(f"RSS trigger stopped: {self.config.name}")
            return True

        except Exception as e:
            logger.error(f"Error stopping RSS trigger: {e}")
            return False

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate RSS trigger configuration."""
        config = self.config.config

        # Feed URL is required
        feed_url = config.get("feed_url", "")
        if not feed_url:
            return False, "feed_url is required"

        if not feed_url.startswith(("http://", "https://")):
            return False, "feed_url must be a valid HTTP(S) URL"

        # Poll interval validation
        poll_interval = config.get("poll_interval", 300)
        if poll_interval < 10:
            return False, "poll_interval must be at least 10 seconds"

        # Track by validation
        track_by = config.get("track_by", "id")
        valid_track_by = ["id", "link", "guid", "title_hash"]
        if track_by not in valid_track_by:
            return False, f"track_by must be one of: {valid_track_by}"

        return True, None

    async def _initial_fetch(self) -> None:
        """Fetch feed initially to populate seen items."""
        try:
            items = await self._fetch_feed()
            for item in items:
                item_id = self._get_item_id(item)
                self._add_seen_item(item_id)
            logger.debug(f"RSS trigger initialized with {len(self._seen_items)} existing items")
        except Exception as e:
            logger.warning(f"Initial RSS fetch failed: {e}")

    def _add_seen_item(self, item_id: str) -> None:
        """Add item to seen set with LRU eviction."""
        if item_id in self._seen_items:
            return
        # Evict oldest if at capacity
        if len(self._seen_items) >= self.MAX_SEEN_ITEMS:
            oldest = self._seen_items_order.popleft()
            self._seen_items.discard(oldest)
        self._seen_items.add(item_id)
        self._seen_items_order.append(item_id)

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        poll_interval = self.config.config.get("poll_interval", 300)

        while self._status == TriggerStatus.ACTIVE:
            try:
                await self._check_for_new_items()
            except Exception as e:
                logger.error(f"RSS poll error: {e}")
                self._error_message = str(e)

            await asyncio.sleep(poll_interval)

    async def _check_for_new_items(self) -> None:
        """Check feed for new items and emit events."""
        items = await self._fetch_feed()
        max_items = self.config.config.get("max_items", 0)
        filter_title = self.config.config.get("filter_title", "")
        filter_category = self.config.config.get("filter_category", "")
        include_content = self.config.config.get("include_content", False)

        new_items: list[dict[str, Any]] = []

        for item in items:
            item_id = self._get_item_id(item)

            # Skip if already seen
            if item_id in self._seen_items:
                continue

            # Apply title filter
            title = item.get("title", "")
            if filter_title and filter_title.lower() not in title.lower():
                continue

            # Apply category filter
            categories = item.get("categories", [])
            if filter_category and filter_category not in categories:
                continue

            # Mark as seen
            self._add_seen_item(item_id)
            new_items.append(item)

            # Check max items
            if max_items > 0 and len(new_items) >= max_items:
                break

        # Emit events for new items
        for item in new_items:
            payload = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "description": item.get("description", ""),
                "published": item.get("published", ""),
                "author": item.get("author", ""),
                "categories": item.get("categories", []),
            }

            if include_content:
                payload["content"] = item.get("content", "")

            await self.emit(
                payload=payload,
                metadata={"feed_url": self.config.config.get("feed_url")},
            )

    async def _fetch_feed(self) -> list[dict[str, Any]]:
        """Fetch and parse the RSS feed."""
        if not self._session:
            raise RuntimeError("HTTP session not initialized")

        feed_url = self.config.config.get("feed_url")

        async with self._session.get(feed_url) as response:
            response.raise_for_status()
            content = await response.text()

        return self._parse_feed(content)

    def _parse_feed(self, content: str) -> list[dict[str, Any]]:
        """Parse RSS/Atom feed content (XXE-safe)."""
        items: list[dict[str, Any]] = []

        try:
            root = ET.fromstring(content)

            # Detect feed type
            if root.tag == "rss" or root.tag.endswith("}rss"):
                items = self._parse_rss(root)
            elif "feed" in root.tag:
                items = self._parse_atom(root)
            else:
                # Try RSS anyway
                items = self._parse_rss(root)

        except Exception as e:
            logger.error(f"Failed to parse feed: {e}")

        return items

    def _parse_rss(self, root) -> list[dict[str, Any]]:
        """Parse RSS 2.0 format."""
        items = []

        for item in root.findall(".//item"):
            parsed = {
                "title": self._get_text(item, "title"),
                "link": self._get_text(item, "link"),
                "description": self._get_text(item, "description"),
                "guid": self._get_text(item, "guid"),
                "published": self._get_text(item, "pubDate"),
                "author": self._get_text(item, "author") or self._get_text(item, "dc:creator"),
                "categories": [c.text for c in item.findall("category") if c.text],
                "content": self._get_text(item, "content:encoded"),
            }
            items.append(parsed)

        return items

    def _parse_atom(self, root) -> list[dict[str, Any]]:
        """Parse Atom format."""
        items = []

        # Handle namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall(".//atom:entry", ns) or root.findall(".//entry"):
            link_elem = entry.find("atom:link[@rel='alternate']", ns) or entry.find("link")
            link = link_elem.get("href", "") if link_elem is not None else ""

            parsed = {
                "title": self._get_text_ns(entry, "title", ns),
                "link": link,
                "description": self._get_text_ns(entry, "summary", ns),
                "guid": self._get_text_ns(entry, "id", ns),
                "published": self._get_text_ns(entry, "published", ns)
                or self._get_text_ns(entry, "updated", ns),
                "author": self._get_author_atom(entry, ns),
                "categories": [
                    c.get("term", "")
                    for c in entry.findall("atom:category", ns) or entry.findall("category")
                ],
                "content": self._get_text_ns(entry, "content", ns),
            }
            items.append(parsed)

        return items

    def _get_text(self, elem, tag: str) -> str:
        """Get text content of child element."""
        child = elem.find(tag)
        return child.text if child is not None and child.text else ""

    def _get_text_ns(self, elem, tag: str, ns: dict) -> str:
        """Get text content with namespace."""
        child = elem.find(f"atom:{tag}", ns) or elem.find(tag)
        return child.text if child is not None and child.text else ""

    def _get_author_atom(self, entry, ns: dict) -> str:
        """Get author from Atom entry."""
        author = entry.find("atom:author/atom:name", ns) or entry.find("author/name")
        return author.text if author is not None and author.text else ""

    def _get_item_id(self, item: dict[str, Any]) -> str:
        """Get unique identifier for an item."""
        track_by = self.config.config.get("track_by", "id")

        if track_by == "id" or track_by == "guid":
            return item.get("guid", "") or item.get("link", "")
        elif track_by == "link":
            return item.get("link", "")
        elif track_by == "title_hash":
            title = item.get("title", "")
            return sha256(title.encode()).hexdigest()[:16]

        return item.get("guid", "") or item.get("link", "")

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get JSON schema for RSS trigger configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 1,
                },
                "feed_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL of the RSS or Atom feed",
                },
                "poll_interval": {
                    "type": "integer",
                    "minimum": 10,
                    "default": 300,
                    "description": "Polling interval in seconds",
                },
                "max_items": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0,
                    "description": "Max items per poll (0 = unlimited)",
                },
                "filter_title": {
                    "type": "string",
                    "description": "Only trigger on items with this in title",
                },
                "filter_category": {
                    "type": "string",
                    "description": "Only trigger on items in this category",
                },
                "include_content": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include full content in payload",
                },
                "track_by": {
                    "type": "string",
                    "enum": ["id", "link", "guid", "title_hash"],
                    "default": "id",
                    "description": "How to identify unique items",
                },
            },
            "required": ["name", "feed_url"],
        }
