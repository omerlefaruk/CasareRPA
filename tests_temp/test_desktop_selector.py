"""
Unit tests for Desktop Selector System

Tests selector parsing, validation, and element finding strategies.
"""

import pytest
from casare_rpa.desktop import DesktopContext, parse_selector


class TestSelectorParsing:
    """Test suite for selector parsing and validation."""
    
    def test_parse_valid_selector_control_type(self):
        """Test parsing a valid control_type selector."""
        selector = {
            "strategy": "control_type",
            "value": "Button"
        }
        
        parsed = parse_selector(selector)
        
        assert parsed["strategy"] == "control_type"
        assert parsed["value"] == "Button"
        assert parsed["properties"] == {}
    
    def test_parse_valid_selector_name(self):
        """Test parsing a valid name selector."""
        selector = {
            "strategy": "name",
            "value": "OK"
        }
        
        parsed = parse_selector(selector)
        
        assert parsed["strategy"] == "name"
        assert parsed["value"] == "OK"
    
    def test_parse_selector_with_properties(self):
        """Test parsing selector with additional properties."""
        selector = {
            "strategy": "control_type",
            "value": "Button",
            "properties": {
                "Name": "Submit",
                "AutomationId": "btnSubmit"
            }
        }
        
        parsed = parse_selector(selector)
        
        assert parsed["strategy"] == "control_type"
        assert parsed["value"] == "Button"
        assert parsed["properties"]["Name"] == "Submit"
        assert parsed["properties"]["AutomationId"] == "btnSubmit"
    
    def test_parse_selector_missing_strategy(self):
        """Test that selector without strategy raises ValueError."""
        selector = {
            "value": "Button"
        }
        
        with pytest.raises(ValueError, match="must have 'strategy'"):
            parse_selector(selector)
    
    def test_parse_selector_missing_value(self):
        """Test that selector without value raises ValueError."""
        selector = {
            "strategy": "control_type"
        }
        
        with pytest.raises(ValueError, match="must have 'value'"):
            parse_selector(selector)
    
    def test_parse_selector_invalid_strategy(self):
        """Test that invalid strategy raises ValueError."""
        selector = {
            "strategy": "invalid_strategy",
            "value": "Something"
        }
        
        with pytest.raises(ValueError, match="Invalid strategy"):
            parse_selector(selector)
    
    def test_parse_selector_not_dict(self):
        """Test that non-dict selector raises ValueError."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            parse_selector("not a dict")
    
    def test_parse_selector_all_strategies(self):
        """Test parsing all valid selector strategies."""
        strategies = ["control_type", "name", "automation_id", "class_name", "xpath"]
        
        for strategy in strategies:
            selector = {
                "strategy": strategy,
                "value": "TestValue"
            }
            
            parsed = parse_selector(selector)
            assert parsed["strategy"] == strategy


class TestElementFinding:
    """Test suite for element finding with selectors."""
    
    @pytest.fixture
    def calculator_window(self):
        """Fixture to launch Calculator."""
        context = DesktopContext()
        window = context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
        
        yield window, context
        
        # Cleanup
        try:
            context.close_application(window, force=True)
        except:
            pass
    
    def test_find_element_by_name(self, calculator_window):
        """Test finding element by name."""
        window, context = calculator_window
        
        selector = {
            "strategy": "name",
            "value": "One"
        }
        
        element = window.find_child(selector, timeout=5.0)
        
        assert element is not None
        text = element.get_text()
        assert "One" in text or "1" in text
    
    def test_find_element_by_control_type(self, calculator_window):
        """Test finding element by control type."""
        window, context = calculator_window
        
        selector = {
            "strategy": "control_type",
            "value": "Button"
        }
        
        # Should find at least one button in Calculator
        element = window.find_child(selector, timeout=5.0)
        assert element is not None
    
    def test_find_element_not_found(self, calculator_window):
        """Test that finding non-existent element raises ValueError."""
        window, context = calculator_window
        
        selector = {
            "strategy": "name",
            "value": "NonExistentElement12345"
        }
        
        with pytest.raises(ValueError, match="Element not found"):
            window.find_child(selector, timeout=1.0)
    
    def test_find_elements_multiple(self, calculator_window):
        """Test finding multiple elements."""
        window, context = calculator_window
        
        selector = {
            "strategy": "control_type",
            "value": "Button"
        }
        
        elements = window.find_children(selector)
        
        assert isinstance(elements, list)
        assert len(elements) > 0  # Calculator has many buttons


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
