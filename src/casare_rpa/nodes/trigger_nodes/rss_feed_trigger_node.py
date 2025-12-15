"""
CasareRPA - RSS Feed Trigger Node

Trigger node that fires when new RSS feed items are published.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


# Add RSS_FEED to TriggerType if not present - this will need to be added to base.py
# For now, we'll use a placeholder that maps to WEBHOOK or create custom handling


@properties(
    PropertyDef(
        "feed_url",
        PropertyType.STRING,
        required=True,
        label="Feed URL",
        placeholder="https://example.com/rss.xml",
        tooltip="URL of the RSS/Atom feed",
    ),
    PropertyDef(
        "poll_interval_minutes",
        PropertyType.INTEGER,
        default=15,
        label="Poll Interval (minutes)",
        tooltip="How often to check for new items",
    ),
    PropertyDef(
        "filter_keywords",
        PropertyType.STRING,
        default="",
        label="Filter Keywords",
        placeholder="python,automation",
        tooltip="Comma-separated keywords to filter items",
    ),
    PropertyDef(
        "filter_mode",
        PropertyType.CHOICE,
        default="any",
        choices=["any", "all", "none"],
        label="Filter Mode",
        tooltip="Match any/all/none of the keywords",
    ),
    PropertyDef(
        "max_items_per_check",
        PropertyType.INTEGER,
        default=10,
        label="Max Items per Check",
        tooltip="Maximum items to process per poll",
    ),
    PropertyDef(
        "include_description",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Description",
        tooltip="Include full description in output",
    ),
)
@node(category="triggers", exec_inputs=[])
class RSSFeedTriggerNode(BaseTriggerNode):
    """
    RSS Feed trigger node that fires when new items are published.

    Outputs:
    - item: Full RSS item object
    - title: Item title
    - link: Item URL
    - description: Item description/summary
    - published: Publication date
    - author: Item author
    - categories: List of categories/tags
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "RSS Feed"
    trigger_description = "Trigger on new RSS feed items"
    trigger_icon = "rss"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "RSS Feed Trigger"
        self.node_type = "RSSFeedTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define RSS-specific output ports."""
        self.add_output_port("item", DataType.DICT, "RSS Item")
        self.add_output_port("title", DataType.STRING, "Title")
        self.add_output_port("link", DataType.STRING, "Link")
        self.add_output_port("description", DataType.STRING, "Description")
        self.add_output_port("published", DataType.STRING, "Published Date")
        self.add_output_port("author", DataType.STRING, "Author")
        self.add_output_port("categories", DataType.LIST, "Categories")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.RSS_FEED

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get RSS-specific configuration."""
        keywords_str = self.config.get("filter_keywords", "")
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]

        return {
            "feed_url": self.config.get("feed_url", ""),
            "poll_interval_minutes": self.config.get("poll_interval_minutes", 15),
            "filter_keywords": keywords,
            "filter_mode": self.config.get("filter_mode", "any"),
            "max_items_per_check": self.config.get("max_items_per_check", 10),
            "include_description": self.config.get("include_description", True),
            # Mark as RSS feed for the trigger implementation
            "_trigger_subtype": "rss_feed",
        }
