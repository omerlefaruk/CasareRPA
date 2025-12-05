"""
Anchor-Based Selector Healer (Tier 2).

Implements self-healing selectors using spatial relationships with stable anchor elements.
When a selector fails, finds the target relative to nearby stable elements (labels, headings, etc.).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from loguru import logger

from casare_rpa.infrastructure.browser.healing.models import (
    AnchorElement,
    AnchorHealingResult,
    BoundingRect,
    SpatialContext,
    SpatialRelation,
)

if TYPE_CHECKING:
    from playwright.async_api import Page


# Threshold in pixels for "near" relationship
NEAR_THRESHOLD_PX = 150

# Maximum anchors to consider per healing attempt
MAX_ANCHORS = 5

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

# ARIA landmarks for structural anchoring
ARIA_LANDMARKS = frozenset(
    [
        "banner",
        "navigation",
        "main",
        "complementary",
        "contentinfo",
        "search",
        "form",
        "region",
    ]
)


class AnchorHealer:
    """
    Tier 2 selector healer using spatial anchor relationships.

    Workflow:
    1. When recording a selector, capture nearby stable anchors and spatial context
    2. When selector fails, use anchors to locate the target element
    3. Generate relative selectors based on spatial relationships

    Example:
        healer = AnchorHealer()

        # During recording
        context = await healer.capture_spatial_context(page, "#submit-btn")
        healer.store_context("#submit-btn", context)

        # During playback (when selector fails)
        result = await healer.heal(page, "#submit-btn")
        if result.success:
            element = await page.query_selector(result.healed_selector)
    """

    def __init__(
        self,
        near_threshold: float = NEAR_THRESHOLD_PX,
        min_confidence: float = 0.6,
    ) -> None:
        """
        Initialize the anchor healer.

        Args:
            near_threshold: Pixel distance threshold for "near" relationship.
            min_confidence: Minimum confidence for accepting a healed selector.
        """
        self._near_threshold = near_threshold
        self._min_confidence = min_confidence
        self._contexts: Dict[str, SpatialContext] = {}

    def store_context(self, selector: str, context: SpatialContext) -> None:
        """
        Store spatial context for a selector.

        Args:
            selector: The original selector string.
            context: Captured spatial context.
        """
        self._contexts[selector] = context
        logger.debug(f"Stored spatial context for: {selector}")

    def get_context(self, selector: str) -> Optional[SpatialContext]:
        """Get stored spatial context for a selector."""
        return self._contexts.get(selector)

    async def capture_spatial_context(
        self,
        page: Page,
        selector: str,
    ) -> Optional[SpatialContext]:
        """
        Capture the spatial context of an element for future healing.

        Args:
            page: Playwright Page object.
            selector: Selector for the target element.

        Returns:
            SpatialContext or None if element not found.

        Raises:
            Exception: If page evaluation fails.
        """
        try:
            context_data = await page.evaluate(
                """
                (selector) => {
                    // Support both CSS and XPath selectors
                    let target;
                    if (selector.startsWith('/') || selector.startsWith('(')) {
                        // XPath selector
                        const result = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                        target = result.singleNodeValue;
                    } else {
                        // CSS selector
                        target = document.querySelector(selector);
                    }
                    if (!target) return null;

                    const targetRect = target.getBoundingClientRect();

                    // Find stable anchor candidates
                    const anchorTags = ['label', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                                       'legend', 'th', 'caption', 'figcaption'];
                    const anchors = [];

                    // Collect potential anchors
                    anchorTags.forEach(tag => {
                        document.querySelectorAll(tag).forEach(el => {
                            const rect = el.getBoundingClientRect();
                            if (rect.width === 0 || rect.height === 0) return;

                            const dx = Math.abs(rect.x + rect.width/2 - targetRect.x - targetRect.width/2);
                            const dy = Math.abs(rect.y + rect.height/2 - targetRect.y - targetRect.height/2);
                            const distance = Math.sqrt(dx*dx + dy*dy);

                            if (distance < 300) {
                                anchors.push({
                                    tag: el.tagName.toLowerCase(),
                                    text: el.textContent?.trim().substring(0, 100) || '',
                                    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                                    id: el.id || '',
                                    forAttr: el.getAttribute('for') || '',
                                    ariaLabel: el.getAttribute('aria-label') || '',
                                    dataTestId: el.getAttribute('data-testid') || '',
                                    distance: distance
                                });
                            }
                        });
                    });

                    // Also check elements with role="heading"
                    document.querySelectorAll('[role="heading"]').forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) return;

                        const dx = Math.abs(rect.x + rect.width/2 - targetRect.x - targetRect.width/2);
                        const dy = Math.abs(rect.y + rect.height/2 - targetRect.y - targetRect.height/2);
                        const distance = Math.sqrt(dx*dx + dy*dy);

                        if (distance < 300) {
                            anchors.push({
                                tag: el.tagName.toLowerCase(),
                                text: el.textContent?.trim().substring(0, 100) || '',
                                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                                id: el.id || '',
                                role: 'heading',
                                ariaLabel: el.getAttribute('aria-label') || '',
                                dataTestId: el.getAttribute('data-testid') || '',
                                distance: distance
                            });
                        }
                    });

                    // Sort by distance and take closest
                    anchors.sort((a, b) => a.distance - b.distance);

                    // Find containing landmark/section
                    let container = target.closest('form, section, article, aside, main, nav, [role]');
                    let containerSelector = null;
                    if (container) {
                        if (container.id) {
                            containerSelector = '#' + container.id;
                        } else if (container.getAttribute('data-testid')) {
                            containerSelector = `[data-testid="${container.getAttribute('data-testid')}"]`;
                        } else if (container.getAttribute('aria-label')) {
                            containerSelector = `${container.tagName.toLowerCase()}[aria-label="${container.getAttribute('aria-label')}"]`;
                        }
                    }

                    // Determine visual quadrant
                    const vpWidth = window.innerWidth;
                    const vpHeight = window.innerHeight;
                    const centerX = targetRect.x + targetRect.width / 2;
                    const centerY = targetRect.y + targetRect.height / 2;
                    let quadrant = '';
                    if (centerY < vpHeight / 2) {
                        quadrant = centerX < vpWidth / 2 ? 'top-left' : 'top-right';
                    } else {
                        quadrant = centerX < vpWidth / 2 ? 'bottom-left' : 'bottom-right';
                    }

                    // Get relative DOM path
                    let domPath = '';
                    if (container) {
                        const containerPath = [];
                        let node = target.parentElement;
                        while (node && node !== container && containerPath.length < 5) {
                            const tag = node.tagName.toLowerCase();
                            const siblings = Array.from(node.parentElement?.children || []).filter(
                                c => c.tagName.toLowerCase() === tag
                            );
                            if (siblings.length > 1) {
                                const index = siblings.indexOf(node) + 1;
                                containerPath.unshift(`${tag}[${index}]`);
                            } else {
                                containerPath.unshift(tag);
                            }
                            node = node.parentElement;
                        }
                        domPath = containerPath.join('/');
                    }

                    return {
                        targetRect: { x: targetRect.x, y: targetRect.y, width: targetRect.width, height: targetRect.height },
                        anchors: anchors.slice(0, 5),
                        containerSelector: containerSelector,
                        visualQuadrant: quadrant,
                        domPath: domPath
                    };
                }
                """,
                selector,
            )

            if not context_data:
                logger.warning(
                    f"Could not capture context: element not found: {selector}"
                )
                return None

            target_rect = BoundingRect.from_dict(context_data["targetRect"])
            anchor_relations: List[Tuple[AnchorElement, SpatialRelation, float]] = []

            for anchor_data in context_data.get("anchors", []):
                anchor_rect = BoundingRect.from_dict(anchor_data["rect"])
                relation = self._determine_spatial_relation(target_rect, anchor_rect)
                stability = self._calculate_anchor_stability(anchor_data)

                anchor_selector = self._build_anchor_selector(anchor_data)
                if not anchor_selector:
                    continue

                anchor = AnchorElement(
                    selector=anchor_selector,
                    tag_name=anchor_data["tag"],
                    text_content=anchor_data.get("text", ""),
                    rect=anchor_rect,
                    stability_score=stability,
                    attributes={
                        k: v
                        for k, v in anchor_data.items()
                        if k not in ("tag", "text", "rect", "distance") and v
                    },
                )

                anchor_relations.append((anchor, relation, anchor_data["distance"]))

            context = SpatialContext(
                anchor_relations=anchor_relations,
                dom_path=context_data.get("domPath", ""),
                visual_quadrant=context_data.get("visualQuadrant", ""),
                container_selector=context_data.get("containerSelector"),
            )

            logger.debug(
                f"Captured context for {selector}: {len(anchor_relations)} anchors, "
                f"quadrant={context.visual_quadrant}"
            )
            return context

        except Exception as e:
            logger.error(f"Failed to capture spatial context for {selector}: {e}")
            raise

    async def heal(
        self,
        page: Page,
        selector: str,
        context: Optional[SpatialContext] = None,
        target_tag: Optional[str] = None,
    ) -> AnchorHealingResult:
        """
        Attempt to heal a broken selector using anchor-based relationships.

        Args:
            page: Playwright Page object.
            selector: The original selector that failed.
            context: Spatial context (uses stored if not provided).
            target_tag: Expected tag name of target element (for filtering).

        Returns:
            AnchorHealingResult with healed selector or failure details.
        """
        start_time = time.perf_counter()

        ctx = context or self._contexts.get(selector)
        if not ctx or not ctx.anchor_relations:
            return AnchorHealingResult(
                success=False,
                original_selector=selector,
                healed_selector="",
                confidence=0.0,
                strategy="anchor-no-context",
                healing_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        logger.info(f"Attempting anchor healing for: {selector}")

        candidates: List[Tuple[str, float, AnchorElement, SpatialRelation]] = []

        for anchor, relation, distance in ctx.anchor_relations:
            if not anchor.is_stable:
                continue

            try:
                anchor_exists = await page.query_selector(anchor.selector)
                if not anchor_exists:
                    logger.debug(f"Anchor no longer exists: {anchor.selector}")
                    continue

                # Generate relative selectors based on the relationship
                relative_selectors = self._generate_relative_selectors(
                    anchor, relation, target_tag
                )

                for rel_selector, base_conf in relative_selectors:
                    element = await page.query_selector(rel_selector)
                    if element:
                        # Adjust confidence based on anchor stability and distance
                        adjusted_conf = base_conf * anchor.stability_score
                        if distance < self._near_threshold:
                            adjusted_conf *= 1.0
                        else:
                            adjusted_conf *= max(0.7, 1.0 - (distance / 500))

                        candidates.append(
                            (rel_selector, adjusted_conf, anchor, relation)
                        )
                        logger.debug(
                            f"Candidate found: {rel_selector} (conf={adjusted_conf:.2f})"
                        )

            except Exception as e:
                logger.warning(f"Error testing anchor {anchor.selector}: {e}")
                continue

        healing_time = (time.perf_counter() - start_time) * 1000

        if not candidates:
            return AnchorHealingResult(
                success=False,
                original_selector=selector,
                healed_selector="",
                confidence=0.0,
                strategy="anchor-no-candidates",
                healing_time_ms=healing_time,
            )

        # Sort by confidence descending
        candidates.sort(key=lambda c: -c[1])
        best_selector, best_conf, best_anchor, best_relation = candidates[0]

        if best_conf >= self._min_confidence:
            logger.info(
                f"Anchor healing succeeded: {selector} -> {best_selector} "
                f"(conf={best_conf:.2f}, anchor={best_anchor.text_content[:30]})"
            )
            return AnchorHealingResult(
                success=True,
                original_selector=selector,
                healed_selector=best_selector,
                confidence=best_conf,
                anchor_used=best_anchor,
                relation_used=best_relation,
                strategy="anchor",
                candidates=[(c[0], c[1]) for c in candidates[:5]],
                healing_time_ms=healing_time,
            )

        return AnchorHealingResult(
            success=False,
            original_selector=selector,
            healed_selector="",
            confidence=best_conf,
            strategy="anchor-low-confidence",
            candidates=[(c[0], c[1]) for c in candidates[:5]],
            healing_time_ms=healing_time,
        )

    def _determine_spatial_relation(
        self,
        target: BoundingRect,
        anchor: BoundingRect,
    ) -> SpatialRelation:
        """
        Determine the spatial relationship between target and anchor.

        Args:
            target: Target element bounding rect.
            anchor: Anchor element bounding rect.

        Returns:
            SpatialRelation describing the relationship.
        """
        # Check containment
        target_inside = (
            anchor.x <= target.x
            and anchor.y <= target.y
            and anchor.right >= target.right
            and anchor.bottom >= target.bottom
        )
        if target_inside:
            return SpatialRelation.INSIDE

        anchor_inside = (
            target.x <= anchor.x
            and target.y <= anchor.y
            and target.right >= anchor.right
            and target.bottom >= anchor.bottom
        )
        if anchor_inside:
            return SpatialRelation.CONTAINS

        # Check directional relationships
        dx = target.center_x - anchor.center_x
        dy = target.center_y - anchor.center_y

        # Determine primary axis
        if abs(dx) > abs(dy):
            # Horizontal relationship is stronger
            if dx > 0:
                return SpatialRelation.RIGHT_OF
            return SpatialRelation.LEFT_OF
        else:
            # Vertical relationship is stronger
            if dy > 0:
                return SpatialRelation.BELOW
            return SpatialRelation.ABOVE

    def _calculate_anchor_stability(self, anchor_data: Dict[str, Any]) -> float:
        """
        Calculate stability score for an anchor element.

        Args:
            anchor_data: Dictionary with anchor element data.

        Returns:
            Stability score between 0.0 and 1.0.
        """
        score = 0.0

        # Tag-based stability
        tag = anchor_data.get("tag", "")
        if tag in ("label", "legend"):
            score += 0.3  # Labels are very stable
        elif tag in ("h1", "h2", "h3"):
            score += 0.25  # Headings are stable
        elif tag in ("h4", "h5", "h6", "th", "caption"):
            score += 0.2
        else:
            score += 0.1

        # Attribute-based stability
        if anchor_data.get("id"):
            score += 0.2
        if anchor_data.get("dataTestId"):
            score += 0.25
        if anchor_data.get("ariaLabel"):
            score += 0.15
        if anchor_data.get("forAttr"):
            score += 0.2  # label[for] is very reliable

        # Text content stability
        text = anchor_data.get("text", "")
        if text and len(text) > 2 and len(text) < 50:
            score += 0.15  # Reasonable text length
        elif text and len(text) >= 50:
            score += 0.05  # Long text is less reliable

        return min(1.0, score)

    def _build_anchor_selector(self, anchor_data: Dict[str, Any]) -> Optional[str]:
        """
        Build a Playwright-compatible selector for an anchor element.

        Args:
            anchor_data: Dictionary with anchor element data.

        Returns:
            Selector string or None if cannot build reliable selector.
        """
        # Priority order for building selector
        if anchor_data.get("id"):
            return f"#{anchor_data['id']}"

        if anchor_data.get("dataTestId"):
            return f'[data-testid="{anchor_data["dataTestId"]}"]'

        if anchor_data.get("ariaLabel"):
            tag = anchor_data.get("tag", "*")
            return f'{tag}[aria-label="{anchor_data["ariaLabel"]}"]'

        # For labels with 'for' attribute - prioritize over text
        if anchor_data.get("forAttr"):
            return f'label[for="{anchor_data["forAttr"]}"]'

        text = anchor_data.get("text", "").strip()
        if text and len(text) < 50:
            tag = anchor_data.get("tag", "")
            if tag in ("label", "h1", "h2", "h3", "h4", "h5", "h6"):
                # Escape quotes in text
                escaped_text = text.replace('"', '\\"')
                return f'{tag}:has-text("{escaped_text}")'

        return None

    def _generate_relative_selectors(
        self,
        anchor: AnchorElement,
        relation: SpatialRelation,
        target_tag: Optional[str] = None,
    ) -> List[Tuple[str, float]]:
        """
        Generate relative selectors based on anchor and spatial relationship.

        Args:
            anchor: The anchor element.
            relation: Spatial relationship to target.
            target_tag: Optional expected tag of target.

        Returns:
            List of (selector, confidence) tuples.
        """
        selectors: List[Tuple[str, float]] = []
        anchor_sel = anchor.selector

        # For labels, check associated form control
        if anchor.tag_name == "label":
            for_attr = anchor.attributes.get("forAttr", "")
            if for_attr:
                selectors.append((f"#{for_attr}", 0.95))

            # Also try label >> input/select/textarea
            selectors.append((f"{anchor_sel} >> input", 0.85))
            selectors.append((f"{anchor_sel} >> select", 0.85))
            selectors.append((f"{anchor_sel} >> textarea", 0.85))
            selectors.append((f"{anchor_sel} + input", 0.8))
            selectors.append((f"{anchor_sel} + select", 0.8))

        # XPath-based relative selectors
        if relation == SpatialRelation.RIGHT_OF:
            # Element to the right - try following sibling
            target = target_tag or "*"
            selectors.append(
                (f"xpath={anchor_sel}/../following-sibling::*[1]//{target}", 0.7)
            )
            selectors.append((f"{anchor_sel} ~ {target}:first-of-type", 0.65))

        elif relation == SpatialRelation.BELOW:
            target = target_tag or "*"
            # Try parent's next sibling
            selectors.append((f"xpath={anchor_sel}/following::*[1]//{target}", 0.65))

        elif relation == SpatialRelation.INSIDE:
            target = target_tag or "input, button, select, textarea, a"
            selectors.append((f"{anchor_sel} >> {target}", 0.8))
            selectors.append((f"{anchor_sel} {target}", 0.75))

        # General proximity using :near() pseudo-class (Playwright-specific)
        if target_tag:
            selectors.append((f"{target_tag}:near({anchor_sel})", 0.6))
        else:
            selectors.append((f"input:near({anchor_sel})", 0.55))
            selectors.append((f"button:near({anchor_sel})", 0.55))
            selectors.append((f"select:near({anchor_sel})", 0.55))

        return selectors

    async def find_nearby_elements(
        self,
        page: Page,
        anchor_selector: str,
        max_distance: float = 200,
        target_tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find elements near an anchor element.

        Args:
            page: Playwright Page object.
            anchor_selector: Selector for the anchor element.
            max_distance: Maximum distance in pixels.
            target_tags: Optional list of tag names to filter.

        Returns:
            List of nearby element data dictionaries.
        """
        try:
            tags_filter = target_tags or ["input", "button", "select", "textarea", "a"]

            nearby = await page.evaluate(
                """
                ({anchorSelector, maxDistance, tagsFilter}) => {
                    // Support both CSS and XPath selectors
                    let anchor;
                    if (anchorSelector.startsWith('/') || anchorSelector.startsWith('(')) {
                        const result = document.evaluate(anchorSelector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                        anchor = result.singleNodeValue;
                    } else {
                        anchor = document.querySelector(anchorSelector);
                    }
                    if (!anchor) return [];

                    const anchorRect = anchor.getBoundingClientRect();
                    const anchorCenterX = anchorRect.x + anchorRect.width / 2;
                    const anchorCenterY = anchorRect.y + anchorRect.height / 2;

                    const candidates = [];
                    const selector = tagsFilter.join(', ');

                    document.querySelectorAll(selector).forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) return;

                        const centerX = rect.x + rect.width / 2;
                        const centerY = rect.y + rect.height / 2;
                        const dx = centerX - anchorCenterX;
                        const dy = centerY - anchorCenterY;
                        const distance = Math.sqrt(dx*dx + dy*dy);

                        if (distance <= maxDistance) {
                            candidates.push({
                                tag: el.tagName.toLowerCase(),
                                id: el.id || null,
                                name: el.getAttribute('name') || null,
                                type: el.getAttribute('type') || null,
                                text: el.textContent?.trim().substring(0, 50) || '',
                                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                                distance: distance
                            });
                        }
                    });

                    return candidates.sort((a, b) => a.distance - b.distance);
                }
                """,
                {
                    "anchorSelector": anchor_selector,
                    "maxDistance": max_distance,
                    "tagsFilter": tags_filter,
                },
            )

            return nearby

        except Exception as e:
            logger.error(f"Failed to find nearby elements: {e}")
            return []


__all__ = ["AnchorHealer"]
