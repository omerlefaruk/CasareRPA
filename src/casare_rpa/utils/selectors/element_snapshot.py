"""Visual diff tool for element comparison.

Captures complete snapshots of DOM elements including visual appearance,
attributes, content, and state. Enables before/after comparison for
detecting element changes during workflow execution.
"""

import base64
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass
class ElementSnapshot:
    """Complete snapshot of element state.

    Captures all relevant element information for comparison:
    - Visual: screenshot, bounding box
    - Identity: tag, id, classes, attributes
    - Content: text, innerHTML
    - State: visibility, enabled status
    """

    selector: str
    timestamp: float

    # Visual
    screenshot_b64: str | None = None
    bounding_rect: dict[str, int] = field(default_factory=dict)

    # Identity
    tag: str = ""
    id: str | None = None
    classes: list[str] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)

    # Content
    text_content: str = ""
    inner_html: str = ""

    # State
    is_visible: bool = True
    is_enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary for serialization."""
        return {
            "selector": self.selector,
            "timestamp": self.timestamp,
            "screenshot_b64": self.screenshot_b64,
            "bounding_rect": self.bounding_rect,
            "tag": self.tag,
            "id": self.id,
            "classes": self.classes,
            "attributes": self.attributes,
            "text_content": self.text_content,
            "inner_html": self.inner_html[:1000],  # Truncate for storage
            "is_visible": self.is_visible,
            "is_enabled": self.is_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ElementSnapshot":
        """Create snapshot from dictionary.

        Args:
            data: Dictionary with snapshot fields

        Returns:
            ElementSnapshot instance
        """
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)

    def get_identity_hash(self) -> str:
        """Get hash of identity attributes for quick comparison."""
        identity = f"{self.tag}#{self.id or ''}|{','.join(sorted(self.classes))}"
        return identity


@dataclass
class ElementDiff:
    """Differences between two element snapshots.

    Tracks all categories of changes:
    - Position and size changes
    - Attribute additions, removals, modifications
    - Class list changes
    - Text content changes
    """

    has_changes: bool = False

    # Position/size changes
    position_changed: bool = False
    size_changed: bool = False
    old_position: tuple[int, int] | None = None
    new_position: tuple[int, int] | None = None
    old_size: tuple[int, int] | None = None
    new_size: tuple[int, int] | None = None

    # Attribute changes
    attributes_added: dict[str, str] = field(default_factory=dict)
    attributes_removed: dict[str, str] = field(default_factory=dict)
    attributes_changed: dict[str, tuple[str, str]] = field(default_factory=dict)  # name: (old, new)

    # Class changes
    classes_added: list[str] = field(default_factory=list)
    classes_removed: list[str] = field(default_factory=list)

    # Content changes
    text_changed: bool = False
    old_text: str = ""
    new_text: str = ""

    # State changes
    visibility_changed: bool = False
    enabled_changed: bool = False

    def summary(self) -> str:
        """Get human-readable summary of changes.

        Returns:
            Semicolon-separated list of change descriptions
        """
        if not self.has_changes:
            return "No changes detected"

        parts: list[str] = []

        if self.position_changed:
            if self.old_position and self.new_position:
                parts.append(
                    f"position: ({self.old_position[0]},{self.old_position[1]}) -> "
                    f"({self.new_position[0]},{self.new_position[1]})"
                )
            else:
                parts.append("position changed")

        if self.size_changed:
            if self.old_size and self.new_size:
                parts.append(
                    f"size: {self.old_size[0]}x{self.old_size[1]} -> "
                    f"{self.new_size[0]}x{self.new_size[1]}"
                )
            else:
                parts.append("size changed")

        if self.attributes_added:
            attrs = list(self.attributes_added.keys())
            parts.append(f"attrs added: {attrs}")

        if self.attributes_removed:
            attrs = list(self.attributes_removed.keys())
            parts.append(f"attrs removed: {attrs}")

        if self.attributes_changed:
            changed = []
            for name, (old_val, new_val) in self.attributes_changed.items():
                # Truncate long values
                old_display = old_val[:20] + "..." if len(old_val) > 20 else old_val
                new_display = new_val[:20] + "..." if len(new_val) > 20 else new_val
                changed.append(f"{name}: '{old_display}' -> '{new_display}'")
            parts.append(f"attrs changed: [{', '.join(changed)}]")

        if self.classes_added:
            parts.append(f"classes added: {self.classes_added}")

        if self.classes_removed:
            parts.append(f"classes removed: {self.classes_removed}")

        if self.text_changed:
            old_preview = self.old_text[:30] + "..." if len(self.old_text) > 30 else self.old_text
            new_preview = self.new_text[:30] + "..." if len(self.new_text) > 30 else self.new_text
            parts.append(f"text: '{old_preview}' -> '{new_preview}'")

        if self.visibility_changed:
            parts.append("visibility changed")

        if self.enabled_changed:
            parts.append("enabled state changed")

        return "; ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert diff to dictionary for serialization."""
        return {
            "has_changes": self.has_changes,
            "position_changed": self.position_changed,
            "size_changed": self.size_changed,
            "old_position": self.old_position,
            "new_position": self.new_position,
            "old_size": self.old_size,
            "new_size": self.new_size,
            "attributes_added": self.attributes_added,
            "attributes_removed": self.attributes_removed,
            "attributes_changed": {k: list(v) for k, v in self.attributes_changed.items()},
            "classes_added": self.classes_added,
            "classes_removed": self.classes_removed,
            "text_changed": self.text_changed,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "visibility_changed": self.visibility_changed,
            "enabled_changed": self.enabled_changed,
            "summary": self.summary(),
        }

    def get_change_severity(self) -> str:
        """Determine severity of changes.

        Returns:
            'none', 'minor', 'moderate', or 'major'
        """
        if not self.has_changes:
            return "none"

        # Major: visibility, enabled, or removed attributes
        if self.visibility_changed or self.enabled_changed or self.attributes_removed:
            return "major"

        # Moderate: position, size, or significant attribute changes
        if self.position_changed or self.size_changed or len(self.attributes_changed) > 2:
            return "moderate"

        # Minor: class changes, text changes, or small attribute changes
        return "minor"


class SnapshotManager:
    """Capture and compare element snapshots.

    Provides async methods for:
    - Capturing complete element state from Playwright page
    - Comparing two snapshots to detect changes
    - Saving/loading snapshots to/from disk
    """

    # Attributes to exclude from comparison (frequently changing)
    IGNORED_ATTRIBUTES = frozenset(
        {
            "data-reactid",
            "data-testid-timestamp",
            "__gwt_cell",
        }
    )

    async def capture(
        self,
        page: "Page",
        selector: str,
        include_screenshot: bool = True,
        max_text_length: int = 500,
        max_html_length: int = 1000,
    ) -> ElementSnapshot:
        """Capture complete snapshot of element.

        Args:
            page: Playwright page instance
            selector: CSS or XPath selector for element
            include_screenshot: Whether to capture element screenshot
            max_text_length: Maximum text content length to capture
            max_html_length: Maximum innerHTML length to capture

        Returns:
            ElementSnapshot with all captured data

        Raises:
            ValueError: If element not found
            Exception: On capture failure
        """
        try:
            el = await page.query_selector(selector)
            if el is None:
                raise ValueError(f"Element not found: {selector}")

            # Get comprehensive element info via JavaScript
            info = await el.evaluate("""(el) => {
                const computedStyle = window.getComputedStyle(el);
                return {
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    classes: Array.from(el.classList),
                    attributes: Object.fromEntries(
                        Array.from(el.attributes).map(a => [a.name, a.value])
                    ),
                    textContent: (el.textContent || "").trim(),
                    innerHTML: el.innerHTML || "",
                    isVisible: el.offsetParent !== null ||
                               computedStyle.display !== 'none' ||
                               computedStyle.visibility !== 'hidden',
                    isEnabled: !el.disabled && !el.hasAttribute('disabled'),
                };
            }""")

            # Truncate content
            text_content = info["textContent"][:max_text_length] if info["textContent"] else ""
            inner_html = info["innerHTML"][:max_html_length] if info["innerHTML"] else ""

            # Get bounding rect
            rect = await el.bounding_box()
            bounding: dict[str, int] = {}
            if rect:
                bounding = {
                    "x": int(rect["x"]),
                    "y": int(rect["y"]),
                    "width": int(rect["width"]),
                    "height": int(rect["height"]),
                }

            # Capture screenshot
            screenshot_b64: str | None = None
            if include_screenshot:
                try:
                    screenshot_bytes = await el.screenshot()
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                except Exception as screenshot_error:
                    logger.warning(f"Screenshot capture failed: {screenshot_error}")

            snapshot = ElementSnapshot(
                selector=selector,
                timestamp=time.time(),
                screenshot_b64=screenshot_b64,
                bounding_rect=bounding,
                tag=info["tag"],
                id=info["id"],
                classes=info["classes"],
                attributes=info["attributes"],
                text_content=text_content,
                inner_html=inner_html,
                is_visible=info["isVisible"],
                is_enabled=info["isEnabled"],
            )

            logger.debug(
                f"Captured snapshot for '{selector}': "
                f"tag={snapshot.tag}, classes={len(snapshot.classes)}, "
                f"attrs={len(snapshot.attributes)}"
            )

            return snapshot

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Snapshot capture failed for '{selector}': {e}")
            raise

    def compare(
        self,
        before: ElementSnapshot,
        after: ElementSnapshot,
        ignore_attributes: list[str] | None = None,
    ) -> ElementDiff:
        """Compare two snapshots and return differences.

        Args:
            before: Original snapshot
            after: New snapshot
            ignore_attributes: Additional attribute names to ignore

        Returns:
            ElementDiff with all detected changes
        """
        diff = ElementDiff()

        # Build ignore set
        ignored = set(self.IGNORED_ATTRIBUTES)
        if ignore_attributes:
            ignored.update(ignore_attributes)

        # Check position changes
        if before.bounding_rect and after.bounding_rect:
            old_x = before.bounding_rect.get("x", 0)
            old_y = before.bounding_rect.get("y", 0)
            new_x = after.bounding_rect.get("x", 0)
            new_y = after.bounding_rect.get("y", 0)

            if old_x != new_x or old_y != new_y:
                diff.position_changed = True
                diff.old_position = (old_x, old_y)
                diff.new_position = (new_x, new_y)
                diff.has_changes = True

            old_w = before.bounding_rect.get("width", 0)
            old_h = before.bounding_rect.get("height", 0)
            new_w = after.bounding_rect.get("width", 0)
            new_h = after.bounding_rect.get("height", 0)

            if old_w != new_w or old_h != new_h:
                diff.size_changed = True
                diff.old_size = (old_w, old_h)
                diff.new_size = (new_w, new_h)
                diff.has_changes = True

        # Check attribute changes (excluding ignored)
        before_attrs = {k: v for k, v in before.attributes.items() if k not in ignored}
        after_attrs = {k: v for k, v in after.attributes.items() if k not in ignored}

        before_keys = set(before_attrs.keys())
        after_keys = set(after_attrs.keys())

        # Added attributes
        for attr in after_keys - before_keys:
            diff.attributes_added[attr] = after_attrs[attr]
            diff.has_changes = True

        # Removed attributes
        for attr in before_keys - after_keys:
            diff.attributes_removed[attr] = before_attrs[attr]
            diff.has_changes = True

        # Changed attributes
        for attr in before_keys & after_keys:
            if before_attrs[attr] != after_attrs[attr]:
                diff.attributes_changed[attr] = (before_attrs[attr], after_attrs[attr])
                diff.has_changes = True

        # Check class changes
        before_classes = set(before.classes)
        after_classes = set(after.classes)

        added_classes = list(after_classes - before_classes)
        removed_classes = list(before_classes - after_classes)

        if added_classes:
            diff.classes_added = added_classes
            diff.has_changes = True

        if removed_classes:
            diff.classes_removed = removed_classes
            diff.has_changes = True

        # Check text content
        if before.text_content != after.text_content:
            diff.text_changed = True
            diff.old_text = before.text_content
            diff.new_text = after.text_content
            diff.has_changes = True

        # Check state changes
        if before.is_visible != after.is_visible:
            diff.visibility_changed = True
            diff.has_changes = True

        if before.is_enabled != after.is_enabled:
            diff.enabled_changed = True
            diff.has_changes = True

        return diff

    def save(self, snapshot: ElementSnapshot, path: str) -> None:
        """Save snapshot to JSON file.

        Args:
            snapshot: Snapshot to save
            path: File path for output
        """
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        data = snapshot.to_dict()
        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.debug(f"Saved snapshot to {path}")

    def load(self, path: str) -> ElementSnapshot:
        """Load snapshot from JSON file.

        Args:
            path: File path to load from

        Returns:
            ElementSnapshot instance

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is invalid JSON
        """
        file_path = Path(path)
        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)

        snapshot = ElementSnapshot.from_dict(data)
        logger.debug(f"Loaded snapshot from {path}")

        return snapshot

    def save_comparison(
        self,
        before: ElementSnapshot,
        after: ElementSnapshot,
        diff: ElementDiff,
        path: str,
    ) -> None:
        """Save full comparison (both snapshots + diff) to JSON file.

        Args:
            before: Original snapshot
            after: New snapshot
            diff: Computed differences
            path: Output file path
        """
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        comparison_data = {
            "before": before.to_dict(),
            "after": after.to_dict(),
            "diff": diff.to_dict(),
            "compared_at": time.time(),
        }

        file_path.write_text(
            json.dumps(comparison_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.debug(f"Saved comparison to {path}")
