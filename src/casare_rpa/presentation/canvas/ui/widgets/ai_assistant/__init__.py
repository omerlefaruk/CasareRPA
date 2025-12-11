"""
AI Assistant Widget Package.

Provides a dockable AI-powered assistant for CasareRPA Canvas.
Enables natural language workflow generation with preview and validation.

Components:
    AIAssistantDock: Main dockable widget container
    ChatArea: Message display with user/AI bubbles
    PreviewCard: Workflow preview with append/regenerate actions

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.ai_assistant import (
        AIAssistantDock,
        ChatArea,
        PreviewCard,
    )

    # Create and add to main window
    assistant = AIAssistantDock(parent=main_window)
    main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, assistant)

    # Connect signals
    assistant.workflow_ready.connect(on_workflow_generated)
    assistant.append_requested.connect(on_append_to_canvas)
"""

from casare_rpa.presentation.canvas.ui.widgets.ai_assistant.dock import (
    AIAssistantDock,
)
from casare_rpa.presentation.canvas.ui.widgets.ai_assistant.chat_area import (
    ChatArea,
    MessageBubble,
)
from casare_rpa.presentation.canvas.ui.widgets.ai_assistant.preview_card import (
    PreviewCard,
)

__all__ = [
    "AIAssistantDock",
    "ChatArea",
    "MessageBubble",
    "PreviewCard",
]
