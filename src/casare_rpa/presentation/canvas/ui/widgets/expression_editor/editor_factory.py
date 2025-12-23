"""
Editor Factory for CasareRPA Expression Editor.

Provides factory method for creating the appropriate editor based on EditorType.
Maps EditorType enum values to concrete editor implementations.

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
        EditorFactory, EditorType
    )

    editor = EditorFactory.create(EditorType.CODE_PYTHON)
"""

from typing import Optional

from PySide6.QtWidgets import QWidget

from loguru import logger

from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
    BaseExpressionEditor,
    EditorType,
)


class EditorFactory:
    """
    Factory for creating expression editors.

    Creates the appropriate editor implementation based on EditorType.
    """

    @staticmethod
    def create(
        editor_type: EditorType,
        parent: Optional[QWidget] = None,
    ) -> BaseExpressionEditor:
        """
        Create an editor for the given type.

        Args:
            editor_type: Type of editor to create
            parent: Optional parent widget

        Returns:
            Concrete BaseExpressionEditor implementation

        Raises:
            ValueError: If editor_type is not recognized
        """
        logger.debug(f"Creating editor for type: {editor_type}")

        if editor_type == EditorType.CODE_PYTHON:
            from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_editor import (
                CodeExpressionEditor,
            )

            return CodeExpressionEditor(language="python", parent=parent)

        elif editor_type == EditorType.CODE_JAVASCRIPT:
            from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_editor import (
                CodeExpressionEditor,
            )

            return CodeExpressionEditor(language="javascript", parent=parent)

        elif editor_type == EditorType.CODE_CMD:
            from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_editor import (
                CodeExpressionEditor,
            )

            return CodeExpressionEditor(language="cmd", parent=parent)

        elif editor_type == EditorType.CODE_JSON:
            from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_editor import (
                CodeExpressionEditor,
            )

            return CodeExpressionEditor(language="json", parent=parent)

        elif editor_type == EditorType.CODE_YAML:
            from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_editor import (
                CodeExpressionEditor,
            )

            return CodeExpressionEditor(language="yaml", parent=parent)

        elif editor_type == EditorType.CODE_MARKDOWN:
            from casare_rpa.presentation.canvas.ui.widgets.expression_editor.markdown_editor import (
                MarkdownEditor,
            )

            return MarkdownEditor(parent=parent)

        elif editor_type == EditorType.RICH_TEXT:
            from casare_rpa.presentation.canvas.ui.widgets.expression_editor.rich_text_editor import (
                RichTextEditor,
            )

            return RichTextEditor(parent=parent)

        elif editor_type == EditorType.AUTO:
            from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_editor import (
                CodeExpressionEditor,
            )

            return CodeExpressionEditor(language="auto", parent=parent)

        else:
            raise ValueError(f"Unknown editor type: {editor_type}")

    @staticmethod
    def create_for_property_type(
        property_type: str,
        node_type: Optional[str] = None,
        property_name: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> BaseExpressionEditor:
        """
        Create an editor based on property type and optional overrides.

        Convenience method that maps property types to editor types
        and checks for node-specific overrides.

        Args:
            property_type: PropertyType name (CODE, TEXT, STRING, JSON, etc.)
            node_type: Optional node type for override lookup
            property_name: Optional property name for override lookup
            parent: Optional parent widget

        Returns:
            Appropriate editor instance
        """
        # Check for node-specific overrides
        if node_type and property_name:
            override = _NODE_EDITOR_OVERRIDES.get(node_type, {}).get(property_name)
            if override:
<<<<<<< HEAD
                logger.debug(
                    f"Using editor override for {node_type}.{property_name}: {override}"
                )
                return EditorFactory.create(override, parent)

        # Map property type to editor type
        editor_type = _PROPERTY_TYPE_TO_EDITOR.get(
            property_type.upper(), EditorType.RICH_TEXT
        )
=======
                logger.debug(f"Using editor override for {node_type}.{property_name}: {override}")
                return EditorFactory.create(override, parent)

        # Map property type to editor type
        editor_type = _PROPERTY_TYPE_TO_EDITOR.get(property_type.upper(), EditorType.RICH_TEXT)
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        return EditorFactory.create(editor_type, parent)


# Property type to editor type mapping
_PROPERTY_TYPE_TO_EDITOR = {
    "CODE": EditorType.CODE_PYTHON,
    "TEXT": EditorType.AUTO,
    "STRING": EditorType.AUTO,
    "JSON": EditorType.CODE_JSON,
    "YAML": EditorType.CODE_YAML,
    "SCRIPT": EditorType.CODE_PYTHON,
}

# Node-specific editor overrides
_NODE_EDITOR_OVERRIDES = {
    "EmailSendNode": {
        "body": EditorType.CODE_MARKDOWN,
    },
    "BrowserEvaluateNode": {
        "script": EditorType.CODE_JAVASCRIPT,
    },
    "RunPythonNode": {
        "code": EditorType.CODE_PYTHON,
    },
    "CommandNode": {
        "command": EditorType.CODE_CMD,
    },
    "ExecuteScriptNode": {
        "script": EditorType.CODE_PYTHON,
    },
    "JsonParseNode": {
        "json_string": EditorType.CODE_JSON,
    },
    "YamlParseNode": {
        "yaml_string": EditorType.CODE_YAML,
    },
}
