"""
DateTime nodes for CasareRPA.

This module provides nodes for date and time operations:
- GetCurrentDateTimeNode: Get current date/time
- FormatDateTimeNode: Format datetime to string
- ParseDateTimeNode: Parse datetime from string
- DateTimeAddNode: Add/subtract time intervals
- DateTimeDiffNode: Calculate difference between dates
- DateTimeCompareNode: Compare two dates
"""

from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.utils.type_converters import safe_int


@executable_node
class GetCurrentDateTimeNode(BaseNode):
    """
    Get the current date and time.

    Config:
        timezone: Timezone name (default: local)
        format: Output format string (default: ISO format)

    Outputs:
        datetime: Formatted datetime string
        timestamp: Unix timestamp
        year, month, day, hour, minute, second: Individual components
        day_of_week: Day name (Monday, Tuesday, etc.)
    """

    def __init__(
        self, node_id: str, name: str = "Get Current DateTime", **kwargs
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetCurrentDateTimeNode"

    def _define_ports(self) -> None:
        self.add_output_port("datetime", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("timestamp", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("year", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("month", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("day", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("hour", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("minute", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("second", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("day_of_week", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            tz_name = self.config.get("timezone", "")
            fmt = self.config.get("format", "")

            # Resolve {{variable}} patterns
            tz_name = context.resolve_value(tz_name)
            fmt = context.resolve_value(fmt)

            if tz_name and ZoneInfo:
                try:
                    tz = ZoneInfo(tz_name)
                    now = datetime.now(tz)
                except Exception:
                    now = datetime.now()
            else:
                now = datetime.now()

            if fmt:
                formatted = now.strftime(fmt)
            else:
                formatted = now.isoformat()

            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]

            self.set_output_value("datetime", formatted)
            self.set_output_value("timestamp", now.timestamp())
            self.set_output_value("year", now.year)
            self.set_output_value("month", now.month)
            self.set_output_value("day", now.day)
            self.set_output_value("hour", now.hour)
            self.set_output_value("minute", now.minute)
            self.set_output_value("second", now.second)
            self.set_output_value("day_of_week", day_names[now.weekday()])
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"datetime": formatted},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class FormatDateTimeNode(BaseNode):
    """
    Format a datetime to a string.

    Config:
        format: strftime format string (default: %Y-%m-%d %H:%M:%S)

    Inputs:
        datetime: DateTime string or timestamp to format
        input_format: Input format if datetime is a string (optional)

    Outputs:
        result: Formatted datetime string
    """

    def __init__(self, node_id: str, name: str = "Format DateTime", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FormatDateTimeNode"

    def _define_ports(self) -> None:
        self.add_input_port("datetime", PortType.INPUT, DataType.ANY)
        self.add_input_port("input_format", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dt_input = self.get_input_value("datetime", context)
            input_format = self.get_input_value("input_format", context)
            output_format = self.config.get("format", "%Y-%m-%d %H:%M:%S")

            # Resolve {{variable}} patterns
            if input_format:
                input_format = context.resolve_value(input_format)
            output_format = context.resolve_value(output_format)

            # Parse input
            if isinstance(dt_input, datetime):
                dt = dt_input
            elif isinstance(dt_input, (int, float)):
                dt = datetime.fromtimestamp(dt_input)
            elif isinstance(dt_input, str):
                if input_format:
                    dt = datetime.strptime(dt_input, input_format)
                else:
                    # Try common formats
                    for fmt in [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%d",
                        "%d/%m/%Y",
                        "%m/%d/%Y",
                    ]:
                        try:
                            dt = datetime.strptime(dt_input, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        dt = datetime.fromisoformat(dt_input.replace("Z", "+00:00"))
            else:
                raise ValueError(f"Cannot parse datetime from: {type(dt_input)}")

            result = dt.strftime(output_format)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class ParseDateTimeNode(BaseNode):
    """
    Parse a datetime string into components.

    Config:
        format: Expected format string (optional, will try auto-detect)

    Inputs:
        datetime_string: The datetime string to parse

    Outputs:
        timestamp: Unix timestamp
        year, month, day, hour, minute, second: Components
        iso_format: ISO formatted string
        success: Whether parsing succeeded
    """

    def __init__(self, node_id: str, name: str = "Parse DateTime", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ParseDateTimeNode"

    def _define_ports(self) -> None:
        self.add_input_port("datetime_string", PortType.INPUT, DataType.STRING)
        self.add_output_port("timestamp", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("year", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("month", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("day", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("hour", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("minute", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("second", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("iso_format", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dt_string = self.get_input_value("datetime_string", context)
            fmt = self.config.get("format", "")

            # Resolve {{variable}} patterns
            if dt_string:
                dt_string = context.resolve_value(dt_string)
            if fmt:
                fmt = context.resolve_value(fmt)

            if not dt_string:
                raise ValueError("datetime_string is required")

            dt = None
            if fmt:
                dt = datetime.strptime(dt_string, fmt)
            else:
                # Try common formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%d",
                    "%d/%m/%Y %H:%M:%S",
                    "%d/%m/%Y",
                    "%m/%d/%Y %H:%M:%S",
                    "%m/%d/%Y",
                    "%d-%m-%Y",
                    "%Y/%m/%d",
                ]
                for f in formats:
                    try:
                        dt = datetime.strptime(dt_string, f)
                        break
                    except ValueError:
                        continue

                if dt is None:
                    # Try ISO format with timezone
                    dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))

            self.set_output_value("timestamp", dt.timestamp())
            self.set_output_value("year", dt.year)
            self.set_output_value("month", dt.month)
            self.set_output_value("day", dt.day)
            self.set_output_value("hour", dt.hour)
            self.set_output_value("minute", dt.minute)
            self.set_output_value("second", dt.second)
            self.set_output_value("iso_format", dt.isoformat())
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"iso_format": dt.isoformat()},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class DateTimeAddNode(BaseNode):
    """
    Add or subtract time from a datetime.

    Inputs:
        datetime: Base datetime (string, timestamp, or datetime object)
        days: Days to add (negative to subtract)
        hours: Hours to add
        minutes: Minutes to add
        seconds: Seconds to add
        weeks: Weeks to add
        months: Months to add (approximate, adds 30 days per month)
        years: Years to add (approximate, adds 365 days per year)

    Outputs:
        result: Resulting datetime (ISO format)
        timestamp: Resulting Unix timestamp
    """

    def __init__(self, node_id: str, name: str = "DateTime Add", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DateTimeAddNode"

    def _define_ports(self) -> None:
        self.add_input_port("datetime", PortType.INPUT, DataType.ANY)
        self.add_input_port("years", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("months", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("weeks", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("days", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("hours", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("minutes", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("seconds", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("timestamp", PortType.OUTPUT, DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dt_input = self.get_input_value("datetime", context)
            years = safe_int(self.get_input_value("years", context), 0)
            months = safe_int(self.get_input_value("months", context), 0)
            weeks = safe_int(self.get_input_value("weeks", context), 0)
            days = safe_int(self.get_input_value("days", context), 0)
            hours = safe_int(self.get_input_value("hours", context), 0)
            minutes = safe_int(self.get_input_value("minutes", context), 0)
            seconds = safe_int(self.get_input_value("seconds", context), 0)

            # Parse input datetime
            if dt_input is None:
                dt = datetime.now()
            elif isinstance(dt_input, datetime):
                dt = dt_input
            elif isinstance(dt_input, (int, float)):
                dt = datetime.fromtimestamp(dt_input)
            elif isinstance(dt_input, str):
                dt = datetime.fromisoformat(dt_input.replace("Z", "+00:00"))
            else:
                raise ValueError(f"Cannot parse datetime from: {type(dt_input)}")

            # Convert years and months to days (approximate)
            total_days = days + (years * 365) + (months * 30) + (weeks * 7)

            # Add the delta
            delta = timedelta(
                days=total_days, hours=hours, minutes=minutes, seconds=seconds
            )
            result_dt = dt + delta

            self.set_output_value("result", result_dt.isoformat())
            self.set_output_value("timestamp", result_dt.timestamp())
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result_dt.isoformat()},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class DateTimeDiffNode(BaseNode):
    """
    Calculate the difference between two datetimes.

    Inputs:
        datetime_1: First datetime (start)
        datetime_2: Second datetime (end)

    Outputs:
        total_seconds: Total difference in seconds
        total_minutes: Total difference in minutes
        total_hours: Total difference in hours
        total_days: Total difference in days
        days: Days component
        hours: Hours component (after days)
        minutes: Minutes component (after hours)
        seconds: Seconds component (after minutes)
    """

    def __init__(self, node_id: str, name: str = "DateTime Diff", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DateTimeDiffNode"

    def _define_ports(self) -> None:
        self.add_input_port("datetime_1", PortType.INPUT, DataType.ANY)
        self.add_input_port("datetime_2", PortType.INPUT, DataType.ANY)
        self.add_output_port("total_seconds", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("total_minutes", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("total_hours", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("total_days", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("days", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("hours", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("minutes", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("seconds", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:

            def parse_dt(val):
                if isinstance(val, datetime):
                    return val
                elif isinstance(val, (int, float)):
                    return datetime.fromtimestamp(val)
                elif isinstance(val, str):
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                else:
                    raise ValueError(f"Cannot parse datetime from: {type(val)}")

            dt1 = parse_dt(self.get_input_value("datetime_1", context))
            dt2 = parse_dt(self.get_input_value("datetime_2", context))

            delta = dt2 - dt1
            total_seconds = delta.total_seconds()

            # Calculate total units
            total_minutes = total_seconds / 60
            total_hours = total_seconds / 3600
            total_days = total_seconds / 86400

            # Break down into components
            abs_seconds = abs(total_seconds)
            days = int(abs_seconds // 86400)
            remaining = abs_seconds % 86400
            hours = int(remaining // 3600)
            remaining = remaining % 3600
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)

            # Preserve sign for days
            if total_seconds < 0:
                days = -days

            self.set_output_value("total_seconds", total_seconds)
            self.set_output_value("total_minutes", total_minutes)
            self.set_output_value("total_hours", total_hours)
            self.set_output_value("total_days", total_days)
            self.set_output_value("days", days)
            self.set_output_value("hours", hours)
            self.set_output_value("minutes", minutes)
            self.set_output_value("seconds", seconds)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"total_seconds": total_seconds, "days": days},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class DateTimeCompareNode(BaseNode):
    """
    Compare two datetimes.

    Inputs:
        datetime_1: First datetime
        datetime_2: Second datetime

    Outputs:
        is_before: datetime_1 < datetime_2
        is_after: datetime_1 > datetime_2
        is_equal: datetime_1 == datetime_2
        comparison: -1, 0, or 1
    """

    def __init__(self, node_id: str, name: str = "DateTime Compare", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DateTimeCompareNode"

    def _define_ports(self) -> None:
        self.add_input_port("datetime_1", PortType.INPUT, DataType.ANY)
        self.add_input_port("datetime_2", PortType.INPUT, DataType.ANY)
        self.add_output_port("is_before", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("is_after", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("is_equal", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("comparison", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:

            def parse_dt(val):
                if isinstance(val, datetime):
                    return val
                elif isinstance(val, (int, float)):
                    return datetime.fromtimestamp(val)
                elif isinstance(val, str):
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                else:
                    raise ValueError(f"Cannot parse datetime from: {type(val)}")

            dt1 = parse_dt(self.get_input_value("datetime_1", context))
            dt2 = parse_dt(self.get_input_value("datetime_2", context))

            is_before = dt1 < dt2
            is_after = dt1 > dt2
            is_equal = dt1 == dt2

            if is_before:
                comparison = -1
            elif is_after:
                comparison = 1
            else:
                comparison = 0

            self.set_output_value("is_before", is_before)
            self.set_output_value("is_after", is_after)
            self.set_output_value("is_equal", is_equal)
            self.set_output_value("comparison", comparison)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"comparison": comparison},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class GetTimestampNode(BaseNode):
    """
    Get current Unix timestamp.

    Config:
        milliseconds: Return milliseconds instead of seconds (default: False)

    Outputs:
        timestamp: Unix timestamp
    """

    def __init__(self, node_id: str, name: str = "Get Timestamp", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetTimestampNode"

    def _define_ports(self) -> None:
        self.add_output_port("timestamp", PortType.OUTPUT, DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            milliseconds = self.config.get("milliseconds", False)

            ts = datetime.now().timestamp()
            if milliseconds:
                ts = ts * 1000

            self.set_output_value("timestamp", ts)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"timestamp": ts},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
