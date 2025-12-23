"""
CasareRPA - XES Exporter Module

Exports execution traces to IEEE XES (eXtensible Event Stream) format,
the standard interchange format for process mining tools.

XES Format Reference: https://www.xes-standard.org/

Features:
- Full XES 2.0 compliance with extensions
- Optional attribute inclusion (inputs/outputs)
- Lifecycle state transitions
- Streaming export for large trace sets
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from casare_rpa.infrastructure.analytics.process_mining import (
    Activity,
    ActivityStatus,
    ExecutionTrace,
)

# =============================================================================
# XES Constants
# =============================================================================

XES_NAMESPACE = "http://www.xes-standard.org/"
XES_VERSION = "2.0"

# Standard XES extensions
CONCEPT_EXTENSION = "http://www.xes-standard.org/concept.xesext"
TIME_EXTENSION = "http://www.xes-standard.org/time.xesext"
LIFECYCLE_EXTENSION = "http://www.xes-standard.org/lifecycle.xesext"
ORGANIZATIONAL_EXTENSION = "http://www.xes-standard.org/org.xesext"

# Lifecycle transition mapping
LIFECYCLE_MAP: dict[ActivityStatus, str] = {
    ActivityStatus.COMPLETED: "complete",
    ActivityStatus.FAILED: "ate_abort",  # abnormal termination
    ActivityStatus.SKIPPED: "pi_abort",  # process instance abort
    ActivityStatus.TIMEOUT: "ate_abort",
}


# =============================================================================
# XES Exporter
# =============================================================================


class XESExporter:
    """
    Export execution traces to XES format.

    XES (eXtensible Event Stream) is the IEEE standard format for
    process mining data interchange (IEEE 1849-2016).

    Usage:
        exporter = XESExporter()
        xes_content = exporter.export_to_xes(traces, include_attributes=True)
        exporter.export_to_file(traces, "output.xes")
    """

    def __init__(self) -> None:
        """Initialize XES exporter."""
        self._include_casare_extension = True

    def export_to_xes(
        self,
        traces: list[ExecutionTrace],
        include_attributes: bool = True,
        include_lifecycle: bool = True,
        classifier_name: str = "Activity Classifier",
    ) -> str:
        """
        Export traces to XES format string.

        Args:
            traces: List of execution traces to export.
            include_attributes: Include node inputs/outputs as XES attributes.
            include_lifecycle: Include lifecycle transition states.
            classifier_name: Name for the event classifier.

        Returns:
            XES XML string content.

        Raises:
            ValueError: If traces list is empty.
        """
        if not traces:
            raise ValueError("Cannot export empty trace list")

        logger.info(f"Exporting {len(traces)} traces to XES format")

        root = self._build_xes_root(traces, classifier_name)

        # Add extensions
        self._add_extensions(root, include_attributes)

        # Add global attributes
        self._add_global_attributes(root, classifier_name)

        # Add traces
        for trace in traces:
            trace_elem = self._build_trace_element(trace, include_attributes, include_lifecycle)
            root.append(trace_elem)

        # Generate XML string with proper formatting
        xml_str = self._element_to_string(root)
        logger.debug(f"Generated XES content: {len(xml_str)} characters")
        return xml_str

    def export_to_file(
        self,
        traces: list[ExecutionTrace],
        output_path: str | Path,
        include_attributes: bool = True,
        include_lifecycle: bool = True,
    ) -> str:
        """
        Export traces to XES file.

        Args:
            traces: List of execution traces to export.
            output_path: File path for output.
            include_attributes: Include node inputs/outputs as XES attributes.
            include_lifecycle: Include lifecycle transition states.

        Returns:
            Absolute path to created file.

        Raises:
            ValueError: If traces list is empty.
            OSError: If file cannot be written.
        """
        output_path = Path(output_path)

        # Ensure .xes extension
        if output_path.suffix.lower() != ".xes":
            output_path = output_path.with_suffix(".xes")

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        xes_content = self.export_to_xes(traces, include_attributes, include_lifecycle)

        try:
            output_path.write_text(xes_content, encoding="utf-8")
            logger.info(f"Exported XES file: {output_path}")
            return str(output_path.absolute())
        except OSError as e:
            logger.error(f"Failed to write XES file {output_path}: {e}")
            raise

    def _build_xes_root(self, traces: list[ExecutionTrace], classifier_name: str) -> ET.Element:
        """Build XES root element with attributes."""
        root = ET.Element("log")
        root.set("xes.version", XES_VERSION)
        root.set("xes.features", "nested-attributes")
        root.set("xmlns", XES_NAMESPACE)

        # Add source info
        source_elem = ET.SubElement(root, "string")
        source_elem.set("key", "source")
        source_elem.set("value", "CasareRPA")

        # Add workflow info from first trace
        if traces:
            workflow_elem = ET.SubElement(root, "string")
            workflow_elem.set("key", "workflow:name")
            workflow_elem.set("value", traces[0].workflow_name)

            workflow_id_elem = ET.SubElement(root, "string")
            workflow_id_elem.set("key", "workflow:id")
            workflow_id_elem.set("value", traces[0].workflow_id)

        return root

    def _add_extensions(self, root: ET.Element, include_attributes: bool) -> None:
        """Add XES extension declarations."""
        extensions = [
            ("Concept", CONCEPT_EXTENSION, "concept"),
            ("Time", TIME_EXTENSION, "time"),
            ("Lifecycle", LIFECYCLE_EXTENSION, "lifecycle"),
            ("Organizational", ORGANIZATIONAL_EXTENSION, "org"),
        ]

        for name, uri, prefix in extensions:
            ext_elem = ET.SubElement(root, "extension")
            ext_elem.set("name", name)
            ext_elem.set("prefix", prefix)
            ext_elem.set("uri", uri)

        # Add CasareRPA custom extension for attributes
        if include_attributes and self._include_casare_extension:
            ext_elem = ET.SubElement(root, "extension")
            ext_elem.set("name", "CasareRPA")
            ext_elem.set("prefix", "casare")
            ext_elem.set("uri", "http://casarerpa.com/xes/casare.xesext")

    def _add_global_attributes(self, root: ET.Element, classifier_name: str) -> None:
        """Add global attributes and classifiers."""
        # Classifier
        classifier = ET.SubElement(root, "classifier")
        classifier.set("name", classifier_name)
        classifier.set("keys", "concept:name")

        # Global trace attributes
        global_trace = ET.SubElement(root, "global")
        global_trace.set("scope", "trace")

        trace_name = ET.SubElement(global_trace, "string")
        trace_name.set("key", "concept:name")
        trace_name.set("value", "UNKNOWN")

        # Global event attributes
        global_event = ET.SubElement(root, "global")
        global_event.set("scope", "event")

        event_name = ET.SubElement(global_event, "string")
        event_name.set("key", "concept:name")
        event_name.set("value", "UNKNOWN")

        event_time = ET.SubElement(global_event, "date")
        event_time.set("key", "time:timestamp")
        event_time.set("value", "1970-01-01T00:00:00.000+00:00")

    def _build_trace_element(
        self,
        trace: ExecutionTrace,
        include_attributes: bool,
        include_lifecycle: bool,
    ) -> ET.Element:
        """Build XES trace element from ExecutionTrace."""
        trace_elem = ET.Element("trace")

        # Trace name (case ID)
        name_elem = ET.SubElement(trace_elem, "string")
        name_elem.set("key", "concept:name")
        name_elem.set("value", trace.case_id)

        # Workflow info
        workflow_elem = ET.SubElement(trace_elem, "string")
        workflow_elem.set("key", "workflow:name")
        workflow_elem.set("value", trace.workflow_name)

        workflow_id_elem = ET.SubElement(trace_elem, "string")
        workflow_id_elem.set("key", "workflow:id")
        workflow_id_elem.set("value", trace.workflow_id)

        # Variant hash
        variant_elem = ET.SubElement(trace_elem, "string")
        variant_elem.set("key", "variant")
        variant_elem.set("value", trace.variant)

        # Trace status
        status_elem = ET.SubElement(trace_elem, "string")
        status_elem.set("key", "status")
        status_elem.set("value", trace.status)

        # Robot ID if present
        if trace.robot_id:
            robot_elem = ET.SubElement(trace_elem, "string")
            robot_elem.set("key", "org:resource")
            robot_elem.set("value", trace.robot_id)

        # Total duration
        duration_elem = ET.SubElement(trace_elem, "int")
        duration_elem.set("key", "duration:ms")
        duration_elem.set("value", str(trace.total_duration_ms))

        # Add events for each activity
        for i, activity in enumerate(trace.activities):
            event_elem = self._build_event_element(
                activity, i, include_attributes, include_lifecycle
            )
            trace_elem.append(event_elem)

        return trace_elem

    def _build_event_element(
        self,
        activity: Activity,
        sequence_number: int,
        include_attributes: bool,
        include_lifecycle: bool,
    ) -> ET.Element:
        """Build XES event element from Activity."""
        event_elem = ET.Element("event")

        # Activity name (node_type is more meaningful than node_id)
        name_elem = ET.SubElement(event_elem, "string")
        name_elem.set("key", "concept:name")
        name_elem.set("value", activity.node_type)

        # Node ID for traceability
        node_id_elem = ET.SubElement(event_elem, "string")
        node_id_elem.set("key", "casare:node_id")
        node_id_elem.set("value", activity.node_id)

        # Timestamp
        timestamp_elem = ET.SubElement(event_elem, "date")
        timestamp_elem.set("key", "time:timestamp")
        timestamp_elem.set("value", self._format_timestamp(activity.timestamp))

        # Duration
        duration_elem = ET.SubElement(event_elem, "int")
        duration_elem.set("key", "duration:ms")
        duration_elem.set("value", str(activity.duration_ms))

        # Sequence number
        seq_elem = ET.SubElement(event_elem, "int")
        seq_elem.set("key", "sequence")
        seq_elem.set("value", str(sequence_number))

        # Lifecycle transition
        if include_lifecycle:
            lifecycle_elem = ET.SubElement(event_elem, "string")
            lifecycle_elem.set("key", "lifecycle:transition")
            lifecycle_elem.set("value", LIFECYCLE_MAP.get(activity.status, "complete"))

        # Status
        status_elem = ET.SubElement(event_elem, "string")
        status_elem.set("key", "status")
        status_elem.set("value", activity.status.value)

        # Error message if present
        if activity.error_message:
            error_elem = ET.SubElement(event_elem, "string")
            error_elem.set("key", "error:message")
            error_elem.set("value", activity.error_message)

        # Include inputs/outputs as nested attributes
        if include_attributes:
            if activity.inputs:
                self._add_data_attributes(event_elem, "inputs", activity.inputs)
            if activity.outputs:
                self._add_data_attributes(event_elem, "outputs", activity.outputs)

        return event_elem

    def _add_data_attributes(
        self, parent: ET.Element, key_prefix: str, data: dict[str, Any]
    ) -> None:
        """Add dictionary data as XES attributes."""
        for key, value in data.items():
            attr_key = f"casare:{key_prefix}:{key}"
            self._add_typed_attribute(parent, attr_key, value)

    def _add_typed_attribute(self, parent: ET.Element, key: str, value: Any) -> None:
        """Add a typed XES attribute based on Python value type."""
        if value is None:
            return

        if isinstance(value, bool):
            elem = ET.SubElement(parent, "boolean")
            elem.set("key", key)
            elem.set("value", str(value).lower())
        elif isinstance(value, int):
            elem = ET.SubElement(parent, "int")
            elem.set("key", key)
            elem.set("value", str(value))
        elif isinstance(value, float):
            elem = ET.SubElement(parent, "float")
            elem.set("key", key)
            elem.set("value", str(value))
        elif isinstance(value, datetime):
            elem = ET.SubElement(parent, "date")
            elem.set("key", key)
            elem.set("value", self._format_timestamp(value))
        elif isinstance(value, (list, dict)):
            # Complex types stored as string representation
            elem = ET.SubElement(parent, "string")
            elem.set("key", key)
            elem.set("value", str(value)[:1000])  # Truncate large values
        else:
            elem = ET.SubElement(parent, "string")
            elem.set("key", key)
            elem.set("value", str(value))

    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime to XES timestamp format (ISO 8601 with timezone)."""
        if dt.tzinfo is None:
            # Assume UTC if no timezone
            return dt.strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
        return dt.isoformat()

    def _element_to_string(self, root: ET.Element) -> str:
        """Convert element tree to formatted XML string."""
        # Use ElementTree to get XML declaration
        tree = ET.ElementTree(root)
        output = StringIO()

        # Write with XML declaration
        tree.write(
            output,
            encoding="unicode",
            xml_declaration=True,
        )

        xml_str = output.getvalue()

        # Add proper formatting (indent)
        try:
            # Python 3.9+ has indent function
            from xml.dom import minidom

            parsed = minidom.parseString(xml_str)
            formatted = parsed.toprettyxml(indent="  ")
            # Remove extra blank lines
            lines = [line for line in formatted.split("\n") if line.strip()]
            return "\n".join(lines)
        except Exception:
            # Fallback: return as-is
            return xml_str


# =============================================================================
# XES Import (for completeness)
# =============================================================================


class XESImporter:
    """
    Import execution traces from XES format.

    Supports reading XES files generated by other process mining tools
    for conformance checking or analysis.
    """

    def import_from_file(self, file_path: str | Path) -> list[ExecutionTrace]:
        """
        Import traces from XES file.

        Args:
            file_path: Path to XES file.

        Returns:
            List of ExecutionTrace objects.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file is not valid XES.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"XES file not found: {file_path}")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self._parse_xes_root(root)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XES file {file_path}: {e}")
            raise ValueError(f"Invalid XES format: {e}") from e

    def import_from_string(self, xes_content: str) -> list[ExecutionTrace]:
        """
        Import traces from XES string content.

        Args:
            xes_content: XES XML string.

        Returns:
            List of ExecutionTrace objects.

        Raises:
            ValueError: If content is not valid XES.
        """
        try:
            root = ET.fromstring(xes_content)
            return self._parse_xes_root(root)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XES content: {e}")
            raise ValueError(f"Invalid XES format: {e}") from e

    def _parse_xes_root(self, root: ET.Element) -> list[ExecutionTrace]:
        """Parse XES root element to extract traces."""
        traces: list[ExecutionTrace] = []

        # Remove namespace prefix if present
        ns = {"": XES_NAMESPACE}

        for trace_elem in root.findall("trace", ns) or root.findall("trace"):
            trace = self._parse_trace_element(trace_elem)
            if trace:
                traces.append(trace)

        logger.info(f"Imported {len(traces)} traces from XES")
        return traces

    def _parse_trace_element(self, trace_elem: ET.Element) -> ExecutionTrace | None:
        """Parse XES trace element to ExecutionTrace."""
        # Extract trace attributes
        case_id = self._get_string_attr(trace_elem, "concept:name", "unknown")
        workflow_name = self._get_string_attr(trace_elem, "workflow:name", "unknown")
        workflow_id = self._get_string_attr(trace_elem, "workflow:id", "unknown")
        status = self._get_string_attr(trace_elem, "status", "completed")
        robot_id = self._get_string_attr(trace_elem, "org:resource")

        # Parse events
        activities: list[Activity] = []
        start_time: datetime | None = None
        end_time: datetime | None = None

        for event_elem in trace_elem.findall("event"):
            activity = self._parse_event_element(event_elem)
            if activity:
                activities.append(activity)
                if start_time is None or activity.timestamp < start_time:
                    start_time = activity.timestamp
                if end_time is None or activity.timestamp > end_time:
                    end_time = activity.timestamp

        if not activities:
            return None

        return ExecutionTrace(
            case_id=case_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            activities=activities,
            start_time=start_time or datetime.now(),
            end_time=end_time,
            status=status,
            robot_id=robot_id,
        )

    def _parse_event_element(self, event_elem: ET.Element) -> Activity | None:
        """Parse XES event element to Activity."""
        node_type = self._get_string_attr(event_elem, "concept:name", "unknown")
        node_id = self._get_string_attr(event_elem, "casare:node_id", node_type)
        timestamp_str = self._get_date_attr(event_elem, "time:timestamp")
        duration_ms = self._get_int_attr(event_elem, "duration:ms", 0)
        status_str = self._get_string_attr(event_elem, "status", "completed")
        error_message = self._get_string_attr(event_elem, "error:message")

        # Parse timestamp
        timestamp = datetime.now()
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("+00:00", "+00:00"))
            except ValueError:
                pass

        # Map status
        try:
            status = ActivityStatus(status_str)
        except ValueError:
            status = ActivityStatus.COMPLETED

        return Activity(
            node_id=node_id,
            node_type=node_type,
            timestamp=timestamp,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
        )

    def _get_string_attr(
        self,
        elem: ET.Element,
        key: str,
        default: str | None = None,
    ) -> str | None:
        """Get string attribute value from element."""
        for child in elem.findall("string"):
            if child.get("key") == key:
                return child.get("value", default)
        return default

    def _get_int_attr(self, elem: ET.Element, key: str, default: int = 0) -> int:
        """Get integer attribute value from element."""
        for child in elem.findall("int"):
            if child.get("key") == key:
                try:
                    return int(child.get("value", default))
                except ValueError:
                    return default
        return default

    def _get_date_attr(self, elem: ET.Element, key: str) -> str | None:
        """Get date attribute value from element."""
        for child in elem.findall("date"):
            if child.get("key") == key:
                return child.get("value")
        return None


__all__ = [
    "XESExporter",
    "XESImporter",
    "XES_NAMESPACE",
    "XES_VERSION",
]
