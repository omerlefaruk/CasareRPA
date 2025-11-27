"""
Smart Selector Generator with Self-Healing Capabilities
Prioritizes XPath, then fallback to other strategies
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import re


class SelectorType(Enum):
    """Types of selectors"""
    XPATH = "xpath"
    CSS = "css"
    ARIA = "aria"
    TEXT = "text"
    DATA_ATTR = "data_attr"
    

@dataclass
class SelectorStrategy:
    """A single selector strategy with metadata"""
    selector_type: SelectorType
    value: str
    score: float  # 0-100, higher is better
    is_unique: bool = False
    execution_time_ms: float = 0.0
    last_validated: Optional[float] = None
    failure_count: int = 0
    
    def __lt__(self, other):
        """Compare by score for sorting"""
        return self.score < other.score


@dataclass
class ElementFingerprint:
    """
    Stores multiple selector strategies for self-healing
    Top 5 ranked selectors with automatic fallback
    """
    tag_name: str
    element_id: Optional[str] = None
    class_names: List[str] = field(default_factory=list)
    text_content: Optional[str] = None
    attributes: Dict[str, str] = field(default_factory=dict)
    
    # Multiple selector strategies ranked by reliability
    selectors: List[SelectorStrategy] = field(default_factory=list)
    
    # Visual/structural fingerprint for similarity detection
    rect: Dict[str, float] = field(default_factory=dict)
    parent_tag: Optional[str] = None
    sibling_count: int = 0
    
    def get_primary_selector(self) -> Optional[SelectorStrategy]:
        """Get the best selector strategy"""
        if not self.selectors:
            return None
        return sorted(self.selectors, key=lambda s: (-s.score, s.failure_count))[0]
    
    def get_fallback_selectors(self) -> List[SelectorStrategy]:
        """Get all selectors except primary, sorted by reliability"""
        if len(self.selectors) <= 1:
            return []
        sorted_selectors = sorted(self.selectors, key=lambda s: (-s.score, s.failure_count))
        return sorted_selectors[1:]
    
    def promote_selector(self, selector: SelectorStrategy):
        """Promote a working fallback selector to primary"""
        if selector in self.selectors:
            selector.score += 10  # Boost score
            selector.failure_count = 0
    
    def demote_selector(self, selector: SelectorStrategy):
        """Demote a failing selector"""
        if selector in self.selectors:
            selector.failure_count += 1
            selector.score = max(0, selector.score - 5)


class SmartSelectorGenerator:
    """
    Generates multiple selector strategies with priority:
    1. XPath (optimized for uniqueness)
    2. CSS Selectors
    3. ARIA attributes
    4. Data attributes
    5. Text content
    """
    
    # Stability scores for different selector types
    TYPE_SCORES = {
        SelectorType.XPATH: 90,
        SelectorType.DATA_ATTR: 85,
        SelectorType.ARIA: 80,
        SelectorType.CSS: 70,
        SelectorType.TEXT: 50
    }
    
    @staticmethod
    def _optimize_xpath(xpath: str) -> str:
        """
        Optimize XPath for better performance and readability
        Remove unnecessary indices where possible
        """
        # Remove [1] indices (first child is default)
        xpath = re.sub(r'\[1\]', '', xpath)
        
        # Simplify double slashes
        xpath = re.sub(r'/{3,}', '//', xpath)
        
        return xpath
    
    @staticmethod
    def _score_selector(selector_type: SelectorType, selector_value: str, 
                       element_data: Dict) -> float:
        """
        Score a selector based on its uniqueness and stability
        Returns 0-100
        """
        base_score = SmartSelectorGenerator.TYPE_SCORES.get(selector_type, 50)
        
        # Bonus for unique IDs
        if 'id=' in selector_value or '@id' in selector_value:
            base_score += 10
        
        # Bonus for data attributes
        if 'data-' in selector_value:
            base_score += 8
        
        # Penalty for index-based selectors
        if re.search(r'\[\d+\]', selector_value):
            base_score -= 15
        
        # Penalty for class-only CSS selectors (fragile)
        if selector_type == SelectorType.CSS and '.' in selector_value and '#' not in selector_value:
            base_score -= 10
        
        # Penalty for very long selectors (complex = fragile)
        if len(selector_value) > 100:
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    @classmethod
    def generate_selectors(cls, element_data: Dict) -> ElementFingerprint:
        """
        Generate multiple selector strategies from element data
        Returns ElementFingerprint with ranked selectors
        """
        fingerprint = ElementFingerprint(
            tag_name=element_data.get('tagName', ''),
            element_id=element_data.get('id'),
            class_names=element_data.get('className', '').split() if element_data.get('className') else [],
            text_content=element_data.get('text'),
            attributes=element_data.get('attributes', {}),
            rect=element_data.get('rect', {})
        )
        
        selectors_data = element_data.get('selectors', {})
        strategies = []
        
        # 1. XPath (highest priority)
        if xpath := selectors_data.get('xpath'):
            optimized_xpath = cls._optimize_xpath(xpath)
            score = cls._score_selector(SelectorType.XPATH, optimized_xpath, element_data)
            strategies.append(SelectorStrategy(
                selector_type=SelectorType.XPATH,
                value=optimized_xpath,
                score=score
            ))
        
        # 2. Data attributes (very stable)
        for attr_name, attr_value in element_data.get('attributes', {}).items():
            if attr_name.startswith('data-'):
                xpath_data = f"//*[@{attr_name}='{attr_value}']"
                score = cls._score_selector(SelectorType.DATA_ATTR, xpath_data, element_data)
                strategies.append(SelectorStrategy(
                    selector_type=SelectorType.DATA_ATTR,
                    value=xpath_data,
                    score=score
                ))
        
        # 3. ARIA attributes
        if aria_xpath := selectors_data.get('aria'):
            score = cls._score_selector(SelectorType.ARIA, aria_xpath, element_data)
            strategies.append(SelectorStrategy(
                selector_type=SelectorType.ARIA,
                value=aria_xpath,
                score=score
            ))
        
        # 4. ARIA-label specifically
        if aria_label := element_data.get('attributes', {}).get('aria-label'):
            xpath_aria = f"//*[@aria-label='{aria_label}']"
            score = cls._score_selector(SelectorType.ARIA, xpath_aria, element_data)
            strategies.append(SelectorStrategy(
                selector_type=SelectorType.ARIA,
                value=xpath_aria,
                score=score
            ))
        
        # 5. CSS selector (fallback)
        if css := selectors_data.get('css'):
            score = cls._score_selector(SelectorType.CSS, css, element_data)
            strategies.append(SelectorStrategy(
                selector_type=SelectorType.CSS,
                value=css,
                score=score
            ))
        
        # 6. Text content (fuzzy matching capable)
        if text := selectors_data.get('text'):
            # Use XPath contains for partial text matching (self-healing)
            text_clean = text.replace("'", "\\'")[:50]  # Escape and limit
            xpath_text = f"//*[contains(text(), '{text_clean}')]"
            score = cls._score_selector(SelectorType.TEXT, xpath_text, element_data)
            strategies.append(SelectorStrategy(
                selector_type=SelectorType.TEXT,
                value=xpath_text,
                score=score
            ))
        
        # Sort by score and keep top 5
        strategies.sort(key=lambda s: -s.score)
        fingerprint.selectors = strategies[:5]
        
        return fingerprint
    
    @staticmethod
    def validate_selector_uniqueness(selector_value: str, 
                                     selector_type: SelectorType) -> bool:
        """
        Placeholder for selector uniqueness validation
        This would be called from Playwright to test against actual page
        """
        # This will be implemented in the Playwright integration
        return True
    
    @staticmethod
    def calculate_element_similarity(fp1: ElementFingerprint, 
                                     fp2: ElementFingerprint) -> float:
        """
        Calculate similarity between two element fingerprints
        Returns 0.0-1.0 (0=completely different, 1=identical)
        Used for self-healing when exact match fails
        """
        score = 0.0
        weights = 0.0
        
        # Tag name match (most important)
        if fp1.tag_name == fp2.tag_name:
            score += 30
        weights += 30
        
        # Position similarity (within 10% of original position)
        if fp1.rect and fp2.rect:
            x_diff = abs(fp1.rect.get('x', 0) - fp2.rect.get('x', 0))
            y_diff = abs(fp1.rect.get('y', 0) - fp2.rect.get('y', 0))
            if x_diff < 50 and y_diff < 50:
                score += 20
            weights += 20
        
        # Text content similarity (fuzzy)
        if fp1.text_content and fp2.text_content:
            text1 = fp1.text_content.lower()
            text2 = fp2.text_content.lower()
            if text1 in text2 or text2 in text1:
                score += 25
            weights += 25
        
        # Class names overlap
        if fp1.class_names and fp2.class_names:
            common_classes = set(fp1.class_names) & set(fp2.class_names)
            if common_classes:
                score += 15 * (len(common_classes) / max(len(fp1.class_names), len(fp2.class_names)))
            weights += 15
        
        # Attribute overlap
        if fp1.attributes and fp2.attributes:
            common_attrs = set(fp1.attributes.keys()) & set(fp2.attributes.keys())
            if common_attrs:
                score += 10 * (len(common_attrs) / max(len(fp1.attributes), len(fp2.attributes)))
            weights += 10
        
        return score / weights if weights > 0 else 0.0
