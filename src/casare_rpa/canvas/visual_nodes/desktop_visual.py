"""
Visual Node Definitions for Desktop Automation

Defines the visual appearance and styling for desktop automation nodes.
"""

from NodeGraphQt import BaseNode


class DesktopFindElementNode(BaseNode):
    """Visual node for Find Element (Desktop)"""

    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Find Element'

    def __init__(self):
        super().__init__()

        # Visual styling - Desktop nodes use purple/lavender theme
        self.set_color(138, 43, 226)  # Blue-violet
        self.set_border_color(75, 0, 130)  # Indigo

        # Input ports
        self.add_input('window', color=(138, 43, 226))
        self.add_text_input('selector_json', 'Selector (JSON)', tab='inputs')

        # Output ports
        self.add_output('element', color=(138, 43, 226))
        self.add_output('found', color=(138, 43, 226))

        # Properties
        self.create_property('timeout', 5.0, widget_type=2, tab='config')  # FloatSpinBox
        self.create_property('throw_on_not_found', True, widget_type=1, tab='config')  # Checkbox


class DesktopClickElementNode(BaseNode):
    """Visual node for Click Element (Desktop)"""

    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Click Element'

    def __init__(self):
        super().__init__()

        # Visual styling
        self.set_color(138, 43, 226)  # Blue-violet
        self.set_border_color(75, 0, 130)  # Indigo

        # Input ports
        self.add_input('element', color=(138, 43, 226))
        self.add_input('window', color=(138, 43, 226))
        self.add_text_input('selector_json', 'Selector (JSON)', tab='inputs')

        # Output ports
        self.add_output('success', color=(138, 43, 226))

        # Properties
        self.create_property('simulate', False, widget_type=1, tab='config')  # Checkbox
        self.create_property('x_offset', 0, widget_type=2, tab='config')  # FloatSpinBox
        self.create_property('y_offset', 0, widget_type=2, tab='config')  # FloatSpinBox
        self.create_property('timeout', 5.0, widget_type=2, tab='config')  # FloatSpinBox


class DesktopTypeTextNode(BaseNode):
    """Visual node for Type Text (Desktop)"""

    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Type Text'

    def __init__(self):
        super().__init__()

        # Visual styling
        self.set_color(138, 43, 226)  # Blue-violet
        self.set_border_color(75, 0, 130)  # Indigo

        # Input ports
        self.add_input('element', color=(138, 43, 226))
        self.add_input('window', color=(138, 43, 226))
        self.add_text_input('selector_json', 'Selector (JSON)', tab='inputs')
        self.add_text_input('text', 'Text to Type', tab='inputs')

        # Output ports
        self.add_output('success', color=(138, 43, 226))

        # Properties
        self.create_property('clear_first', False, widget_type=1, tab='config')  # Checkbox
        self.create_property('interval', 0.01, widget_type=2, tab='config')  # FloatSpinBox
        self.create_property('timeout', 5.0, widget_type=2, tab='config')  # FloatSpinBox


class DesktopGetElementTextNode(BaseNode):
    """Visual node for Get Element Text (Desktop)"""

    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Get Element Text'

    def __init__(self):
        super().__init__()

        # Visual styling
        self.set_color(138, 43, 226)  # Blue-violet
        self.set_border_color(75, 0, 130)  # Indigo

        # Input ports
        self.add_input('element', color=(138, 43, 226))
        self.add_input('window', color=(138, 43, 226))
        self.add_text_input('selector_json', 'Selector (JSON)', tab='inputs')

        # Output ports
        self.add_output('text', color=(138, 43, 226))
        self.add_output('element', color=(138, 43, 226))

        # Properties
        self.create_property('timeout', 5.0, widget_type=2, tab='config')  # FloatSpinBox
        self.create_property('variable_name', '', widget_type=0, tab='config')  # TextInput


class DesktopGetElementPropertyNode(BaseNode):
    """Visual node for Get Element Property (Desktop)"""

    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Get Element Property'

    def __init__(self):
        super().__init__()

        # Visual styling
        self.set_color(138, 43, 226)  # Blue-violet
        self.set_border_color(75, 0, 130)  # Indigo

        # Input ports
        self.add_input('element', color=(138, 43, 226))
        self.add_input('window', color=(138, 43, 226))
        self.add_text_input('selector_json', 'Selector (JSON)', tab='inputs')
        self.add_text_input('property_name_input', 'Property Name', tab='inputs')

        # Output ports
        self.add_output('value', color=(138, 43, 226))
        self.add_output('element', color=(138, 43, 226))

        # Properties
        self.create_property('timeout', 5.0, widget_type=2, tab='config')  # FloatSpinBox
        self.create_property('property_name', 'Name', widget_type=0, tab='config')  # TextInput


class DesktopLaunchApplicationNode(BaseNode):
    """Visual node for Launch Application"""
    
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Launch Application'
    
    def __init__(self):
        super().__init__()
        
        # Visual styling - Desktop nodes use purple/lavender theme
        self.set_color(138, 43, 226)  # Blue-violet
        self.set_border_color(75, 0, 130)  # Indigo
        
        # Input ports
        self.add_text_input('application_path', 'Application Path', tab='inputs')
        self.add_text_input('arguments', 'Arguments', tab='inputs')
        self.add_text_input('working_directory', 'Working Directory', tab='inputs')
        
        # Output ports
        self.add_output('window', color=(138, 43, 226))
        self.add_output('process_id', color=(138, 43, 226))
        self.add_output('window_title', color=(138, 43, 226))
        
        # Properties
        self.create_property('timeout', 10.0, widget_type=2, tab='config')  # FloatSpinBox
        self.create_property('window_title_hint', '', widget_type=0, tab='config')  # TextInput
        self.create_property('window_state', 'normal', 
                           items=['normal', 'maximized', 'minimized'],
                           widget_type=3, tab='config')  # ComboBox


class DesktopCloseApplicationNode(BaseNode):
    """Visual node for Close Application"""
    
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Close Application'
    
    def __init__(self):
        super().__init__()
        
        # Visual styling
        self.set_color(138, 43, 226)  # Blue-violet
        self.set_border_color(75, 0, 130)  # Indigo
        
        # Input ports
        self.add_input('window', color=(138, 43, 226))
        self.add_input('process_id', color=(138, 43, 226))
        self.add_text_input('window_title', 'Window Title', tab='inputs')
        
        # Output ports
        self.add_output('success', color=(138, 43, 226))
        
        # Properties
        self.create_property('force_close', False, widget_type=1, tab='config')  # Checkbox
        self.create_property('timeout', 5.0, widget_type=2, tab='config')  # FloatSpinBox


class DesktopActivateWindowNode(BaseNode):
    """Visual node for Activate Window"""
    
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Activate Window'
    
    def __init__(self):
        super().__init__()
        
        # Visual styling
        self.set_color(138, 43, 226)  # Blue-violet
        self.set_border_color(75, 0, 130)  # Indigo
        
        # Input ports
        self.add_input('window', color=(138, 43, 226))
        self.add_text_input('window_title', 'Window Title', tab='inputs')
        
        # Output ports
        self.add_output('success', color=(138, 43, 226))
        self.add_output('window', color=(138, 43, 226))
        
        # Properties
        self.create_property('match_partial', True, widget_type=1, tab='config')  # Checkbox
        self.create_property('timeout', 5.0, widget_type=2, tab='config')  # FloatSpinBox


class DesktopGetWindowListNode(BaseNode):
    """Visual node for Get Window List"""
    
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Get Window List'
    
    def __init__(self):
        super().__init__()
        
        # Visual styling
        self.set_color(138, 43, 226)  # Blue-violet
        self.set_border_color(75, 0, 130)  # Indigo
        
        # Output ports
        self.add_output('window_list', color=(138, 43, 226))
        self.add_output('window_count', color=(138, 43, 226))
        
        # Properties
        self.create_property('include_invisible', False, widget_type=1, tab='config')  # Checkbox
        self.create_property('filter_title', '', widget_type=0, tab='config')  # TextInput
