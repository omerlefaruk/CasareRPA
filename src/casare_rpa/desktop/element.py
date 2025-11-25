"""
Desktop Element - Wrapper for UI Automation controls

Provides simplified API for interacting with Windows UI elements.
Includes stale element detection and automatic recovery.
"""

import time
from typing import Any, List, Optional, Dict, Callable, TypeVar
from functools import wraps
from loguru import logger
import uiautomation as auto


T = TypeVar("T")


class StaleElementError(Exception):
    """Raised when an element is no longer valid in the UI tree."""
    pass


def with_stale_check(method: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that checks for stale elements before executing a method.

    If the element is stale, attempts to re-find it using stored locator info.
    """
    @wraps(method)
    def wrapper(self: "DesktopElement", *args: Any, **kwargs: Any) -> T:
        if not self._validate_element():
            if not self._try_recover():
                raise StaleElementError(
                    f"Element is stale and could not be recovered: {self._locator_info}"
                )
        return method(self, *args, **kwargs)
    return wrapper


class DesktopElement:
    """
    Wrapper around UI Automation Control with simplified API.
    
    Provides methods to interact with desktop UI elements (click, type, read text, etc.)
    """
    
    def __init__(
        self,
        control: auto.Control,
        locator_info: Optional[Dict[str, Any]] = None,
        parent: Optional["DesktopElement"] = None
    ):
        """
        Initialize DesktopElement wrapper.

        Args:
            control: UI Automation Control object
            locator_info: Optional locator info for re-finding stale elements
            parent: Optional parent element for relative re-finding
        """
        if not isinstance(control, auto.Control):
            raise TypeError(f"Expected uiautomation.Control, got {type(control)}")

        self._control = control
        self._parent = parent
        self._last_validated = time.time()
        self._validation_cache_ttl = 0.5  # Cache validation for 500ms

        # Store locator info for stale element recovery
        self._locator_info = locator_info or self._capture_locator_info()

        logger.debug(f"DesktopElement created: {self._control.ControlTypeName} - '{self._control.Name}'")
    
    def _capture_locator_info(self) -> Dict[str, Any]:
        """Capture identifying information for re-finding this element."""
        try:
            return {
                "name": self._control.Name or "",
                "automation_id": self._control.AutomationId or "",
                "control_type": self._control.ControlTypeName or "",
                "class_name": self._control.ClassName or "",
                "process_id": getattr(self._control, "ProcessId", 0),
            }
        except Exception as e:
            logger.warning(f"Failed to capture locator info: {e}")
            return {}

    def _validate_element(self) -> bool:
        """
        Validate that the element is still valid in the UI tree.

        Uses caching to avoid excessive validation calls.
        """
        now = time.time()
        if now - self._last_validated < self._validation_cache_ttl:
            return True  # Use cached result

        try:
            # Try to access a basic property - if it fails, element is stale
            _ = self._control.Name
            _ = self._control.BoundingRectangle

            # Check if element still exists
            if not self._control.Exists(0, 0):
                logger.debug("Element validation failed: Exists() returned False")
                return False

            self._last_validated = now
            return True

        except Exception as e:
            logger.debug(f"Element validation failed: {e}")
            return False

    def _try_recover(self) -> bool:
        """
        Attempt to recover a stale element by re-finding it.

        Returns:
            True if element was successfully recovered
        """
        if not self._locator_info:
            logger.warning("Cannot recover element: no locator info available")
            return False

        logger.info(f"Attempting to recover stale element: {self._locator_info}")

        try:
            # Build search criteria from locator info
            search_kwargs = {}

            if self._locator_info.get("automation_id"):
                search_kwargs["AutomationId"] = self._locator_info["automation_id"]
            if self._locator_info.get("name"):
                search_kwargs["Name"] = self._locator_info["name"]
            if self._locator_info.get("control_type"):
                # Map control type name to Control class
                control_type_map = {
                    "ButtonControl": auto.ButtonControl,
                    "EditControl": auto.EditControl,
                    "TextControl": auto.TextControl,
                    "WindowControl": auto.WindowControl,
                    "ListControl": auto.ListControl,
                    "ListItemControl": auto.ListItemControl,
                    "TreeControl": auto.TreeControl,
                    "TreeItemControl": auto.TreeItemControl,
                    "CheckBoxControl": auto.CheckBoxControl,
                    "RadioButtonControl": auto.RadioButtonControl,
                    "ComboBoxControl": auto.ComboBoxControl,
                    "MenuControl": auto.MenuControl,
                    "MenuItemControl": auto.MenuItemControl,
                    "TabControl": auto.TabControl,
                    "TabItemControl": auto.TabItemControl,
                }
                control_class = control_type_map.get(
                    self._locator_info["control_type"],
                    auto.Control
                )
            else:
                control_class = auto.Control

            # Search from parent or root
            if self._parent and self._parent._validate_element():
                search_root = self._parent._control
            else:
                search_root = auto.GetRootControl()

            # Attempt to find the element
            if search_kwargs:
                new_control = control_class(searchFromControl=search_root, **search_kwargs)
                if new_control.Exists(1, 0.5):  # Wait up to 1 second
                    self._control = new_control
                    self._last_validated = time.time()
                    logger.info("Successfully recovered stale element")
                    return True

            logger.warning("Failed to recover stale element: element not found")
            return False

        except Exception as e:
            logger.error(f"Error recovering stale element: {e}")
            return False

    def is_stale(self) -> bool:
        """
        Check if the element is stale (no longer valid).

        Returns:
            True if element is stale, False if still valid
        """
        return not self._validate_element()

    def refresh(self) -> bool:
        """
        Force refresh the element reference.

        Useful when you know the element has changed but want to get
        the updated version.

        Returns:
            True if element was successfully refreshed
        """
        # Invalidate cache
        self._last_validated = 0
        return self._try_recover()

    @with_stale_check
    def click(self, simulate: bool = False, x_offset: int = 0, y_offset: int = 0) -> bool:
        """
        Click the element.

        Args:
            simulate: If True, use simulated click; if False, use actual mouse click
            x_offset: X offset from element center
            y_offset: Y offset from element center

        Returns:
            True if click was successful

        Raises:
            RuntimeError: If click fails
            StaleElementError: If element is stale and cannot be recovered
        """
        logger.debug(f"Clicking element: {self._control.Name} (simulate={simulate})")
        
        try:
            # Try to use InvokePattern first (most reliable for buttons)
            if not simulate:
                try:
                    invoke_pattern = self._control.GetInvokePattern()
                    if invoke_pattern:
                        invoke_pattern.Invoke()
                        logger.info(f"Clicked element using InvokePattern: {self._control.Name}")
                        return True
                except:
                    pass
            
            # Fallback to mouse click
            rect = self._control.BoundingRectangle
            if rect.width() > 0 and rect.height() > 0:
                center_x = rect.left + rect.width() // 2 + x_offset
                center_y = rect.top + rect.height() // 2 + y_offset
                
                if simulate:
                    self._control.Click(simulateMove=True, x=center_x, y=center_y)
                else:
                    self._control.Click(simulateMove=False, x=center_x, y=center_y)
                
                logger.info(f"Clicked element at ({center_x}, {center_y}): {self._control.Name}")
                return True
            else:
                raise RuntimeError(f"Element has invalid bounds: {rect}")
                
        except Exception as e:
            error_msg = f"Failed to click element '{self._control.Name}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    @with_stale_check
    def type_text(self, text: str, clear_first: bool = False, interval: float = 0.01) -> bool:
        """
        Type text into the element.
        
        Args:
            text: Text to type
            clear_first: If True, clear existing text before typing
            interval: Interval between keystrokes in seconds
            
        Returns:
            True if typing was successful
            
        Raises:
            RuntimeError: If typing fails
        """
        logger.debug(f"Typing text into element: {self._control.Name}")
        
        try:
            # Set focus first
            self._control.SetFocus()
            
            # Clear existing text if requested
            if clear_first:
                try:
                    # Try using ValuePattern first
                    value_pattern = self._control.GetValuePattern()
                    if value_pattern:
                        value_pattern.SetValue("")
                except:
                    # Fallback: select all and delete
                    self._control.SendKeys('{Ctrl}a{Delete}')
            
            # Type the text
            if text:
                # Try using ValuePattern for direct value setting (faster)
                try:
                    value_pattern = self._control.GetValuePattern()
                    if value_pattern and not value_pattern.IsReadOnly:
                        value_pattern.SetValue(text)
                        logger.info(f"Set text using ValuePattern: '{text[:50]}...'")
                        return True
                except:
                    pass
                
                # Fallback: send keys
                self._control.SendKeys(text, interval=interval)
                logger.info(f"Typed text using SendKeys: '{text[:50]}...'")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to type text into element '{self._control.Name}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    @with_stale_check
    def get_text(self) -> str:
        """
        Get the text content of the element.
        
        Returns:
            Element text (Name property by default)
        """
        try:
            # Try ValuePattern first (for textboxes)
            try:
                value_pattern = self._control.GetValuePattern()
                if value_pattern:
                    text = value_pattern.Value
                    if text:
                        return text
            except:
                pass
            
            # Try Name property
            if self._control.Name:
                return self._control.Name
            
            # Try LegacyValue
            try:
                legacy_pattern = self._control.GetLegacyIAccessiblePattern()
                if legacy_pattern and legacy_pattern.Value:
                    return legacy_pattern.Value
            except:
                pass
            
            # Return empty string if no text found
            return ""
            
        except Exception as e:
            logger.warning(f"Failed to get text from element: {e}")
            return ""

    @with_stale_check
    def get_property(self, property_name: str) -> Any:
        """
        Get an element property by name.
        
        Args:
            property_name: Property name (e.g., "Name", "AutomationId", "ControlType")
            
        Returns:
            Property value, or None if property doesn't exist
        """
        try:
            return getattr(self._control, property_name, None)
        except Exception as e:
            logger.warning(f"Failed to get property '{property_name}': {e}")
            return None
    
    def find_child(self, selector: Dict[str, Any], timeout: float = 5.0) -> Optional["DesktopElement"]:
        """
        Find a child element using selector.
        
        Args:
            selector: Selector dictionary
            timeout: Maximum time to wait for element
            
        Returns:
            DesktopElement if found, None otherwise
        """
        from .selector import find_element
        return find_element(self._control, selector, timeout=timeout)
    
    def find_children(self, selector: Dict[str, Any]) -> List["DesktopElement"]:
        """
        Find all child elements matching selector.
        
        Args:
            selector: Selector dictionary
            
        Returns:
            List of DesktopElement objects
        """
        from .selector import find_elements
        return find_elements(self._control, selector)
    
    def exists(self) -> bool:
        """
        Check if element still exists in UI tree.
        
        Returns:
            True if element exists
        """
        try:
            return self._control.Exists(0, 0)
        except:
            return False
    
    def is_enabled(self) -> bool:
        """Check if element is enabled."""
        try:
            return self._control.IsEnabled
        except:
            return False
    
    def is_visible(self) -> bool:
        """Check if element is visible."""
        try:
            return self._control.IsOffscreen == False
        except:
            return False
    
    def get_bounding_rect(self) -> Dict[str, int]:
        """
        Get element's bounding rectangle.
        
        Returns:
            Dictionary with keys: left, top, right, bottom, width, height
        """
        try:
            rect = self._control.BoundingRectangle
            return {
                'left': rect.left,
                'top': rect.top,
                'right': rect.right,
                'bottom': rect.bottom,
                'width': rect.width(),
                'height': rect.height()
            }
        except Exception as e:
            logger.warning(f"Failed to get bounding rect: {e}")
            return {'left': 0, 'top': 0, 'right': 0, 'bottom': 0, 'width': 0, 'height': 0}
    
    def __repr__(self) -> str:
        """String representation of element."""
        try:
            return f"DesktopElement({self._control.ControlTypeName}: '{self._control.Name}')"
        except:
            return "DesktopElement(<invalid>)"
