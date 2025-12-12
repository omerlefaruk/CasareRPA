"""
Visual nodes for workflow orchestration.

Provides visual representation for CallSubworkflowNode and related
workflow orchestration nodes.
"""

from typing import Any, Dict, List

from loguru import logger

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType


class VisualCallSubworkflowNode(VisualNode):
    """
    Visual node for CallSubworkflowNode.

    Allows visual configuration of subworkflow calls with support for:
    - Subworkflow picker button
    - Dynamic ports based on selected subworkflow
    - Execution mode configuration
    """

    __identifier__ = "casare_rpa.workflow"
    NODE_NAME = "Call Subworkflow"
    NODE_CATEGORY = "Workflow"

    def __init__(self) -> None:
        """Initialize the visual node."""
        super().__init__()

        self._selected_subworkflow_id: str = ""
        self._selected_subworkflow_name: str = ""
        self._dynamic_inputs: List[str] = []
        self._dynamic_outputs: List[str] = []

        self._apply_styling()

    def setup_ports(self) -> None:
        """Setup default ports."""
        # Exec ports
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_exec_output("error")

        # Standard outputs
        self.add_typed_output("job_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("execution_time_ms", DataType.INTEGER)

    def setup_widgets(self) -> None:
        """Setup custom widgets."""
        # Subworkflow picker button
        self.add_custom_widget(
            "select_subworkflow_btn",
            widget_type="button",
            text="Select Subworkflow...",
            callback=self._on_select_subworkflow,
        )

        # Execution mode
        self.add_combo_menu(
            "execution_mode",
            "Execution Mode",
            items=["sync", "async"],
        )

        # Timeout
        self.add_text_input(
            "timeout_seconds",
            "Timeout (seconds)",
            text="300",
        )

        # Wait for result (async mode)
        self.add_checkbox(
            "wait_for_result",
            label="",
            text="Wait for Result (async)",
            state=True,
        )

        # Poll interval
        self.add_text_input(
            "poll_interval",
            "Poll Interval (seconds)",
            text="5",
        )

    def _apply_styling(self) -> None:
        """Apply distinctive styling for workflow nodes."""
        try:
            self.set_color(50, 80, 100)  # Blue-gray for workflow
            self.model.border_color = (100, 150, 200, 255)

            if hasattr(self, "view") and self.view is not None:
                if hasattr(self.view, "set_category"):
                    self.view.set_category("workflow")
        except Exception as e:
            logger.debug(f"Could not apply styling: {e}")

    def _on_select_subworkflow(self) -> None:
        """Handle subworkflow selection button click."""
        try:
            from casare_rpa.presentation.canvas.ui.dialogs.subworkflow_picker_dialog import (
                show_subworkflow_picker,
            )

            result = show_subworkflow_picker()
            if result:
                self._configure_from_subworkflow_data(result)
        except ImportError as e:
            logger.error(f"Could not import picker dialog: {e}")
        except Exception as e:
            logger.error(f"Error selecting subworkflow: {e}")

    def _configure_from_subworkflow_data(self, subflow_data: Dict[str, Any]) -> None:
        """
        Configure node from subworkflow data dict.

        Args:
            subflow_data: Dict with id, name, inputs, outputs, etc.
        """
        self._selected_subworkflow_id = subflow_data.get("id", "")
        self._selected_subworkflow_name = subflow_data.get("name", "Unnamed")

        # Update node name
        self.set_name(f"Call: {self._selected_subworkflow_name}")

        # Store in properties
        self.set_property("subworkflow_id", self._selected_subworkflow_id)

        # Remove previous dynamic ports
        for port_name in self._dynamic_inputs:
            try:
                self.delete_input(port_name)
            except Exception:
                pass
        for port_name in self._dynamic_outputs:
            try:
                self.delete_output(port_name)
            except Exception:
                pass

        self._dynamic_inputs.clear()
        self._dynamic_outputs.clear()

        # Add input ports
        inputs = subflow_data.get("inputs", [])
        for port_info in inputs:
            port_name = port_info.get("name", "")
            data_type_str = port_info.get("data_type", "ANY")
            data_type = self._parse_data_type(data_type_str)
            self.add_typed_input(port_name, data_type)
            self._dynamic_inputs.append(port_name)

        # Add output ports
        outputs = subflow_data.get("outputs", [])
        for port_info in outputs:
            port_name = port_info.get("name", "")
            data_type_str = port_info.get("data_type", "ANY")
            data_type = self._parse_data_type(data_type_str)
            self.add_typed_output(port_name, data_type)
            self._dynamic_outputs.append(port_name)

        # Re-configure port colors
        self._configure_port_colors()

        # Update casare node if available
        casare_node = self.get_casare_node()
        if casare_node:
            casare_node.config["subworkflow_id"] = self._selected_subworkflow_id
            casare_node.config["subworkflow_path"] = subflow_data.get("path", "")

            # Try to load subflow entity and configure
            try:
                from casare_rpa.domain.entities.subflow import Subflow

                path = subflow_data.get("path", "")
                if path:
                    subflow = Subflow.load_from_file(path)
                    if hasattr(casare_node, "configure_from_subworkflow"):
                        casare_node.configure_from_subworkflow(subflow)
            except Exception as e:
                logger.debug(f"Could not load subflow for casare node: {e}")

        logger.info(
            f"Configured VisualCallSubworkflowNode from '{self._selected_subworkflow_name}': "
            f"{len(self._dynamic_inputs)} inputs, {len(self._dynamic_outputs)} outputs"
        )

    def configure_from_subworkflow(self, subflow: Any) -> None:
        """
        Configure from Subflow entity.

        Args:
            subflow: Subflow entity
        """
        self._selected_subworkflow_id = subflow.id
        self._selected_subworkflow_name = subflow.name

        # Update node name
        self.set_name(f"Call: {subflow.name}")

        # Store in properties
        self.set_property("subworkflow_id", subflow.id)

        # Remove previous dynamic ports
        for port_name in self._dynamic_inputs:
            try:
                self.delete_input(port_name)
            except Exception:
                pass
        for port_name in self._dynamic_outputs:
            try:
                self.delete_output(port_name)
            except Exception:
                pass

        self._dynamic_inputs.clear()
        self._dynamic_outputs.clear()

        # Add input ports
        for port in subflow.inputs:
            data_type = self._normalize_data_type(port.data_type)
            self.add_typed_input(port.name, data_type)
            self._dynamic_inputs.append(port.name)

        # Add output ports
        for port in subflow.outputs:
            data_type = self._normalize_data_type(port.data_type)
            self.add_typed_output(port.name, data_type)
            self._dynamic_outputs.append(port.name)

        # Re-configure port colors
        self._configure_port_colors()

        # Update casare node
        casare_node = self.get_casare_node()
        if casare_node and hasattr(casare_node, "configure_from_subworkflow"):
            casare_node.configure_from_subworkflow(subflow)

        logger.info(
            f"Configured VisualCallSubworkflowNode from subflow entity '{subflow.name}'"
        )

    def _parse_data_type(self, type_str: str) -> DataType:
        """Parse data type string to enum."""
        type_map = {
            "STRING": DataType.STRING,
            "INTEGER": DataType.INTEGER,
            "FLOAT": DataType.FLOAT,
            "BOOLEAN": DataType.BOOLEAN,
            "LIST": DataType.LIST,
            "DICT": DataType.DICT,
            "OBJECT": DataType.OBJECT,
            "ANY": DataType.ANY,
            "PAGE": DataType.PAGE,
            "ELEMENT": DataType.ELEMENT,
        }
        return type_map.get(type_str.upper(), DataType.ANY)

    def _normalize_data_type(self, data_type: Any) -> DataType:
        """Normalize data type to enum."""
        if isinstance(data_type, DataType):
            return data_type
        if isinstance(data_type, str):
            return self._parse_data_type(data_type)
        return DataType.ANY

    @property
    def subworkflow_id(self) -> str:
        """Get selected subworkflow ID."""
        return self._selected_subworkflow_id

    @property
    def subworkflow_name(self) -> str:
        """Get selected subworkflow name."""
        return self._selected_subworkflow_name


__all__ = ["VisualCallSubworkflowNode"]
