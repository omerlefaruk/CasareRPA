"""
Frame Managers

Contains management components for NodeFrame:
- FrameBoundsManager: Centralized timer for bounds checking
- FrameDeletedCmd: Undo command for frame deletion

Following Single Responsibility Principle - separating manager concerns
from the frame UI component.
"""

from typing import TYPE_CHECKING, Optional, Set
from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QTimer, QObject

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.graph.node_frame import NodeFrame


class FrameDeletedCmd(QUndoCommand):
    """
    Undo command for frame deletion.

    Stores all frame state to allow restoring the frame on undo.
    """

    def __init__(self, frame: "NodeFrame", scene, description: str = "Delete Frame"):
        super().__init__(description)
        self._scene = scene
        self._frame_data = None
        self._frame = frame
        self._was_deleted = False

        self._store_frame_state()

    def _store_frame_state(self):
        """Store all frame state for restoration."""
        self._frame_data = {
            "title": self._frame.frame_title,
            "color": self._frame.frame_color,
            "pos": (self._frame.pos().x(), self._frame.pos().y()),
            "rect": (self._frame.rect().width(), self._frame.rect().height()),
            "contained_node_ids": [
                node.id if hasattr(node, "id") else id(node)
                for node in self._frame.contained_nodes
            ],
            "is_collapsed": self._frame._is_collapsed,
            "expanded_rect": (
                self._frame._expanded_rect.width(),
                self._frame._expanded_rect.height(),
            )
            if self._frame._expanded_rect
            else None,
        }

    def undo(self):
        """Restore the deleted frame."""
        if not self._was_deleted or not self._frame_data:
            return

        if self._scene and self._frame:
            self._scene.addItem(self._frame)

            if hasattr(self._frame, "_bounds_manager") and self._frame._bounds_manager:
                self._frame._bounds_manager.register_frame(self._frame)

            self._was_deleted = False

    def redo(self):
        """Delete the frame again."""
        if self._frame:
            if hasattr(self._frame, "_bounds_manager") and self._frame._bounds_manager:
                self._frame._bounds_manager.unregister_frame(self._frame)

            if self._frame.scene():
                self._frame.scene().removeItem(self._frame)
            self._was_deleted = True


class FrameBoundsManager(QObject):
    """
    Centralized manager for all frame bounds checking.

    Instead of each frame having its own 100ms timer, this manager uses
    a single timer to check all frames. This significantly reduces CPU
    usage when there are many frames.

    Usage:
        manager = FrameBoundsManager.get_instance()
        manager.register_frame(frame)
        manager.unregister_frame(frame)
    """

    _instance: Optional["FrameBoundsManager"] = None

    @classmethod
    def get_instance(cls) -> "FrameBoundsManager":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        if cls._instance:
            cls._instance._timer.stop()
            cls._instance._frames.clear()
        cls._instance = None

    def __init__(self, parent: Optional[QObject] = None):
        """Initialize the bounds manager."""
        super().__init__(parent)
        self._frames: Set["NodeFrame"] = set()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._batch_check)
        self._interval = 150  # ms

    def register_frame(self, frame: "NodeFrame") -> None:
        """Register a frame for bounds checking."""
        self._frames.add(frame)
        if not self._timer.isActive():
            self._timer.start(self._interval)

    def unregister_frame(self, frame: "NodeFrame") -> None:
        """Unregister a frame from bounds checking."""
        self._frames.discard(frame)
        if not self._frames and self._timer.isActive():
            self._timer.stop()

    def _batch_check(self) -> None:
        """Check all frames in a single pass."""
        if not self._frames:
            return

        for frame in list(self._frames):
            try:
                if frame.scene():
                    frame._check_node_bounds()
            except Exception:
                pass

    @property
    def frame_count(self) -> int:
        """Get the number of registered frames."""
        return len(self._frames)

    @property
    def is_running(self) -> bool:
        """Check if the timer is running."""
        return self._timer.isActive()
