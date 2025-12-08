# System & Dialog Nodes Expansion Plan

## Overview
Implement 19 new nodes across Dialog, System, and Quick categories.

## Existing Nodes (Skip)
- Screenshot → CaptureScreenshotNode (desktop_nodes/screenshot_ocr_nodes.py)
- WindowFocus → ActivateWindowNode (desktop_nodes/application_nodes.py)
- WindowList → GetWindowListNode (desktop_nodes/application_nodes.py)
- WindowMinimize → MinimizeWindowNode (desktop_nodes/window_nodes.py)

## Nodes to Implement

### Dialog Nodes (9) → dialog_nodes.py
| Node | Purpose | Key Properties |
|------|---------|----------------|
| ListPickerDialogNode | Single/multi-select from list | items, multi_select, search_enabled |
| MultilineInputDialogNode | Multi-line text input | default_text, placeholder, max_chars |
| CredentialDialogNode | Username/password input | show_remember, mask_password |
| FormDialogNode | Custom form with fields | fields (JSON schema) |
| ImagePreviewDialogNode | Show image with OK/Cancel | image_path, scale, allow_zoom |
| TableDialogNode | Display tabular data | data, columns, selectable |
| WizardDialogNode | Multi-step wizard | steps (JSON), allow_back |
| SplashScreenNode | Splash with progress | image, message, duration, progress |
| AudioAlertNode | Play audio/beep | file_path, volume, loop |

### System Nodes (6) → system_nodes.py (new file)
| Node | Purpose | Key Properties |
|------|---------|----------------|
| ScreenRegionPickerNode | User selects screen region | default_region, show_crosshair |
| VolumeControlNode | Get/set system volume | action (get/set/mute), level |
| ProcessListNode | List running processes | filter_name, include_details |
| ProcessKillNode | Kill process | pid_or_name, force, timeout |
| EnvironmentVariableNode | Get/set env vars | action, name, value, scope |
| SystemInfoNode | Get system info | info_type (os/cpu/ram/disk/all) |

### Quick Nodes (3) → quick_nodes.py (new file)
| Node | Purpose | Key Properties |
|------|---------|----------------|
| HotkeyWaitNode | Wait for key combo | hotkey, timeout, consume_key |
| BeepNode | System beep | frequency, duration |
| ClipboardMonitorNode | Monitor clipboard | timeout, trigger_on_change |

## Implementation Order
1. Dialog nodes (add to existing dialog_nodes.py)
2. System nodes (new system_nodes.py)
3. Quick nodes (new quick_nodes.py)

## Registration Files (6)
1. `nodes/system/__init__.py` - Export new classes
2. `nodes/__init__.py` - Add to _NODE_REGISTRY
3. `utils/workflow/workflow_loader.py` - Add to NODE_TYPE_MAP
4. `visual_nodes/system/nodes.py` - Visual node classes
5. `visual_nodes/system/__init__.py` - Export visual classes
6. `visual_nodes/__init__.py` - Add to _VISUAL_NODE_REGISTRY

## Dependencies
- psutil: Process management, system info
- pycaw: Volume control (Windows)
- keyboard: Hotkey detection (or pynput)
- pyperclip: Clipboard monitoring
- winsound: Beep functionality
- pygame/playsound: Audio playback

## Notes
- All dialogs use asyncio.create_future() for non-blocking Qt
- System nodes require admin for some operations
- HotkeyWait should be interruptible with timeout
