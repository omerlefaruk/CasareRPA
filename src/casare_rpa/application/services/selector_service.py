import re
from functools import lru_cache
from typing import Any, Dict, Tuple

from casare_rpa.domain.entities.selector import (
    ElementFingerprint,
    SelectorStrategy,
    SelectorTarget,
    SelectorType,
)


class SelectorService:
    """
    Unified service for managing element selectors.

    Responsibilities:
    - Generate multiple selector strategies for a UI element
    - Normalize and validate selectors (Web, Desktop, XML, Wildcard)
    - Calculate similarity between elements for self-healing
    """

    # Stability scores for different selector types
    BROWSER_SCORES = {
        SelectorType.XPATH: 90,
        SelectorType.DATA_ATTR: 85,
        SelectorType.ARIA: 80,
        SelectorType.CSS: 70,
        SelectorType.TEXT: 50,
    }

    DESKTOP_SCORES = {
        SelectorType.UIA_AUTOMATION_ID: 95,
        SelectorType.UIA_NAME: 85,
        SelectorType.UIA_CLASS_NAME: 70,
        SelectorType.UIA_CONTROL_TYPE: 40,
        SelectorType.UIA_XPATH: 80,
    }

    # =========================================================================
    # Normalization & Validation
    # =========================================================================

    @staticmethod
    @lru_cache(maxsize=1024)
    def normalize(selector: str) -> str:
        """
        Normalize any selector format to work with Playwright.

        Supports:
        - Common CSS selectors (#id, .class)
        - XPath (//, /*, xpath=)
        - Playwright text (text=)
        - Case-insensitive text (itext=)
        - Wildcard patterns (btn-*)
        - UiPath-style XML (<webctrl .../>)
        """
        if not selector or not isinstance(selector, str):
            return selector

        selector = selector.strip()

        # 1. XML selector (<webctrl .../> or <input id='x' />)
        if selector.startswith("<"):
            parsed, _ = SelectorService.parse_xml_selector(selector)
            return SelectorService.normalize(parsed)

        # 2. Wildcard patterns
        if "*" in selector or "?" in selector:
            from casare_rpa.utils.selectors.wildcard_selector import WildcardSelector

            if WildcardSelector.has_wildcard(selector):
                normalized = WildcardSelector.parse(selector)
                if normalized != selector:
                    return SelectorService.normalize(normalized)

        # 3. Case-insensitive text (itext=)
        if selector.startswith("itext="):
            value = selector[6:]
            if ":" in value:
                element, text = value.split(":", 1)
                element = element.strip() or "*"
                text = text.strip()
            else:
                element = "*"
                text = value.strip()

            if text:
                upper, lower = text.upper(), text.lower()
                return f"//{element}[contains(translate(., '{upper}', '{lower}'), '{lower}')]"
            return selector

        # 4. Standard prefixes & combinators
        if selector.startswith(("xpath=", "text=", "id=", "css=", "aria=")) or ">>" in selector:
            return selector

        # 5. XPath variations
        if selector.startswith("//"):
            return selector
        if selector.startswith("/*"):
            return "//" + selector[2:]
        if selector.startswith("/") and not selector.startswith("//"):
            return f"xpath={selector}"

        # 6. XPath indicators (looks like XPath but missing prefix)
        if "@" in selector or any(
            f in selector for f in ["contains(", "text()", "normalize-space("]
        ):
            if not selector.startswith("/"):
                return f"//{selector}"

        # 7. Default to CSS
        return selector

    @staticmethod
    def validate(selector: str) -> Tuple[bool, str]:
        """Validate selector format (balanced brackets, non-empty, etc)."""
        if not selector:
            return False, "Selector cannot be empty"
        if not isinstance(selector, str):
            return False, "Selector must be a string"

        s = selector.strip()
        if s.count("[") != s.count("]"):
            return False, "Unbalanced brackets"
        if s.count("(") != s.count(")"):
            return False, "Unbalanced parentheses"

        return True, ""

    @staticmethod
    def parse_xml_selector(xml_selector: str) -> Tuple[str, str]:
        """
        Parse UiPath-style XML selector and convert to XPath.

        Supports single-line and multi-line hierarchical selectors:
            Single: <input id='abc' class='foo bar' />
            Multi:  <webctrl aaname='First Name' tag='LABEL' />
                    <nav up='1' />
                    <webctrl tag='INPUT' />
        """
        xml_selector = xml_selector.strip()

        # Already an XPath?
        if xml_selector.startswith("//") or xml_selector.startswith("(//"):
            return xml_selector, "xpath"

        # Already a CSS selector?
        if not xml_selector.startswith("<"):
            return xml_selector, "css"

        # Split into lines/elements
        lines = [line.strip() for line in xml_selector.split("\n") if line.strip()]

        # Handle single-line with multiple elements: <a /><b />
        if len(lines) == 1 and lines[0].count("<") > 1:
            parts = re.split(r">\s*<", lines[0])
            lines = []
            for i, part in enumerate(parts):
                if i == 0:
                    lines.append(part + ">")
                elif i == len(parts) - 1:
                    lines.append("<" + part)
                else:
                    lines.append("<" + part + ">")

        if not lines:
            return xml_selector, "css"

        # Parse each element
        xpath_parts = []
        pending_nav = None

        for line in lines:
            tag, attrs = SelectorService._parse_single_xml_element(line)

            if not tag:
                continue

            if tag == "nav":
                pending_nav = attrs
                continue

            if tag in ("webctrl", "html", "wnd", "ctrl"):
                element_xpath = SelectorService._build_xpath_for_element(tag, attrs)

                if pending_nav:
                    up_count = int(pending_nav.get("up", "0"))
                    right_count = int(pending_nav.get("right", "0"))
                    left_count = int(pending_nav.get("left", "0"))
                    down_count = int(pending_nav.get("down", "0"))

                    if up_count > 0 and xpath_parts:
                        nav_xpath = "/parent::*" * up_count
                        xpath_parts[-1] += nav_xpath
                        xpath_parts.append(f"/descendant::{element_xpath}")
                    elif right_count > 0 and xpath_parts:
                        xpath_parts.append(f"/following::{element_xpath}[{right_count}]")
                    elif left_count > 0 and xpath_parts:
                        xpath_parts.append(f"/preceding::{element_xpath}[{left_count}]")
                    elif down_count > 0 and xpath_parts:
                        xpath_parts.append(f"/following::{element_xpath}[{down_count}]")
                    else:
                        xpath_parts.append(f"//{element_xpath}")
                    pending_nav = None
                elif xpath_parts:
                    xpath_parts.append(f"/descendant::{element_xpath}")
                else:
                    xpath_parts.append(f"//{element_xpath}")
            else:
                element_xpath = SelectorService._build_xpath_for_element(tag, {"tag": tag, **attrs})
                xpath_parts.append(f"//{element_xpath}")

        if not xpath_parts:
            return xml_selector, "css"

        final_xpath = "".join(xpath_parts)

        if final_xpath.startswith("//css="):
            return final_xpath[6:], "css"
        elif "css=" in final_xpath and len(xpath_parts) == 1:
            return final_xpath.replace("//css=", "").replace("css=", ""), "css"

        # Handle idx (index)
        last_tag, last_attrs = SelectorService._parse_single_xml_element(lines[-1])
        if "idx" in last_attrs:
            idx = int(last_attrs["idx"]) + 1
            final_xpath = f"({final_xpath})[{idx}]"

        return final_xpath, "xpath"

    @staticmethod
    def _parse_single_xml_element(element_str: str) -> Tuple[str, Dict[str, str]]:
        """Parse a single XML element like <webctrl tag='INPUT' id='foo' />."""
        element_str = element_str.strip()
        if not element_str.startswith("<"):
            return "", {}

        tag_match = re.match(r"<(\w+)", element_str)
        if not tag_match:
            return "", {}

        tag = tag_match.group(1).lower()
        attrs = {}
        pos = len(tag_match.group(0))
        rest = element_str[pos:]

        for m in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', rest):
            attrs[m.group(1).lower()] = m.group(2)
        for m in re.finditer(r"(\w+)\s*=\s*'([^']*)'", rest):
            name = m.group(1).lower()
            if name not in attrs:
                attrs[name] = m.group(2)

        return tag, attrs

    @staticmethod
    def _build_xpath_for_element(tag: str, attrs: Dict[str, str]) -> str:
        """Build XPath predicate for a webctrl element."""
        if "selector" in attrs:
            embedded = attrs["selector"].strip()
            if embedded.startswith("<"):
                embedded_tag, embedded_attrs = SelectorService._parse_single_xml_element(embedded)
                if embedded_tag and embedded_tag not in ("webctrl", "html", "wnd", "ctrl"):
                    return SelectorService._build_xpath_for_element(
                        embedded_tag, {"tag": embedded_tag, **embedded_attrs}
                    )
            elif embedded.startswith("//") or embedded.startswith("xpath="):
                xpath = embedded[6:] if embedded.startswith("xpath=") else embedded
                return xpath.lstrip("/")
            elif not embedded.startswith("/"):
                return f"css={embedded}"

        html_tag = attrs.get("tag", "*").lower()
        xpath_parts = [html_tag]

        for attr_name, attr_value in attrs.items():
            if attr_name in ("tag", "selector"):
                continue

            if attr_name == "aaname":
                if "'" in attr_value:
                    xpath_parts.append(
                        f'[contains(text(), "{attr_value}") or @aria-label="{attr_value}" or @name="{attr_value}"]'
                    )
                else:
                    xpath_parts.append(
                        f"[contains(text(), '{attr_value}') or @aria-label='{attr_value}' or @name='{attr_value}']"
                    )
            elif attr_name == "id":
                xpath_parts.append(f"[@id='{attr_value}']")
            elif attr_name == "class":
                xpath_parts.append(f"[contains(@class, '{attr_value}')]")
            elif attr_name == "name":
                xpath_parts.append(f"[@name='{attr_value}']")
            elif attr_name == "type":
                xpath_parts.append(f"[@type='{attr_value}']")
            elif attr_name == "placeholder":
                xpath_parts.append(f"[@placeholder='{attr_value}']")
            elif attr_name == "value":
                xpath_parts.append(f"[@value='{attr_value}']")
            elif attr_name == "href":
                xpath_parts.append(f"[contains(@href, '{attr_value}')]")
            elif attr_name == "innertext":
                xpath_parts.append(f"[contains(text(), '{attr_value}')]")
            elif attr_name != "idx":
                xpath_parts.append(f"[@{attr_name}='{attr_value}']")

        return "".join(xpath_parts)

    # =========================================================================
    # Generation (Browser/Desktop)
    # =========================================================================

    @classmethod
    def generate_browser_fingerprint(cls, element_data: Dict[str, Any]) -> ElementFingerprint:
        """Generate multiple selector strategies from browser element data."""
        fingerprint = ElementFingerprint(
            target=SelectorTarget.BROWSER,
            tag_name=element_data.get("tagName", ""),
            element_id=element_data.get("id"),
            class_names=element_data.get("className", "").split()
            if element_data.get("className")
            else [],
            text_content=element_data.get("text"),
            attributes=element_data.get("attributes", {}),
            rect=element_data.get("rect", {}),
        )

        selectors_data = element_data.get("selectors", {})
        strategies = []

        # 1. XPath
        if xpath := selectors_data.get("xpath"):
            optimized_xpath = cls._optimize_xpath(xpath)
            score = cls._score_browser_selector(SelectorType.XPATH, optimized_xpath, element_data)
            strategies.append(
                SelectorStrategy(
                    selector_type=SelectorType.XPATH,
                    value=optimized_xpath,
                    target=SelectorTarget.BROWSER,
                    score=score,
                )
            )

        # 2. Data attributes
        for attr_name, attr_value in element_data.get("attributes", {}).items():
            if attr_name.startswith("data-"):
                xpath_data = f"//*[@{attr_name}='{attr_value}']"
                score = cls._score_browser_selector(
                    SelectorType.DATA_ATTR, xpath_data, element_data
                )
                strategies.append(
                    SelectorStrategy(
                        selector_type=SelectorType.DATA_ATTR,
                        value=xpath_data,
                        target=SelectorTarget.BROWSER,
                        score=score,
                    )
                )

        # 3. ARIA attributes
        if aria_xpath := selectors_data.get("aria"):
            score = cls._score_browser_selector(SelectorType.ARIA, aria_xpath, element_data)
            strategies.append(
                SelectorStrategy(
                    selector_type=SelectorType.ARIA,
                    value=aria_xpath,
                    target=SelectorTarget.BROWSER,
                    score=score,
                )
            )

        # 4. CSS selector
        if css := selectors_data.get("css"):
            score = cls._score_browser_selector(SelectorType.CSS, css, element_data)
            strategies.append(
                SelectorStrategy(
                    selector_type=SelectorType.CSS,
                    value=css,
                    target=SelectorTarget.BROWSER,
                    score=score,
                )
            )

        strategies.sort(key=lambda s: -s.score)
        fingerprint.selectors = strategies[:5]
        return fingerprint

    @classmethod
    def generate_desktop_fingerprint(cls, element_data: Dict[str, Any]) -> ElementFingerprint:
        """Generate multiple selector strategies from desktop element data (UIA)."""
        fingerprint = ElementFingerprint(
            target=SelectorTarget.DESKTOP,
            tag_name=element_data.get("ControlType", ""),
            element_id=element_data.get("AutomationId"),
            name=element_data.get("Name"),
            class_names=[element_data.get("ClassName")] if element_data.get("ClassName") else [],
            attributes=element_data,
        )

        strategies = []

        if auto_id := element_data.get("AutomationId"):
            strategies.append(
                SelectorStrategy(
                    selector_type=SelectorType.UIA_AUTOMATION_ID,
                    value=auto_id,
                    target=SelectorTarget.DESKTOP,
                    score=cls.DESKTOP_SCORES[SelectorType.UIA_AUTOMATION_ID],
                )
            )

        if name := element_data.get("Name"):
            strategies.append(
                SelectorStrategy(
                    selector_type=SelectorType.UIA_NAME,
                    value=name,
                    target=SelectorTarget.DESKTOP,
                    score=cls.DESKTOP_SCORES[SelectorType.UIA_NAME],
                )
            )

        if cls_name := element_data.get("ClassName"):
            strategies.append(
                SelectorStrategy(
                    selector_type=SelectorType.UIA_CLASS_NAME,
                    value=cls_name,
                    target=SelectorTarget.DESKTOP,
                    score=cls.DESKTOP_SCORES[SelectorType.UIA_CLASS_NAME],
                )
            )

        if ctrl_type := element_data.get("ControlType"):
            strategies.append(
                SelectorStrategy(
                    selector_type=SelectorType.UIA_CONTROL_TYPE,
                    value=ctrl_type,
                    target=SelectorTarget.DESKTOP,
                    score=cls.DESKTOP_SCORES[SelectorType.UIA_CONTROL_TYPE],
                )
            )

        strategies.sort(key=lambda s: -s.score)
        fingerprint.selectors = strategies
        return fingerprint

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _optimize_xpath(xpath: str) -> str:
        """Optimize XPath for better performance."""
        xpath = re.sub(r"\[1\]", "", xpath)
        xpath = re.sub(r"/{3,}", "//", xpath)
        return xpath

    @staticmethod
    def _score_browser_selector(
        selector_type: SelectorType, selector_value: str, element_data: Dict
    ) -> float:
        """Score a browser selector based on uniqueness and stability."""
        base_score = SelectorService.BROWSER_SCORES.get(selector_type, 50)
        if "id=" in selector_value or "@id" in selector_value:
            base_score += 10
        if "data-" in selector_value:
            base_score += 8
        if re.search(r"\[\d+\]", selector_value):
            base_score -= 15
        if (
            selector_type == SelectorType.CSS
            and "." in selector_value
            and "#" not in selector_value
        ):
            base_score -= 10
        if len(selector_value) > 100:
            base_score -= 10
        return max(0, min(100, base_score))

    @staticmethod
    def calculate_similarity(fp1: ElementFingerprint, fp2: ElementFingerprint) -> float:
        """Calculate similarity between two element fingerprints (0.0-1.0)."""
        if fp1.target != fp2.target:
            return 0.0

        score = 0.0
        weights = 0.0

        if fp1.tag_name == fp2.tag_name:
            score += 30
        weights += 30

        if fp1.element_id and fp2.element_id:
            if fp1.element_id == fp2.element_id:
                score += 20
            weights += 20

        if fp1.name and fp2.name:
            if fp1.name == fp2.name:
                score += 15
            weights += 15

        if fp1.rect and fp2.rect:
            x_diff = abs(fp1.rect.get("x", 0) - fp2.rect.get("x", 0))
            y_diff = abs(fp1.rect.get("y", 0) - fp2.rect.get("y", 0))
            if x_diff < 50 and y_diff < 50:
                score += 15
            weights += 15

        if fp1.text_content and fp2.text_content:
            text1, text2 = fp1.text_content.lower(), fp2.text_content.lower()
            if text1 in text2 or text2 in text1:
                score += 20
            weights += 20

        return score / weights if weights > 0 else 0.0


# Backward compatibility alias
SmartSelectorGenerator = SelectorService
