"""
Tests for Anchor-Based Selector Healer (Tier 2).

These tests verify the anchor healer's spatial relationship detection,
anchor selection, and relative selector generation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.infrastructure.browser.healing.models import (
    AnchorElement,
    AnchorHealingResult,
    BoundingRect,
    SpatialContext,
    SpatialRelation,
)
from casare_rpa.infrastructure.browser.healing.anchor_healer import AnchorHealer


class TestBoundingRect:
    """Tests for BoundingRect model."""

    def test_center_coordinates(self) -> None:
        """Verify center point calculation."""
        rect = BoundingRect(x=100, y=200, width=50, height=30)
        assert rect.center_x == 125
        assert rect.center_y == 215

    def test_right_bottom_edges(self) -> None:
        """Verify edge coordinate calculation."""
        rect = BoundingRect(x=100, y=200, width=50, height=30)
        assert rect.right == 150
        assert rect.bottom == 230

    def test_distance_to(self) -> None:
        """Verify distance calculation between rects."""
        rect1 = BoundingRect(x=0, y=0, width=10, height=10)
        rect2 = BoundingRect(x=30, y=40, width=10, height=10)

        # Centers are at (5,5) and (35,45), distance = sqrt(30^2 + 40^2) = 50
        assert rect1.distance_to(rect2) == 50.0

    def test_edge_distance_overlapping(self) -> None:
        """Verify edge distance is 0 for overlapping rects."""
        rect1 = BoundingRect(x=0, y=0, width=100, height=100)
        rect2 = BoundingRect(x=50, y=50, width=100, height=100)

        assert rect1.edge_distance_to(rect2) == 0.0

    def test_edge_distance_separated(self) -> None:
        """Verify edge distance for separated rects."""
        rect1 = BoundingRect(x=0, y=0, width=10, height=10)
        rect2 = BoundingRect(x=20, y=0, width=10, height=10)

        # Horizontal gap of 10 pixels
        assert rect1.edge_distance_to(rect2) == 10.0

    def test_serialization(self) -> None:
        """Verify dict serialization roundtrip."""
        rect = BoundingRect(x=100.5, y=200.5, width=50.0, height=30.0)
        data = rect.to_dict()
        restored = BoundingRect.from_dict(data)

        assert restored.x == rect.x
        assert restored.y == rect.y
        assert restored.width == rect.width
        assert restored.height == rect.height


class TestSpatialRelation:
    """Tests for SpatialRelation enum and detection."""

    def test_all_relations_defined(self) -> None:
        """Verify all expected relations exist."""
        expected = [
            "NEAR",
            "ABOVE",
            "BELOW",
            "LEFT_OF",
            "RIGHT_OF",
            "INSIDE",
            "CONTAINS",
            "ADJACENT",
        ]
        for rel in expected:
            assert hasattr(SpatialRelation, rel)


class TestAnchorElement:
    """Tests for AnchorElement model."""

    def test_stability_threshold(self) -> None:
        """Verify stability threshold check."""
        stable_anchor = AnchorElement(
            selector="#header",
            tag_name="h1",
            text_content="Page Title",
            rect=BoundingRect(x=0, y=0, width=100, height=30),
            stability_score=0.8,
        )
        assert stable_anchor.is_stable is True

        unstable_anchor = AnchorElement(
            selector=".dynamic-class",
            tag_name="div",
            text_content="Dynamic Content",
            rect=BoundingRect(x=0, y=0, width=100, height=30),
            stability_score=0.5,
        )
        assert unstable_anchor.is_stable is False

    def test_serialization(self) -> None:
        """Verify dict serialization roundtrip."""
        anchor = AnchorElement(
            selector='label[for="email"]',
            tag_name="label",
            text_content="Email Address",
            rect=BoundingRect(x=10, y=20, width=100, height=20),
            stability_score=0.9,
            attributes={"for": "email"},
            is_landmark=False,
        )
        data = anchor.to_dict()
        restored = AnchorElement.from_dict(data)

        assert restored.selector == anchor.selector
        assert restored.tag_name == anchor.tag_name
        assert restored.text_content == anchor.text_content
        assert restored.stability_score == anchor.stability_score


class TestSpatialContext:
    """Tests for SpatialContext model."""

    def test_get_best_anchor(self) -> None:
        """Verify best anchor selection."""
        anchor1 = AnchorElement(
            selector="#stable-anchor",
            tag_name="label",
            text_content="Stable",
            rect=BoundingRect(x=0, y=0, width=50, height=20),
            stability_score=0.9,
        )
        anchor2 = AnchorElement(
            selector=".less-stable",
            tag_name="div",
            text_content="Less Stable",
            rect=BoundingRect(x=0, y=50, width=50, height=20),
            stability_score=0.6,
        )

        context = SpatialContext(
            anchor_relations=[
                (anchor2, SpatialRelation.ABOVE, 30.0),
                (anchor1, SpatialRelation.LEFT_OF, 50.0),
            ],
            dom_path="div/form",
            visual_quadrant="top-left",
        )

        best = context.get_best_anchor()
        assert best is not None
        assert best[0].selector == "#stable-anchor"

    def test_empty_context(self) -> None:
        """Verify handling of empty context."""
        context = SpatialContext(
            anchor_relations=[],
            dom_path="",
            visual_quadrant="",
        )
        assert context.get_best_anchor() is None


class TestAnchorHealer:
    """Tests for AnchorHealer class."""

    def test_initialization(self) -> None:
        """Verify default initialization."""
        healer = AnchorHealer()
        assert healer._near_threshold == 150
        assert healer._min_confidence == 0.6

    def test_custom_initialization(self) -> None:
        """Verify custom initialization parameters."""
        healer = AnchorHealer(near_threshold=200, min_confidence=0.8)
        assert healer._near_threshold == 200
        assert healer._min_confidence == 0.8

    def test_store_and_get_context(self) -> None:
        """Verify context storage and retrieval."""
        healer = AnchorHealer()
        anchor = AnchorElement(
            selector="#label",
            tag_name="label",
            text_content="Test",
            rect=BoundingRect(x=0, y=0, width=50, height=20),
            stability_score=0.9,
        )
        context = SpatialContext(
            anchor_relations=[(anchor, SpatialRelation.LEFT_OF, 20.0)],
            dom_path="form",
            visual_quadrant="top-left",
        )

        healer.store_context("#input", context)
        retrieved = healer.get_context("#input")

        assert retrieved is not None
        assert len(retrieved.anchor_relations) == 1
        assert retrieved.visual_quadrant == "top-left"

    def test_determine_spatial_relation_above(self) -> None:
        """Verify ABOVE relation detection."""
        healer = AnchorHealer()
        target = BoundingRect(x=100, y=50, width=50, height=20)
        anchor = BoundingRect(x=100, y=100, width=50, height=20)

        relation = healer._determine_spatial_relation(target, anchor)
        assert relation == SpatialRelation.ABOVE

    def test_determine_spatial_relation_below(self) -> None:
        """Verify BELOW relation detection."""
        healer = AnchorHealer()
        target = BoundingRect(x=100, y=150, width=50, height=20)
        anchor = BoundingRect(x=100, y=100, width=50, height=20)

        relation = healer._determine_spatial_relation(target, anchor)
        assert relation == SpatialRelation.BELOW

    def test_determine_spatial_relation_left_of(self) -> None:
        """Verify LEFT_OF relation detection."""
        healer = AnchorHealer()
        target = BoundingRect(x=50, y=100, width=50, height=20)
        anchor = BoundingRect(x=150, y=100, width=50, height=20)

        relation = healer._determine_spatial_relation(target, anchor)
        assert relation == SpatialRelation.LEFT_OF

    def test_determine_spatial_relation_right_of(self) -> None:
        """Verify RIGHT_OF relation detection."""
        healer = AnchorHealer()
        target = BoundingRect(x=200, y=100, width=50, height=20)
        anchor = BoundingRect(x=100, y=100, width=50, height=20)

        relation = healer._determine_spatial_relation(target, anchor)
        assert relation == SpatialRelation.RIGHT_OF

    def test_determine_spatial_relation_inside(self) -> None:
        """Verify INSIDE relation detection."""
        healer = AnchorHealer()
        target = BoundingRect(x=110, y=110, width=30, height=30)
        anchor = BoundingRect(x=100, y=100, width=100, height=100)

        relation = healer._determine_spatial_relation(target, anchor)
        assert relation == SpatialRelation.INSIDE

    def test_determine_spatial_relation_contains(self) -> None:
        """Verify CONTAINS relation detection."""
        healer = AnchorHealer()
        target = BoundingRect(x=100, y=100, width=100, height=100)
        anchor = BoundingRect(x=110, y=110, width=30, height=30)

        relation = healer._determine_spatial_relation(target, anchor)
        assert relation == SpatialRelation.CONTAINS

    def test_calculate_anchor_stability_label(self) -> None:
        """Verify stability scoring for labels."""
        healer = AnchorHealer()

        # Label with for attribute - very stable
        anchor_data = {
            "tag": "label",
            "text": "Email",
            "forAttr": "email-input",
            "id": "",
        }
        stability = healer._calculate_anchor_stability(anchor_data)
        assert stability >= 0.5  # label + forAttr bonus

    def test_calculate_anchor_stability_heading_with_id(self) -> None:
        """Verify stability scoring for headings with ID."""
        healer = AnchorHealer()

        anchor_data = {
            "tag": "h1",
            "text": "Page Title",
            "id": "main-title",
            "dataTestId": "page-title",
        }
        stability = healer._calculate_anchor_stability(anchor_data)
        assert stability >= 0.7  # heading + id + data-testid

    def test_build_anchor_selector_with_id(self) -> None:
        """Verify selector building prioritizes ID."""
        healer = AnchorHealer()

        anchor_data = {
            "tag": "label",
            "id": "email-label",
            "dataTestId": "email",
        }
        selector = healer._build_anchor_selector(anchor_data)
        assert selector == "#email-label"

    def test_build_anchor_selector_with_testid(self) -> None:
        """Verify selector uses data-testid when no ID."""
        healer = AnchorHealer()

        anchor_data = {
            "tag": "label",
            "id": "",
            "dataTestId": "email-label",
        }
        selector = healer._build_anchor_selector(anchor_data)
        assert selector == '[data-testid="email-label"]'

    def test_build_anchor_selector_with_for_attr(self) -> None:
        """Verify selector uses for attribute for labels."""
        healer = AnchorHealer()

        anchor_data = {
            "tag": "label",
            "id": "",
            "dataTestId": "",
            "ariaLabel": "",
            "forAttr": "email",
            "text": "Email Address",
        }
        selector = healer._build_anchor_selector(anchor_data)
        assert selector == 'label[for="email"]'

    def test_build_anchor_selector_with_text(self) -> None:
        """Verify selector uses text content as fallback."""
        healer = AnchorHealer()

        anchor_data = {
            "tag": "label",
            "id": "",
            "dataTestId": "",
            "ariaLabel": "",
            "forAttr": "",
            "text": "Email",
        }
        selector = healer._build_anchor_selector(anchor_data)
        assert selector == 'label:has-text("Email")'

    def test_generate_relative_selectors_for_label(self) -> None:
        """Verify relative selector generation for labels."""
        healer = AnchorHealer()

        anchor = AnchorElement(
            selector='label[for="email"]',
            tag_name="label",
            text_content="Email",
            rect=BoundingRect(x=0, y=0, width=50, height=20),
            stability_score=0.9,
            attributes={"forAttr": "email"},
        )

        selectors = healer._generate_relative_selectors(
            anchor, SpatialRelation.RIGHT_OF, target_tag="input"
        )

        # Should include the for attribute selector
        selector_values = [s[0] for s in selectors]
        assert "#email" in selector_values

    def test_generate_relative_selectors_inside_relation(self) -> None:
        """Verify relative selectors for INSIDE relation."""
        healer = AnchorHealer()

        anchor = AnchorElement(
            selector="#form-container",
            tag_name="div",
            text_content="",
            rect=BoundingRect(x=0, y=0, width=200, height=200),
            stability_score=0.8,
        )

        selectors = healer._generate_relative_selectors(
            anchor, SpatialRelation.INSIDE, target_tag="button"
        )

        selector_values = [s[0] for s in selectors]
        assert any(">> button" in s for s in selector_values)


class TestAnchorHealerAsync:
    """Async tests for AnchorHealer."""

    @pytest.mark.asyncio
    async def test_capture_spatial_context(self) -> None:
        """Verify spatial context capture from page."""
        healer = AnchorHealer()

        # Mock page
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(
            return_value={
                "targetRect": {"x": 100, "y": 100, "width": 100, "height": 30},
                "anchors": [
                    {
                        "tag": "label",
                        "text": "Email",
                        "rect": {"x": 10, "y": 100, "width": 50, "height": 20},
                        "id": "",
                        "forAttr": "email",
                        "distance": 40.0,
                    }
                ],
                "containerSelector": "#form",
                "visualQuadrant": "top-left",
                "domPath": "form/div",
            }
        )

        context = await healer.capture_spatial_context(mock_page, "#email-input")

        assert context is not None
        assert len(context.anchor_relations) == 1
        assert context.visual_quadrant == "top-left"
        assert context.container_selector == "#form"

    @pytest.mark.asyncio
    async def test_capture_spatial_context_element_not_found(self) -> None:
        """Verify handling when element not found."""
        healer = AnchorHealer()

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=None)

        context = await healer.capture_spatial_context(mock_page, "#nonexistent")
        assert context is None

    @pytest.mark.asyncio
    async def test_heal_no_context(self) -> None:
        """Verify healing fails gracefully without context."""
        healer = AnchorHealer()

        mock_page = AsyncMock()

        result = await healer.heal(mock_page, "#unknown-selector")

        assert result.success is False
        assert result.strategy == "anchor-no-context"

    @pytest.mark.asyncio
    async def test_heal_with_context(self) -> None:
        """Verify healing with stored context."""
        healer = AnchorHealer()

        # Store context
        anchor = AnchorElement(
            selector='label[for="email"]',
            tag_name="label",
            text_content="Email",
            rect=BoundingRect(x=10, y=100, width=50, height=20),
            stability_score=0.9,
            attributes={"forAttr": "email"},
        )
        context = SpatialContext(
            anchor_relations=[(anchor, SpatialRelation.LEFT_OF, 40.0)],
            dom_path="form/div",
            visual_quadrant="top-left",
        )
        healer.store_context("#email-input", context)

        # Mock page
        mock_page = AsyncMock()
        mock_page.url = "https://example.com/form"

        # Anchor exists on page
        mock_anchor_element = AsyncMock()
        mock_target_element = AsyncMock()

        async def mock_query_selector(selector: str):
            if selector == 'label[for="email"]':
                return mock_anchor_element
            elif selector == "#email":
                return mock_target_element
            return None

        mock_page.query_selector = mock_query_selector

        result = await healer.heal(mock_page, "#email-input")

        assert result.success is True
        assert result.healed_selector == "#email"
        assert result.anchor_used is not None
        assert result.confidence >= 0.6

    @pytest.mark.asyncio
    async def test_heal_anchor_missing(self) -> None:
        """Verify handling when anchor no longer exists."""
        healer = AnchorHealer()

        # Store context with anchor that won't be found
        anchor = AnchorElement(
            selector="#old-label",
            tag_name="label",
            text_content="Old Label",
            rect=BoundingRect(x=10, y=100, width=50, height=20),
            stability_score=0.9,
        )
        context = SpatialContext(
            anchor_relations=[(anchor, SpatialRelation.LEFT_OF, 40.0)],
            dom_path="form/div",
            visual_quadrant="top-left",
        )
        healer.store_context("#target", context)

        # Mock page - anchor not found
        mock_page = AsyncMock()
        mock_page.url = "https://example.com/form"
        mock_page.query_selector = AsyncMock(return_value=None)

        result = await healer.heal(mock_page, "#target")

        assert result.success is False
        assert result.strategy == "anchor-no-candidates"

    @pytest.mark.asyncio
    async def test_find_nearby_elements(self) -> None:
        """Verify finding nearby elements."""
        healer = AnchorHealer()

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(
            return_value=[
                {
                    "tag": "input",
                    "id": "email",
                    "name": "email",
                    "type": "email",
                    "text": "",
                    "rect": {"x": 100, "y": 100, "width": 200, "height": 30},
                    "distance": 20.0,
                },
                {
                    "tag": "button",
                    "id": "submit",
                    "name": "",
                    "type": "submit",
                    "text": "Submit",
                    "rect": {"x": 100, "y": 150, "width": 100, "height": 40},
                    "distance": 50.0,
                },
            ]
        )

        nearby = await healer.find_nearby_elements(
            mock_page,
            "#email-label",
            max_distance=100,
        )

        assert len(nearby) == 2
        assert nearby[0]["tag"] == "input"
        assert nearby[1]["tag"] == "button"
