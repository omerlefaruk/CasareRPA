"""
CasareRPA - Schedule Trigger Node

Trigger node that fires on a schedule (cron, interval, once).
"""

from typing import Any, Dict

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    PropertyDef(
        "frequency",
        PropertyType.CHOICE,
        default="daily",
        choices=["once", "interval", "hourly", "daily", "weekly", "monthly", "cron"],
        label="Frequency",
        tooltip="How often to trigger",
        essential=True,
    ),
    # Time settings
    PropertyDef(
        "time_hour",
        PropertyType.INTEGER,
        default=9,
        label="Hour (0-23)",
        tooltip="Hour of day (for daily/weekly/monthly)",
        display_when={"frequency": ["daily", "weekly", "monthly"]},
    ),
    PropertyDef(
        "time_minute",
        PropertyType.INTEGER,
        default=0,
        label="Minute (0-59)",
        tooltip="Minute of hour",
        display_when={"frequency": ["hourly", "daily", "weekly", "monthly"]},
    ),
    # Interval settings
    PropertyDef(
        "interval_seconds",
        PropertyType.INTEGER,
        default=60,
        label="Interval (seconds)",
        tooltip="Interval in seconds (for interval mode)",
        display_when={"frequency": "interval"},
    ),
    # Weekly/Monthly settings
    PropertyDef(
        "day_of_week",
        PropertyType.CHOICE,
        default="mon",
        choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        label="Day of Week",
        tooltip="Day of week (for weekly)",
        display_when={"frequency": "weekly"},
    ),
    PropertyDef(
        "day_of_month",
        PropertyType.INTEGER,
        default=1,
        label="Day of Month (1-31)",
        tooltip="Day of month (for monthly)",
        display_when={"frequency": "monthly"},
    ),
    # Cron
    PropertyDef(
        "cron_expression",
        PropertyType.STRING,
        default="0 9 * * *",
        label="Cron Expression",
        placeholder="0 9 * * *",
        tooltip="Cron expression (minute hour day month weekday)",
        display_when={"frequency": "cron"},
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
        display_when={"frequency": "once"},
    ),
)
@node(category="triggers", exec_inputs=[])
class ScheduleTriggerNode(BaseTriggerNode):
    """
    Schedule trigger node that fires on a time-based schedule.

    Outputs:
    - trigger_time: When the trigger fired (ISO format)
    - run_number: How many times this trigger has fired
    - scheduled_time: The originally scheduled time
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Schedule"
    trigger_description = "Trigger workflow on a schedule"
    trigger_icon = "schedule"
    trigger_category = "triggers"

    def __init__(self, node_id: str, **kwargs) -> None:
        super().__init__(node_id, **kwargs)
        self.name = "Schedule Trigger"
        self.node_type = "ScheduleTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define schedule-specific output ports."""
        self.add_output_port("trigger_time", DataType.STRING, "Trigger Time")
        self.add_output_port("run_number", DataType.INTEGER, "Run Number")
        self.add_output_port("scheduled_time", DataType.STRING, "Scheduled Time")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.SCHEDULED

    def get_trigger_config(self) -> dict[str, Any]:
        """Get schedule-specific configuration."""
        return {
            "frequency": self.get_parameter("frequency", "daily"),
            "time_hour": self.get_parameter("time_hour", 9),
            "time_minute": self.get_parameter("time_minute", 0),
            "interval_seconds": self.get_parameter("interval_seconds", 60),
            "day_of_week": self.get_parameter("day_of_week", "mon"),
            "day_of_month": self.get_parameter("day_of_month", 1),
            "cron_expression": self.get_parameter("cron_expression", "0 9 * * *"),
            "timezone": self.get_parameter("timezone", "UTC"),
            "max_runs": self.get_parameter("max_runs", 0),
            "start_time": self.get_parameter("start_time", ""),
        }
