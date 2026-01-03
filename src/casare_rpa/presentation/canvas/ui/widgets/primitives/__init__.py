"""
Primitive UI Components v2 - Epic 5.1 Component Library.

Low-level reusable UI components using THEME_V2 and TOKENS_V2.
These are the building blocks for more complex widgets.

Components:
    buttons: PushButton, ToolButton, ButtonGroup
    inputs: TextInput, SearchInput, SpinBox, DoubleSpinBox
    selection: CheckBox, Switch, RadioButton, RadioGroup
    selects: Select, ComboBox, ItemList
    lists: ListItem, TreeItem, TableHeader
    range: Slider, ProgressBar, Dial
    tabs: TabWidget, TabBar, Tab (tabbed interfaces)
    structural: SectionHeader, Divider, EmptyState, Card
    feedback: Badge, Tooltip, InlineAlert, Breadcrumb, Avatar
    loading: Skeleton, Spinner (loading indicators)
    pickers: FilePicker, FolderPicker (file/folder selection)
    forms: FormField, FormRow, ReadOnlyField, validators (Epic 5.2)
    (More to be added in future epics)

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives import (
        # Buttons
        PushButton,
        ToolButton,
        ButtonGroup,
        create_button,
        create_icon_button,
        # Inputs
        TextInput,
        SearchInput,
        SpinBox,
        DoubleSpinBox,
        # Selection
        CheckBox,
        Switch,
        RadioButton,
        RadioGroup,
        # Selects
        Select,
        ComboBox,
        ItemList,
        # Range
        Slider,
        ProgressBar,
        Dial,
        create_slider,
        create_progress,
        create_dial,
        # Structural
        SectionHeader,
        Divider,
        EmptyState,
        Card,
        create_divider,
        create_empty_state,
        create_card,
    )

    # Create a primary button
    btn = create_button("Save", variant="primary", size="md")

    # Create an icon button
    from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon
    icon_btn = ToolButton(icon=get_icon("settings", size=20), tooltip="Settings")

    # Create text input
    text_input = TextInput(placeholder="Enter text", size="md", clearable=True)

    # Create search input with debounce
    search_input = SearchInput(placeholder="Search...", search_delay=50)

    # Create spin boxes
    spin = SpinBox(min=0, max=100, value=50)
    decimal = DoubleSpinBox(min=0.0, max=1.0, value=0.5, decimals=2)

    # Create selection controls
    checkbox = CheckBox(text="Enable feature", checked=True)
    switch = Switch(text="Dark mode", checked=False)
    radio_group = RadioGroup(items=[{"value": "a", "label": "Option A"}])

    # Create select dropdown
    select = Select(
        items=[
            {"value": "1", "label": "Option 1", "icon": "check"},
            {"value": "2", "label": "Option 2"},
        ],
        placeholder="Choose...",
        clearable=True,
    )

    # Create editable combobox
    combo = ComboBox(items=["Apple", "Banana", "Cherry"], placeholder="Select or type...")

    # Create item list
    list_widget = ItemList(items=[{"value": "1", "label": "Item 1"}], selected="1")

    # Create slider
    slider = create_slider(min=0, max=100, value=50, show_value=True)

    # Create progress bar
    progress = create_progress(value=75, show_text=True)

    # Create dial
    dial = create_dial(min=0, max=360, value=180, wrapping=True)

    # Create tab widget
    from casare_rpa.presentation.canvas.ui.widgets.primitives import Tab, TabWidget
    tabs = [
        Tab(id="home", title="Home", content=QLabel("Home content")),
        Tab(id="settings", title="Settings", icon=get_icon("settings"), content=QLabel("Settings")),
    ]
    tab_widget = TabWidget(tabs=tabs, position="top", closable=True)

    # Create file picker
    from casare_rpa.presentation.canvas.ui.widgets.primitives import FilePicker, FileFilter, PathType
    file_picker = FilePicker(
        path_type=PathType.FILE,
        filter=FileFilter.EXCEL,
        placeholder="Select Excel file...",
        size="md",
    )
    file_picker.path_changed.connect(lambda path: print(f"Selected: {path}"))

    # Create folder picker
    from casare_rpa.presentation.canvas.ui.widgets.primitives import FolderPicker
    folder_picker = FolderPicker(placeholder="Select output folder...", size="md")
    folder_picker.path_changed.connect(lambda path: print(f"Folder: {path}"))

    # Create form field with validation
    from casare_rpa.presentation.canvas.ui.widgets.primitives import FormField, required_validator
    field = FormField(
        label="Email",
        widget=TextInput(placeholder="user@example.com"),
        required=True,
        validator=required_validator,
    )
    field.validation_changed.connect(lambda r: print(f"Valid: {r.status.value}"))

    # Create form row (horizontal layout)
    from casare_rpa.presentation.canvas.ui.widgets.primitives import FormRow
    row = FormRow(
        label="Port",
        widget=SpinBox(min=1, max=65535, value=8080),
        label_width="sm",
    )

    # Create read-only field
    from casare_rpa.presentation.canvas.ui.widgets.primitives import ReadOnlyField
    readonly = ReadOnlyField(label="Generated ID", value="abc-123-def", copyable=True)

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

# Base class for all v2 primitives
from casare_rpa.presentation.canvas.ui.widgets.primitives.base_primitive import (
    BasePrimitive,
    FontVariant,
    MarginPreset,
    SizeVariant,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import (
    ButtonGroup,
    ButtonSize,
    ButtonVariant,
    GroupOrientation,
    PushButton,
    ToolButton,
    ToolButtonVariant,
    create_button,
    create_icon_button,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.feedback import (
    AlertVariant,
    Avatar,
    AvatarSize,
    AvatarVariant,
    Badge,
    BadgeColor,
    BadgeVariant,
    Breadcrumb,
    BreadcrumbItem,
    InlineAlert,
    create_alert,
    create_avatar,
    create_badge,
    create_breadcrumb,
    set_tooltip,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.forms import (
    Fieldset,
    FormContainer,
    FormField,
    FormRow,
    FormValidationResult,
    FormValidationStatus,
    ReadOnlyField,
    ValidatorFunc,
    create_fieldset,
    create_form_container,
    create_form_field,
    create_form_row,
    create_read_only_field,
    email_validator,
    integer_validator,
    max_value_validator,
    min_value_validator,
    non_negative_validator,
    positive_validator,
    range_validator,
    required_validator,
    url_validator,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import (
    DoubleSpinBox,
    InputSize,
    SearchInput,
    SpinBox,
    TextInput,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import (
    ListItem,
    RowSize,
    SortOrder,
    TableHeader,
    TreeItem,
    apply_header_style,
    apply_list_style,
    apply_table_style,
    apply_tree_style,
    create_list_item,
    create_tree_item,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.loading import (
    Skeleton,
    SkeletonVariant,
    Spinner,
    create_skeleton,
    create_spinner,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.pickers import (
    FileFilter,
    FilePicker,
    FolderPicker,
    PathType,
    create_file_picker,
    create_folder_picker,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.range import (
    Dial,
    ProgressBar,
    ProgressBarSize,
    Slider,
    SliderSize,
    create_dial,
    create_progress,
    create_slider,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.selection import (
    CheckBox,
    RadioButton,
    RadioGroup,
    RadioOrientation,
    Switch,
    create_checkbox,
    create_switch,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.selects import (
    ComboBox,
    ItemList,
    Select,
    SelectItem,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import (
    Card,
    Divider,
    EmptyState,
    Orientation,
    SectionHeader,
    create_card,
    create_divider,
    create_empty_state,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.tabs import (
    Tab,
    TabBar,
    TabPosition,
    TabWidget,
    create_tab,
)

__all__ = [
    # Base
    "BasePrimitive",
    "SizeVariant",
    "FontVariant",
    "MarginPreset",
    # Buttons
    "PushButton",
    "ToolButton",
    "ButtonGroup",
    "ButtonVariant",
    "ButtonSize",
    "ToolButtonVariant",
    "GroupOrientation",
    "create_button",
    "create_icon_button",
    # Inputs
    "TextInput",
    "SearchInput",
    "SpinBox",
    "DoubleSpinBox",
    "InputSize",
    # Selection
    "CheckBox",
    "Switch",
    "RadioButton",
    "RadioGroup",
    "RadioOrientation",
    "create_checkbox",
    "create_switch",
    # Selects
    "Select",
    "ComboBox",
    "ItemList",
    "SelectItem",
    # Lists
    "ListItem",
    "TreeItem",
    "TableHeader",
    "RowSize",
    "SortOrder",
    "apply_list_style",
    "apply_tree_style",
    "apply_table_style",
    "apply_header_style",
    "create_list_item",
    "create_tree_item",
    # Range
    "Slider",
    "SliderSize",
    "ProgressBar",
    "ProgressBarSize",
    "Dial",
    "create_slider",
    "create_progress",
    "create_dial",
    # Tabs
    "Tab",
    "TabWidget",
    "TabBar",
    "TabPosition",
    "create_tab",
    # Structural
    "SectionHeader",
    "Divider",
    "EmptyState",
    "Card",
    "Orientation",
    "create_divider",
    "create_empty_state",
    "create_card",
    # Feedback
    "Badge",
    "InlineAlert",
    "Breadcrumb",
    "Avatar",
    "BadgeVariant",
    "BadgeColor",
    "AlertVariant",
    "AvatarSize",
    "AvatarVariant",
    "BreadcrumbItem",
    "set_tooltip",
    "create_badge",
    "create_alert",
    "create_breadcrumb",
    "create_avatar",
    # Loading
    "Skeleton",
    "Spinner",
    "SkeletonVariant",
    "create_skeleton",
    "create_spinner",
    # Pickers
    "FilePicker",
    "FolderPicker",
    "PathType",
    "FileFilter",
    "create_file_picker",
    "create_folder_picker",
    # Forms
    "FormField",
    "FormRow",
    "ReadOnlyField",
    "FormContainer",
    "Fieldset",
    "FormValidationStatus",
    "FormValidationResult",
    "ValidatorFunc",
    "required_validator",
    "min_value_validator",
    "max_value_validator",
    "range_validator",
    "integer_validator",
    "positive_validator",
    "non_negative_validator",
    "email_validator",
    "url_validator",
    "create_form_field",
    "create_form_row",
    "create_read_only_field",
    "create_form_container",
    "create_fieldset",
]

