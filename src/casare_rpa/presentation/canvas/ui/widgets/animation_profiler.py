"""
Animation performance profiler widget.

Displays real-time animation performance metrics for debugging.
Toggle visibility with Ctrl+Shift+A in development mode.

Usage:
    profiler = AnimationProfiler()
    profiler.show()  # Shows floating debug window

    # Update stats from your animation loop:
    profiler.record_frame(frame_time_ms)
    profiler.set_active_animations(count)
    profiler.set_lod_level("full")
    profiler.set_pool_stats(used=5, total=10)
"""

from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.ui.theme import Theme


class AnimationProfiler(QWidget):
    """
    Debug overlay widget showing animation performance stats.

    Displays:
    - FPS (calculated from avg frame time)
    - Frame time (average and max)
    - Active animation count
    - Dropped frames count
    - LOD level
    - Object pool stats

    Stats update every 500ms. Semi-transparent overlay, stays on top.
    Fixed size 300x200.

    Keyboard shortcut: Ctrl+Shift+A (implement in parent widget).
    """

    # Update interval in milliseconds
    UPDATE_INTERVAL_MS = 500

    # Frame time thresholds (ms) for dropped frame detection
    TARGET_FRAME_TIME_MS = 16.67  # 60 FPS target
    DROPPED_FRAME_THRESHOLD_MS = 33.33  # Below 30 FPS = dropped

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Frame timing data
        self._frame_times: list[float] = []
        self._max_frame_time: float = 0.0
        self._dropped_frames: int = 0
        self._active_animations: int = 0
        self._lod_level: str = "full"
        self._pool_used: int = 0
        self._pool_total: int = 0

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self) -> None:
        """Initialize the widget UI."""
        colors = Theme.get_colors()

        # Window flags: tool window, stays on top, frameless
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Fixed size
        self.setFixedSize(300, 200)

        # Semi-transparent dark background
        self.setStyleSheet(f"""
            AnimationProfiler {{
                background-color: rgba(30, 30, 30, 230);
                border: 1px solid {colors.border};
                border-radius: 8px;
            }}
        """)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Title
        title = QLabel("Animation Profiler")
        title.setStyleSheet(f"""
            color: {colors.text_primary};
            font-size: 12px;
            font-weight: bold;
            padding-bottom: 4px;
            border-bottom: 1px solid {colors.border};
        """)
        layout.addWidget(title)

        # Stats container
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: transparent; border: none;")
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 8, 0, 0)
        stats_layout.setSpacing(6)

        # Monospace font for stats
        mono_font = QFont("Consolas", 11)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)

        # Create stat labels
        self._fps_label = self._create_stat_label("FPS:", "0", mono_font, colors)
        stats_layout.addWidget(self._fps_label)

        self._frame_label = self._create_stat_label(
            "Frame:", "0.0ms (max: 0.0ms)", mono_font, colors
        )
        stats_layout.addWidget(self._frame_label)

        self._animations_label = self._create_stat_label(
            "Active Animations:", "0", mono_font, colors
        )
        stats_layout.addWidget(self._animations_label)

        self._dropped_label = self._create_stat_label(
            "Dropped Frames:", "0", mono_font, colors
        )
        stats_layout.addWidget(self._dropped_label)

        self._lod_label = self._create_stat_label(
            "LOD Level:", "full", mono_font, colors
        )
        stats_layout.addWidget(self._lod_label)

        self._pool_label = self._create_stat_label(
            "Pool Stats:", "0/0 used", mono_font, colors
        )
        stats_layout.addWidget(self._pool_label)

        layout.addWidget(stats_frame)
        layout.addStretch()

    def _create_stat_label(self, name: str, value: str, font: QFont, colors) -> QLabel:
        """Create a formatted stat label."""
        label = QLabel(f"{name} {value}")
        label.setFont(font)
        label.setStyleSheet(f"""
            color: {colors.text_secondary};
            background: transparent;
        """)
        return label

    def _setup_timer(self) -> None:
        """Set up the stats update timer."""
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(self.UPDATE_INTERVAL_MS)

    def record_frame(self, frame_time_ms: float) -> None:
        """
        Record a frame time measurement.

        Args:
            frame_time_ms: Time taken to render the frame in milliseconds.
        """
        self._frame_times.append(frame_time_ms)

        # Track max frame time
        if frame_time_ms > self._max_frame_time:
            self._max_frame_time = frame_time_ms

        # Detect dropped frames
        if frame_time_ms > self.DROPPED_FRAME_THRESHOLD_MS:
            self._dropped_frames += 1

        # Keep only recent samples (last 2 seconds worth at 60fps = 120 samples)
        if len(self._frame_times) > 120:
            self._frame_times = self._frame_times[-120:]

    def set_active_animations(self, count: int) -> None:
        """
        Set the number of currently active animations.

        Args:
            count: Number of animations currently running.
        """
        self._active_animations = count

    def set_lod_level(self, level: str) -> None:
        """
        Set the current LOD level display.

        Args:
            level: LOD level string (full/medium/low/ultra_low).
        """
        self._lod_level = level

    def set_pool_stats(self, used: int, total: int) -> None:
        """
        Set object pool statistics.

        Args:
            used: Number of pool objects in use.
            total: Total pool capacity.
        """
        self._pool_used = used
        self._pool_total = total

    def _update_display(self) -> None:
        """Update all stat displays with current values."""
        colors = Theme.get_colors()

        # Calculate FPS and average frame time
        if self._frame_times:
            avg_frame_ms = sum(self._frame_times) / len(self._frame_times)
            fps = 1000.0 / avg_frame_ms if avg_frame_ms > 0 else 0
        else:
            avg_frame_ms = 0.0
            fps = 0.0

        # FPS with color coding
        fps_color = colors.success
        if fps < 30:
            fps_color = colors.error
        elif fps < 55:
            fps_color = colors.warning

        self._fps_label.setText(f"FPS: {fps:.0f}")
        self._fps_label.setStyleSheet(f"""
            color: {fps_color};
            background: transparent;
            font-weight: bold;
        """)

        # Frame time
        self._frame_label.setText(
            f"Frame: {avg_frame_ms:.1f}ms (max: {self._max_frame_time:.1f}ms)"
        )

        # Active animations
        self._animations_label.setText(f"Active Animations: {self._active_animations}")

        # Dropped frames with color coding
        dropped_color = colors.text_secondary
        if self._dropped_frames > 0:
            dropped_color = colors.warning
        if self._dropped_frames > 10:
            dropped_color = colors.error

        self._dropped_label.setText(f"Dropped Frames: {self._dropped_frames}")
        self._dropped_label.setStyleSheet(f"""
            color: {dropped_color};
            background: transparent;
        """)

        # LOD level
        self._lod_label.setText(f"LOD Level: {self._lod_level}")

        # Pool stats
        self._pool_label.setText(
            f"Pool Stats: {self._pool_used}/{self._pool_total} used"
        )

    def reset_stats(self) -> None:
        """Reset all statistics to initial values."""
        self._frame_times.clear()
        self._max_frame_time = 0.0
        self._dropped_frames = 0
        self._active_animations = 0
        self._update_display()

    def showEvent(self, event) -> None:
        """Handle show event - reset max frame time on each show."""
        super().showEvent(event)
        self._max_frame_time = 0.0
        self._update_display()

    def closeEvent(self, event) -> None:
        """Handle close event - stop timer."""
        self._update_timer.stop()
        super().closeEvent(event)
