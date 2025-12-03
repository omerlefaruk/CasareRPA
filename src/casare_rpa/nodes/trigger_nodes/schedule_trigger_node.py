"""
CasareRPA - Schedule Trigger Node

Trigger node that fires on a schedule (cron, interval, once).
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import (
    BaseTriggerNode,
    trigger_node,
)
from casare_rpa.triggers.base import TriggerType


@node_schema(
    PropertyDef(
        "frequency",
        PropertyType.CHOICE,
        default="daily",
        choices=["once", "interval", "hourly", "daily", "weekly", "monthly", "cron"],
        label="Frequency",
        tooltip="How often to trigger",
    ),
    # Time settings
    PropertyDef(
        "time_hour",
        PropertyType.INTEGER,
        default=9,
        label="Hour (0-23)",
        tooltip="Hour of day (for daily/weekly/monthly)",
    ),
    PropertyDef(
        "time_minute",
        PropertyType.INTEGER,
        default=0,
        label="Minute (0-59)",
        tooltip="Minute of hour",
    ),
    # Interval settings
    PropertyDef(
        "interval_seconds",
        PropertyType.INTEGER,
        default=60,
        label="Interval (seconds)",
        tooltip="Interval in seconds (for interval mode)",
    ),
    # Weekly/Monthly settings
    PropertyDef(
        "day_of_week",
        PropertyType.CHOICE,
        default="mon",
        choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        label="Day of Week",
        tooltip="Day of week (for weekly)",
    ),
    PropertyDef(
        "day_of_month",
        PropertyType.INTEGER,
        default=1,
        label="Day of Month (1-31)",
        tooltip="Day of month (for monthly)",
    ),
    # Cron
    PropertyDef(
        "cron_expression",
        PropertyType.STRING,
        default="0 9 * * *",
        label="Cron Expression",
        placeholder="0 9 * * *",
        tooltip="Cron expression (minute hour day month weekday)",
    ),
    # Advanced
    PropertyDef(
        "timezone",
        PropertyType.STRING,
        default="UTC",
        label="Timezone",
        placeholder="America/New_York",
        tooltip="Timezone for schedule",
    ),
    PropertyDef(
        "max_runs",
        PropertyType.INTEGER,
        default=0,
        label="Max Runs",
        tooltip="Maximum number of runs (0 = unlimited)",
    ),
    PropertyDef(
        "start_time",
        PropertyType.STRING,
        default="",
        label="Start Time",
        placeholder="2024-01-01T09:00:00",
        tooltip="When to start (for once mode)",
    ),
)
@trigger_node
class ScheduleTriggerNode(BaseTriggerNode):
    """
    Schedule trigger node that fires on a time-based schedule.

    Outputs:
    - trigger_time: When the trigger fired (ISO format)
    - run_number: How many times this trigger has fired
    - scheduled_time: The originally scheduled time
    """

    trigger_display_name = "Schedule"
    trigger_description = "Trigger workflow on a schedule"
    trigger_icon = "schedule"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "Schedule Trigger"
        self.node_type = "ScheduleTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define schedule-specific output ports."""
        self.add_output_port("trigger_time", DataType.STRING, "Trigger Time")
        self.add_output_port("run_number", DataType.INTEGER, "Run Number")
        self.add_output_port("scheduled_time", DataType.STRING, "Scheduled Time")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.SCHEDULED

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get schedule-specific configuration."""
        return {
            "frequency": self.config.get("frequency", "daily"),
            "time_hour": self.config.get("time_hour", 9),
            "time_minute": self.config.get("time_minute", 0),
            "interval_seconds": self.config.get("interval_seconds", 60),
            "day_of_week": self.config.get("day_of_week", "mon"),
            "day_of_month": self.config.get("day_of_month", 1),
            "cron_expression": self.config.get("cron_expression", "0 9 * * *"),
            "timezone": self.config.get("timezone", "UTC"),
            "max_runs": self.config.get("max_runs", 0),
            "start_time": self.config.get("start_time", ""),
        }
