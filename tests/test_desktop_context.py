"""
Unit tests for Desktop Context

Tests window finding, application management, and desktop context functionality.
"""

import pytest
import time
import subprocess
from casare_rpa.desktop import DesktopContext


class TestDesktopContext:
    """Test suite for DesktopContext class."""
    
    def test_context_initialization(self):
        """Test that DesktopContext initializes correctly."""
        context = DesktopContext()
        assert context is not None
        assert context._launched_processes == []
    
    def test_context_manager(self):
        """Test DesktopContext as context manager."""
        with DesktopContext() as context:
            assert context is not None
    
    def test_find_window_not_found(self):
        """Test finding a window that doesn't exist raises ValueError."""
        context = DesktopContext()
        
        with pytest.raises(ValueError, match="Window not found"):
            context.find_window("NonExistentWindowTitle12345", exact=True, timeout=1.0)
    
    def test_launch_and_find_calculator(self):
        """Test launching Calculator and finding its window."""
        context = DesktopContext()
        
        try:
            # Launch Calculator
            window = context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
            
            assert window is not None
            assert "Calculator" in window.get_text() or "Calc" in window.get_text()
            
            # Verify we can find it again
            found_window = context.find_window("Calculator", exact=False, timeout=2.0)
            assert found_window is not None
            
        finally:
            # Clean up
            try:
                context.close_application(window, force=True)
            except:
                pass
    
    def test_launch_notepad(self):
        """Test launching Notepad."""
        context = DesktopContext()
        
        try:
            # Launch Notepad
            window = context.launch_application("notepad.exe", timeout=10.0, window_title="Notepad")
            
            assert window is not None
            window_text = window.get_text()
            assert "Notepad" in window_text or "Untitled" in window_text
            
        finally:
            # Clean up
            try:
                context.close_application(window, force=True)
            except:
                pass
    
    def test_get_all_windows(self):
        """Test getting all windows."""
        context = DesktopContext()
        
        # Get all windows
        windows = context.get_all_windows(include_invisible=False)
        
        assert isinstance(windows, list)
        assert len(windows) > 0  # Should have at least some windows
        
        # Each item should be a DesktopElement
        for window in windows:
            assert hasattr(window, '_control')
            assert hasattr(window, 'get_text')
    
    def test_close_application_graceful(self):
        """Test gracefully closing an application."""
        context = DesktopContext()
        
        try:
            # Launch Notepad
            window = context.launch_application("notepad.exe", timeout=10.0, window_title="Notepad")
            assert window.exists()
            
            # Close gracefully
            result = context.close_application(window, force=False, timeout=5.0)
            assert result is True
            
            # Give it a moment
            time.sleep(0.5)
            
            # Verify it's closed
            assert not window.exists()
            
        except Exception as e:
            # Cleanup if test fails
            try:
                context.close_application(window, force=True)
            except:
                pass
            raise e
    
    def test_close_application_force(self):
        """Test force-closing an application."""
        context = DesktopContext()
        
        try:
            # Launch Calculator
            window = context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
            assert window.exists()
            
            # Force close
            result = context.close_application(window, force=True, timeout=5.0)
            assert result is True
            
            # Give it a moment
            time.sleep(0.5)
            
            # Verify it's closed
            assert not window.exists()
            
        except Exception as e:
            # Cleanup if test fails
            try:
                context.close_application(window, force=True)
            except:
                pass
            raise e
    
    def test_context_cleanup(self):
        """Test that context cleanup closes launched applications."""
        context = DesktopContext()
        
        try:
            # Launch Calculator
            window = context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
            pid = context._launched_processes[0]
            
            # Cleanup
            context.cleanup()
            
            # Give it a moment
            time.sleep(1.0)
            
            # Verify Calculator is closed
            import psutil
            assert not psutil.pid_exists(pid) or not any(
                p.name().lower() == "calculator.exe" for p in psutil.process_iter(['name'])
            )
            
        except Exception as e:
            # Cleanup if test fails
            try:
                context.cleanup()
            except:
                pass
            raise e
    
    def test_find_window_partial_match(self):
        """Test finding window with partial title match."""
        context = DesktopContext()
        
        try:
            # Launch Calculator
            window = context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
            
            # Find with partial match
            found = context.find_window("Calc", exact=False, timeout=2.0)
            assert found is not None
            
        finally:
            try:
                context.close_application(window, force=True)
            except:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
