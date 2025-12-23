"""
Selector Healing Utility

Provides automatic selector healing capabilities to make web automation more robust.
When a selector fails to find an element, the healer attempts to find alternative
selectors based on element attributes, position, and similarity.
"""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


@dataclass
class ElementFingerprint:
    """
    Fingerprint of an element for identification and healing.

    Stores multiple attributes that can be used to re-identify an element
    when the primary selector fails.
    """

    tag_name: str = ""
    """HTML tag name (e.g., 'button', 'input', 'div')."""

    text_content: str = ""
    """Visible text content of the element."""

    id_attr: str = ""
    """Element's id attribute."""

    class_list: list[str] = field(default_factory=list)
    """List of CSS classes."""

    name_attr: str = ""
    """Element's name attribute."""

    type_attr: str = ""
    """Element's type attribute (for inputs)."""

    role_attr: str = ""
    """Element's ARIA role."""

    aria_label: str = ""
    """Element's aria-label attribute."""

    placeholder: str = ""
    """Element's placeholder attribute."""

    href: str = ""
    """Element's href attribute (for links)."""

    data_testid: str = ""
    """Element's data-testid attribute."""

    data_id: str = ""
    """Element's data-id attribute."""

    parent_tag: str = ""
    """Parent element's tag name."""

    sibling_index: int = 0
    """Index among siblings."""

    position: tuple[int, int] = (0, 0)
    """Approximate position (x, y)."""

    @property
    def fingerprint_hash(self) -> str:
        """Generate a hash of the fingerprint for caching."""
        data = {
            "tag": self.tag_name,
            "text": self.text_content[:100],  # Limit text length
            "id": self.id_attr,
            "classes": sorted(self.class_list),
            "name": self.name_attr,
            "type": self.type_attr,
            "role": self.role_attr,
            "aria_label": self.aria_label,
            "data_testid": self.data_testid,
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tag_name": self.tag_name,
            "text_content": self.text_content,
            "id_attr": self.id_attr,
            "class_list": self.class_list,
            "name_attr": self.name_attr,
            "type_attr": self.type_attr,
            "role_attr": self.role_attr,
            "aria_label": self.aria_label,
            "placeholder": self.placeholder,
            "href": self.href,
            "data_testid": self.data_testid,
            "data_id": self.data_id,
            "parent_tag": self.parent_tag,
            "sibling_index": self.sibling_index,
            "position": list(self.position),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ElementFingerprint":
        """Create from dictionary."""
        return cls(
            tag_name=data.get("tag_name", ""),
            text_content=data.get("text_content", ""),
            id_attr=data.get("id_attr", ""),
            class_list=data.get("class_list", []),
            name_attr=data.get("name_attr", ""),
            type_attr=data.get("type_attr", ""),
            role_attr=data.get("role_attr", ""),
            aria_label=data.get("aria_label", ""),
            placeholder=data.get("placeholder", ""),
            href=data.get("href", ""),
            data_testid=data.get("data_testid", ""),
            data_id=data.get("data_id", ""),
            parent_tag=data.get("parent_tag", ""),
            sibling_index=data.get("sibling_index", 0),
            position=tuple(data.get("position", [0, 0])),
        )


@dataclass
class HealingResult:
    """Result of a selector healing attempt."""

    success: bool
    """Whether healing was successful."""

    original_selector: str
    """The original selector that failed."""

    healed_selector: str
    """The healed selector (if successful)."""

    confidence: float
    """Confidence score (0.0 to 1.0)."""

    strategy_used: str
    """Name of the healing strategy that worked."""

    alternatives: list[tuple[str, float]] = field(default_factory=list)
    """List of alternative selectors with confidence scores."""


class SelectorHealer:
    """
    Selector healing engine for web automation.

    When a selector fails to find an element, the healer:
    1. Generates alternative selectors based on element fingerprints
    2. Scores alternatives by similarity to the original target
    3. Returns the best match or a ranked list of alternatives

    Example:
        healer = SelectorHealer()

        # Record successful element location
        fingerprint = await healer.capture_fingerprint(page, "#submit-btn")
        healer.store_fingerprint("#submit-btn", fingerprint)

        # Later, if selector fails:
        result = await healer.heal(page, "#submit-btn")
        if result.success:
            new_element = await page.query_selector(result.healed_selector)
    """

    def __init__(self, storage_path: Path | None = None, min_confidence: float = 0.6):
        """
        Initialize selector healer.

        Args:
            storage_path: Path to persist fingerprint database
            min_confidence: Minimum confidence threshold for healing
        """
        self.storage_path = storage_path
        self.min_confidence = min_confidence
        self._fingerprints: dict[str, ElementFingerprint] = {}
        self._healing_history: list[HealingResult] = []

        if storage_path and storage_path.exists():
            self._load_fingerprints()

    def store_fingerprint(self, selector: str, fingerprint: ElementFingerprint) -> None:
        """
        Store a fingerprint for a selector.

        Args:
            selector: The selector string
            fingerprint: Element fingerprint to store
        """
        self._fingerprints[selector] = fingerprint
        logger.debug(f"Stored fingerprint for selector: {selector}")

        if self.storage_path:
            self._save_fingerprints()

    def get_fingerprint(self, selector: str) -> ElementFingerprint | None:
        """Get stored fingerprint for a selector."""
        return self._fingerprints.get(selector)

    async def capture_fingerprint(
        self,
        page: Any,  # Playwright Page
        selector: str,
    ) -> ElementFingerprint | None:
        """
        Capture fingerprint of an element on a page.

        Args:
            page: Playwright page object
            selector: Selector for the element (CSS or XPath)

        Returns:
            ElementFingerprint or None if element not found
        """
        try:
            fingerprint_data = await page.evaluate(
                """
                (selector) => {
                    // Detect if selector is XPath (starts with / or //)
                    let el;
                    if (selector.startsWith('/') || selector.startsWith('(')) {
                        // XPath selector - use document.evaluate
                        const result = document.evaluate(
                            selector,
                            document,
                            null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE,
                            null
                        );
                        el = result.singleNodeValue;
                    } else {
                        // CSS selector
                        el = document.querySelector(selector);
                    }

                    if (!el) return null;

                    const rect = el.getBoundingClientRect();
                    const parent = el.parentElement;
                    let siblingIndex = 0;
                    if (parent) {
                        siblingIndex = Array.from(parent.children).indexOf(el);
                    }

                    return {
                        tag_name: el.tagName.toLowerCase(),
                        text_content: el.textContent?.trim().substring(0, 200) || '',
                        id_attr: el.id || '',
                        class_list: Array.from(el.classList),
                        name_attr: el.getAttribute('name') || '',
                        type_attr: el.getAttribute('type') || '',
                        role_attr: el.getAttribute('role') || '',
                        aria_label: el.getAttribute('aria-label') || '',
                        placeholder: el.getAttribute('placeholder') || '',
                        href: el.getAttribute('href') || '',
                        data_testid: el.getAttribute('data-testid') || '',
                        data_id: el.getAttribute('data-id') || '',
                        parent_tag: parent?.tagName.toLowerCase() || '',
                        sibling_index: siblingIndex,
                        position: [Math.round(rect.x), Math.round(rect.y)]
                    };
                }
            """,
                selector,
            )

            if fingerprint_data:
                return ElementFingerprint.from_dict(fingerprint_data)
            return None

        except Exception as e:
            logger.warning(f"Failed to capture fingerprint: {e}")
            return None

    async def heal(
        self,
        page: Any,  # Playwright Page
        selector: str,
        fingerprint: ElementFingerprint | None = None,
    ) -> HealingResult:
        """
        Attempt to heal a broken selector.

        Args:
            page: Playwright page object
            selector: Original selector that failed
            fingerprint: Optional fingerprint (uses stored if not provided)

        Returns:
            HealingResult with healed selector or failure details
        """
        fp = fingerprint or self._fingerprints.get(selector)

        if not fp:
            return HealingResult(
                success=False,
                original_selector=selector,
                healed_selector="",
                confidence=0.0,
                strategy_used="none",
            )

        logger.info(f"Attempting to heal selector: {selector}")

        # Generate alternative selectors
        alternatives = self._generate_alternatives(fp)

        # Test each alternative
        scored_alternatives: list[tuple[str, float]] = []

        for alt_selector, base_score in alternatives:
            try:
                element = await page.query_selector(alt_selector)
                if element:
                    # Capture fingerprint of found element and compare
                    found_fp = await self.capture_fingerprint(page, alt_selector)
                    if found_fp:
                        similarity = self._calculate_similarity(fp, found_fp)
                        final_score = base_score * similarity
                        scored_alternatives.append((alt_selector, final_score))
                        logger.debug(f"Alternative '{alt_selector}' score: {final_score:.2f}")
            except Exception as e:
                logger.debug(f"Alternative '{alt_selector}' failed: {e}")

        # Sort by score and return best match
        scored_alternatives.sort(key=lambda x: x[1], reverse=True)

        if scored_alternatives and scored_alternatives[0][1] >= self.min_confidence:
            best_selector, best_score = scored_alternatives[0]
            result = HealingResult(
                success=True,
                original_selector=selector,
                healed_selector=best_selector,
                confidence=best_score,
                strategy_used=self._get_strategy_name(best_selector, fp),
                alternatives=scored_alternatives[:5],
            )
            logger.info(
                f"Selector healed: '{selector}' -> '{best_selector}' "
                f"(confidence: {best_score:.2f})"
            )
        else:
            result = HealingResult(
                success=False,
                original_selector=selector,
                healed_selector="",
                confidence=0.0,
                strategy_used="none",
                alternatives=scored_alternatives[:5],
            )
            logger.warning(f"Failed to heal selector: {selector}")

        self._healing_history.append(result)
        return result

    def _generate_alternatives(self, fp: ElementFingerprint) -> list[tuple[str, float]]:
        """
        Generate alternative selectors from fingerprint.

        Returns list of (selector, base_confidence) tuples.
        """
        alternatives = []

        # Strategy 1: data-testid (highest confidence)
        if fp.data_testid:
            alternatives.append((f'[data-testid="{fp.data_testid}"]', 0.95))

        # Strategy 2: id attribute
        if fp.id_attr:
            alternatives.append((f"#{fp.id_attr}", 0.9))

        # Strategy 3: aria-label
        if fp.aria_label:
            alternatives.append((f'[aria-label="{fp.aria_label}"]', 0.85))

        # Strategy 4: name attribute
        if fp.name_attr:
            alternatives.append((f'[name="{fp.name_attr}"]', 0.8))

        # Strategy 5: text content (for buttons, links)
        if fp.text_content and len(fp.text_content) < 50:
            text = fp.text_content.strip()
            if fp.tag_name == "button":
                alternatives.append((f'button:has-text("{text}")', 0.75))
            elif fp.tag_name == "a":
                alternatives.append((f'a:has-text("{text}")', 0.75))
            else:
                alternatives.append((f'text="{text}"', 0.7))

        # Strategy 6: placeholder
        if fp.placeholder:
            alternatives.append((f'[placeholder="{fp.placeholder}"]', 0.75))

        # Strategy 7: role + type combination
        if fp.role_attr:
            if fp.type_attr:
                alternatives.append(
                    (
                        f'{fp.tag_name}[role="{fp.role_attr}"][type="{fp.type_attr}"]',
                        0.7,
                    )
                )
            else:
                alternatives.append((f'[role="{fp.role_attr}"]', 0.65))

        # Strategy 8: tag + class combination
        if fp.class_list:
            # Use most specific class
            specific_classes = [c for c in fp.class_list if len(c) > 3]
            if specific_classes:
                class_selector = ".".join(specific_classes[:3])
                alternatives.append((f"{fp.tag_name}.{class_selector}", 0.6))

        # Strategy 9: tag + type for inputs
        if fp.tag_name == "input" and fp.type_attr:
            alternatives.append((f'input[type="{fp.type_attr}"]', 0.5))

        return alternatives

    def _calculate_similarity(
        self, original: ElementFingerprint, found: ElementFingerprint
    ) -> float:
        """
        Calculate similarity between two fingerprints.

        Returns a score between 0.0 and 1.0.
        """
        score = 0.0
        weights = {
            "tag_name": 0.15,
            "id_attr": 0.15,
            "text_content": 0.15,
            "class_list": 0.1,
            "name_attr": 0.1,
            "role_attr": 0.1,
            "aria_label": 0.1,
            "data_testid": 0.15,
        }

        # Tag name match
        if original.tag_name == found.tag_name:
            score += weights["tag_name"]

        # ID match
        if original.id_attr and original.id_attr == found.id_attr:
            score += weights["id_attr"]

        # Text content similarity
        if original.text_content and found.text_content:
            text_sim = self._text_similarity(original.text_content, found.text_content)
            score += weights["text_content"] * text_sim

        # Class list overlap
        if original.class_list and found.class_list:
            common = set(original.class_list) & set(found.class_list)
            total = set(original.class_list) | set(found.class_list)
            if total:
                score += weights["class_list"] * (len(common) / len(total))

        # Name attribute
        if original.name_attr and original.name_attr == found.name_attr:
            score += weights["name_attr"]

        # Role attribute
        if original.role_attr and original.role_attr == found.role_attr:
            score += weights["role_attr"]

        # Aria label
        if original.aria_label and original.aria_label == found.aria_label:
            score += weights["aria_label"]

        # data-testid
        if original.data_testid and original.data_testid == found.data_testid:
            score += weights["data_testid"]

        return min(score, 1.0)

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        if not text1 or not text2:
            return 0.0

        # Normalize
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        if t1 == t2:
            return 1.0

        # Check if one contains the other
        if t1 in t2 or t2 in t1:
            return 0.8

        # Word overlap
        words1 = set(t1.split())
        words2 = set(t2.split())
        if words1 and words2:
            common = words1 & words2
            total = words1 | words2
            return len(common) / len(total)

        return 0.0

    def _get_strategy_name(self, selector: str, fp: ElementFingerprint) -> str:
        """Get the name of the strategy used for a selector."""
        if "data-testid" in selector:
            return "data-testid"
        if selector.startswith("#"):
            return "id"
        if "aria-label" in selector:
            return "aria-label"
        if "name=" in selector:
            return "name"
        if ":has-text" in selector or "text=" in selector:
            return "text-content"
        if "placeholder" in selector:
            return "placeholder"
        if "role=" in selector:
            return "role"
        if "." in selector:
            return "class"
        return "unknown"

    def _load_fingerprints(self) -> None:
        """Load fingerprints from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
                for selector, fp_data in data.items():
                    self._fingerprints[selector] = ElementFingerprint.from_dict(fp_data)
            logger.info(f"Loaded {len(self._fingerprints)} fingerprints")
        except Exception as e:
            logger.warning(f"Failed to load fingerprints: {e}")

    def _save_fingerprints(self) -> None:
        """Save fingerprints to storage."""
        if not self.storage_path:
            return

        try:
            data = {selector: fp.to_dict() for selector, fp in self._fingerprints.items()}
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save fingerprints: {e}")

    @property
    def healing_history(self) -> list[HealingResult]:
        """Get healing attempt history."""
        return self._healing_history.copy()

    def get_healing_stats(self) -> dict[str, Any]:
        """Get statistics about healing attempts."""
        total = len(self._healing_history)
        successful = sum(1 for r in self._healing_history if r.success)

        return {
            "total_attempts": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "strategies_used": self._count_strategies(),
        }

    def _count_strategies(self) -> dict[str, int]:
        """Count healing strategies used."""
        counts: dict[str, int] = {}
        for result in self._healing_history:
            if result.success:
                strategy = result.strategy_used
                counts[strategy] = counts.get(strategy, 0) + 1
        return counts


# Global healer instance
_global_healer: SelectorHealer | None = None


def get_selector_healer(storage_path: Path | None = None) -> SelectorHealer:
    """Get or create global selector healer instance."""
    global _global_healer
    if _global_healer is None:
        _global_healer = SelectorHealer(storage_path)
    return _global_healer


__all__ = [
    "ElementFingerprint",
    "HealingResult",
    "SelectorHealer",
    "get_selector_healer",
]
