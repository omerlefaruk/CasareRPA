import os

import pytest

from casare_rpa.presentation.canvas.theme import THEME_V2

# Ensure Qt headless mode (importing theme can import Qt resources in some paths)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.ui
def test_theme_v2_has_no_legacy_aliases() -> None:
    # Enforce v2 theme as the single source of truth (no legacy alias names).
    assert not hasattr(THEME_V2, "bg_input")
    assert not hasattr(THEME_V2, "status_disabled")
    assert not hasattr(THEME_V2, "status_success")
    assert not hasattr(THEME_V2, "node_border_normal")


@pytest.mark.ui
def test_theme_v2_node_disabled_overlay_tokens_exist() -> None:
    assert hasattr(THEME_V2, "input_bg")
    assert hasattr(THEME_V2, "node_disabled_wash")
