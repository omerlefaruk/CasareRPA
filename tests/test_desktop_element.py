"""
Unit tests for Desktop Element

Tests element interaction, property access, and element finding.
"""

import pytest
import time
from casare_rpa.desktop import DesktopContext, DesktopElement
import uiautomation as auto


class TestDesktopElement:
    """Test suite for DesktopElement class."""
    
    @pytest.fixture
    def calculator_window(self):
        """Fixture to launch Calculator and return its window."""
        context = DesktopContext()
        window = context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
        
        yield window
        
        # Cleanup
        try:
            context.close_application(window, force=True)
        except:
            pass
    
    def test_element_initialization(self, calculator_window):
        """Test DesktopElement initialization."""
        assert calculator_window is not None
        assert isinstance(calculator_window, DesktopElement)
        assert calculator_window._control is not None
    
    def test_element_initialization_invalid_type(self):
        """Test that DesktopElement rejects non-Control objects."""
        with pytest.raises(TypeError):
            DesktopElement("not a control")
    
    def test_get_text(self, calculator_window):
        """Test getting element text."""
        text = calculator_window.get_text()
        assert isinstance(text, str)
        assert len(text) > 0
        assert "Calculator" in text or "Calc" in text
    
    def test_get_property(self, calculator_window):
        """Test getting element properties."""
        # Test Name property
        name = calculator_window.get_property("Name")
        assert isinstance(name, str)
        assert len(name) > 0
        
        # Test AutomationId property
        automation_id = calculator_window.get_property("AutomationId")
        # May be None or a string
        assert automation_id is None or isinstance(automation_id, str)
        
        # Test ControlTypeName property
        control_type = calculator_window.get_property("ControlTypeName")
        assert control_type == "WindowControl"
    
    def test_exists(self, calculator_window):
        """Test checking if element exists."""
        assert calculator_window.exists() is True
    
    def test_is_enabled(self, calculator_window):
        """Test checking if element is enabled."""
        # Window should be enabled
        assert calculator_window.is_enabled() is True
    
    def test_is_visible(self, calculator_window):
        """Test checking if element is visible."""
        # Window should be visible
        assert calculator_window.is_visible() is True
    
    def test_get_bounding_rect(self, calculator_window):
        """Test getting element bounding rectangle."""
        rect = calculator_window.get_bounding_rect()
        
        assert isinstance(rect, dict)
        assert 'left' in rect
        assert 'top' in rect
        assert 'width' in rect
        assert 'height' in rect
        
        # Rectangle should have reasonable dimensions
        assert rect['width'] > 0
        assert rect['height'] > 0
    
    def test_find_child_element(self, calculator_window):
        """Test finding a child element."""
        # Find the "One" button in Calculator
        selector = {
            "strategy": "name",
            "value": "One"
        }
        
        button = calculator_window.find_child(selector, timeout=5.0)
        
        assert button is not None
        assert isinstance(button, DesktopElement)
        
        # Verify it's the right button
        text = button.get_text()
        assert "One" in text or "1" in text
    
    def test_click_button(self, calculator_window):
        """Test clicking a button element."""
        # Find and click the "One" button
        selector = {
            "strategy": "name",
            "value": "One"
        }
        
        button = calculator_window.find_child(selector, timeout=5.0)
        assert button is not None
        
        # Click the button
        result = button.click()
        assert result is True
        
        time.sleep(0.2)  # Give Calculator time to register click
    
    def test_element_repr(self, calculator_window):
        """Test element string representation."""
        repr_str = repr(calculator_window)
        
        assert isinstance(repr_str, str)
        assert "DesktopElement" in repr_str
        assert "WindowControl" in repr_str


class TestDesktopElementNotepad:
    """Test suite for DesktopElement with Notepad (text input testing)."""
    
    @pytest.fixture
    def notepad_window(self):
        """Fixture to launch Notepad and return its window."""
        context = DesktopContext()
        window = context.launch_application("notepad.exe", timeout=10.0, window_title="Notepad")
        
        yield window, context
        
        # Cleanup - close without saving
        try:
            # Send Alt+F4 then N (don't save)
            window._control.SendKeys('{Alt}F4')
            time.sleep(0.3)
            window._control.SendKeys('n')
            time.sleep(0.3)
        except:
            pass
        
        try:
            context.close_application(window, force=True)
        except:
            pass
    
    def test_type_text_in_notepad(self, notepad_window):
        """Test typing text into Notepad."""
        window, context = notepad_window
        
        # Find the text edit area
        time.sleep(0.5)  # Wait for Notepad to fully initialize
        
        selector = {
            "strategy": "control_type",
            "value": "Edit"
        }
        
        text_box = window.find_child(selector, timeout=5.0)
        assert text_box is not None
        
        # Type some text
        test_text = "Hello from CasareRPA Desktop Automation!"
        result = text_box.type_text(test_text, clear_first=True)
        assert result is True
        
        time.sleep(0.3)
        
        # Verify text was typed
        actual_text = text_box.get_text()
        assert test_text in actual_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
