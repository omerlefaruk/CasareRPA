# Google Drive Folder Navigator - Implementation Plan

## Overview
Replace the simple folder dropdown with a comprehensive folder navigation widget that supports:
1. Hierarchical folder browsing with drill-down
2. Flat list with full paths (recursive fetch)
3. Manual folder ID input
4. Search by folder name

## Architecture

### New Widget: `GoogleDriveFolderNavigator`

```
+------------------------------------------------------------------+
| Current Path: My Drive / Projects / 2024                    [<] |
+------------------------------------------------------------------+
| [Search folders...]                                              |
+------------------------------------------------------------------+
| [Folder] [Dropdown v]  [>] [ID]                                 |
| Selected: Projects/2024/Reports (1abc...xyz)                     |
+------------------------------------------------------------------+
```

**Components:**
1. **Path Breadcrumb** - Shows current navigation path, clickable segments
2. **Search Input** - Filter/search folders by name
3. **Folder Dropdown** - Shows folders at current level
4. **Navigation Buttons**:
   - `<` Back/Up - Go to parent folder
   - `>` Enter - Drill into selected folder
   - `ID` - Toggle manual ID input mode
5. **Selection Display** - Shows selected folder name and ID

### File Structure

```
src/casare_rpa/presentation/canvas/ui/widgets/
├── google_pickers.py                    # Existing - keep simple pickers
├── google_folder_navigator.py           # NEW - comprehensive navigator
└── google_folder_navigator_components.py # NEW - sub-components
```

### Classes

#### 1. `FolderNavigatorState` (dataclass)
```python
@dataclass
class FolderNavigatorState:
    current_folder_id: str = "root"
    current_path: List[Tuple[str, str]] = field(default_factory=list)  # [(id, name), ...]
    selected_folder_id: Optional[str] = None
    selected_folder_name: str = ""
    search_query: str = ""
    view_mode: str = "browse"  # "browse" | "search" | "manual"
```

#### 2. `GoogleDriveFolderNavigator` (QWidget)
Main widget that composes all sub-components.

**Signals:**
- `folder_selected(str)` - Emitted when folder is selected, passes folder_id
- `navigation_changed(str)` - Emitted when current browse location changes

**Methods:**
- `get_folder_id() -> Optional[str]`
- `set_folder_id(folder_id: str)`
- `refresh()`
- `navigate_to(folder_id: str)`
- `navigate_up()`
- `search(query: str)`

#### 3. `PathBreadcrumb` (QWidget)
Clickable breadcrumb showing current path.

```python
class PathBreadcrumb(QWidget):
    path_clicked = Signal(str, int)  # folder_id, depth

    def set_path(self, path: List[Tuple[str, str]]):
        """Update displayed path."""

    def _on_segment_clicked(self, folder_id: str, depth: int):
        """Handle click on path segment."""
```

#### 4. `FolderSearchInput` (QLineEdit)
Search input with debounced search trigger.

```python
class FolderSearchInput(QLineEdit):
    search_triggered = Signal(str)  # query

    def __init__(self, debounce_ms: int = 300):
        # Debounce typing to avoid excessive API calls
```

#### 5. `FolderListDropdown` (GraphicsSceneComboBox)
Enhanced dropdown that shows folders with indentation for hierarchy.

```python
class FolderListDropdown(GraphicsSceneComboBox):
    def set_folders(self, folders: List[DropdownItem], show_hierarchy: bool = False):
        """Populate with folders, optionally showing hierarchy."""
```

### API Integration

#### Recursive Folder Fetch
```python
async def fetch_folders_recursive(
    credential_id: str,
    parent_folder_id: str = "root",
    max_depth: int = 3,
    max_total: int = 500,
) -> List[FolderInfo]:
    """
    Fetch folders recursively up to max_depth levels.
    Returns flat list with path information.
    """
```

#### Search Folders
```python
async def search_folders(
    credential_id: str,
    query: str,
    max_results: int = 50,
) -> List[FolderInfo]:
    """
    Search folders by name across entire Drive.
    Uses: name contains 'query' and mimeType='folder'
    """
```

### Data Models

```python
@dataclass
class FolderInfo:
    id: str
    name: str
    path: str  # Full path like "My Drive/Projects/2024"
    parent_id: Optional[str]
    depth: int
    has_children: bool = False
```

### UI Layout

```
┌────────────────────────────────────────────────────────────────┐
│ Path: [My Drive] > [Projects] > [2024]                    [^] │
├────────────────────────────────────────────────────────────────┤
│ [Search: ________________]  [Browse | Search | ID]            │
├────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────┐ [<] [>] [Refresh]   │
│ │ [Folder] Select folder...        [v] │                      │
│ └──────────────────────────────────────┘                      │
├────────────────────────────────────────────────────────────────┤
│ Selected: Reports (ID: 1a2b3c...)                             │
└────────────────────────────────────────────────────────────────┘
```

### View Modes

1. **Browse Mode** (default)
   - Shows folders at current navigation level
   - Breadcrumb shows current path
   - Can drill down/up

2. **Search Mode**
   - Shows search results from entire Drive
   - Results show full path
   - Selecting navigates to that folder's parent

3. **Manual ID Mode**
   - Text input for folder ID
   - Validates ID exists
   - Shows folder name after validation

### Integration with Node Widgets

Update `create_google_drive_folder_widget()` to use the new navigator:

```python
def create_google_drive_folder_widget(
    name: str,
    label: str,
    credential_widget=None,
    enhanced: bool = True,  # Use new navigator by default
):
    if enhanced:
        navigator = GoogleDriveFolderNavigator()
        # ... setup
    else:
        # Fallback to simple picker
        picker = GoogleDriveFolderPicker()
```

### Styling (VSCode Dark Theme)

```python
NAVIGATOR_STYLE = """
/* Breadcrumb */
.PathBreadcrumb {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 3px;
    padding: 4px 8px;
}
.PathSegment {
    color: #569cd6;
    padding: 2px 4px;
}
.PathSegment:hover {
    background: #094771;
    border-radius: 2px;
}
.PathSeparator {
    color: #666666;
}

/* Mode Toggle */
.ModeButton {
    background: transparent;
    border: 1px solid #3c3c3c;
    color: #d4d4d4;
    padding: 4px 8px;
}
.ModeButton:checked {
    background: #094771;
    border-color: #007acc;
}

/* Selection Display */
.SelectionDisplay {
    background: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 3px;
    padding: 4px 8px;
    color: #9cdcfe;
    font-family: Consolas, monospace;
}
"""
```

## Implementation Phases

### Phase 1: Core Navigator Widget
1. Create `FolderNavigatorState` dataclass
2. Create `GoogleDriveFolderNavigator` main widget
3. Implement basic folder dropdown with current level browsing
4. Add back/forward navigation buttons

### Phase 2: Path Breadcrumb
1. Create `PathBreadcrumb` widget
2. Implement clickable path segments
3. Connect to navigation state

### Phase 3: Recursive Fetch & Search
1. Implement `fetch_folders_recursive()` API helper
2. Implement `search_folders()` API helper
3. Add search input with debounce
4. Implement search mode

### Phase 4: Manual ID Input
1. Add ID input text field
2. Implement folder ID validation
3. Show folder name after validation

### Phase 5: Integration
1. Update `create_google_drive_folder_widget()`
2. Update visual nodes to use new navigator
3. Add caching for folder hierarchy
4. Test with real Google Drive

## Caching Strategy

```python
class FolderCache:
    """Cache folder hierarchy to reduce API calls."""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._ttl = ttl_seconds

    def get_children(self, folder_id: str) -> Optional[List[FolderInfo]]:
        """Get cached children of folder."""

    def set_children(self, folder_id: str, children: List[FolderInfo]):
        """Cache folder children."""

    def get_folder_path(self, folder_id: str) -> Optional[str]:
        """Get cached path to folder."""

    def invalidate(self, folder_id: Optional[str] = None):
        """Invalidate cache for folder or entire cache."""
```

## Error Handling

- Network errors: Show retry button, keep last known state
- Auth errors: Prompt to re-authenticate
- Not found: Show message, allow manual ID input
- Rate limiting: Implement exponential backoff

## Questions Resolved
- Use QWidget composition, not complex inheritance
- Keep simple picker as fallback for basic use cases
- Default to browse mode, search is secondary
- Cache aggressively to reduce API calls
