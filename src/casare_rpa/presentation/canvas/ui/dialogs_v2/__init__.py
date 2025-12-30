"""
Dialog Framework v2 - Epic 7.1.

Standardized dialog components with v2 design system:
- Consistent title area, body padding, footer button placement
- Primary/secondary/destructive button variants
- Keyboard shortcuts (Enter = primary, Esc = cancel)
- No QGraphicsDropShadowEffect, no animations
- Full THEME_V2/TOKENS_V2 integration

Usage:
    from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
        BaseDialogV2,
        MessageBoxV2,
        ConfirmDialogV2,
        ButtonRole,
        DialogSizeV2,
    )

    # Message boxes
    MessageBoxV2.show_info(parent, "Success", "Operation completed")
    MessageBoxV2.show_warning(parent, "Warning", "Check your inputs")
    MessageBoxV2.show_error(parent, "Error", "Something went wrong")

    # Question dialog (returns bool)
    if MessageBoxV2.show_question(parent, "Confirm", "Continue?"):
        print("User confirmed")

    # Destructive confirmation
    if ConfirmDialogV2.show_confirm(parent, "Delete", "Are you sure?", "Delete"):
        print("User confirmed deletion")

    # Custom dialog
    class MyDialog(BaseDialogV2):
        def __init__(self, parent=None):
            super().__init__(
                title="My Dialog",
                parent=parent,
                size=DialogSizeV2.MD,
            )
            # Set body content
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.addWidget(QLabel("Dialog content here"))
            self.set_body_widget(content)

            # Set buttons
            self.set_primary_button("Save", self._on_save)
            self.set_secondary_button("Cancel", self.reject)

See: docs/UX_REDESIGN_PLAN.md Epic 7.1
"""

# =============================================================================
# ENUMS
# =============================================================================

# =============================================================================
# BASE DIALOG
# =============================================================================
from casare_rpa.presentation.canvas.ui.dialogs_v2.base_dialog_v2 import (
    BaseDialogV2,
    ButtonRole,
    DialogFooter,
    DialogSizeV2,
    DialogTitleBar,
)

# =============================================================================
# CONFIRM DIALOG
# =============================================================================
from casare_rpa.presentation.canvas.ui.dialogs_v2.confirm_dialog_v2 import ConfirmDialogV2

# =============================================================================
# INPUT DIALOG
# =============================================================================
from casare_rpa.presentation.canvas.ui.dialogs_v2.input_dialog_v2 import InputDialogV2

# =============================================================================
# MESSAGE BOX
# =============================================================================
from casare_rpa.presentation.canvas.ui.dialogs_v2.message_box_v2 import MessageBoxV2

# =============================================================================
# PROMPTS V2 (Migration Convenience API)
# =============================================================================
from casare_rpa.presentation.canvas.ui.dialogs_v2.prompts_v2 import (
    ToastLevel,
    ToastV2,
    get_password,
    get_text,
    show_confirm,
    show_error,
    show_info,
    show_question,
    show_warning,
    toast_error,
    toast_info,
    toast_success,
    toast_warning,
)

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Enums
    "ButtonRole",
    "DialogSizeV2",
    # Base classes
    "BaseDialogV2",
    "DialogFooter",
    "DialogTitleBar",
    # Dialogs
    "MessageBoxV2",
    "ConfirmDialogV2",
    "InputDialogV2",
    # Convenience API (Epic 7.3 migration)
    "ToastLevel",
    "ToastV2",
    "get_password",
    "get_text",
    "show_confirm",
    "show_error",
    "show_info",
    "show_question",
    "show_warning",
    "toast_error",
    "toast_info",
    "toast_success",
    "toast_warning",
]
