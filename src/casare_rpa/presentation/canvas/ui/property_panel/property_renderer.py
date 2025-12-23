"""
Property renderer for enhanced PropertyDef features.

Handles:
- Visibility levels (essential, normal, advanced, internal)
- Conditional display (display_when, hidden_when)
- Property ordering (order field)
- Property groups with collapse
- Dynamic choices

This module provides PropertyRenderer which orchestrates rendering of
properties based on NodeSchema metadata. It reuses the existing
CollapsibleSection widget for grouped/advanced properties.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.ui.theme import Theme
from casare_rpa.presentation.canvas.ui.widgets.collapsible_section import (
    CollapsibleSection,
)

if TYPE_CHECKING:
    from casare_rpa.domain.schemas import NodeSchema, PropertyDef


class PropertyRenderer:
    """
    Renders properties from NodeSchema with enhanced features.

    Coordinates property rendering based on visibility, groups, order,
    and conditional display rules.

    Usage:
        renderer = PropertyRenderer(schema, config, widget_factory)
        container = renderer.render_all(parent_widget)
    """

    def __init__(
        self,
        schema: "NodeSchema",
        current_config: dict[str, Any],
        widget_factory: Callable[["PropertyDef", Any], QWidget | None],
        on_config_change: Callable[[str, Any], None] | None = None,
    ):
        """
        Initialize PropertyRenderer.

        Args:
            schema: The node's property schema
            current_config: Current configuration values
            widget_factory: Function that creates a widget for a PropertyDef and value
            on_config_change: Optional callback when config changes (for conditional display)
        """
        self._schema = schema
        self._config = current_config
        self._widget_factory = widget_factory
        self._on_config_change = on_config_change
        self._widgets: dict[str, QWidget] = {}
        self._sections: dict[str, CollapsibleSection] = {}

    def render_all(self, parent: QWidget) -> QWidget:
        """
        Render all properties into a container widget.

        Properties are organized by:
        1. Essential/Normal ungrouped properties first
        2. Property groups (each in a CollapsibleSection)
        3. Advanced properties in a collapsed section

        Args:
            parent: Parent widget for the container

        Returns:
            Container widget with all property widgets
        """
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Get properties organized by group
        grouped = self._schema.get_properties_by_group()

        # Render ungrouped properties first (group=None)
        ungrouped = grouped.pop(None, [])
        visible_ungrouped = [
            p for p in self._filter_visible_properties(ungrouped) if self._should_display(p)
        ]

        for prop in visible_ungrouped:
            widget = self._render_property(prop, container)
            if widget:
                layout.addWidget(widget)

        # Render each named group in a CollapsibleSection
        for group_name, props in grouped.items():
            visible_props = [
                p for p in self._filter_visible_properties(props) if self._should_display(p)
            ]
            if visible_props:
                # Determine if group should start collapsed
                # Use group_collapsed from first property in group
                start_collapsed = visible_props[0].group_collapsed if visible_props else True

                section = self._render_group(
                    group_name, visible_props, container, collapsed=start_collapsed
                )
                layout.addWidget(section)

        # Render advanced properties in a separate collapsed section
        advanced_props = self._schema.get_properties_by_visibility("advanced")
        displayable_advanced = [p for p in advanced_props if self._should_display(p)]

        if displayable_advanced:
            advanced_section = self._render_group(
                "Advanced", displayable_advanced, container, collapsed=True
            )
            layout.addWidget(advanced_section)

        layout.addStretch()
        return container

    def _filter_visible_properties(self, props: list["PropertyDef"]) -> list["PropertyDef"]:
        """
        Filter out internal and advanced properties.

        Essential and normal visibility properties are returned.
        Advanced properties are handled separately.

        Args:
            props: List of property definitions

        Returns:
            Filtered list excluding internal/advanced properties
        """
        return [p for p in props if p.visibility not in ("internal", "advanced")]

    def _should_display(self, prop: "PropertyDef") -> bool:
        """
        Check if property should be displayed based on conditions.

        Uses schema.should_display() which evaluates display_when
        and hidden_when conditions.

        Args:
            prop: Property definition to check

        Returns:
            True if property should be displayed
        """
        return self._schema.should_display(prop.name, self._config)

    def _render_property(self, prop: "PropertyDef", parent: QWidget) -> QWidget | None:
        """
        Render a single property widget.

        Args:
            prop: Property definition
            parent: Parent widget

        Returns:
            Created widget or None if creation failed
        """
        try:
            # Get current value or default
            value = self._config.get(prop.name, prop.default)

            # Handle dynamic choices - resolve them before widget creation
            if prop.dynamic_choices:
                self._schema.get_dynamic_choices(prop.name, self._config)
                # Widget factory should handle the resolved choices
                # This is a hint - actual implementation depends on widget_factory

            # Create widget using factory
            widget = self._widget_factory(prop, value)
            if widget:
                self._widgets[prop.name] = widget

                # Set up change callback for conditional display updates
                if self._on_config_change:
                    # Connect to value change signal if widget has one
                    if hasattr(widget, "valueChanged"):
                        widget.valueChanged.connect(
                            lambda v, name=prop.name: self._handle_value_change(name, v)
                        )
                    elif hasattr(widget, "textChanged"):
                        widget.textChanged.connect(
                            lambda v, name=prop.name: self._handle_value_change(name, v)
                        )
                    elif hasattr(widget, "currentTextChanged"):
                        widget.currentTextChanged.connect(
                            lambda v, name=prop.name: self._handle_value_change(name, v)
                        )
                    elif hasattr(widget, "stateChanged"):
                        widget.stateChanged.connect(
                            lambda v, name=prop.name: self._handle_value_change(name, bool(v))
                        )

            return widget

        except Exception as e:
            logger.error(f"Failed to render property {prop.name}: {e}")
            return None

    def _render_group(
        self,
        name: str,
        props: list["PropertyDef"],
        parent: QWidget,
        collapsed: bool = False,
    ) -> QWidget:
        """
        Render a property group using CollapsibleSection.

        Args:
            name: Group display name
            props: Properties in this group
            parent: Parent widget
            collapsed: Whether to start collapsed

        Returns:
            CollapsibleSection widget containing grouped properties
        """
        section = CollapsibleSection(title=name, expanded=not collapsed, parent=parent)

        # Create content widget for the section
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(4)

        for prop in props:
            widget = self._render_property(prop, content)
            if widget:
                content_layout.addWidget(widget)

        section.setContentWidget(content)
        self._sections[name] = section
        return section

    def _handle_value_change(self, name: str, value: Any) -> None:
        """
        Handle property value change.

        Updates internal config and triggers callback for
        conditional display re-evaluation.

        Args:
            name: Property name that changed
            value: New value
        """
        self._config[name] = value
        if self._on_config_change:
            self._on_config_change(name, value)
        # Trigger visibility update for dependent properties
        self.update_visibility()

    def get_widget(self, prop_name: str) -> QWidget | None:
        """
        Get widget for a specific property.

        Args:
            prop_name: Property name

        Returns:
            Widget if found, None otherwise
        """
        return self._widgets.get(prop_name)

    def get_all_widgets(self) -> dict[str, QWidget]:
        """
        Get all property widgets.

        Returns:
            Dictionary mapping property names to widgets
        """
        return self._widgets.copy()

    def update_visibility(self) -> None:
        """
        Update visibility of all widgets based on current config.

        Called when a property value changes to re-evaluate
        display_when/hidden_when conditions.
        """
        for prop in self._schema.properties:
            widget = self._widgets.get(prop.name)
            if widget:
                should_show = self._should_display(prop)
                widget.setVisible(should_show)

    def get_section(self, name: str) -> CollapsibleSection | None:
        """
        Get a collapsible section by name.

        Args:
            name: Section/group name

        Returns:
            CollapsibleSection if found, None otherwise
        """
        return self._sections.get(name)


def create_property_section_label(text: str, parent: QWidget | None = None) -> QLabel:
    """
    Create a styled section header label.

    Args:
        text: Label text
        parent: Optional parent widget

    Returns:
        Styled QLabel for section headers
    """
    label = QLabel(text, parent)
    colors = Theme.get_colors()
    label.setStyleSheet(f"""
        QLabel {{
            font-weight: 600;
            font-size: 11px;
            color: {colors.text_secondary};
            padding-top: 8px;
            padding-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
    """)
    return label


def create_property_row_widget(
    label_text: str,
    value_widget: QWidget,
    tooltip: str = "",
    parent: QWidget | None = None,
) -> QWidget:
    """
    Create a horizontal label-widget row.

    Args:
        label_text: Label text
        value_widget: Widget for the value
        tooltip: Optional tooltip for the row
        parent: Optional parent widget

    Returns:
        Container widget with label and value widget
    """
    from PySide6.QtWidgets import QHBoxLayout

    row = QWidget(parent)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 2, 0, 2)
    layout.setSpacing(8)

    label = QLabel(label_text)
    colors = Theme.get_colors()
    label.setStyleSheet(f"color: {colors.text_secondary};")
    label.setMinimumWidth(100)

    layout.addWidget(label)
    layout.addWidget(value_widget, stretch=1)

    if tooltip:
        row.setToolTip(tooltip)

    return row
