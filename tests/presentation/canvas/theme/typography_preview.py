"""
Visual Typography Preview Screen - Epic 1.2 Testing.

Standalone test widget to verify Geist fonts render correctly
in both dev and PyInstaller builds.

Usage:
    python tests/presentation/canvas/theme/typography_preview.py

Expected output:
    - Window showing all font variants (sizes, weights, families)
    - Registration status for each font family
    - Visual indication of loaded vs fallback fonts
"""

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.presentation.canvas.theme import TOKENS_V2 as TOKENS
from casare_rpa.presentation.canvas.theme import alpha
from casare_rpa.presentation.canvas.theme.font_loader import (
    GEIST_MONO_FAMILY,
    GEIST_SANS_FAMILY,
    ensure_font_registered,
    get_registered_fonts,
)

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

# Sizes to display in preview
SIZES = [10, 11, 12, 14, 16, 18, 20, 24]

# Weights to test (may not all be available in Geist)
WEIGHTS = [
    (QFont.Weight.Normal, "Regular"),
    (QFont.Weight.Medium, "Medium"),
    (QFont.Weight.DemiBold, "SemiBold"),
    (QFont.Weight.Bold, "Bold"),
]

# Sample texts for preview
SAMPLE_TEXTS = {
    "en": "The quick brown fox jumps over the lazy dog.",
    "numbers": "0123456789",
    "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?",
    "ui": "Button Cancel Save Delete",
}


class TypographyPreview(QWidget):
    """Visual preview of typography for Epic 1.2 testing."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self._populate_content()

    def _setup_ui(self) -> None:
        """Set up the preview window layout."""
        self.setWindowTitle("Typography Preview - Epic 1.2")
        self.setMinimumSize(800, 600)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(TOKENS.spacing.md)
        layout.setContentsMargins(
            TOKENS.spacing.lg, TOKENS.spacing.lg, TOKENS.spacing.lg, TOKENS.spacing.lg
        )

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        self._content_layout = QVBoxLayout(content_widget)
        self._content_layout.setSpacing(TOKENS.spacing.lg)
        self._content_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Apply theme background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME.bg_canvas};
                color: {THEME.text_primary};
            }}
        """)

    def _create_header(self) -> QWidget:
        """Create the header section with font registration status."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(TOKENS.spacing.sm)

        # Title
        title = QLabel("Typography Preview")
        title.setFont(self._make_font(size=20, weight=QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {THEME.text_primary};")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Geist Sans/Mono font rendering test")
        subtitle.setFont(self._make_font(size=12))
        subtitle.setStyleSheet(f"color: {THEME.text_secondary};")
        layout.addWidget(subtitle)

        # Registration status
        status_widget = self._create_status_section()
        layout.addWidget(status_widget)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"color: {THEME.border};")
        layout.addWidget(separator)

        return container

    def _create_status_section(self) -> QWidget:
        """Create the font registration status display."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(TOKENS.spacing.md)

        registered = get_registered_fonts()

        # Geist Sans status
        sans_status = self._create_status_badge(
            f"{GEIST_SANS_FAMILY}: {'LOADED' if registered[GEIST_SANS_FAMILY] else 'FALLBACK'}",
            is_ok=registered[GEIST_SANS_FAMILY],
        )
        layout.addWidget(sans_status)

        # Geist Mono status
        mono_status = self._create_status_badge(
            f"{GEIST_MONO_FAMILY}: {'LOADED' if registered[GEIST_MONO_FAMILY] else 'FALLBACK'}",
            is_ok=registered[GEIST_MONO_FAMILY],
        )
        layout.addWidget(mono_status)

        layout.addStretch()

        return container

    def _create_status_badge(self, text: str, is_ok: bool) -> QLabel:
        """Create a status badge label."""
        badge = QLabel(text)
        badge.setFont(self._make_font(size=11, weight=QFont.Weight.Medium))

        bg_color = alpha(THEME.success, 0.18) if is_ok else alpha(THEME.warning, 0.18)
        text_color = THEME.success if is_ok else THEME.warning

        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                border-radius: {TOKENS.radius.sm}px;
            }}
        """)
        return badge

    def _populate_content(self) -> None:
        """Populate the preview with font samples."""
        registered = get_registered_fonts()

        # Geist Sans section
        sans_section = self._create_font_section(
            GEIST_SANS_FAMILY, is_loaded=registered[GEIST_SANS_FAMILY], is_mono=False
        )
        self._content_layout.addWidget(sans_section)

        # Geist Mono section
        mono_section = self._create_font_section(
            GEIST_MONO_FAMILY, is_loaded=registered[GEIST_MONO_FAMILY], is_mono=True
        )
        self._content_layout.addWidget(mono_section)

        # System fallback section
        fallback_section = self._create_font_section(
            "Segoe UI", is_loaded=True, is_mono=False, title="System Fallback"
        )
        self._content_layout.addWidget(fallback_section)

        self._content_layout.addStretch()

    def _create_font_section(
        self,
        family: str,
        is_loaded: bool,
        is_mono: bool,
        title: str | None = None,
    ) -> QWidget:
        """Create a section showing all variants of a font family."""
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME.bg_surface};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                padding: {TOKENS.spacing.md}px;
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setSpacing(TOKENS.spacing.md)

        # Section header
        header_text = title or f"{family} ({'Loaded' if is_loaded else 'Fallback'})"
        header = QLabel(header_text)
        header.setFont(
            self._make_font(
                size=14, weight=QFont.Weight.DemiBold, family=family if is_loaded else None
            )
        )
        header.setStyleSheet(f"color: {THEME.text_primary};")
        layout.addWidget(header)

        # Size samples
        for size in SIZES:
            size_label = QLabel(f"{size}px: {SAMPLE_TEXTS['en']}")
            size_label.setFont(self._make_font(size=size, family=family if is_loaded else None))
            size_label.setStyleSheet(f"color: {THEME.text_primary};")
            layout.addWidget(size_label)

        # Weight samples (at 14px)
        weights_label = QLabel("Weights:")
        weights_label.setFont(self._make_font(size=11))
        weights_label.setStyleSheet(f"color: {THEME.text_secondary};")
        layout.addWidget(weights_label)

        for weight, weight_name in WEIGHTS:
            # Check if this weight is available
            font = QFont(family if is_loaded else "Segoe UI", 14)
            font.setWeight(weight)

            weight_label = QLabel(f"  {weight_name} ({weight}): {SAMPLE_TEXTS['ui']}")
            weight_label.setFont(font)
            weight_label.setStyleSheet(f"color: {THEME.text_primary};")
            layout.addWidget(weight_label)

        # Mono-specific samples
        if is_mono:
            mono_label = QLabel("Code sample:")
            mono_label.setFont(self._make_font(size=11))
            mono_label.setStyleSheet(f"color: {THEME.text_secondary};")
            layout.addWidget(mono_label)

            code_sample = QLabel(
                "def process_workflow(data: dict) -> None:\n"
                "    for item in data['items']:\n"
                "        yield transform(item)"
            )
            code_sample.setFont(
                self._make_font(size=12, family=family if is_loaded else "Cascadia Code")
            )
            code_sample.setStyleSheet(f"color: {THEME.text_primary};")
            layout.addWidget(code_sample)

        return container

    def _make_font(
        self,
        size: int = 12,
        weight: QFont.Weight = QFont.Weight.Normal,
        family: str | None = None,
    ) -> QFont:
        """Create a QFont with specified parameters."""
        if family:
            font = QFont(family, size)
        else:
            # Use default UI font
            font = QFont()
            font.setPointSize(size)
        font.setWeight(weight)
        return font


def main() -> None:
    """Run the typography preview standalone."""
    # Ensure fonts are registered
    ensure_font_registered()

    app = QApplication()

    # Show available font families (for debugging)
    families = QFontDatabase.families()
    geist_families = [f for f in families if "geist" in f.lower()]
    if geist_families:
        print(f"Found Geist fonts: {geist_families}")
    else:
        print("No Geist fonts found - using system fallbacks")

    # Create and show window
    preview = TypographyPreview()
    preview.show()

    app.exec()


if __name__ == "__main__":
    main()
