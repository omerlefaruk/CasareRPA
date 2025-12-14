"""
Expression Editor Module for CasareRPA.

Provides enhanced text editing capabilities for node properties with:
- Code editing (Python/JS/CMD) with syntax highlighting
- Markdown editing for email bodies
- Rich text editing with variable support
- Popup window with resize and drag support

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
        ExpressionEditorPopup,
        EditorType,
        EditorFactory,
        CodeExpressionEditor,
        MarkdownEditor,
        RichTextEditor,
        ExpandButton,
    )

    # Show expression editor popup for a widget
    popup = ExpressionEditorPopup()
    popup.show_for_widget(widget, EditorType.CODE_PYTHON, "print('hello')")

    # Or create editors directly via factory
    editor = EditorFactory.create(EditorType.CODE_PYTHON)
    editor.set_value("print('hello')")
"""

from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
    BaseExpressionEditor,
    EditorType,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.expression_editor_popup import (
    ExpressionEditorPopup,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.editor_factory import (
    EditorFactory,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_editor import (
    CodeExpressionEditor,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.markdown_editor import (
    MarkdownEditor,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.rich_text_editor import (
    RichTextEditor,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets import (
    ExpandButton,
)

__all__ = [
    # Base classes and types
    "BaseExpressionEditor",
    "EditorType",
    # Factory
    "EditorFactory",
    # Main popup
    "ExpressionEditorPopup",
    # Editor implementations
    "CodeExpressionEditor",
    "MarkdownEditor",
    "RichTextEditor",
    # Widgets
    "ExpandButton",
]
