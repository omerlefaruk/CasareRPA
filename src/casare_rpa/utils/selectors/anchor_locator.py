"""
Anchor-Based Element Locator.

Implements UiPath-style anchor-based element location strategy.
Uses stable reference elements (labels, headings) to reliably find target elements
even when the UI structure changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import ElementHandle, Page


# Tags that typically make stable anchors
STABLE_ANCHOR_TAGS = frozenset(
    [
        "label",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "legend",
        "th",
        "caption",
        "figcaption",
    ]
)

# Maximum distance in pixels for anchor consideration
MAX_ANCHOR_DISTANCE = 300

# Minimum stability score to consider anchor
MIN_ANCHOR_STABILITY = 0.5


@dataclass
class AnchorCandidate:
    """Candidate anchor element with metadata."""

    selector: str
    tag_name: str
    text_content: str
    distance: float
    stability_score: float
    position: str
    rect: dict[str, float]
    attributes: dict[str, str]


class AnchorLocator:
    """
    Locate elements using anchor-based strategy.

    This class provides methods to:
    1. Auto-detect the best anchor for a target element
    2. Find target elements relative to anchors
    3. Calculate anchor stability scores

    Example:
        locator = AnchorLocator()

        # Auto-detect anchor
        anchor_data = await locator.auto_detect_anchor(page, "#submit-btn")

        # Find element using anchor
        element = await locator.find_element_with_anchor(
            page,
            target_selector="#submit-btn",
            anchor_selector="label:has-text('Submit')",
            position="left",
        )
    """

    def __init__(
        self,
        max_distance: float = MAX_ANCHOR_DISTANCE,
        min_stability: float = MIN_ANCHOR_STABILITY,
    ) -> None:
        """
        Initialize the anchor locator.

        Args:
            max_distance: Maximum distance in pixels for anchor consideration.
            min_stability: Minimum stability score (0.0-1.0) to consider anchor.
        """
        self._max_distance = max_distance
        self._min_stability = min_stability

    async def auto_detect_anchor(
        self,
        page: Page,
        target_selector: str,
    ) -> dict[str, Any] | None:
        """
        Auto-detect the best anchor for a target element.

        Looks for stable elements (labels, headings) near the target
        and returns the best candidate based on stability and distance.

        Args:
            page: Playwright Page object.
            target_selector: CSS/XPath selector for the target element.

        Returns:
            Dictionary with anchor data or None if no suitable anchor found.

        Raises:
            Exception: If page evaluation fails.
        """
        try:
            candidates = await self._find_anchor_candidates(page, target_selector)

            if not candidates:
                logger.debug(f"No anchor candidates found for: {target_selector}")
                return None

            # Sort by stability (desc) then distance (asc)
            candidates.sort(key=lambda c: (-c.stability_score, c.distance))

            best = candidates[0]

            if best.stability_score < self._min_stability:
                logger.debug(
                    f"Best anchor stability too low: {best.stability_score:.2f} < {self._min_stability}"
                )
                return None

            logger.info(
                f"Auto-detected anchor: {best.tag_name} '{best.text_content[:30]}' "
                f"(stability={best.stability_score:.2f}, dist={best.distance:.0f}px)"
            )

            return {
                "selector": best.selector,
                "tag_name": best.tag_name,
                "text_content": best.text_content,
                "position": best.position,
                "stability_score": best.stability_score,
                "attributes": best.attributes,
                "rect": best.rect,
            }

        except Exception as e:
            logger.error(f"Failed to auto-detect anchor: {e}")
            raise

    async def _find_anchor_candidates(
        self,
        page: Page,
        target_selector: str,
    ) -> list[AnchorCandidate]:
        """
        Find candidate anchor elements near the target.

        Args:
            page: Playwright Page object.
            target_selector: Selector for target element.

        Returns:
            List of AnchorCandidate objects.
        """
        anchor_data = await page.evaluate(
            """
            ({targetSelector, stableTagsList, maxDistance}) => {
                // Support both CSS and XPath selectors
                let target;
                if (targetSelector.startsWith('/') || targetSelector.startsWith('(')) {
                    const result = document.evaluate(
                        targetSelector, document, null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE, null
                    );
                    target = result.singleNodeValue;
                } else {
                    target = document.querySelector(targetSelector);
                }

                if (!target) return [];

                const targetRect = target.getBoundingClientRect();
                const targetCenterX = targetRect.x + targetRect.width / 2;
                const targetCenterY = targetRect.y + targetRect.height / 2;

                const candidates = [];

                // Find stable elements
                const stableTags = stableTagsList.join(', ');
                document.querySelectorAll(stableTags).forEach(el => {
                    // Skip invisible elements
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return;

                    // Skip if too far
                    const centerX = rect.x + rect.width / 2;
                    const centerY = rect.y + rect.height / 2;
                    const dx = centerX - targetCenterX;
                    const dy = centerY - targetCenterY;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance > maxDistance) return;

                    // Determine position relationship
                    let position;
                    if (Math.abs(dx) > Math.abs(dy)) {
                        position = dx < 0 ? 'left' : 'right';
                    } else {
                        position = dy < 0 ? 'above' : 'below';
                    }

                    // Check if target is inside anchor
                    if (
                        rect.x <= targetRect.x &&
                        rect.y <= targetRect.y &&
                        rect.x + rect.width >= targetRect.x + targetRect.width &&
                        rect.y + rect.height >= targetRect.y + targetRect.height
                    ) {
                        position = 'inside';
                    }

                    candidates.push({
                        tag: el.tagName.toLowerCase(),
                        text: el.textContent?.trim().substring(0, 100) || '',
                        distance: distance,
                        position: position,
                        rect: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                        },
                        id: el.id || '',
                        for_attr: el.getAttribute('for') || '',
                        data_testid: el.getAttribute('data-testid') || '',
                        aria_label: el.getAttribute('aria-label') || '',
                        class_name: el.className || '',
                    });
                });

                // Also check elements with heading role
                document.querySelectorAll('[role="heading"]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return;

                    const centerX = rect.x + rect.width / 2;
                    const centerY = rect.y + rect.height / 2;
                    const dx = centerX - targetCenterX;
                    const dy = centerY - targetCenterY;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance > maxDistance) return;

                    let position;
                    if (Math.abs(dx) > Math.abs(dy)) {
                        position = dx < 0 ? 'left' : 'right';
                    } else {
                        position = dy < 0 ? 'above' : 'below';
                    }

                    candidates.push({
                        tag: el.tagName.toLowerCase(),
                        text: el.textContent?.trim().substring(0, 100) || '',
                        distance: distance,
                        position: position,
                        rect: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                        },
                        id: el.id || '',
                        for_attr: '',
                        data_testid: el.getAttribute('data-testid') || '',
                        aria_label: el.getAttribute('aria-label') || '',
                        class_name: el.className || '',
                        role: 'heading',
                    });
                });

                return candidates;
            }
            """,
            {
                "targetSelector": target_selector,
                "stableTagsList": list(STABLE_ANCHOR_TAGS),
                "maxDistance": self._max_distance,
            },
        )

        candidates = []
        for data in anchor_data:
            selector = self._build_selector(data)
            if not selector:
                continue

            stability = self._calculate_stability(data)
            attributes = {
                k: v
                for k, v in {
                    "id": data.get("id"),
                    "for": data.get("for_attr"),
                    "data-testid": data.get("data_testid"),
                    "aria-label": data.get("aria_label"),
                    "class": data.get("class_name"),
                }.items()
                if v
            }

            candidates.append(
                AnchorCandidate(
                    selector=selector,
                    tag_name=data["tag"],
                    text_content=data.get("text", ""),
                    distance=data["distance"],
                    stability_score=stability,
                    position=data["position"],
                    rect=data["rect"],
                    attributes=attributes,
                )
            )

        return candidates

    def _build_selector(self, data: dict[str, Any]) -> str | None:
        """
        Build a CSS selector for an anchor element.

        Args:
            data: Element data dictionary.

        Returns:
            CSS selector string or None if cannot build reliable selector.
        """
        # Priority: id > data-testid > for attr > aria-label > text
        if data.get("id"):
            return f"#{data['id']}"

        if data.get("data_testid"):
            return f'[data-testid="{data["data_testid"]}"]'

        tag = data.get("tag", "")

        if tag == "label" and data.get("for_attr"):
            return f'label[for="{data["for_attr"]}"]'

        if data.get("aria_label"):
            return f'{tag}[aria-label="{data["aria_label"]}"]'

        text = data.get("text", "").strip()
        if text and len(text) < 50:
            # Use text-based selector
            escaped_text = text.replace('"', '\\"')
            return f'{tag}:has-text("{escaped_text}")'

        return None

    def _calculate_stability(self, data: dict[str, Any]) -> float:
        """
        Calculate stability score for a potential anchor element.

        Args:
            data: Element data dictionary.

        Returns:
            Stability score between 0.0 and 1.0.
        """
        score = 0.0
        tag = data.get("tag", "")

        # Tag-based stability
        if tag in ("label", "legend"):
            score += 0.30
        elif tag in ("h1", "h2", "h3"):
            score += 0.25
        elif tag in ("h4", "h5", "h6", "th", "caption"):
            score += 0.20
        elif tag == "figcaption":
            score += 0.15
        else:
            score += 0.05

        # Attribute-based stability
        if data.get("id"):
            score += 0.20
        if data.get("data_testid"):
            score += 0.25
        if data.get("aria_label"):
            score += 0.15
        if data.get("for_attr"):
            score += 0.20  # label[for] is very reliable

        # Text content stability
        text = data.get("text", "")
        if text:
            text_len = len(text.strip())
            if 2 < text_len < 50:
                score += 0.15
            elif text_len >= 50:
                score += 0.05

        return min(1.0, score)

    async def find_element_with_anchor(
        self,
        page: Page,
        target_selector: str,
        anchor_selector: str,
        position: str = "left",
        fallback_to_target: bool = True,
    ) -> ElementHandle | None:
        """
        Find element using anchor as reference.

        Strategy:
        1. Find anchor element first (it should be stable)
        2. Based on position, search for target near anchor
        3. If found, validate target matches expected attributes
        4. Fallback to direct target selector if enabled

        Args:
            page: Playwright Page object.
            target_selector: CSS/XPath selector for target element.
            anchor_selector: CSS selector for anchor element.
            position: Position of target relative to anchor.
            fallback_to_target: If True, try target_selector directly on failure.

        Returns:
            ElementHandle for target element or None.
        """
        try:
            # First try anchor-based location
            anchor = await page.query_selector(anchor_selector)

            if anchor:
                # Anchor found - try to find target relative to it
                target = await self._find_target_near_anchor(
                    page, anchor, target_selector, position
                )
                if target:
                    logger.debug(f"Found target via anchor: {anchor_selector}")
                    return target

                logger.debug(f"Target not found near anchor, anchor={anchor_selector}")

            # Fallback to direct target selector
            if fallback_to_target:
                target = await page.query_selector(target_selector)
                if target:
                    logger.debug(f"Found target via direct selector: {target_selector}")
                    return target

            return None

        except Exception as e:
            logger.error(f"Error in anchor-based element location: {e}")
            return None

    async def _find_target_near_anchor(
        self,
        page: Page,
        anchor: ElementHandle,
        target_selector: str,
        position: str,
    ) -> ElementHandle | None:
        """
        Find target element near anchor based on position.

        Args:
            page: Playwright Page object.
            anchor: ElementHandle for anchor element.
            target_selector: Selector for target element.
            position: Expected position (left/right/above/below/inside).

        Returns:
            ElementHandle for target or None.
        """
        try:
            # Get anchor bounding box
            anchor_box = await anchor.bounding_box()
            if not anchor_box:
                return None

            # Find all candidates matching target selector
            candidates = await page.query_selector_all(target_selector)
            if not candidates:
                return None

            # Find the one closest to expected position
            best_match = None
            best_score = float("inf")

            for candidate in candidates:
                box = await candidate.bounding_box()
                if not box:
                    continue

                # Calculate position score
                score = self._calculate_position_score(anchor_box, box, position)

                if score < best_score:
                    best_score = score
                    best_match = candidate

            # Only return if score is reasonable
            if best_match and best_score < self._max_distance:
                return best_match

            return None

        except Exception as e:
            logger.debug(f"Error finding target near anchor: {e}")
            return None

    def _calculate_position_score(
        self,
        anchor_box: dict[str, float],
        target_box: dict[str, float],
        expected_position: str,
    ) -> float:
        """
        Calculate how well target position matches expected position.

        Lower score = better match.

        Args:
            anchor_box: Anchor bounding box.
            target_box: Target bounding box.
            expected_position: Expected position relationship.

        Returns:
            Position score (lower is better).
        """
        anchor_cx = anchor_box["x"] + anchor_box["width"] / 2
        anchor_cy = anchor_box["y"] + anchor_box["height"] / 2
        target_cx = target_box["x"] + target_box["width"] / 2
        target_cy = target_box["y"] + target_box["height"] / 2

        dx = target_cx - anchor_cx
        dy = target_cy - anchor_cy
        distance = (dx**2 + dy**2) ** 0.5

        # Penalize if position doesn't match expectation
        penalty = 0

        if expected_position == "left" and dx > 0:
            penalty = abs(dx) * 2
        elif expected_position == "right" and dx < 0:
            penalty = abs(dx) * 2
        elif expected_position == "above" and dy > 0:
            penalty = abs(dy) * 2
        elif expected_position == "below" and dy < 0:
            penalty = abs(dy) * 2
        elif expected_position == "inside":
            # Check containment
            if not (
                anchor_box["x"] <= target_box["x"]
                and anchor_box["y"] <= target_box["y"]
                and anchor_box["x"] + anchor_box["width"] >= target_box["x"] + target_box["width"]
                and anchor_box["y"] + anchor_box["height"] >= target_box["y"] + target_box["height"]
            ):
                penalty = distance * 2

        return distance + penalty

    async def validate_anchor(
        self,
        page: Page,
        anchor_selector: str,
    ) -> dict[str, Any]:
        """
        Validate that an anchor selector still matches an element.

        Args:
            page: Playwright Page object.
            anchor_selector: Selector for anchor element.

        Returns:
            Dictionary with validation results:
            - valid: bool
            - count: int (number of matches)
            - text: str (anchor text if found)
        """
        try:
            elements = await page.query_selector_all(anchor_selector)
            count = len(elements)

            if count == 0:
                return {"valid": False, "count": 0, "text": ""}

            # Get text of first match
            text = ""
            if elements:
                text = await elements[0].text_content() or ""
                text = text.strip()[:50]

            return {
                "valid": count == 1,  # Ideally should be unique
                "count": count,
                "text": text,
            }

        except Exception as e:
            logger.error(f"Error validating anchor: {e}")
            return {"valid": False, "count": 0, "text": "", "error": str(e)}


__all__ = ["AnchorLocator", "AnchorCandidate", "STABLE_ANCHOR_TAGS"]
