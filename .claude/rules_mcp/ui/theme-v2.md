<rules category="ui">
  <theme_v2>
    <name>Theme System V2 Patterns</name>
    <file>@src/casare_rpa/presentation/canvas/theme_system/tokens_v2.py</file>

    <import_pattern>
      <correct><![CDATA[
from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme_system.icons_v2 import get_icon
]]></correct>
    </import_pattern>

    <styling>
      <correct><![CDATA[
# Background and foreground
widget.setStyleSheet(f"""
    background: {THEME_V2.bg.primary};
    color: {THEME_V2.text.primary};
    border: 1px solid {THEME_V2.border.default};
    border-radius: {TOKENS_V2.radius.sm}px;
""")

# Accent colors
button.setStyleSheet(f"""
    background: {THEME_V2.accent.primary};
    color: {THEME_V2.text.onaccent};
""")

# State colors
status_success.setStyleSheet(f"color: {THEME_V2.success};")
status_error.setStyleSheet(f"color: {THEME_V2.error};")
status_warning.setStyleSheet(f"color: {THEME_V2.warning};")
]]></correct>

      <forbidden>widget.setStyleSheet("color: #ffffff")  # Hardcoded colors</forbidden>
    </styling>

    <icons>
      <correct><![CDATA[
# Get icon with size and state
icon = get_icon("play", size=20)
icon_accent = get_icon("play", size=20, state="accent")
icon_disabled = get_icon("play", size=20, state="disabled")
]]></correct>
    </icons>

    <spacing>
      <use>TOKENS_V2 for all spacing/sizing</use>

      <correct><![CDATA[
widget.setContentsMargins(
    TOKENS_V2.spacing.sm,
    TOKENS_V2.spacing.md,
    TOKENS_V2.spacing.sm,
    TOKENS_V2.spacing.md,
)
]]></correct>
    </spacing>

    <caching>
      <rule>Module-level caching for stylesheets</rule>
      <correct><![CDATA[
_CACHED_STYLESHEET: str | None = None

def get_component_stylesheet() -> str:
    global _CACHED_STYLESHEET
    if _CACHED_STYLESHEET is None:
        _CACHED_STYLESHEET = _generate_stylesheet()
    return _CACHED_STYLESHEET
]]></correct>
    </caching>
  </theme_v2>

  <fonts>
    <loader>@src/casare_rpa/presentation/canvas/theme_system/font_loader.py</loader>

    <correct><![CDATA[
from casare_rpa.presentation.canvas.theme_system.font_loader import (
    ensure_font_registered,
    GEIST_SANS_FAMILY,
    GEIST_MONO_FAMILY,
)

# Call BEFORE QApplication creation
def main():
    ensure_font_registered()
    app = QApplication([])
    # ...
]]></correct>

    <usage>
      <rule>Use font family constants, not string literals</rule>
      <correct>font.setFamily(GEIST_SANS_FAMILY)</correct>
      <wrong>font.setFamily("Segoe UI")  # Use constant</wrong>
    </usage>
  </fonts>
</rules>
