"""
Project Creation Wizard Dialog.

3-step wizard for creating new CasareRPA projects from templates:
1. Select Template - Grid of template cards with preview
2. Project Details - Name, location, description, author
3. Environment Setup - Dev/staging/prod checkboxes, .env import

Epic 7.x - Migrated to THEME_V2/TOKENS_V2 (kept QDialog due to dynamic wizard navigation).
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from casare_rpa.domain.entities.project import Project
    from casare_rpa.domain.entities.project_template import ProjectTemplate

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2


class TemplateCard(QFrame):
    """Clickable template card widget.

    Epic 7.x - Migrated to THEME_V2/TOKENS_V2.
    """

    clicked = Signal(object)  # Emits ProjectTemplate

    def __init__(
        self,
        template: "ProjectTemplate",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._template = template
        self._selected = False

        self.setFixedSize(TOKENS_V2.sizes.dialog_sm_width // 2, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Set up card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.lg, TOKENS_V2.spacing.lg, TOKENS_V2.spacing.lg, TOKENS_V2.spacing.lg
        )
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Icon with color background
        icon_container = QWidget()
        icon_container.setFixedSize(TOKENS_V2.sizes.icon_xl, TOKENS_V2.sizes.icon_xl)
        icon_container.setStyleSheet(
            f"background: {self._template.color}; border-radius: {TOKENS_V2.radius.md}px;"
        )

        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setText(self._get_icon_text())
        icon_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        icon_layout.addWidget(icon_label)

        layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Template name
        name_label = QLabel(self._template.name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(
            f"font-weight: bold; font-size: {TOKENS_V2.typography.md}px; color: {THEME_V2.text_primary};"
        )
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # Category badge
        category_label = QLabel(self._template.category.value)
        category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        category_label.setStyleSheet(
            f"font-size: {TOKENS_V2.typography.xs}px; color: {THEME_V2.text_disabled}; "
            f"background: {THEME_V2.bg_component}; border-radius: {TOKENS_V2.radius.sm}px; "
            f"padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;"
        )
        layout.addWidget(category_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Difficulty badge
        difficulty_color = {
            "beginner": THEME_V2.success,
            "intermediate": THEME_V2.warning,
            "advanced": THEME_V2.error,
        }.get(self._template.difficulty.value, THEME_V2.text_disabled)

        difficulty_label = QLabel(self._template.difficulty.value.capitalize())
        difficulty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        difficulty_label.setStyleSheet(
            f"font-size: 9px; color: {difficulty_color}; font-weight: TOKENS_V2.sizes.dialog_lg_width;"
        )
        layout.addWidget(difficulty_label)

        layout.addStretch()

    def _get_icon_text(self) -> str:
        """Get icon text for template."""
        icon_map = {
            "web": "WEB",
            "google": "G",
            "desktop": "DT",
            "data": "ETL",
            "email": "EM",
            "api": "API",
            "notify": "NT",
            "office": "OFF",
            "template": "T",
        }
        return icon_map.get(self._template.icon, self._template.name[:2].upper())

    def _apply_style(self) -> None:
        """Apply card styling."""
        if self._selected:
            self.setStyleSheet(f"""
                TemplateCard {{
                    background: {THEME_V2.bg_component};
                    border: 2px solid {THEME_V2.primary};
                    border-radius: {TOKENS_V2.radius.md}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                TemplateCard {{
                    background: {THEME_V2.bg_surface};
                    border: 1px solid {THEME_V2.border};
                    border-radius: {TOKENS_V2.radius.md}px;
                }}
                TemplateCard:hover {{
                    background: {THEME_V2.bg_hover};
                    border-color: {THEME_V2.border_light};
                }}
            """)

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self._selected = selected
        self._apply_style()

    def is_selected(self) -> bool:
        """Check if selected."""
        return self._selected

    def get_template(self) -> "ProjectTemplate":
        """Get template."""
        return self._template

    def mousePressEvent(self, event) -> None:
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._template)
        super().mousePressEvent(event)


class TemplatePreviewPanel(QFrame):
    """Panel showing template details."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(TOKENS_V2.sizes.panel_default_width - 20)
        self.setMaximumWidth(TOKENS_V2.sizes.panel_default_width + 20)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Set up preview panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*TOKENS_V2.margin.comfortable)
        layout.setSpacing(TOKENS_V2.spacing.lg)

        # Header
        self._header_label = QLabel("Select a Template")
        self._header_label.setStyleSheet(
            f"font-size: {TOKENS_V2.typography.xl}px; font-weight: bold; color: {THEME_V2.text_primary};"
        )
        layout.addWidget(self._header_label)

        # Description
        self._description_label = QLabel("Choose a template from the list to see its details.")
        self._description_label.setWordWrap(True)
        self._description_label.setStyleSheet(
            f"color: {THEME_V2.text_disabled}; font-size: {TOKENS_V2.typography.md}px;"
        )
        layout.addWidget(self._description_label)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background: {THEME_V2.border};")
        layout.addWidget(divider)

        # Included nodes group
        self._nodes_group = QGroupBox("Included Nodes")
        self._nodes_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                margin-top: {TOKENS_V2.spacing.sm}px;
                padding-top: {TOKENS_V2.spacing.xl}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.sm}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
                color: {THEME_V2.text_primary};
            }}
        """)
        nodes_layout = QVBoxLayout(self._nodes_group)
        self._nodes_label = QLabel("No nodes yet")
        self._nodes_label.setWordWrap(True)
        self._nodes_label.setStyleSheet(
            f"color: {THEME_V2.text_disabled}; font-size: {TOKENS_V2.typography.sm}px;"
        )
        nodes_layout.addWidget(self._nodes_label)
        layout.addWidget(self._nodes_group)

        # Variables group
        self._vars_group = QGroupBox("Default Variables")
        self._vars_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                margin-top: {TOKENS_V2.spacing.sm}px;
                padding-top: {TOKENS_V2.spacing.xl}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.sm}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
                color: {THEME_V2.text_primary};
            }}
        """)
        vars_layout = QVBoxLayout(self._vars_group)
        self._vars_label = QLabel("No variables")
        self._vars_label.setWordWrap(True)
        self._vars_label.setStyleSheet(
            f"color: {THEME_V2.text_disabled}; font-size: {TOKENS_V2.typography.sm}px;"
        )
        vars_layout.addWidget(self._vars_label)
        layout.addWidget(self._vars_group)

        # Metadata
        self._meta_label = QLabel("")
        self._meta_label.setWordWrap(True)
        self._meta_label.setStyleSheet(
            f"color: {THEME_V2.text_muted}; font-size: {TOKENS_V2.typography.xs}px;"
        )
        layout.addWidget(self._meta_label)

        layout.addStretch()

    def _apply_style(self) -> None:
        """Apply panel styling."""
        self.setStyleSheet(f"""
            TemplatePreviewPanel {{
                background: {THEME_V2.bg_surface};
                border-left: 1px solid {THEME_V2.border};
            }}
        """)

    def update_template(self, template: Optional["ProjectTemplate"]) -> None:
        """Update preview with template info."""
        if not template:
            self._header_label.setText("Select a Template")
            self._description_label.setText("Choose a template from the list to see its details.")
            self._nodes_label.setText("No nodes yet")
            self._vars_label.setText("No variables")
            self._meta_label.setText("")
            return

        self._header_label.setText(template.name)
        self._description_label.setText(template.description or "No description")

        # Show nodes from workflow
        nodes_count = 0
        node_types = []
        if template.base_workflow:
            nodes = template.base_workflow.get("nodes", {})
            nodes_count = len(nodes)
            for node in list(nodes.values())[:5]:
                node_type = node.get("node_type", "Unknown")
                node_types.append(node_type.replace("Node", ""))
            if nodes_count > 5:
                node_types.append(f"... +{nodes_count - 5} more")

        if node_types:
            self._nodes_label.setText("\n".join(f"- {nt}" for nt in node_types))
        else:
            self._nodes_label.setText(f"{template.estimated_nodes} nodes (empty starter)")

        # Show variables
        if template.default_variables:
            var_names = [v.name for v in template.default_variables[:5]]
            if len(template.default_variables) > 5:
                var_names.append(f"... +{len(template.default_variables) - 5} more")
            self._vars_label.setText("\n".join(f"- {vn}" for vn in var_names))
        else:
            self._vars_label.setText("No default variables")

        # Metadata
        meta_parts = [
            f"Author: {template.author}",
            f"Version: {template.version}",
        ]
        if template.tags:
            meta_parts.append(f"Tags: {', '.join(template.tags[:3])}")
        self._meta_label.setText("\n".join(meta_parts))


from casare_rpa.presentation.canvas.ui.dialogs_v2 import BaseDialogV2, DialogSizeV2


class ProjectWizard(BaseDialogV2):
    """
    3-step project creation wizard.

    Steps:
    1. Template Selection - Grid of template cards with preview
    2. Project Details - Name, location, description, author
    3. Environment Setup - Dev/staging/prod, .env import

    Migrated to BaseDialogV2 (Epic 7.x).

    Signals:
        project_created: Emitted when project is successfully created
    """

    project_created = Signal(str, str)  # project_path, template_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            title="New Project Wizard",
            parent=parent,
            size=DialogSizeV2.XL,
            resizable=True,
        )

        self._templates: list[ProjectTemplate] = []
        self._selected_template: ProjectTemplate | None = None
        self._template_cards: list[TemplateCard] = []

        # Content widget
        content = QWidget()
        self._setup_ui(content)
        self.set_body_widget(content)

        # We use a custom navigation bar for the wizard (Back/Next/Cancel)
        self.set_footer_visible(False)

        self._load_templates()
        self._update_navigation()

    def _setup_ui(self, content: QWidget) -> None:
        """Set up wizard UI."""
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Step indicator header
        self._step_header = self._create_step_header()
        layout.addWidget(self._step_header)

        # Content area with stacked widget
        self._stack = QStackedWidget()
        self._stack.addWidget(self._create_step1_template())
        self._stack.addWidget(self._create_step2_details())
        self._stack.addWidget(self._create_step3_environment())
        layout.addWidget(self._stack, 1)

        # Navigation buttons
        nav_bar = self._create_navigation_bar()
        layout.addWidget(nav_bar)

    def _create_step_header(self) -> QWidget:
        """Create step indicator header."""
        header = QFrame()
        header.setFixedHeight(TOKENS_V2.sizes.toolbar_height + TOKENS_V2.spacing.lg)
        header.setStyleSheet(f"""
            QFrame {{
                background: {THEME_V2.bg_surface};
                border-bottom: 1px solid {THEME_V2.border};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(TOKENS_V2.margin.dialog)

        self._step_labels = []
        steps = [
            ("1", "Select Template"),
            ("2", "Project Details"),
            ("3", "Environment Setup"),
        ]

        for i, (num, text) in enumerate(steps):
            step_widget = QWidget()
            step_layout = QHBoxLayout(step_widget)
            step_layout.setContentsMargins(0, 0, 0, 0)
            step_layout.setSpacing(8)

            # Step number circle
            num_label = QLabel(num)
            num_label.setFixedSize(TOKENS_V2.sizes.button_lg, TOKENS_V2.sizes.button_lg)
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setObjectName(f"step_num_{i}")
            step_layout.addWidget(num_label)

            # Step text
            text_label = QLabel(text)
            text_label.setObjectName(f"step_text_{i}")
            step_layout.addWidget(text_label)

            layout.addWidget(step_widget)
            self._step_labels.append((num_label, text_label))

            # Arrow between steps
            if i < len(steps) - 1:
                arrow = QLabel(">")
                arrow.setStyleSheet(
                    f"color: {THEME_V2.text_disabled}; font-size: {TOKENS_V2.typography.display_l}px; padding: 0 16px;"
                )
                layout.addWidget(arrow)

        layout.addStretch()
        return header

    def _create_step1_template(self) -> QWidget:
        """Create Step 1: Template Selection."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left: Template grid in scroll area
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Choose a Template")
        title.setStyleSheet(
            f"font-size: {TOKENS_V2.typography.xl}px; font-weight: bold; color: {THEME_V2.text_primary};"
        )
        left_layout.addWidget(title)

        subtitle = QLabel(
            "Select a template to start your project with pre-configured nodes and settings."
        )
        subtitle.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body}px;"
        )
        left_layout.addWidget(subtitle)

        # Scroll area for template cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"background: {THEME_V2.bg_surface}; border: none;")

        self._template_grid_widget = QWidget()
        self._template_grid = QGridLayout(self._template_grid_widget)
        self._template_grid.setSpacing(16)
        scroll.setWidget(self._template_grid_widget)

        left_layout.addWidget(scroll, 1)
        layout.addWidget(left_panel, 1)

        # Right: Preview panel
        self._preview_panel = TemplatePreviewPanel()
        layout.addWidget(self._preview_panel)

        return page

    def _create_step2_details(self) -> QWidget:
        """Create Step 2: Project Details."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(*TOKENS_V2.margin.spacious)
        layout.setSpacing(TOKENS_V2.spacing.xl)

        # Title
        title = QLabel("Project Details")
        title.setStyleSheet(
            f"font-size: {TOKENS_V2.typography.xl}px; font-weight: bold; color: {THEME_V2.text_primary};"
        )
        layout.addWidget(title)

        subtitle = QLabel("Configure your new project settings.")
        subtitle.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body}px;"
        )
        layout.addWidget(subtitle)

        # Form container
        form = QWidget()
        form_layout = QVBoxLayout(form)
        form_layout.setSpacing(16)

        # Project name
        name_group = self._create_form_field("Project Name *", "Enter project name...")
        self._name_input = name_group.findChild(QLineEdit)
        self._name_input.textChanged.connect(self._on_name_changed)
        form_layout.addWidget(name_group)

        # Project location
        location_group = QGroupBox("Project Location *")
        location_group.setStyleSheet(self._get_form_group_style())
        loc_layout = QHBoxLayout(location_group)
        loc_layout.setContentsMargins(12, 16, 12, 12)

        self._location_input = QLineEdit()
        self._location_input.setReadOnly(True)
        self._location_input.setPlaceholderText("Select a folder for your project...")
        self._location_input.setStyleSheet(self._get_input_style())
        loc_layout.addWidget(self._location_input, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet(self._get_inline_button_style())
        browse_btn.clicked.connect(self._browse_location)
        loc_layout.addWidget(browse_btn)

        form_layout.addWidget(location_group)

        # Description
        desc_group = QGroupBox("Description")
        desc_group.setStyleSheet(self._get_form_group_style())
        desc_layout = QVBoxLayout(desc_group)
        desc_layout.setContentsMargins(12, 16, 12, 12)

        self._description_input = QTextEdit()
        self._description_input.setPlaceholderText("Optional project description...")
        self._description_input.setMaximumHeight(
            TOKENS_V2.sizes.input_lg * 2 + TOKENS_V2.spacing.xl
        )
        self._description_input.setStyleSheet(f"""
            QTextEdit {{
                background: {THEME_V2.input_bg};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QTextEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)
        desc_layout.addWidget(self._description_input)
        form_layout.addWidget(desc_group)

        # Author
        author_group = self._create_form_field("Author", "Your name...")
        self._author_input = author_group.findChild(QLineEdit)
        form_layout.addWidget(author_group)

        layout.addWidget(form)
        layout.addStretch()

        return page

    def _create_step3_environment(self) -> QWidget:
        """Create Step 3: Environment Setup."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(*TOKENS_V2.margin.spacious)
        layout.setSpacing(TOKENS_V2.spacing.xl)

        # Title
        title = QLabel("Environment Setup")
        title.setStyleSheet(
            f"font-size: {TOKENS_V2.typography.xl}px; font-weight: bold; color: {THEME_V2.text_primary};"
        )
        layout.addWidget(title)

        subtitle = QLabel("Configure environments for different deployment stages.")
        subtitle.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body}px;"
        )
        layout.addWidget(subtitle)

        # Environments group
        env_group = QGroupBox("Create Environments")
        env_group.setStyleSheet(self._get_form_group_style())
        env_layout = QVBoxLayout(env_group)
        env_layout.setContentsMargins(16, 20, 16, 16)
        env_layout.setSpacing(12)

        env_desc = QLabel(
            "Environments allow you to have separate configurations for "
            "development, testing, and production."
        )
        env_desc.setWordWrap(True)
        env_desc.setStyleSheet(
            f"color: {THEME_V2.text_disabled}; font-size: {TOKENS_V2.typography.sm}px; margin-bottom: {TOKENS_V2.spacing.sm}px;"
        )
        env_layout.addWidget(env_desc)

        self._env_dev = QCheckBox("Development (dev)")
        self._env_dev.setChecked(True)
        self._env_dev.setStyleSheet(self._get_checkbox_style())
        env_layout.addWidget(self._env_dev)

        self._env_staging = QCheckBox("Staging (staging)")
        self._env_staging.setChecked(True)
        self._env_staging.setStyleSheet(self._get_checkbox_style())
        env_layout.addWidget(self._env_staging)

        self._env_prod = QCheckBox("Production (prod)")
        self._env_prod.setChecked(True)
        self._env_prod.setStyleSheet(self._get_checkbox_style())
        env_layout.addWidget(self._env_prod)

        layout.addWidget(env_group)

        # Import .env group
        import_group = QGroupBox("Import Variables from .env File")
        import_group.setStyleSheet(self._get_form_group_style())
        import_layout = QVBoxLayout(import_group)
        import_layout.setContentsMargins(16, 20, 16, 16)
        import_layout.setSpacing(12)

        import_desc = QLabel(
            "Optionally import environment variables from an existing .env file. "
            "These will be added to your project variables."
        )
        import_desc.setWordWrap(True)
        import_desc.setStyleSheet(
            f"color: {THEME_V2.text_disabled}; font-size: {TOKENS_V2.typography.sm}px; margin-bottom: {TOKENS_V2.spacing.sm}px;"
        )
        import_layout.addWidget(import_desc)

        import_row = QHBoxLayout()
        self._env_file_input = QLineEdit()
        self._env_file_input.setReadOnly(True)
        self._env_file_input.setPlaceholderText("No .env file selected (optional)")
        self._env_file_input.setStyleSheet(self._get_input_style())
        import_row.addWidget(self._env_file_input, 1)

        import_btn = QPushButton("Select .env File...")
        import_btn.setStyleSheet(self._get_inline_button_style())
        import_btn.clicked.connect(self._browse_env_file)
        import_row.addWidget(import_btn)

        import_layout.addLayout(import_row)

        # Preview of imported variables
        self._env_preview_label = QLabel("")
        self._env_preview_label.setWordWrap(True)
        self._env_preview_label.setStyleSheet(
            f"color: {THEME_V2.success}; font-size: {TOKENS_V2.typography.sm}px; "
            f"padding: {TOKENS_V2.spacing.sm}px; background: {THEME_V2.bg_component}; "
            f"border-radius: {TOKENS_V2.radius.md}px;"
        )
        self._env_preview_label.hide()
        import_layout.addWidget(self._env_preview_label)

        layout.addWidget(import_group)

        layout.addStretch()

        # Summary
        summary_group = QGroupBox("Summary")
        summary_group.setStyleSheet(self._get_form_group_style())
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setContentsMargins(16, 20, 16, 16)

        self._summary_label = QLabel("")
        self._summary_label.setWordWrap(True)
        self._summary_label.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body}px;"
        )
        summary_layout.addWidget(self._summary_label)

        layout.addWidget(summary_group)

        return page

    def _create_navigation_bar(self) -> QWidget:
        """Create navigation button bar."""
        nav = QFrame()
        nav.setFixedHeight(TOKENS_V2.sizes.toolbar_height + TOKENS_V2.spacing.lg)
        nav.setStyleSheet(
            f"background: {THEME_V2.bg_surface}; border-top: 1px solid {THEME_V2.border};"
        )

        layout = QHBoxLayout(nav)
        layout.setContentsMargins(
            *TOKENS_V2.margin.comfortable[:2] + TOKENS_V2.margin.comfortable[2:]
        )

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setStyleSheet(self._get_button_secondary_style())
        self._cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self._cancel_btn)

        layout.addStretch()

        # Back button
        self._back_btn = QPushButton("Back")
        self._back_btn.setStyleSheet(self._get_button_secondary_style())
        self._back_btn.clicked.connect(self._go_back)
        layout.addWidget(self._back_btn)

        # Next/Finish button
        self._next_btn = QPushButton("Next")
        self._next_btn.setStyleSheet(self._get_button_primary_style())
        self._next_btn.clicked.connect(self._go_next)
        layout.addWidget(self._next_btn)

        return nav

    def _create_form_field(
        self,
        label: str,
        placeholder: str,
    ) -> QGroupBox:
        """Create a labeled form field."""
        group = QGroupBox(label)
        group.setStyleSheet(self._get_form_group_style())

        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 16, 12, 12)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setStyleSheet(self._get_input_style())
        layout.addWidget(line_edit)

        return group

    def _load_templates(self) -> None:
        """Load templates from storage."""
        try:
            from casare_rpa.infrastructure.persistence.template_storage import (
                TemplateStorage,
            )

            self._templates = TemplateStorage.get_all_templates()

            # Sort by category then name
            self._templates.sort(key=lambda t: (t.category.value, t.name))

            # Populate grid
            self._populate_template_grid()

        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            self._templates = []

    def _populate_template_grid(self) -> None:
        """Populate template card grid."""
        # Clear existing
        for card in self._template_cards:
            card.deleteLater()
        self._template_cards.clear()

        # Add cards
        row, col = 0, 0
        cols_per_row = 3

        for template in self._templates:
            card = TemplateCard(template)
            card.clicked.connect(self._on_template_selected)
            self._template_grid.addWidget(card, row, col)
            self._template_cards.append(card)

            col += 1
            if col >= cols_per_row:
                col = 0
                row += 1

    def _on_template_selected(self, template: "ProjectTemplate") -> None:
        """Handle template selection."""
        self._selected_template = template

        # Update card selection states
        for card in self._template_cards:
            card.set_selected(card.get_template() == template)

        # Update preview
        self._preview_panel.update_template(template)

        # Update navigation
        self._update_navigation()

    def _on_name_changed(self, text: str) -> None:
        """Handle project name change."""
        # Auto-suggest location based on name
        if text and not self._location_input.text():
            from pathlib import Path

            default_dir = Path.home() / "Documents" / "CasareRPA" / "Projects"
            suggested = default_dir / text.replace(" ", "_")
            self._location_input.setPlaceholderText(f"e.g., {suggested}")

        self._update_navigation()

    def _browse_location(self) -> None:
        """Open folder browser for project location."""
        from pathlib import Path

        default_dir = Path.home() / "Documents" / "CasareRPA" / "Projects"
        default_dir.mkdir(parents=True, exist_ok=True)

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Location",
            str(default_dir),
            QFileDialog.Option.ShowDirsOnly,
        )

        if folder:
            self._location_input.setText(folder)
            self._update_navigation()

    def _browse_env_file(self) -> None:
        """Open file browser for .env file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select .env File",
            str(Path.home()),
            "Environment Files (*.env);;All Files (*)",
        )

        if file_path:
            self._env_file_input.setText(file_path)
            self._preview_env_file(file_path)

    def _preview_env_file(self, file_path: str) -> None:
        """Preview variables from .env file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return

            variables = {}
            content = path.read_text(encoding="utf-8")

            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    variables[key.strip()] = value.strip()

            if variables:
                preview_text = f"Found {len(variables)} variables:\n"
                preview_text += ", ".join(list(variables.keys())[:5])
                if len(variables) > 5:
                    preview_text += f", ... +{len(variables) - 5} more"
                self._env_preview_label.setText(preview_text)
                self._env_preview_label.show()
            else:
                self._env_preview_label.hide()

        except Exception as e:
            logger.warning(f"Failed to preview .env file: {e}")
            self._env_preview_label.hide()

    def _go_back(self) -> None:
        """Go to previous step."""
        current = self._stack.currentIndex()
        if current > 0:
            self._stack.setCurrentIndex(current - 1)
            self._update_navigation()

    def _go_next(self) -> None:
        """Go to next step or finish."""
        current = self._stack.currentIndex()

        if current == 0:
            # Validate step 1
            if not self._selected_template:
                self._show_warning("Please select a template.")
                return
            self._stack.setCurrentIndex(1)

        elif current == 1:
            # Validate step 2
            if not self._name_input.text().strip():
                self._show_warning("Please enter a project name.")
                return
            if not self._location_input.text().strip():
                self._show_warning("Please select a project location.")
                return
            self._update_summary()
            self._stack.setCurrentIndex(2)

        elif current == 2:
            # Finish - create project
            self._create_project()

        self._update_navigation()

    def _update_navigation(self) -> None:
        """Update navigation button states."""
        current = self._stack.currentIndex()

        # Back button
        self._back_btn.setVisible(current > 0)

        # Next button text
        if current == 2:
            self._next_btn.setText("Create Project")
        else:
            self._next_btn.setText("Next")

        # Next button enabled state
        can_proceed = True
        if current == 0:
            can_proceed = self._selected_template is not None
        elif current == 1:
            can_proceed = bool(
                self._name_input.text().strip() and self._location_input.text().strip()
            )

        self._next_btn.setEnabled(can_proceed)

        # Update step indicators
        for i, (num_label, text_label) in enumerate(self._step_labels):
            if i < current:
                # Completed
                num_label.setStyleSheet(f"""
                    background: {THEME_V2.success};
                    border-radius: {TOKENS_V2.sizes.button_lg // 2}px;
                    color: white;
                    font-weight: bold;
                """)
                text_label.setStyleSheet(f"color: {THEME_V2.success}; font-weight: bold;")
            elif i == current:
                # Current
                num_label.setStyleSheet(f"""
                    background: {THEME_V2.primary};
                    border-radius: {TOKENS_V2.sizes.button_lg // 2}px;
                    color: white;
                    font-weight: bold;
                """)
                text_label.setStyleSheet(f"color: {THEME_V2.primary}; font-weight: bold;")
            else:
                # Future
                num_label.setStyleSheet(f"""
                    background: {THEME_V2.border};
                    border-radius: {TOKENS_V2.sizes.button_lg // 2}px;
                    color: {THEME_V2.text_disabled};
                """)
                text_label.setStyleSheet(f"color: {THEME_V2.text_disabled};")

    def _update_summary(self) -> None:
        """Update summary label on step 3."""
        envs = []
        if self._env_dev.isChecked():
            envs.append("Development")
        if self._env_staging.isChecked():
            envs.append("Staging")
        if self._env_prod.isChecked():
            envs.append("Production")

        summary = f"""
        <b>Template:</b> {self._selected_template.name if self._selected_template else "None"}<br>
        <b>Project Name:</b> {self._name_input.text()}<br>
        <b>Location:</b> {self._location_input.text()}<br>
        <b>Environments:</b> {", ".join(envs) if envs else "None"}
        """

        if self._env_file_input.text():
            summary += "<br><b>.env Import:</b> Yes"

        self._summary_label.setText(summary.strip())

    def _create_project(self) -> None:
        """Create the project using the use case."""
        try:
            import asyncio

            from casare_rpa.application.use_cases.template_management import (
                CreateProjectFromTemplateUseCase,
            )

            project_name = self._name_input.text().strip()
            project_path = Path(self._location_input.text())
            description = self._description_input.toPlainText().strip()
            author = self._author_input.text().strip()

            # Determine if creating environments
            create_envs = (
                self._env_dev.isChecked()
                or self._env_staging.isChecked()
                or self._env_prod.isChecked()
            )

            # Run use case
            use_case = CreateProjectFromTemplateUseCase()

            async def do_create():
                return await use_case.execute(
                    template_id=self._selected_template.id,
                    project_name=project_name,
                    project_path=project_path,
                    author=author,
                    description=description,
                    create_default_environments=create_envs,
                )

            # Execute - use qasync if available, else run sync
            try:
                loop = asyncio.get_running_loop()
                # Already in async context (qasync), schedule coroutine
                import qasync

                future = qasync.asyncio.ensure_future(do_create())
                future.add_done_callback(lambda f: self._on_project_created(f, project_path))
                return  # Don't close dialog yet, wait for callback
            except RuntimeError:
                # No running loop, run synchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(do_create())
                finally:
                    loop.close()

            if result and result.success:
                # Import .env if specified
                env_file = self._env_file_input.text()
                if env_file:
                    self._import_env_to_project(
                        Path(env_file),
                        result.project,
                    )

                logger.info(f"Project created: {project_path}")
                self.project_created.emit(
                    str(project_path),
                    self._selected_template.id,
                )
                self.accept()
            else:
                self._show_error(f"Failed to create project:\n{result.error}")

        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            self._show_error(f"Failed to create project:\n{str(e)}")

    def _on_project_created(self, future, project_path: Path) -> None:
        """Handle async project creation result."""
        from PySide6.QtCore import QTimer

        try:
            result = future.result()

            if result.success:
                # Import .env if specified
                env_file = self._env_file_input.text()
                if env_file:
                    self._import_env_to_project_sync(
                        Path(env_file),
                        result.project,
                    )

                logger.info(f"Project created: {project_path}")
                # Emit signal and close on main thread
                QTimer.singleShot(0, lambda: self._finish_creation(project_path))
            else:
                QTimer.singleShot(
                    0,
                    lambda: self._show_error(f"Failed to create project:\n{result.error}"),
                )

        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            QTimer.singleShot(
                0, lambda err=e: self._show_error(f"Failed to create project:\n{str(err)}")
            )

    def _finish_creation(self, project_path: Path) -> None:
        """Finish project creation on main thread."""
        self.project_created.emit(
            str(project_path),
            self._selected_template.id,
        )
        self.accept()

    def _import_env_to_project_sync(
        self,
        env_file: Path,
        project: "Project",
    ) -> None:
        """Import .env variables synchronously (already in async context)."""
        try:
            # Parse .env file directly without async
            if not env_file.exists():
                return

            variables = {}
            content = env_file.read_text(encoding="utf-8")

            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

                    variables[key] = value

            if variables and project.variables_file:
                import orjson

                # Load existing variables
                var_data = {"scope": "project", "variables": {}}
                if project.variables_file.exists():
                    var_data = orjson.loads(project.variables_file.read_bytes())

                # Merge imported variables
                if "variables" not in var_data:
                    var_data["variables"] = {}
                var_data["variables"].update(variables)

                # Save
                project.variables_file.write_bytes(
                    orjson.dumps(var_data, option=orjson.OPT_INDENT_2)
                )

                logger.info(f"Imported {len(variables)} variables from .env")

        except Exception as e:
            logger.warning(f"Failed to import .env: {e}")

    def _import_env_to_project(
        self,
        env_file: Path,
        project: "Project",
    ) -> None:
        """Import .env variables to project."""
        try:
            import asyncio

            from casare_rpa.application.use_cases.template_management import (
                ImportEnvFileUseCase,
            )

            use_case = ImportEnvFileUseCase()

            async def do_import():
                return await use_case.execute(env_file)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(do_import())
            finally:
                loop.close()

            if result.success and result.variables:
                # Add to project variables
                import orjson

                from casare_rpa.domain.entities.project import (
                    VariableScope,
                    VariablesFile,
                )
                from casare_rpa.domain.entities.variable import Variable

                var_file = project.variables_file
                if var_file.exists():
                    data = orjson.loads(var_file.read_bytes())
                    variables_file = VariablesFile.from_dict(data)
                else:
                    variables_file = VariablesFile(scope=VariableScope.PROJECT)

                for name, value in result.variables.items():
                    var = Variable(
                        name=name,
                        type="String",
                        default_value=value,
                        description="Imported from .env",
                    )
                    variables_file.set_variable(var)

                var_file.write_bytes(
                    orjson.dumps(variables_file.to_dict(), option=orjson.OPT_INDENT_2)
                )
                logger.info(f"Imported {len(result.variables)} variables from .env")

        except Exception as e:
            logger.warning(f"Failed to import .env variables: {e}")

    def _show_warning(self, message: str) -> None:
        """Show warning message box."""
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.warning(self, "Warning", message)

    def _show_error(self, message: str) -> None:
        """Show error message box."""
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(self, "Error", message)

    def _get_form_group_style(self) -> str:
        """Get form group box style."""
        return f"""
            QGroupBox {{
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                margin-top: {TOKENS_V2.spacing.sm}px;
                padding-top: {TOKENS_V2.spacing.md}px;
                font-weight: bold;
                color: {THEME_V2.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.md}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
            }}
        """

    def _get_input_style(self) -> str:
        """Get input field style."""
        return f"""
            QLineEdit {{
                background: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QLineEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """

    def _get_checkbox_style(self) -> str:
        """Get checkbox style."""
        return f"""
            QCheckBox {{
                color: {THEME_V2.text_primary};
                spacing: {TOKENS_V2.spacing.sm}px;
            }}
            QCheckBox::indicator {{
                width: {TOKENS_V2.sizes.checkbox_size}px;
                height: {TOKENS_V2.sizes.checkbox_size}px;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                background: {THEME_V2.bg_component};
            }}
            QCheckBox::indicator:checked {{
                background: {THEME_V2.accent_base};
                border-color: {THEME_V2.accent_base};
            }}
            QCheckBox::indicator:hover {{
                border-color: {THEME_V2.border_focus};
            }}
        """

    def _get_inline_button_style(self) -> str:
        """Get inline button style."""
        return f"""
            QPushButton {{
                background: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_hover};
            }}
            QPushButton:pressed {{
                background: {THEME_V2.bg_selected};
            }}
        """

    def _get_button_primary_style(self) -> str:
        """Get primary button style."""
        return f"""
            QPushButton {{
                background: {THEME_V2.primary};
                color: white;
                border: none;
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.xl}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {THEME_V2.primary_hover};
            }}
            QPushButton:pressed {{
                background: {THEME_V2.primary_active};
            }}
        """

    def _get_button_secondary_style(self) -> str:
        """Get secondary button style."""
        return f"""
            QPushButton {{
                background: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.xl}px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_hover};
            }}
            QPushButton:pressed {{
                background: {THEME_V2.bg_selected};
            }}
        """


def show_project_wizard(parent: QWidget | None = None) -> str | None:
    """
    Show project wizard dialog.

    Args:
        parent: Parent widget

    Returns:
        Project path if created, None if cancelled
    """
    wizard = ProjectWizard(parent)
    result_path = None

    def on_created(path: str, template_id: str):
        nonlocal result_path
        result_path = path

    wizard.project_created.connect(on_created)

    if wizard.exec() == QDialog.DialogCode.Accepted:
        return result_path
    return None
