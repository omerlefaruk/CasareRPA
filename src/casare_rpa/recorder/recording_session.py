"""
Recording session for capturing user interactions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from loguru import logger


class ActionType(Enum):
    """Types of actions that can be recorded."""
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    NAVIGATE = "navigate"
    WAIT = "wait"


@dataclass
class RecordedAction:
    """Represents a single recorded action."""
    
    action_type: ActionType
    selector: str
    timestamp: datetime = field(default_factory=datetime.now)
    value: Optional[str] = None
    element_info: Dict[str, Any] = field(default_factory=dict)
    url: Optional[str] = None
    # Element metadata for better node naming
    element_text: Optional[str] = None
    element_id: Optional[str] = None
    element_tag: Optional[str] = None
    element_class: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary."""
        return {
            'action_type': self.action_type.value,
            'selector': self.selector,
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'element_info': self.element_info,
            'url': self.url,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecordedAction':
        """Create action from dictionary."""
        data['action_type'] = ActionType(data['action_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class RecordingSession:
    """Manages a recording session."""
    
    def __init__(self):
        """Initialize recording session."""
        self.actions: List[RecordedAction] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_recording = False
        self.is_paused = False
        
        logger.info("Recording session initialized")
    
    def start(self):
        """Start recording."""
        if self.is_recording:
            logger.warning("Recording session already started")
            return
        
        self.start_time = datetime.now()
        self.is_recording = True
        self.is_paused = False
        self.actions.clear()
        
        logger.info("Recording session started")
    
    def pause(self):
        """Pause recording."""
        if not self.is_recording:
            logger.warning("No recording session to pause")
            return
        
        self.is_paused = True
        logger.info("Recording session paused")
    
    def resume(self):
        """Resume recording."""
        if not self.is_recording:
            logger.warning("No recording session to resume")
            return
        
        self.is_paused = False
        logger.info("Recording session resumed")
    
    def stop(self):
        """Stop recording."""
        if not self.is_recording:
            logger.warning("No recording session to stop")
            return
        
        self.end_time = datetime.now()
        self.is_recording = False
        self.is_paused = False
        
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"Recording session stopped. Duration: {duration:.2f}s, Actions: {len(self.actions)}")
    
    def add_action(self, action: RecordedAction):
        """Add an action to the recording."""
        if not self.is_recording or self.is_paused:
            logger.debug("Ignoring action - recording not active or paused")
            return
        
        self.actions.append(action)
        logger.debug(f"Action recorded: {action.action_type.value} on {action.selector}")
    
    def get_actions(self) -> List[RecordedAction]:
        """Get all recorded actions."""
        return self.actions.copy()
    
    def clear(self):
        """Clear all recorded actions."""
        self.actions.clear()
        self.start_time = None
        self.end_time = None
        self.is_recording = False
        self.is_paused = False
        
        logger.info("Recording session cleared")
    
    def get_duration(self) -> float:
        """Get recording duration in seconds."""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time if self.end_time else datetime.now()
        return (end - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.get_duration(),
            'action_count': len(self.actions),
            'actions': [action.to_dict() for action in self.actions],
        }
