from __future__ import annotations

from casare_rpa.presentation.canvas.managers.quick_node_manager import QuickNodeManager


class _DummySettings:
    def __init__(self) -> None:
        self.data: dict[str, object] = {}

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value) -> None:
        self.data[key] = value


class _TestableQuickNodeManager(QuickNodeManager):
    _VALID_TYPES = {"LaunchBrowserNode", "ClickElementNode", "TypeTextNode", "OtherNode"}

    def _is_valid_node_type(self, node_type: str) -> bool:  # type: ignore[override]
        return node_type in self._VALID_TYPES

    def _get_node_metadata(self, node_type: str) -> tuple[str, str]:  # type: ignore[override]
        return (f"Name:{node_type}", f"cat:{node_type}")


def test_defaults_applied_when_no_saved_bindings() -> None:
    settings = _DummySettings()
    mgr = _TestableQuickNodeManager(settings_manager=settings)

    bindings = mgr.get_bindings()
    assert "b" in bindings and bindings["b"].node_type == "LaunchBrowserNode"
    assert "c" in bindings and bindings["c"].node_type == "ClickElementNode"
    assert "t" in bindings and bindings["t"].node_type == "TypeTextNode"


def test_save_and_reload_roundtrip() -> None:
    settings = _DummySettings()
    mgr1 = _TestableQuickNodeManager(settings_manager=settings)
    mgr1.set_binding("o", "OtherNode", "Other", "misc")
    mgr1.save_bindings()

    mgr2 = _TestableQuickNodeManager(settings_manager=settings)
    assert mgr2.get_binding("o") is not None
    assert mgr2.get_binding("o").node_type == "OtherNode"


def test_set_binding_enforces_one_key_per_node() -> None:
    settings = _DummySettings()
    mgr = _TestableQuickNodeManager(settings_manager=settings)

    mgr.set_binding("o", "OtherNode", "Other", "misc")
    mgr.set_binding("p", "OtherNode", "Other", "misc")

    assert mgr.get_binding("o") is None
    assert mgr.get_binding("p") is not None
