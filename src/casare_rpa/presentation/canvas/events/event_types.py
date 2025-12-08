"""
Event type definitions for the Canvas event system.

This module defines all event types that can be emitted and subscribed to
within the Canvas UI. Events are organized by category for better organization.

Event Naming Convention:
    - Use NOUN_VERB pattern (e.g., WORKFLOW_NEW, NODE_ADDED)
    - Past tense for completed actions (e.g., NODE_ADDED, WORKFLOW_SAVED)
    - Present tense for ongoing actions (e.g., EXECUTION_RUNNING)
    - Use descriptive names that clearly indicate what happened

Usage:
    from casare_rpa.presentation.canvas.events import EventType

    event_type = EventType.WORKFLOW_NEW
    print(event_type.name)  # "WORKFLOW_NEW"
    print(event_type.value)  # unique integer
"""

from enum import Enum, auto


class EventCategory(Enum):
    """
    Categories for organizing event types.

    Used for event filtering and logging.
    """

    WORKFLOW = "workflow"
    NODE = "node"
    CONNECTION = "connection"
    EXECUTION = "execution"
    UI = "ui"
    SYSTEM = "system"
    PROJECT = "project"
    VARIABLE = "variable"
    DEBUG = "debug"
    TRIGGER = "trigger"
    CREDENTIAL = "credential"


class EventType(Enum):
    """
    Comprehensive enumeration of all Canvas event types.

    Each event type represents a specific action or state change
    in the Canvas UI that components can react to.

    Organization:
        - Workflow events (20+)
        - Node events (15+)
        - Connection events (10+)
        - Execution events (15+)
        - UI events (10+)
        - System events (10+)
        - Project events (10+)
        - Variable events (5+)
        - Debug events (5+)
        - Trigger events (5+)

    Total: 100+ event types
    """

    # =========================================================================
    # Workflow Events (Lifecycle)
    # =========================================================================

    WORKFLOW_NEW = auto()
    """New workflow created."""

    WORKFLOW_OPENED = auto()
    """Workflow loaded from file."""

    WORKFLOW_SAVED = auto()
    """Workflow saved to file."""

    WORKFLOW_SAVE_AS = auto()
    """Workflow saved with new filename."""

    WORKFLOW_CLOSED = auto()
    """Workflow closed."""

    WORKFLOW_MODIFIED = auto()
    """Workflow has unsaved changes."""

    WORKFLOW_VALIDATED = auto()
    """Workflow validation completed."""

    WORKFLOW_VALIDATION_FAILED = auto()
    """Workflow validation found errors."""

    WORKFLOW_IMPORTED = auto()
    """Workflow imported from external source."""

    WORKFLOW_EXPORTED = auto()
    """Workflow exported to file."""

    WORKFLOW_DUPLICATED = auto()
    """Workflow duplicated."""

    WORKFLOW_RENAMED = auto()
    """Workflow renamed."""

    WORKFLOW_METADATA_UPDATED = auto()
    """Workflow metadata (tags, description) updated."""

    # =========================================================================
    # Workflow Events (Undo/Redo)
    # =========================================================================

    WORKFLOW_UNDO = auto()
    """Undo operation performed."""

    WORKFLOW_REDO = auto()
    """Redo operation performed."""

    WORKFLOW_HISTORY_CLEARED = auto()
    """Undo/redo history cleared."""

    # =========================================================================
    # Workflow Events (Template)
    # =========================================================================

    WORKFLOW_TEMPLATE_APPLIED = auto()
    """Workflow template applied."""

    WORKFLOW_SAVED_AS_TEMPLATE = auto()
    """Workflow saved as template."""

    # =========================================================================
    # Node Events (Lifecycle)
    # =========================================================================

    NODE_ADDED = auto()
    """Node added to workflow."""

    NODE_REMOVED = auto()
    """Node removed from workflow."""

    NODE_DUPLICATED = auto()
    """Node duplicated."""

    NODE_CUT = auto()
    """Node cut to clipboard."""

    NODE_COPIED = auto()
    """Node copied to clipboard."""

    NODE_PASTED = auto()
    """Node pasted from clipboard."""

    # =========================================================================
    # Node Events (Selection)
    # =========================================================================

    NODE_SELECTED = auto()
    """Node selected."""

    NODE_DESELECTED = auto()
    """Node deselected."""

    NODE_SELECTION_CHANGED = auto()
    """Node selection changed (multiple nodes)."""

    NODES_GROUPED = auto()
    """Nodes grouped together."""

    NODES_UNGROUPED = auto()
    """Node group dissolved."""

    # =========================================================================
    # Node Events (Properties)
    # =========================================================================

    NODE_PROPERTY_CHANGED = auto()
    """Node property value changed."""

    NODE_CONFIG_UPDATED = auto()
    """Node configuration updated."""

    NODE_POSITION_CHANGED = auto()
    """Node position changed (drag)."""

    NODE_RENAMED = auto()
    """Node display name changed."""

    NODE_ENABLED = auto()
    """Node enabled for execution."""

    NODE_DISABLED = auto()
    """Node disabled from execution."""

    NODE_BREAKPOINT_ADDED = auto()
    """Breakpoint added to node."""

    NODE_BREAKPOINT_REMOVED = auto()
    """Breakpoint removed from node."""

    # =========================================================================
    # Connection Events
    # =========================================================================

    CONNECTION_ADDED = auto()
    """Connection created between nodes."""

    CONNECTION_REMOVED = auto()
    """Connection deleted."""

    CONNECTION_SELECTED = auto()
    """Connection selected."""

    CONNECTION_DESELECTED = auto()
    """Connection deselected."""

    CONNECTION_VALIDATED = auto()
    """Connection validated (type checking)."""

    CONNECTION_VALIDATION_FAILED = auto()
    """Connection validation failed."""

    CONNECTION_REROUTED = auto()
    """Connection rerouted to different port."""

    # =========================================================================
    # Port Events
    # =========================================================================

    PORT_CONNECTED = auto()
    """Port connected to another port."""

    PORT_DISCONNECTED = auto()
    """Port disconnected."""

    PORT_VALUE_CHANGED = auto()
    """Port value changed."""

    # =========================================================================
    # Execution Events (Lifecycle)
    # =========================================================================

    EXECUTION_STARTED = auto()
    """Workflow execution started."""

    EXECUTION_PAUSED = auto()
    """Workflow execution paused."""

    EXECUTION_RESUMED = auto()
    """Workflow execution resumed."""

    EXECUTION_STOPPED = auto()
    """Workflow execution stopped."""

    EXECUTION_COMPLETED = auto()
    """Workflow execution completed successfully."""

    EXECUTION_FAILED = auto()
    """Workflow execution failed with error."""

    EXECUTION_CANCELLED = auto()
    """Workflow execution cancelled by user."""

    # =========================================================================
    # Execution Events (Node-level)
    # =========================================================================

    NODE_EXECUTION_STARTED = auto()
    """Individual node execution started."""

    NODE_EXECUTION_COMPLETED = auto()
    """Individual node execution completed."""

    NODE_EXECUTION_FAILED = auto()
    """Individual node execution failed."""

    NODE_EXECUTION_SKIPPED = auto()
    """Individual node execution skipped."""

    # =========================================================================
    # Execution Events (Debug)
    # =========================================================================

    EXECUTION_STEP_INTO = auto()
    """Debug: step into node execution."""

    EXECUTION_STEP_OVER = auto()
    """Debug: step over node execution."""

    EXECUTION_STEP_OUT = auto()
    """Debug: step out of current scope."""

    BREAKPOINT_HIT = auto()
    """Execution paused at breakpoint."""

    # =========================================================================
    # UI Events (Panels)
    # =========================================================================

    PANEL_OPENED = auto()
    """Panel opened/shown."""

    PANEL_CLOSED = auto()
    """Panel closed/hidden."""

    PANEL_TOGGLED = auto()
    """Panel visibility toggled."""

    PANEL_RESIZED = auto()
    """Panel resized."""

    PANEL_TAB_CHANGED = auto()
    """Panel active tab changed."""

    # =========================================================================
    # UI Events (View)
    # =========================================================================

    ZOOM_CHANGED = auto()
    """Canvas zoom level changed."""

    VIEW_CENTERED = auto()
    """View centered on workflow."""

    VIEW_FIT_TO_SELECTION = auto()
    """View fitted to selected nodes."""

    MINIMAP_TOGGLED = auto()
    """Minimap visibility toggled."""

    # =========================================================================
    # UI Events (Theme)
    # =========================================================================

    THEME_CHANGED = auto()
    """UI theme changed."""

    PREFERENCES_UPDATED = auto()
    """User preferences updated."""

    HOTKEY_TRIGGERED = auto()
    """Keyboard shortcut triggered."""

    # =========================================================================
    # UI Events (Search/Filter)
    # =========================================================================

    NODE_SEARCH_OPENED = auto()
    """Node search dialog opened."""

    NODE_FILTER_APPLIED = auto()
    """Node filter applied to palette."""

    COMMAND_PALETTE_OPENED = auto()
    """Command palette opened."""

    # =========================================================================
    # System Events (Logging)
    # =========================================================================

    LOG_MESSAGE = auto()
    """Log message emitted."""

    ERROR_OCCURRED = auto()
    """Error occurred in system."""

    WARNING_ISSUED = auto()
    """Warning issued."""

    INFO_MESSAGE = auto()
    """Informational message."""

    DEBUG_OUTPUT = auto()
    """Debug output message."""

    # =========================================================================
    # System Events (Performance)
    # =========================================================================

    PERFORMANCE_METRIC = auto()
    """Performance metric recorded."""

    MEMORY_WARNING = auto()
    """Memory usage warning."""

    # =========================================================================
    # System Events (Autosave)
    # =========================================================================

    AUTOSAVE_TRIGGERED = auto()
    """Autosave triggered."""

    AUTOSAVE_COMPLETED = auto()
    """Autosave completed successfully."""

    AUTOSAVE_FAILED = auto()
    """Autosave failed."""

    # =========================================================================
    # Project Events
    # =========================================================================

    PROJECT_CREATED = auto()
    """Project created."""

    PROJECT_OPENED = auto()
    """Project opened."""

    PROJECT_CLOSED = auto()
    """Project closed."""

    PROJECT_RENAMED = auto()
    """Project renamed."""

    PROJECT_DELETED = auto()
    """Project deleted."""

    SCENARIO_CREATED = auto()
    """Scenario created within project."""

    SCENARIO_OPENED = auto()
    """Scenario opened."""

    SCENARIO_DELETED = auto()
    """Scenario deleted."""

    PROJECT_STRUCTURE_CHANGED = auto()
    """Project hierarchy structure changed."""

    # =========================================================================
    # Variable Events
    # =========================================================================

    VARIABLE_SET = auto()
    """Variable value set."""

    VARIABLE_UPDATED = auto()
    """Variable value updated."""

    VARIABLE_DELETED = auto()
    """Variable deleted."""

    VARIABLE_CLEARED = auto()
    """All variables cleared."""

    VARIABLE_SCOPE_CHANGED = auto()
    """Variable scope changed (workflow/scenario/project)."""

    # =========================================================================
    # Debug Events
    # =========================================================================

    DEBUG_MODE_ENABLED = auto()
    """Debug mode enabled."""

    DEBUG_MODE_DISABLED = auto()
    """Debug mode disabled."""

    DEBUG_CALL_STACK_UPDATED = auto()
    """Debug call stack updated with current execution frames."""

    VARIABLE_INSPECTOR_UPDATED = auto()
    """Variable inspector data updated."""

    EXECUTION_TRACE_UPDATED = auto()
    """Execution trace log updated."""

    WATCH_EXPRESSION_ADDED = auto()
    """Watch expression added."""

    WATCH_EXPRESSION_REMOVED = auto()
    """Watch expression removed."""

    # =========================================================================
    # Trigger Events
    # =========================================================================

    TRIGGER_CREATED = auto()
    """Trigger created for workflow."""

    TRIGGER_UPDATED = auto()
    """Trigger configuration updated."""

    TRIGGER_DELETED = auto()
    """Trigger deleted."""

    TRIGGER_ENABLED = auto()
    """Trigger enabled."""

    TRIGGER_DISABLED = auto()
    """Trigger disabled."""

    TRIGGER_FIRED = auto()
    """Trigger fired and started workflow."""

    # =========================================================================
    # Clipboard Events
    # =========================================================================

    CLIPBOARD_UPDATED = auto()
    """Clipboard content updated."""

    # =========================================================================
    # History Events
    # =========================================================================

    EXECUTION_HISTORY_UPDATED = auto()
    """Execution history updated."""

    # =========================================================================
    # Browser/Selector Events (Canvas-specific)
    # =========================================================================

    SELECTOR_PICKER_OPENED = auto()
    """Element selector picker opened."""

    SELECTOR_PICKED = auto()
    """Element selector picked."""

    BROWSER_PREVIEW_OPENED = auto()
    """Browser preview window opened."""

    # =========================================================================
    # Credential Events
    # =========================================================================

    CREDENTIAL_ADDED = auto()
    """Credential added to store."""

    CREDENTIAL_UPDATED = auto()
    """Credential updated."""

    CREDENTIAL_DELETED = auto()
    """Credential deleted from store."""

    CREDENTIAL_TESTED = auto()
    """Credential connection tested."""

    @property
    def category(self) -> EventCategory:
        """
        Get the category of this event type.

        Returns:
            EventCategory: The category this event belongs to
        """
        # Workflow events
        if "WORKFLOW" in self.name:
            return EventCategory.WORKFLOW

        # Node events
        if "NODE" in self.name and "CONNECTION" not in self.name:
            return EventCategory.NODE

        # Connection/Port events
        if "CONNECTION" in self.name or "PORT" in self.name:
            return EventCategory.CONNECTION

        # Execution events
        if "EXECUTION" in self.name or "BREAKPOINT" in self.name:
            return EventCategory.EXECUTION

        # UI events
        if any(
            keyword in self.name
            for keyword in [
                "PANEL",
                "ZOOM",
                "VIEW",
                "THEME",
                "MINIMAP",
                "SEARCH",
                "COMMAND",
                "HOTKEY",
            ]
        ):
            return EventCategory.UI

        # Project events
        if "PROJECT" in self.name or "SCENARIO" in self.name:
            return EventCategory.PROJECT

        # Variable events
        if "VARIABLE" in self.name or "WATCH" in self.name:
            return EventCategory.VARIABLE

        # Debug events
        if "DEBUG" in self.name or "INSPECTOR" in self.name or "TRACE" in self.name:
            return EventCategory.DEBUG

        # Trigger events
        if "TRIGGER" in self.name:
            return EventCategory.TRIGGER

        # Credential events
        if "CREDENTIAL" in self.name:
            return EventCategory.CREDENTIAL

        # Default to system
        return EventCategory.SYSTEM

    def __str__(self) -> str:
        """String representation of event type."""
        return self.name

    def __repr__(self) -> str:
        """Detailed representation of event type."""
        return f"EventType.{self.name}"
