"""
Advanced Options Widget for Element Selector Dialog.

Collapsible section containing Fuzzy, CV, Image, and Healing options.
These are secondary options, hidden by default for progressive disclosure.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class FuzzyOptionsTab(QWidget):
    """Tab for fuzzy matching options."""

    options_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Enable checkbox
        self._enable_check = QCheckBox("Enable fuzzy matching")
        self._enable_check.toggled.connect(self._on_enabled_changed)
        self._enable_check.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        layout.addWidget(self._enable_check)

        # Info
        info = QLabel(
            "Fuzzy matching allows partial text matches. "
            "Useful when exact text may vary slightly."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

        # Options frame
        self._options = QWidget()
        self._options.setEnabled(False)
        options_layout = QVBoxLayout(self._options)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(8)

        # Match type
        type_row = QHBoxLayout()
        type_label = QLabel("Match type:")
        type_label.setStyleSheet("color: #888; font-size: 11px;")
        type_row.addWidget(type_label)

        self._match_type = QComboBox()
        self._match_type.addItems(["Contains", "Equals", "StartsWith", "EndsWith", "Regex"])
        self._match_type.setStyleSheet("""
            QComboBox {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
                min-width: 100px;
            }
        """)
        type_row.addWidget(self._match_type)
        type_row.addStretch()
        options_layout.addLayout(type_row)

        # Text to match
        text_row = QHBoxLayout()
        text_label = QLabel("Text:")
        text_label.setStyleSheet("color: #888; font-size: 11px;")
        text_row.addWidget(text_label)

        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText("Text to match...")
        self._text_input.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
        """)
        text_row.addWidget(self._text_input, 1)
        options_layout.addLayout(text_row)

        # Accuracy slider
        acc_row = QHBoxLayout()
        acc_label = QLabel("Accuracy:")
        acc_label.setStyleSheet("color: #888; font-size: 11px;")
        acc_row.addWidget(acc_label)

        self._accuracy_slider = QSlider(Qt.Orientation.Horizontal)
        self._accuracy_slider.setMinimum(50)
        self._accuracy_slider.setMaximum(100)
        self._accuracy_slider.setValue(80)
        self._accuracy_slider.setFixedWidth(150)
        self._accuracy_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #3a3a3a;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: #f59e0b;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #f59e0b;
                border-radius: 2px;
            }
        """)
        acc_row.addWidget(self._accuracy_slider)

        self._accuracy_label = QLabel("80%")
        self._accuracy_label.setStyleSheet("color: #e0e0e0; font-size: 11px; min-width: 35px;")
        self._accuracy_slider.valueChanged.connect(lambda v: self._accuracy_label.setText(f"{v}%"))
        acc_row.addWidget(self._accuracy_label)
        acc_row.addStretch()
        options_layout.addLayout(acc_row)

        layout.addWidget(self._options)
        layout.addStretch()

    def _on_enabled_changed(self, enabled: bool) -> None:
        self._options.setEnabled(enabled)
        self.options_changed.emit()

    def is_enabled(self) -> bool:
        return self._enable_check.isChecked()

    def get_accuracy(self) -> float:
        return self._accuracy_slider.value() / 100.0

    def get_match_type(self) -> str:
        return self._match_type.currentText()

    def get_text(self) -> str:
        return self._text_input.text().strip()


class CVOptionsTab(QWidget):
    """Tab for computer vision options."""

    options_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Enable checkbox
        self._enable_check = QCheckBox("Enable computer vision fallback")
        self._enable_check.toggled.connect(self._on_enabled_changed)
        self._enable_check.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        layout.addWidget(self._enable_check)

        # Info
        info = QLabel(
            "CV uses visual recognition to find elements. "
            "Useful when DOM structure changes but appearance stays consistent."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

        # Options frame
        self._options = QWidget()
        self._options.setEnabled(False)
        options_layout = QVBoxLayout(self._options)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(8)

        # Element type
        type_row = QHBoxLayout()
        type_label = QLabel("Element type:")
        type_label.setStyleSheet("color: #888; font-size: 11px;")
        type_row.addWidget(type_label)

        self._element_type = QComboBox()
        self._element_type.addItems(["Button", "Link", "Input", "Text", "Image", "Checkbox", "Any"])
        self._element_type.setStyleSheet("""
            QComboBox {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
                min-width: 100px;
            }
        """)
        type_row.addWidget(self._element_type)
        type_row.addStretch()
        options_layout.addLayout(type_row)

        # Expected text
        text_row = QHBoxLayout()
        text_label = QLabel("Expected text:")
        text_label.setStyleSheet("color: #888; font-size: 11px;")
        text_row.addWidget(text_label)

        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText("Visible text on element...")
        self._text_input.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
        """)
        text_row.addWidget(self._text_input, 1)
        options_layout.addLayout(text_row)

        # Accuracy slider
        acc_row = QHBoxLayout()
        acc_label = QLabel("Accuracy:")
        acc_label.setStyleSheet("color: #888; font-size: 11px;")
        acc_row.addWidget(acc_label)

        self._accuracy_slider = QSlider(Qt.Orientation.Horizontal)
        self._accuracy_slider.setMinimum(50)
        self._accuracy_slider.setMaximum(100)
        self._accuracy_slider.setValue(80)
        self._accuracy_slider.setFixedWidth(150)
        self._accuracy_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #3a3a3a;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: #8b5cf6;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #8b5cf6;
                border-radius: 2px;
            }
        """)
        acc_row.addWidget(self._accuracy_slider)

        self._accuracy_label = QLabel("80%")
        self._accuracy_label.setStyleSheet("color: #e0e0e0; font-size: 11px; min-width: 35px;")
        self._accuracy_slider.valueChanged.connect(lambda v: self._accuracy_label.setText(f"{v}%"))
        acc_row.addWidget(self._accuracy_label)
        acc_row.addStretch()
        options_layout.addLayout(acc_row)

        layout.addWidget(self._options)
        layout.addStretch()

    def _on_enabled_changed(self, enabled: bool) -> None:
        self._options.setEnabled(enabled)
        self.options_changed.emit()

    def is_enabled(self) -> bool:
        return self._enable_check.isChecked()

    def get_element_type(self) -> str:
        return self._element_type.currentText()

    def get_text(self) -> str:
        return self._text_input.text().strip()

    def get_accuracy(self) -> float:
        return self._accuracy_slider.value() / 100.0


class ImageOptionsTab(QWidget):
    """Tab for image template matching options."""

    options_changed = Signal()
    capture_requested = Signal()
    load_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._template_bytes: bytes | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Enable checkbox
        self._enable_check = QCheckBox("Enable image template matching")
        self._enable_check.toggled.connect(self._on_enabled_changed)
        self._enable_check.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        layout.addWidget(self._enable_check)

        # Info
        info = QLabel(
            "Image matching finds elements by visual appearance. "
            "Best for static UI elements that don't change."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

        # Options frame
        self._options = QWidget()
        self._options.setEnabled(False)
        options_layout = QVBoxLayout(self._options)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(8)

        # Image preview row
        preview_row = QHBoxLayout()

        self._image_preview = QLabel("No image")
        self._image_preview.setFixedSize(120, 80)
        self._image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_preview.setStyleSheet("""
            QLabel {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #888;
                font-size: 10px;
            }
        """)
        preview_row.addWidget(self._image_preview)

        # Buttons
        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)

        self._capture_btn = QPushButton("Capture")
        self._capture_btn.clicked.connect(self.capture_requested.emit)
        self._capture_btn.setStyleSheet("""
            QPushButton {
                background: #ec4899;
                border: 1px solid #db2777;
                border-radius: 4px;
                padding: 4px 12px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #db2777;
            }
        """)
        btn_col.addWidget(self._capture_btn)

        self._load_btn = QPushButton("Load File")
        self._load_btn.clicked.connect(self._on_load_clicked)
        self._load_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #e0e0e0;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)
        btn_col.addWidget(self._load_btn)

        btn_col.addStretch()
        preview_row.addLayout(btn_col)
        preview_row.addStretch()
        options_layout.addLayout(preview_row)

        # Accuracy slider
        acc_row = QHBoxLayout()
        acc_label = QLabel("Accuracy:")
        acc_label.setStyleSheet("color: #888; font-size: 11px;")
        acc_row.addWidget(acc_label)

        self._accuracy_slider = QSlider(Qt.Orientation.Horizontal)
        self._accuracy_slider.setMinimum(50)
        self._accuracy_slider.setMaximum(100)
        self._accuracy_slider.setValue(80)
        self._accuracy_slider.setFixedWidth(150)
        self._accuracy_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #3a3a3a;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: #ec4899;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #ec4899;
                border-radius: 2px;
            }
        """)
        acc_row.addWidget(self._accuracy_slider)

        self._accuracy_label = QLabel("80%")
        self._accuracy_label.setStyleSheet("color: #e0e0e0; font-size: 11px; min-width: 35px;")
        self._accuracy_slider.valueChanged.connect(lambda v: self._accuracy_label.setText(f"{v}%"))
        acc_row.addWidget(self._accuracy_label)
        acc_row.addStretch()
        options_layout.addLayout(acc_row)

        layout.addWidget(self._options)
        layout.addStretch()

    def _on_enabled_changed(self, enabled: bool) -> None:
        self._options.setEnabled(enabled)
        self.options_changed.emit()

    def _on_load_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)",
        )
        if file_path:
            try:
                from pathlib import Path

                self._template_bytes = Path(file_path).read_bytes()
                self._display_template()
                self.load_requested.emit()
            except Exception:
                pass

    def _display_template(self) -> None:
        if self._template_bytes:
            image = QImage.fromData(self._template_bytes)
            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(
                110,
                70,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._image_preview.setPixmap(scaled)
        else:
            self._image_preview.setText("No image")

    def set_template(self, image_bytes: bytes) -> None:
        self._template_bytes = image_bytes
        self._display_template()

    def is_enabled(self) -> bool:
        return self._enable_check.isChecked()

    def get_template(self) -> bytes | None:
        return self._template_bytes

    def get_accuracy(self) -> float:
        return self._accuracy_slider.value() / 100.0


class HealingOptionsTab(QWidget):
    """Tab for healing context capture options."""

    options_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Title
        title = QLabel("Healing Context Capture")
        title.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        layout.addWidget(title)

        # Info
        info = QLabel(
            "Healing context is captured at design time and used to "
            "automatically recover when selectors break at runtime."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

        # Options
        self._fingerprint_check = QCheckBox("Capture element fingerprint")
        self._fingerprint_check.setChecked(True)
        self._fingerprint_check.setToolTip(
            "Store element attributes (tag, id, classes, text) for heuristic healing"
        )
        self._fingerprint_check.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self._fingerprint_check)

        self._spatial_check = QCheckBox("Capture spatial context")
        self._spatial_check.setChecked(True)
        self._spatial_check.setToolTip(
            "Store anchor relationships and positions for spatial healing"
        )
        self._spatial_check.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self._spatial_check)

        self._cv_check = QCheckBox("Capture CV template")
        self._cv_check.setChecked(False)
        self._cv_check.setToolTip(
            "Store element screenshot for visual healing (increases file size)"
        )
        self._cv_check.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self._cv_check)

        layout.addStretch()

    def get_fingerprint_enabled(self) -> bool:
        return self._fingerprint_check.isChecked()

    def get_spatial_enabled(self) -> bool:
        return self._spatial_check.isChecked()

    def get_cv_enabled(self) -> bool:
        return self._cv_check.isChecked()


class AdvancedOptionsWidget(QWidget):
    """
    Collapsible advanced options section.

    Contains tabs for:
    - Fuzzy matching
    - Computer vision
    - Image template
    - Healing context

    Signals:
        options_changed: Any option changed
    """

    options_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Collapsible header
        self._header = QPushButton("> Advanced Options")
        self._header.setCheckable(True)
        self._header.setChecked(False)
        self._header.clicked.connect(self._on_toggle)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                text-align: left;
                padding: 8px 12px;
                color: #888;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #333333;
                color: #e0e0e0;
            }
            QPushButton:checked {
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            }
        """)
        layout.addWidget(self._header)

        # Content container
        self._content = QWidget()
        self._content.setVisible(False)
        self._content.setStyleSheet("""
            QWidget {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }
        """)

        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #252525;
            }
            QTabBar::tab {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                padding: 6px 12px;
                color: #888;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: #3a3a3a;
                color: #e0e0e0;
            }
            QTabBar::tab:hover {
                background: #333333;
            }
        """)

        # Create tabs
        self._fuzzy_tab = FuzzyOptionsTab()
        self._fuzzy_tab.options_changed.connect(self.options_changed.emit)
        self._tabs.addTab(self._fuzzy_tab, "Fuzzy")

        self._cv_tab = CVOptionsTab()
        self._cv_tab.options_changed.connect(self.options_changed.emit)
        self._tabs.addTab(self._cv_tab, "CV")

        self._image_tab = ImageOptionsTab()
        self._image_tab.options_changed.connect(self.options_changed.emit)
        self._tabs.addTab(self._image_tab, "Image")

        self._healing_tab = HealingOptionsTab()
        self._healing_tab.options_changed.connect(self.options_changed.emit)
        self._tabs.addTab(self._healing_tab, "Healing")

        content_layout.addWidget(self._tabs)
        layout.addWidget(self._content)

    def _on_toggle(self) -> None:
        self._expanded = self._header.isChecked()
        self._content.setVisible(self._expanded)
        self._header.setText("v Advanced Options" if self._expanded else "> Advanced Options")

    def expand(self) -> None:
        """Expand the section."""
        self._header.setChecked(True)
        self._on_toggle()

    def collapse(self) -> None:
        """Collapse the section."""
        self._header.setChecked(False)
        self._on_toggle()

    def is_expanded(self) -> bool:
        return self._expanded

    # Accessors for tab data
    @property
    def fuzzy_tab(self) -> FuzzyOptionsTab:
        return self._fuzzy_tab

    @property
    def cv_tab(self) -> CVOptionsTab:
        return self._cv_tab

    @property
    def image_tab(self) -> ImageOptionsTab:
        return self._image_tab

    @property
    def healing_tab(self) -> HealingOptionsTab:
        return self._healing_tab

    def set_image_template(self, image_bytes: bytes) -> None:
        """Set image template in image tab."""
        self._image_tab.set_template(image_bytes)


__all__ = [
    "AdvancedOptionsWidget",
    "FuzzyOptionsTab",
    "CVOptionsTab",
    "ImageOptionsTab",
    "HealingOptionsTab",
]
