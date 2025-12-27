"""
Google Drive Folder Navigator Widget for CasareRPA.

Comprehensive folder navigation widget supporting:
1. Browse mode: Navigate folder hierarchy with breadcrumb and drill-down
2. Search mode: Search folders across Drive, show full paths
3. Manual ID mode: Paste folder ID directly from Google Drive URL

Components:
- FolderNavigatorState: State dataclass for widget state
- FolderInfo: Data model for folder information
- FolderCache: Cache for folder hierarchy with TTL
- PathBreadcrumb: Clickable path navigation
- FolderSearchInput: Debounced search input
- GoogleDriveFolderNavigator: Main composite widget
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger
from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS

# =============================================================================
# Constants and API Configuration
# =============================================================================

DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
ROOT_FOLDER_ID = "root"


class NavigatorMode(Enum):
    """Navigator view mode."""

    BROWSE = "browse"
    SEARCH = "search"
    MANUAL = "manual"


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class FolderInfo:
    """Information about a Google Drive folder."""

    id: str
    name: str
    path: str  # Full path like "My Drive/Projects/2024"
    parent_id: str | None = None
    depth: int = 0
    has_children: bool = False

    @property
    def is_root(self) -> bool:
        """Check if this is the root folder."""
        return self.id == ROOT_FOLDER_ID


@dataclass
class FolderNavigatorState:
    """State for the folder navigator widget."""

    current_folder_id: str = ROOT_FOLDER_ID
    current_path: list[tuple[str, str]] = field(default_factory=list)  # [(id, name), ...]
    selected_folder_id: str | None = None
    selected_folder_name: str = ""
    search_query: str = ""
    view_mode: NavigatorMode = NavigatorMode.BROWSE

    def get_path_string(self) -> str:
        """Get path as a string."""
        if not self.current_path:
            return "My Drive"
        return " / ".join(name for _, name in self.current_path)


@dataclass
class CacheEntry:
    """Cache entry with TTL tracking."""

    data: Any
    timestamp: float = field(default_factory=time.time)

    def is_expired(self, ttl_seconds: float) -> bool:
        """Check if cache entry has expired."""
        return (time.time() - self.timestamp) > ttl_seconds


class FolderCache:
    """
    Cache for folder hierarchy to reduce API calls.

    Caches:
    - Children of folders
    - Full paths to folders
    - Search results
    """

    DEFAULT_TTL: float = 300.0  # 5 minutes

    def __init__(self, ttl_seconds: float = DEFAULT_TTL) -> None:
        self._ttl: float = ttl_seconds
        self._children_cache: dict[str, CacheEntry] = {}
        self._path_cache: dict[str, CacheEntry] = {}
        self._search_cache: dict[str, CacheEntry] = {}

    def get_children(self, folder_id: str) -> list[FolderInfo] | None:
        """Get cached children of a folder."""
        entry = self._children_cache.get(folder_id)
        if entry and not entry.is_expired(self._ttl):
            return entry.data
        return None

    def set_children(self, folder_id: str, children: list[FolderInfo]) -> None:
        """Cache folder children."""
        self._children_cache[folder_id] = CacheEntry(data=children)

    def get_folder_path(self, folder_id: str) -> list[tuple[str, str]] | None:
        """Get cached path to folder."""
        entry = self._path_cache.get(folder_id)
        if entry and not entry.is_expired(self._ttl):
            return entry.data
        return None

    def set_folder_path(self, folder_id: str, path: list[tuple[str, str]]) -> None:
        """Cache folder path."""
        self._path_cache[folder_id] = CacheEntry(data=path)

    def get_search_results(self, query: str) -> list[FolderInfo] | None:
        """Get cached search results."""
        entry = self._search_cache.get(query.lower())
        if entry and not entry.is_expired(self._ttl):
            return entry.data
        return None

    def set_search_results(self, query: str, results: list[FolderInfo]) -> None:
        """Cache search results."""
        self._search_cache[query.lower()] = CacheEntry(data=results)

    def invalidate(self, folder_id: str | None = None) -> None:
        """Invalidate cache for folder or entire cache."""
        if folder_id:
            self._children_cache.pop(folder_id, None)
            self._path_cache.pop(folder_id, None)
        else:
            self._children_cache.clear()
            self._path_cache.clear()
            self._search_cache.clear()


# =============================================================================
# API Helpers
# =============================================================================


def _get_http_client() -> Any:
    """Get configured UnifiedHttpClient for Google API calls."""
    from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

    # Configure client for external Google APIs (SSRF protection enabled)
    return UnifiedHttpClient(
        UnifiedHttpClientConfig(
            enable_ssrf_protection=True,
            max_retries=2,
            default_timeout=30.0,
        )
    )


async def _get_access_token(credential_id: str) -> str:
    """Get a valid access token for the credential."""
    from casare_rpa.infrastructure.security.google_oauth import (
        get_google_access_token,
    )

    return await get_google_access_token(credential_id)


async def fetch_folder_children(
    credential_id: str,
    folder_id: str = ROOT_FOLDER_ID,
    max_results: int = 100,
) -> list[FolderInfo]:
    """
    Fetch immediate children folders of a parent folder.

    Args:
        credential_id: Google OAuth credential ID
        folder_id: Parent folder ID (use "root" for My Drive)
        max_results: Maximum number of folders to return

    Returns:
        List of FolderInfo objects for child folders
    """
    if not credential_id:
        return []

    try:
        access_token = await _get_access_token(credential_id)

        # Build query for folders in parent
        parent_query = (
            "'root' in parents" if folder_id == ROOT_FOLDER_ID else f"'{folder_id}' in parents"
        )
        query = f"mimeType='{FOLDER_MIME_TYPE}' and {parent_query} and trashed=false"

        params = {
            "q": query,
            "pageSize": max_results,
            "fields": "files(id,name,mimeType,parents)",
            "orderBy": "name",
        }

        headers = {"Authorization": f"Bearer {access_token}"}

        async with _get_http_client() as http_client:
            url = f"{DRIVE_API_BASE}/files"
            response = await http_client.get(url, params=params, headers=headers)
            if response.status == 401:
                raise Exception("Authentication failed - token may be expired")
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"API error ({response.status}): {error_text}")

            data = await response.json()

        files = data.get("files", [])
        folders = []

        for f in files:
            folders.append(
                FolderInfo(
                    id=f.get("id", ""),
                    name=f.get("name", "Untitled"),
                    path="",  # Path will be set by caller
                    parent_id=folder_id if folder_id != ROOT_FOLDER_ID else None,
                    depth=0,
                    has_children=True,  # Assume folders can have children
                )
            )

        logger.debug(f"Fetched {len(folders)} child folders from {folder_id}")
        return folders

    except Exception as e:
        logger.error(f"Failed to fetch folder children: {e}")
        raise


async def fetch_folders_recursive(
    credential_id: str,
    parent_folder_id: str = ROOT_FOLDER_ID,
    max_depth: int = 3,
    max_total: int = 500,
    current_path: str = "My Drive",
    current_depth: int = 0,
) -> list[FolderInfo]:
    """
    Fetch folders recursively up to max_depth levels.

    Returns a flat list with full path information for each folder.
    Useful for flat dropdown display showing full paths.

    Args:
        credential_id: Google OAuth credential ID
        parent_folder_id: Starting folder ID
        max_depth: Maximum recursion depth
        max_total: Maximum total folders to fetch
        current_path: Path prefix for building full paths
        current_depth: Current recursion depth

    Returns:
        Flat list of FolderInfo objects with full paths
    """
    if not credential_id or current_depth >= max_depth:
        return []

    results: list[FolderInfo] = []

    try:
        children = await fetch_folder_children(credential_id, parent_folder_id)

        for child in children:
            if len(results) >= max_total:
                break

            # Set full path
            child.path = f"{current_path}/{child.name}" if current_path else child.name
            child.depth = current_depth
            results.append(child)

            # Recurse into child (if not at max depth and under total limit)
            if current_depth < max_depth - 1 and len(results) < max_total:
                sub_folders = await fetch_folders_recursive(
                    credential_id=credential_id,
                    parent_folder_id=child.id,
                    max_depth=max_depth,
                    max_total=max_total - len(results),
                    current_path=child.path,
                    current_depth=current_depth + 1,
                )
                results.extend(sub_folders)

        return results

    except Exception as e:
        logger.error(f"Failed to fetch folders recursively: {e}")
        return results  # Return what we have so far


async def search_folders(
    credential_id: str,
    query: str,
    max_results: int = 50,
) -> list[FolderInfo]:
    """
    Search folders by name across entire Drive.

    Args:
        credential_id: Google OAuth credential ID
        query: Search query (folder name)
        max_results: Maximum results to return

    Returns:
        List of FolderInfo objects matching the query
    """
    if not credential_id or not query:
        return []

    try:
        access_token = await _get_access_token(credential_id)

        # Search for folders by name
        api_query = f"mimeType='{FOLDER_MIME_TYPE}' and name contains '{query}' and trashed=false"

        params = {
            "q": api_query,
            "pageSize": max_results,
            "fields": "files(id,name,parents)",
            "orderBy": "modifiedTime desc",
        }

        headers = {"Authorization": f"Bearer {access_token}"}

        async with _get_http_client() as http_client:
            url = f"{DRIVE_API_BASE}/files"
            response = await http_client.get(url, params=params, headers=headers)
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"API error ({response.status}): {error_text}")

            data = await response.json()

        files = data.get("files", [])
        results = []

        for f in files:
            parent_ids = f.get("parents", [])
            parent_id = parent_ids[0] if parent_ids else None

            results.append(
                FolderInfo(
                    id=f.get("id", ""),
                    name=f.get("name", "Untitled"),
                    path="",  # Path will be fetched separately if needed
                    parent_id=parent_id,
                    depth=0,
                )
            )

        logger.debug(f"Search found {len(results)} folders matching '{query}'")
        return results

    except Exception as e:
        logger.error(f"Failed to search folders: {e}")
        return []


async def validate_folder_id(
    credential_id: str,
    folder_id: str,
) -> tuple[bool, str]:
    """
    Validate that a folder ID exists and get its name.

    Args:
        credential_id: Google OAuth credential ID
        folder_id: Folder ID to validate

    Returns:
        Tuple of (is_valid, folder_name or error_message)
    """
    if not credential_id:
        return False, "No credential selected"

    if not folder_id:
        return False, "No folder ID provided"

    # Root is always valid
    if folder_id == ROOT_FOLDER_ID:
        return True, "My Drive"

    try:
        access_token = await _get_access_token(credential_id)

        params = {
            "fields": "id,name,mimeType",
        }

        headers = {"Authorization": f"Bearer {access_token}"}

        async with _get_http_client() as http_client:
            url = f"{DRIVE_API_BASE}/files/{folder_id}"
            response = await http_client.get(url, params=params, headers=headers, timeout=15.0)
            if response.status == 404:
                return False, "Folder not found"
            if response.status != 200:
                return False, f"API error ({response.status})"

            data = await response.json()

        # Verify it's a folder
        mime_type = data.get("mimeType", "")
        if mime_type != FOLDER_MIME_TYPE:
            return False, "ID is not a folder"

        return True, data.get("name", "Unknown")

    except Exception as e:
        logger.error(f"Failed to validate folder ID: {e}")
        return False, str(e)


async def get_folder_path(
    credential_id: str,
    folder_id: str,
) -> list[tuple[str, str]]:
    """
    Get the full path to a folder as list of (id, name) tuples.

    Args:
        credential_id: Google OAuth credential ID
        folder_id: Target folder ID

    Returns:
        List of (folder_id, folder_name) from root to target
    """
    if not credential_id or not folder_id:
        return []

    if folder_id == ROOT_FOLDER_ID:
        return [(ROOT_FOLDER_ID, "My Drive")]

    path: list[tuple[str, str]] = []
    current_id = folder_id

    try:
        access_token = await _get_access_token(credential_id)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Walk up the tree
        async with _get_http_client() as http_client:
            while current_id and current_id != ROOT_FOLDER_ID:
                params = {"fields": "id,name,parents"}

                url = f"{DRIVE_API_BASE}/files/{current_id}"
                response = await http_client.get(url, params=params, headers=headers, timeout=15.0)
                if response.status != 200:
                    break

                data = await response.json()

                folder_name = data.get("name", "Unknown")
                path.insert(0, (current_id, folder_name))

                parents = data.get("parents", [])
                current_id = parents[0] if parents else None

        # Add root
        path.insert(0, (ROOT_FOLDER_ID, "My Drive"))

        return path

    except Exception as e:
        logger.error(f"Failed to get folder path: {e}")
        return [(ROOT_FOLDER_ID, "My Drive")]


def extract_folder_id_from_url(url_or_id: str) -> str | None:
    """
    Extract folder ID from a Google Drive URL or return as-is if already an ID.

    Supports formats:
    - https://drive.google.com/drive/folders/1abc...xyz
    - https://drive.google.com/drive/u/0/folders/1abc...xyz
    - 1abc...xyz (raw ID)

    Args:
        url_or_id: Google Drive URL or folder ID

    Returns:
        Extracted folder ID or None if invalid
    """
    if not url_or_id:
        return None

    url_or_id = url_or_id.strip()

    # Pattern for Google Drive folder URLs
    patterns = [
        r"drive\.google\.com/drive/(?:u/\d+/)?folders/([a-zA-Z0-9_-]+)",
        r"^([a-zA-Z0-9_-]{25,})$",  # Raw ID (at least 25 chars)
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    return None


# =============================================================================
# VSCode Dark Theme Styles (Using THEME)
# =============================================================================

NAVIGATOR_STYLE = f"""
/* Container */
.GoogleDriveFolderNavigator {{
    background: transparent;
}}

/* Breadcrumb container */
QFrame#BreadcrumbFrame {{
    background: {THEME.bg_component};
    border: 1px solid {THEME.border};
    border-radius: {TOKENS.radius.sm};
    padding: {TOKENS.spacing.xs};
}}

/* Path segment buttons */
QPushButton.PathSegment {{
    background: transparent;
    border: none;
    color: {THEME.primary};
    padding: {TOKENS.spacing.xs} {TOKENS.spacing.md};
    font-size: 12px;
}}
QPushButton.PathSegment:hover {{
    background: {THEME.bg_selected};
    border-radius: 2px;
}}
QPushButton.PathSegment:pressed {{
    background: {THEME.bg_component};
}}

/* Path separator */
QLabel.PathSeparator {{
    color: {THEME.text_disabled};
    padding: 0 2px;
}}

/* Mode toggle buttons */
QPushButton.ModeButton {{
    background: transparent;
    border: 1px solid {THEME.border};
    border-radius: {TOKENS.radius.sm};
    color: {THEME.text_primary};
    padding: {TOKENS.spacing.xs} {TOKENS.spacing.md};
    font-size: 11px;
    min-width: 50px;
}}
QPushButton.ModeButton:hover {{
    background: {THEME.border};
    border-color: {THEME.border_light};
}}
QPushButton.ModeButton:checked {{
    background: {THEME.bg_selected};
    border-color: {THEME.primary};
    color: {THEME.text_primary};
}}

/* Navigation buttons */
QPushButton.NavButton {{
    background: {THEME.bg_component};
    border: 1px solid {THEME.border_light};
    border-radius: {TOKENS.radius.sm};
    color: {THEME.text_primary};
    padding: 0px;
    min-width: 26px;
    min-height: 26px;
    font-size: 14px;
}}
QPushButton.NavButton:hover {{
    background: {THEME.bg_hover};
    border-color: {THEME.primary};
}}
QPushButton.NavButton:pressed {{
    background: {THEME.bg_elevated};
}}
QPushButton.NavButton:disabled {{
    background: {THEME.bg_component};
    color: {THEME.text_disabled};
    border-color: {THEME.border};
}}

/* Search input */
QLineEdit.FolderSearch {{
    background: {THEME.input_bg};
    border: 1px solid {THEME.border_light};
    border-radius: {TOKENS.radius.sm};
    color: {THEME.text_primary};
    padding: {TOKENS.spacing.xs} {TOKENS.spacing.md};
    selection-background-color: {THEME.bg_selected};
}}
QLineEdit.FolderSearch:focus {{
    border-color: {THEME.primary};
}}
QLineEdit.FolderSearch::placeholder {{
    color: {THEME.text_secondary};
}}

/* Manual ID input */
QLineEdit.ManualIdInput {{
    background: {THEME.bg_header};
    border: 1px solid {THEME.border};
    border-radius: {TOKENS.radius.sm};
    color: {THEME.json_key};
    padding: {TOKENS.spacing.xs} {TOKENS.spacing.md};
    font-family: Consolas, monospace;
    font-size: 12px;
}}
QLineEdit.ManualIdInput:focus {{
    border-color: {THEME.primary};
}}

/* Selection display */
QLabel.SelectionDisplay {{
    background: {THEME.bg_header};
    border: 1px solid {THEME.border};
    border-radius: {TOKENS.radius.sm};
    padding: {TOKENS.spacing.xs} {TOKENS.spacing.md};
    color: {THEME.json_key};
    font-family: Consolas, monospace;
    font-size: 11px;
}}

/* Status label */
QLabel.StatusLabel {{
    color: {THEME.text_secondary};
    font-size: 11px;
}}
QLabel.StatusLabel[status="error"] {{
    color: {THEME.error};
}}
QLabel.StatusLabel[status="success"] {{
    color: {THEME.success};
}}
QLabel.StatusLabel[status="loading"] {{
    color: {THEME.warning};
    font-style: italic;
}}

/* Dropdown button (replaces QComboBox for better graphics scene support) */
QPushButton#FolderDropdownButton {{
    background: {THEME.input_bg};
    border: 1px solid {THEME.border_light};
    border-radius: {TOKENS.radius.sm};
    padding: {TOKENS.spacing.xs} {TOKENS.spacing.md};
    padding-right: 24px;
    color: {THEME.text_primary};
    text-align: left;
    min-width: 150px;
    min-height: 26px;
}}
QPushButton#FolderDropdownButton:hover {{
    border-color: {THEME.primary};
    background: {THEME.bg_hover};
}}
QPushButton#FolderDropdownButton:pressed {{
    background: {THEME.bg_hover};
}}
QPushButton#FolderDropdownButton:disabled {{
    background: {THEME.bg_component};
    color: {THEME.text_disabled};
}}
"""

# Style for dropdown menu popup - use VS Code/Cursor style
DROPDOWN_MENU_STYLE = f"""
QMenu {{
    background: {THEME.bg_elevated};
    border: 1px solid {THEME.border};
    border-radius: {TOKENS.radius.sm}px;
    padding: {TOKENS.spacing.xs}px;
}}
QMenu::item {{
    padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
    border-radius: {TOKENS.radius.sm}px;
}}
QMenu::item:selected {{
    background: {THEME.bg_selected};
}}
QMenu::separator {{
    height: 1px;
    background: {THEME.border};
    margin: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
}}
"""

# Style for folder list widget in popup
FOLDER_LIST_STYLE = f"""
QListWidget {{
    background: {THEME.bg_surface};
    border: none;
    outline: none;
    padding: {TOKENS.spacing.xs};
}}
QListWidget::item {{
    padding: {TOKENS.spacing.xs} {TOKENS.spacing.md};
    color: {THEME.text_primary};
    border: none;
}}
QListWidget::item:hover {{
    background: {THEME.bg_hover};
}}
QListWidget::item:selected {{
    background: {THEME.bg_selected};
    color: {THEME.text_primary};
}}
"""


# =============================================================================
# GraphicsSceneDropdownButton - Reliable dropdown for QGraphicsProxyWidget
# =============================================================================


class GraphicsSceneDropdownButton(QWidget):
    """
    A dropdown widget that works reliably in QGraphicsProxyWidget.

    Uses QPushButton + QMenu instead of QComboBox because:
    - QMenu is designed as a standalone popup window
    - It handles its own positioning correctly
    - It doesn't have QComboBox's focus management issues in graphics scenes

    Signals:
        item_selected(int): Emitted when an item is selected (index)
        current_index_changed(int): Alias for item_selected (QComboBox compatibility)
    """

    item_selected = Signal(int)
    currentIndexChanged = Signal(int)  # QComboBox compatibility

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._items: list[tuple[str, Any]] = []  # [(display_text, user_data), ...]
        self._current_index: int = -1
        self._placeholder: str = "Select..."

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the button and layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main button that shows current selection
        self._button = QPushButton()
        self._button.setObjectName("FolderDropdownButton")
        self._button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._button.setMinimumWidth(150)
        self._button.setMinimumHeight(26)
        self._button.setMaximumHeight(26)

        # Add dropdown arrow indicator using CSS border trick
        self._button.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border_light};
                border-radius: 4px;
                padding: 4px 24px 4px 8px;
                color: {THEME.text_primary};
                text-align: left;
            }}
            QPushButton:hover {{
                border-color: {THEME.accent};
                background: {THEME.bg_hover};
            }}
            QPushButton:pressed {{
                background: {THEME.bg_hover};
            }}
            QPushButton:disabled {{
                background: {THEME.bg_component};
                color: {THEME.text_disabled};
            }}
        """)

        layout.addWidget(self._button)

        # Create dropdown arrow overlay label
        self._arrow = QLabel(self._button)
        self._arrow.setFixedSize(20, 26)
        self._arrow.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {THEME.text_primary};
                margin: 10px 4px 0 0;
            }}
        """)

        self._update_display()

    def _connect_signals(self) -> None:
        """Connect button click to show menu."""
        self._button.clicked.connect(self._show_dropdown)

    def resizeEvent(self, event) -> None:
        """Position arrow on resize."""
        super().resizeEvent(event)
        # Position arrow at right side of button
        arrow_x = self._button.width() - self._arrow.width() - 2
        self._arrow.move(arrow_x, 0)

    def _show_dropdown(self) -> None:
        """Show the dropdown menu with items."""
        if not self._items:
            return

        # Create menu with proper window flags to stay on top
        menu = QMenu(self)
        menu.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        menu.setStyleSheet(DROPDOWN_MENU_STYLE)
        menu.setMinimumWidth(self._button.width())

        # If we have many items, use a scrollable list widget
        if len(self._items) > 15:
            self._show_list_popup()
            return

        # Add items to menu
        for i, (text, _data) in enumerate(self._items):
            action = menu.addAction(text)
            action.setData(i)

            # Mark current selection
            if i == self._current_index:
                font = action.font()
                font.setBold(True)
                action.setFont(font)

        # Connect selection
        menu.triggered.connect(self._on_menu_triggered)

        # Show menu below button
        # Get global position - works correctly even in graphics scenes
        global_pos = self._button.mapToGlobal(self._button.rect().bottomLeft())
        menu.exec(global_pos)

    def _show_list_popup(self) -> None:
        """Show a scrollable list popup for many items."""
        menu = QMenu(self)
        menu.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        menu.setStyleSheet(Theme.context_menu_style())

        # Create list widget
        list_widget = QListWidget()
        list_widget.setStyleSheet(FOLDER_LIST_STYLE)
        list_widget.setMinimumWidth(max(200, self._button.width()))
        list_widget.setMaximumHeight(300)

        for i, (text, _data) in enumerate(self._items):
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, i)
            list_widget.addItem(item)

            if i == self._current_index:
                list_widget.setCurrentItem(item)

        # Wrap in QWidgetAction
        action = QWidgetAction(menu)
        action.setDefaultWidget(list_widget)
        menu.addAction(action)

        # Handle selection
        def on_item_clicked(item):
            index = item.data(Qt.ItemDataRole.UserRole)
            self._set_current_index(index)
            menu.close()

        list_widget.itemClicked.connect(on_item_clicked)

        # Show at button position
        global_pos = self._button.mapToGlobal(self._button.rect().bottomLeft())
        menu.exec(global_pos)

    def _on_menu_triggered(self, action) -> None:
        """Handle menu item selection."""
        index = action.data()
        if index is not None:
            self._set_current_index(index)

    def _set_current_index(self, index: int) -> None:
        """Set current index and emit signals."""
        if index != self._current_index and 0 <= index < len(self._items):
            self._current_index = index
            self._update_display()
            self.item_selected.emit(index)
            self.currentIndexChanged.emit(index)

    def _update_display(self) -> None:
        """Update button text to show current selection."""
        if self._current_index >= 0 and self._current_index < len(self._items):
            text = self._items[self._current_index][0]
            # Elide long text
            if len(text) > 30:
                text = text[:27] + "..."
            self._button.setText(text)
        else:
            self._button.setText(self._placeholder)

    # =========================================================================
    # QComboBox-compatible API
    # =========================================================================

    def addItem(self, text: str, data=None) -> None:
        """Add an item to the dropdown."""
        self._items.append((text, data))
        if self._current_index < 0:
            self._update_display()

    def clear(self) -> None:
        """Clear all items."""
        self._items.clear()
        self._current_index = -1
        self._update_display()

    def count(self) -> int:
        """Return number of items."""
        return len(self._items)

    def currentIndex(self) -> int:
        """Return current selected index."""
        return self._current_index

    def setCurrentIndex(self, index: int) -> None:
        """Set current index without emitting signals."""
        if 0 <= index < len(self._items):
            self._current_index = index
            self._update_display()

    def currentText(self) -> str:
        """Return current item text."""
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index][0]
        return ""

    def itemData(self, index: int):
        """Return data for item at index."""
        if 0 <= index < len(self._items):
            return self._items[index][1]
        return None

    def findData(self, data) -> int:
        """Find index of item with given data."""
        for i, (_, item_data) in enumerate(self._items):
            if item_data == data:
                return i
        return -1

    def setPlaceholderText(self, text: str) -> None:
        """Set placeholder text shown when nothing selected."""
        self._placeholder = text
        if self._current_index < 0:
            self._update_display()

    def setToolTip(self, tip: str) -> None:
        """Set tooltip on the button."""
        self._button.setToolTip(tip)

    def setEnabled(self, enabled: bool) -> None:
        """Enable/disable the dropdown."""
        self._button.setEnabled(enabled)
        super().setEnabled(enabled)

    def blockSignals(self, block: bool) -> bool:
        """Block/unblock signals (for compatibility)."""
        return super().blockSignals(block)

    def setFocusPolicy(self, policy) -> None:
        """Set focus policy on button."""
        self._button.setFocusPolicy(policy)


# =============================================================================
# PathBreadcrumb Widget
# =============================================================================


class PathBreadcrumb(QWidget):
    """
    Clickable breadcrumb showing current folder path.

    Displays path segments as clickable buttons:
    My Drive > Projects > 2024 > Reports

    Signals:
        path_clicked(str, int): Emitted when segment clicked (folder_id, depth)
    """

    path_clicked = Signal(str, int)  # folder_id, depth

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path: list[tuple[str, str]] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the breadcrumb layout."""
        self._frame = QFrame()
        self._frame.setObjectName("BreadcrumbFrame")

        self._layout = QHBoxLayout(self._frame)
        self._layout.setContentsMargins(6, 4, 6, 4)
        self._layout.setSpacing(0)

        # Scroll area for long paths
        scroll = QScrollArea()
        scroll.setWidget(self._frame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(32)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def set_path(self, path: list[tuple[str, str]]) -> None:
        """
        Update displayed path.

        Args:
            path: List of (folder_id, folder_name) tuples from root
        """
        self._path = path
        self._rebuild_segments()

    def _rebuild_segments(self) -> None:
        """Rebuild the breadcrumb segments."""
        # Clear existing widgets
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._path:
            # Show default
            label = QLabel("My Drive")
            label.setStyleSheet(f"color: {THEME.primary}; padding: 2px 6px;")
            self._layout.addWidget(label)
            self._layout.addStretch()
            return

        for i, (folder_id, folder_name) in enumerate(self._path):
            # Add separator if not first
            if i > 0:
                sep = QLabel(">")
                sep.setProperty("class", "PathSeparator")
                sep.setStyleSheet(f"color: {THEME.text_disabled}; padding: 0 4px;")
                self._layout.addWidget(sep)

            # Add clickable segment
            btn = QPushButton(folder_name)
            btn.setProperty("class", "PathSegment")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {THEME.primary};
                    padding: 2px 6px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: {THEME.selected};
                    border-radius: 2px;
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"Navigate to {folder_name}")

            # Capture values for lambda
            fid, depth = folder_id, i
            btn.clicked.connect(lambda checked, f=fid, d=depth: self._on_segment_clicked(f, d))

            self._layout.addWidget(btn)

        self._layout.addStretch()

    def _on_segment_clicked(self, folder_id: str, depth: int) -> None:
        """Handle click on path segment."""
        self.path_clicked.emit(folder_id, depth)


# =============================================================================
# FolderSearchInput Widget
# =============================================================================


class FolderSearchInput(QLineEdit):
    """
    Search input with debounced search trigger.

    Waits for user to stop typing before emitting search signal.

    Signals:
        search_triggered(str): Emitted after debounce, passes query string
    """

    search_triggered = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        debounce_ms: int = 400,
    ) -> None:
        super().__init__(parent)
        self._debounce_ms: int = debounce_ms
        self._debounce_timer: QTimer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_search)

        self.setObjectName("FolderSearch")
        self.setPlaceholderText("Search folders...")
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border_light};
                border-radius: {TOKENS.radius.sm};
                color: {THEME.text_primary};
                padding: {TOKENS.spacing.xs} {TOKENS.spacing.md};
                selection-background-color: {THEME.bg_selected};
            }}
            QLineEdit:focus {{
                border-color: {THEME.primary};
            }}
        """)

        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str) -> None:
        """Handle text change with debounce."""
        self._debounce_timer.stop()
        if text.strip():
            self._debounce_timer.start(self._debounce_ms)
        else:
            # Clear search immediately if empty
            self.search_triggered.emit("")

    def _emit_search(self) -> None:
        """Emit search signal after debounce."""
        query = self.text().strip()
        if query:
            self.search_triggered.emit(query)


# =============================================================================
# Background Worker
# =============================================================================


class FolderFetchWorker(QObject):
    """Worker for fetching folders in background."""

    finished = Signal(object, str)  # result, error

    def __init__(
        self,
        fetch_func,
        args: tuple = (),
        kwargs: dict | None = None,
    ) -> None:
        super().__init__()
        self.fetch_func = fetch_func
        self.args: tuple = args
        self.kwargs: dict | None = kwargs or {}

    def run(self) -> None:
        """Execute fetch function."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.fetch_func(*self.args, **self.kwargs))
                self.finished.emit(result, "")
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Folder fetch error: {e}")
            self.finished.emit(None, str(e))


class FolderFetchThread(QThread):
    """Thread wrapper for folder fetch worker."""

    finished = Signal(object, str)

    def __init__(
        self,
        fetch_func,
        args: tuple = (),
        kwargs: dict | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._worker: FolderFetchWorker = FolderFetchWorker(fetch_func, args, kwargs)

    def run(self):
        self._worker.finished.connect(self.finished.emit)
        self._worker.run()


# =============================================================================
# GoogleDriveFolderNavigator - Main Widget
# =============================================================================


class GoogleDriveFolderNavigator(QWidget):
    """
    Comprehensive Google Drive folder navigation widget.

    Supports three modes:
    1. Browse: Navigate folder hierarchy with drill-down
    2. Search: Search folders across Drive
    3. Manual: Enter folder ID directly

    Signals:
        folder_selected(str): Emitted when folder is selected, passes folder_id
        navigation_changed(str): Emitted when browse location changes
    """

    folder_selected = Signal(str)  # folder_id
    navigation_changed = Signal(str)  # current_folder_id

    def __init__(
        self,
        parent: QWidget | None = None,
        show_mode_buttons: bool = True,
    ) -> None:
        super().__init__(parent)

        self._credential_id: str | None = None
        self._state: FolderNavigatorState = FolderNavigatorState()
        self._cache: FolderCache = FolderCache()
        self._fetch_thread: FolderFetchThread | None = None
        self._show_mode_buttons: bool = show_mode_buttons

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the widget layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Top row: Breadcrumb + back button (Browse mode only)
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        self._back_btn = QPushButton("<")
        self._back_btn.setProperty("class", "NavButton")
        self._back_btn.setFixedSize(26, 26)
        self._back_btn.setToolTip("Go to parent folder")
        self._back_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border_light};
                border-radius: 3px;
                color: {THEME.text_primary};
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {THEME.bg_hover}; border-color: {THEME.accent}; }}
            QPushButton:disabled {{ background: {THEME.bg_component}; color: {THEME.text_disabled}; }}
        """)
        top_row.addWidget(self._back_btn)

        self._breadcrumb = PathBreadcrumb()
        top_row.addWidget(self._breadcrumb, 1)

        main_layout.addLayout(top_row)

        # Mode buttons row (if enabled)
        if self._show_mode_buttons:
            mode_row = QHBoxLayout()
            mode_row.setSpacing(4)

            self._mode_group = QButtonGroup(self)
            self._mode_group.setExclusive(True)

            self._browse_btn = QPushButton("Browse")
            self._browse_btn.setCheckable(True)
            self._browse_btn.setChecked(True)
            self._browse_btn.setProperty("class", "ModeButton")

            self._search_btn = QPushButton("Search")
            self._search_btn.setCheckable(True)
            self._search_btn.setProperty("class", "ModeButton")

            self._manual_btn = QPushButton("ID")
            self._manual_btn.setCheckable(True)
            self._manual_btn.setProperty("class", "ModeButton")
            self._manual_btn.setToolTip("Enter folder ID manually")

            mode_style = f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid {THEME.border};
                    border-radius: 3px;
                    color: {THEME.text_primary};
                    padding: 3px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: {THEME.border};
                }}
                QPushButton:checked {{
                    background: {THEME.selected};
                    border-color: {THEME.accent};
                    color: #ffffff;
                }}
            """
            self._browse_btn.setStyleSheet(mode_style)
            self._search_btn.setStyleSheet(mode_style)
            self._manual_btn.setStyleSheet(mode_style)

            self._mode_group.addButton(self._browse_btn, 0)
            self._mode_group.addButton(self._search_btn, 1)
            self._mode_group.addButton(self._manual_btn, 2)

            mode_row.addWidget(self._browse_btn)
            mode_row.addWidget(self._search_btn)
            mode_row.addWidget(self._manual_btn)
            mode_row.addStretch()

            main_layout.addLayout(mode_row)

        # Stacked widget for different mode views
        self._stack = QStackedWidget()

        # Browse mode view
        browse_widget = QWidget()
        browse_layout = QVBoxLayout(browse_widget)
        browse_layout.setContentsMargins(0, 0, 0, 0)
        browse_layout.setSpacing(4)

        dropdown_row = QHBoxLayout()
        dropdown_row.setSpacing(4)

        # Use GraphicsSceneDropdownButton instead of QComboBox for reliable
        # popup behavior inside QGraphicsProxyWidget (NodeGraphQt nodes)
        self._folder_combo = GraphicsSceneDropdownButton()
        self._folder_combo.setMinimumWidth(150)
        self._folder_combo.setPlaceholderText("Select folder...")
        self._folder_combo.addItem("Select folder...", "")
        dropdown_row.addWidget(self._folder_combo, 1)

        self._enter_btn = QPushButton(">")
        self._enter_btn.setProperty("class", "NavButton")
        self._enter_btn.setFixedSize(26, 26)
        self._enter_btn.setToolTip("Enter selected folder")
        self._enter_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border_light};
                border-radius: 3px;
                color: {THEME.text_primary};
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {THEME.bg_hover}; border-color: {THEME.accent}; }}
            QPushButton:disabled {{ background: {THEME.bg_component}; color: {THEME.text_disabled}; }}
        """)
        dropdown_row.addWidget(self._enter_btn)

        self._refresh_btn = QPushButton("\u21bb")
        self._refresh_btn.setProperty("class", "NavButton")
        self._refresh_btn.setFixedSize(26, 26)
        self._refresh_btn.setToolTip("Refresh folder list")
        self._refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border_light};
                border-radius: 3px;
                color: {THEME.text_primary};
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {THEME.bg_hover}; border-color: {THEME.accent}; }}
        """)
        dropdown_row.addWidget(self._refresh_btn)

        browse_layout.addLayout(dropdown_row)
        self._stack.addWidget(browse_widget)

        # Search mode view
        search_widget = QWidget()
        search_layout = QVBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(4)

        self._search_input = FolderSearchInput()
        search_layout.addWidget(self._search_input)

        # Use GraphicsSceneDropdownButton instead of QComboBox for reliable
        # popup behavior inside QGraphicsProxyWidget (NodeGraphQt nodes)
        self._search_results_combo = GraphicsSceneDropdownButton()
        self._search_results_combo.setMinimumWidth(150)
        self._search_results_combo.setPlaceholderText("Search for folders...")
        self._search_results_combo.addItem("Search for folders...", "")
        search_layout.addWidget(self._search_results_combo)

        self._stack.addWidget(search_widget)

        # Manual ID mode view
        manual_widget = QWidget()
        manual_layout = QVBoxLayout(manual_widget)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(4)

        self._manual_input = QLineEdit()
        self._manual_input.setPlaceholderText("Paste folder ID or Google Drive URL...")
        self._manual_input.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME.bg_header};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                color: {THEME.json_key};
                padding: 6px 10px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {THEME.accent}; }}
        """)
        manual_layout.addWidget(self._manual_input)

        validate_row = QHBoxLayout()
        validate_row.setSpacing(4)

        self._validate_btn = QPushButton("Validate")
        self._validate_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.accent};
                border: 1px solid {THEME.primary_hover};
                border-radius: 3px;
                color: #ffffff;
                padding: 4px 12px;
            }}
            QPushButton:hover {{ background: {THEME.primary_hover}; }}
            QPushButton:disabled {{ background: {THEME.border}; color: {THEME.text_disabled}; }}
        """)
        validate_row.addWidget(self._validate_btn)

        self._validation_status = QLabel("")
        self._validation_status.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        validate_row.addWidget(self._validation_status, 1)

        manual_layout.addLayout(validate_row)
        self._stack.addWidget(manual_widget)

        main_layout.addWidget(self._stack)

        # Bottom: Selection display
        self._selection_label = QLabel("No folder selected")
        self._selection_label.setStyleSheet(f"""
            QLabel {{
                background: {THEME.bg_header};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 4px 8px;
                color: {THEME.text_secondary};
                font-size: 11px;
            }}
        """)
        main_layout.addWidget(self._selection_label)

        # Loading indicator
        self._loading_label = QLabel("Loading...")
        self._loading_label.setStyleSheet(
            f"color: {THEME.warning}; font-style: italic; font-size: 11px;"
        )
        self._loading_label.setVisible(False)
        main_layout.addWidget(self._loading_label)

        # Set initial mode visibility
        self._update_mode_visibility()

    def _apply_styles(self) -> None:
        """Apply stylesheet."""
        self.setStyleSheet(NAVIGATOR_STYLE)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._back_btn.clicked.connect(self._navigate_up)
        self._enter_btn.clicked.connect(self._enter_selected_folder)
        self._refresh_btn.clicked.connect(self._refresh_current)

        self._breadcrumb.path_clicked.connect(self._on_breadcrumb_clicked)
        self._folder_combo.currentIndexChanged.connect(self._on_folder_selected)

        self._search_input.search_triggered.connect(self._on_search_triggered)
        self._search_results_combo.currentIndexChanged.connect(self._on_search_result_selected)

        self._manual_input.returnPressed.connect(self._validate_manual_id)
        self._validate_btn.clicked.connect(self._validate_manual_id)

        if self._show_mode_buttons:
            self._mode_group.idClicked.connect(self._on_mode_changed)

    def _update_mode_visibility(self) -> None:
        """Update visibility based on current mode."""
        mode = self._state.view_mode

        # Show/hide browse-specific widgets
        show_browse = mode == NavigatorMode.BROWSE
        self._back_btn.setVisible(show_browse)
        self._breadcrumb.setVisible(show_browse)

        # Switch stacked widget
        if mode == NavigatorMode.BROWSE:
            self._stack.setCurrentIndex(0)
        elif mode == NavigatorMode.SEARCH:
            self._stack.setCurrentIndex(1)
        else:
            self._stack.setCurrentIndex(2)

    # =========================================================================
    # Mode Handlers
    # =========================================================================

    def _on_mode_changed(self, mode_id: int) -> None:
        """Handle mode button click."""
        if mode_id == 0:
            self._state.view_mode = NavigatorMode.BROWSE
            self._load_current_folder()
        elif mode_id == 1:
            self._state.view_mode = NavigatorMode.SEARCH
        else:
            self._state.view_mode = NavigatorMode.MANUAL

        self._update_mode_visibility()

    # =========================================================================
    # Browse Mode
    # =========================================================================

    def _load_current_folder(self) -> None:
        """Load folders at current navigation level."""
        if not self._credential_id:
            self._show_no_credential()
            return

        self._set_loading(True)

        folder_id = self._state.current_folder_id

        # Check cache first
        cached = self._cache.get_children(folder_id)
        if cached is not None:
            self._populate_browse_combo(cached)
            self._set_loading(False)
            return

        # Fetch in background
        self._fetch_thread = FolderFetchThread(
            fetch_func=fetch_folder_children,
            kwargs={
                "credential_id": self._credential_id,
                "folder_id": folder_id,
            },
            parent=self,
        )
        self._fetch_thread.finished.connect(self._on_browse_fetch_complete)
        self._fetch_thread.start()

    def _on_browse_fetch_complete(self, folders: list[FolderInfo] | None, error: str) -> None:
        """Handle browse fetch completion."""
        self._set_loading(False)
        self._fetch_thread = None

        if error:
            logger.error(f"Browse fetch error: {error}")
            self._show_error(error)
            return

        if folders is None:
            folders = []

        # Cache results
        self._cache.set_children(self._state.current_folder_id, folders)

        self._populate_browse_combo(folders)

    def _populate_browse_combo(self, folders: list[FolderInfo]) -> None:
        """Populate browse dropdown with folders."""
        self._folder_combo.blockSignals(True)
        self._folder_combo.clear()

        # Add "Select this folder" option at top
        current_name = self._state.current_path[-1][1] if self._state.current_path else "My Drive"
        self._folder_combo.addItem(f"[Select] {current_name}", self._state.current_folder_id)

        if not folders:
            self._folder_combo.addItem("(No subfolders)", "")
        else:
            for folder in folders:
                self._folder_combo.addItem(f"  {folder.name}", folder.id)

        self._folder_combo.blockSignals(False)

        # Update breadcrumb
        self._breadcrumb.set_path(self._state.current_path)

        # Update back button state
        self._back_btn.setEnabled(len(self._state.current_path) > 1)

    def _on_folder_selected(self, index: int) -> None:
        """Handle folder selection in browse combo."""
        if index < 0:
            return

        folder_id = self._folder_combo.itemData(index)
        if not folder_id:
            return

        # If first item (current folder), select it
        if index == 0:
            self._select_folder(folder_id)
        # Otherwise just highlight (use enter button to drill down)

    def _enter_selected_folder(self) -> None:
        """Enter the selected folder (drill down)."""
        index = self._folder_combo.currentIndex()
        if index <= 0:
            return

        folder_id = self._folder_combo.itemData(index)
        folder_name = self._folder_combo.currentText().strip()

        if not folder_id:
            return

        # Navigate into folder
        self._state.current_folder_id = folder_id
        self._state.current_path.append((folder_id, folder_name))

        self._load_current_folder()
        self.navigation_changed.emit(folder_id)

    def _navigate_up(self) -> None:
        """Navigate to parent folder."""
        if len(self._state.current_path) <= 1:
            return

        # Remove current folder from path
        self._state.current_path.pop()

        # Set current to parent
        if self._state.current_path:
            self._state.current_folder_id = self._state.current_path[-1][0]
        else:
            self._state.current_folder_id = ROOT_FOLDER_ID

        self._load_current_folder()
        self.navigation_changed.emit(self._state.current_folder_id)

    def _on_breadcrumb_clicked(self, folder_id: str, depth: int) -> None:
        """Handle breadcrumb segment click."""
        # Truncate path to clicked depth
        self._state.current_path = self._state.current_path[: depth + 1]
        self._state.current_folder_id = folder_id

        self._load_current_folder()
        self.navigation_changed.emit(folder_id)

    def _refresh_current(self) -> None:
        """Force refresh current folder."""
        self._cache.invalidate(self._state.current_folder_id)
        self._load_current_folder()

    # =========================================================================
    # Search Mode
    # =========================================================================

    def _on_search_triggered(self, query: str) -> None:
        """Handle search query."""
        if not query:
            self._search_results_combo.blockSignals(True)
            self._search_results_combo.clear()
            self._search_results_combo.addItem("Search for folders...", "")
            self._search_results_combo.blockSignals(False)
            return

        if not self._credential_id:
            self._show_no_credential()
            return

        # Check cache
        cached = self._cache.get_search_results(query)
        if cached is not None:
            self._populate_search_results(cached)
            return

        self._set_loading(True)

        self._fetch_thread = FolderFetchThread(
            fetch_func=search_folders,
            kwargs={
                "credential_id": self._credential_id,
                "query": query,
            },
            parent=self,
        )
        self._fetch_thread.finished.connect(
            lambda results, err: self._on_search_complete(query, results, err)
        )
        self._fetch_thread.start()

    def _on_search_complete(
        self,
        query: str,
        results: list[FolderInfo] | None,
        error: str,
    ) -> None:
        """Handle search completion."""
        self._set_loading(False)
        self._fetch_thread = None

        if error:
            logger.error(f"Search error: {error}")
            self._show_error(error)
            return

        if results is None:
            results = []

        # Cache results
        self._cache.set_search_results(query, results)

        self._populate_search_results(results)

    def _populate_search_results(self, results: list[FolderInfo]) -> None:
        """Populate search results dropdown."""
        self._search_results_combo.blockSignals(True)
        self._search_results_combo.clear()

        if not results:
            self._search_results_combo.addItem("No folders found", "")
        else:
            for folder in results:
                display = folder.name
                if folder.path:
                    display = f"{folder.name}  ({folder.path})"
                self._search_results_combo.addItem(display, folder.id)

        self._search_results_combo.blockSignals(False)

    def _on_search_result_selected(self, index: int) -> None:
        """Handle search result selection."""
        if index < 0:
            return

        folder_id = self._search_results_combo.itemData(index)
        if folder_id:
            self._select_folder(folder_id)

    # =========================================================================
    # Manual ID Mode
    # =========================================================================

    def _validate_manual_id(self) -> None:
        """Validate manually entered folder ID."""
        input_text = self._manual_input.text().strip()
        if not input_text:
            self._validation_status.setText("Enter a folder ID or URL")
            self._validation_status.setStyleSheet(f"color: {THEME.text_secondary};")
            return

        # Extract ID from URL if needed
        folder_id = extract_folder_id_from_url(input_text)
        if not folder_id:
            self._validation_status.setText("Invalid folder ID or URL")
            self._validation_status.setStyleSheet(f"color: {THEME.error};")
            return

        if not self._credential_id:
            self._validation_status.setText("Select a Google account first")
            self._validation_status.setStyleSheet(f"color: {THEME.error};")
            return

        self._validation_status.setText("Validating...")
        self._validation_status.setStyleSheet(f"color: {THEME.warning}; font-style: italic;")

        self._fetch_thread = FolderFetchThread(
            fetch_func=validate_folder_id,
            kwargs={
                "credential_id": self._credential_id,
                "folder_id": folder_id,
            },
            parent=self,
        )
        self._fetch_thread.finished.connect(
            lambda result, err: self._on_validation_complete(folder_id, result, err)
        )
        self._fetch_thread.start()

    def _on_validation_complete(
        self,
        folder_id: str,
        result: tuple[bool, str] | None,
        error: str,
    ) -> None:
        """Handle validation completion."""
        self._fetch_thread = None

        if error:
            self._validation_status.setText(f"Error: {error}")
            self._validation_status.setStyleSheet(f"color: {THEME.error};")
            return

        if result is None:
            self._validation_status.setText("Validation failed")
            self._validation_status.setStyleSheet(f"color: {THEME.error};")
            return

        is_valid, message = result

        if is_valid:
            self._validation_status.setText(f"Valid: {message}")
            self._validation_status.setStyleSheet(f"color: {THEME.success};")
            self._select_folder(folder_id, message)
        else:
            self._validation_status.setText(f"Invalid: {message}")
            self._validation_status.setStyleSheet(f"color: {THEME.error};")

    # =========================================================================
    # Selection
    # =========================================================================

    def _select_folder(self, folder_id: str, folder_name: str | None = None) -> None:
        """Select a folder and emit signal."""
        self._state.selected_folder_id = folder_id

        if folder_name:
            self._state.selected_folder_name = folder_name
        else:
            # Try to get name from combo or cache
            self._state.selected_folder_name = folder_id

        # Update selection display
        display_text = self._state.selected_folder_name
        if folder_id != ROOT_FOLDER_ID:
            display_text = f"{display_text}  (ID: {folder_id[:12]}...)"
        else:
            display_text = "My Drive (root)"

        self._selection_label.setText(display_text)
        self._selection_label.setStyleSheet(f"""
            QLabel {{
                background: {THEME.bg_header};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 4px 8px;
                color: {THEME.json_key};
                font-size: 11px;
            }}
        """)

        self.folder_selected.emit(folder_id)

    # =========================================================================
    # UI Helpers
    # =========================================================================

    def _set_loading(self, loading: bool) -> None:
        """Set loading state."""
        self._loading_label.setVisible(loading)
        self._folder_combo.setEnabled(not loading)
        self._search_results_combo.setEnabled(not loading)
        self._validate_btn.setEnabled(not loading)

    def _show_no_credential(self) -> None:
        """Show no credential message."""
        self._folder_combo.blockSignals(True)
        self._folder_combo.clear()
        self._folder_combo.addItem("Select Google account first...", "")
        self._folder_combo.blockSignals(False)

    def _show_error(self, error: str) -> None:
        """Show error in UI."""
        self._folder_combo.blockSignals(True)
        self._folder_combo.clear()
        self._folder_combo.addItem(f"Error: {error[:30]}...", "")
        self._folder_combo.setToolTip(error)
        self._folder_combo.blockSignals(False)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_credential_id(self, credential_id: str) -> None:
        """
        Set the Google credential ID for API calls.

        Args:
            credential_id: Google OAuth credential ID
        """
        if credential_id == self._credential_id:
            return

        self._credential_id = credential_id
        self._cache.invalidate()  # Clear cache for new credential

        # Reset state
        self._state = FolderNavigatorState()
        self._state.current_path = [(ROOT_FOLDER_ID, "My Drive")]

        if credential_id:
            self._load_current_folder()
        else:
            self._show_no_credential()

    def get_credential_id(self) -> str | None:
        """Get the current credential ID."""
        return self._credential_id

    def get_folder_id(self) -> str | None:
        """Get the selected folder ID."""
        return self._state.selected_folder_id

    def set_folder_id(self, folder_id: str) -> None:
        """
        Set the selected folder ID.

        If in browse mode and credential is set, will navigate to that folder.

        Args:
            folder_id: Folder ID to select
        """
        if folder_id == self._state.selected_folder_id:
            return

        self._state.selected_folder_id = folder_id

        if folder_id == ROOT_FOLDER_ID:
            self._select_folder(ROOT_FOLDER_ID, "My Drive")
            return

        # If we have a credential, try to validate and get name
        if self._credential_id:
            self._fetch_thread = FolderFetchThread(
                fetch_func=validate_folder_id,
                kwargs={
                    "credential_id": self._credential_id,
                    "folder_id": folder_id,
                },
                parent=self,
            )
            self._fetch_thread.finished.connect(
                lambda result, err: self._on_set_folder_complete(folder_id, result, err)
            )
            self._fetch_thread.start()
        else:
            # Just set the ID without validation
            self._select_folder(folder_id, folder_id)

    def _on_set_folder_complete(
        self,
        folder_id: str,
        result: tuple[bool, str] | None,
        error: str,
    ) -> None:
        """Handle set_folder_id validation completion."""
        self._fetch_thread = None

        if result and result[0]:
            # Valid folder
            is_valid, folder_name = result
            self._select_folder(folder_id, folder_name)
        else:
            # Invalid or error - still set ID
            self._select_folder(folder_id, folder_id)

    def get_folder_name(self) -> str:
        """Get the selected folder name."""
        return self._state.selected_folder_name

    def refresh(self) -> None:
        """Refresh the current view."""
        if self._state.view_mode == NavigatorMode.BROWSE:
            self._refresh_current()

    def clear_cache(self) -> None:
        """Clear the folder cache."""
        self._cache.invalidate()

    def is_valid(self) -> bool:
        """Check if a valid folder is selected."""
        return self._state.selected_folder_id is not None and self._state.selected_folder_id != ""

    def navigate_to(self, folder_id: str) -> None:
        """
        Navigate to a specific folder (browse mode).

        Args:
            folder_id: Target folder ID
        """
        if not self._credential_id:
            return

        self._state.view_mode = NavigatorMode.BROWSE
        if self._show_mode_buttons:
            self._browse_btn.setChecked(True)
        self._update_mode_visibility()

        # Fetch path to folder and navigate
        self._fetch_thread = FolderFetchThread(
            fetch_func=get_folder_path,
            kwargs={
                "credential_id": self._credential_id,
                "folder_id": folder_id,
            },
            parent=self,
        )
        self._fetch_thread.finished.connect(
            lambda path, err: self._on_navigate_to_complete(folder_id, path, err)
        )
        self._fetch_thread.start()

    def _on_navigate_to_complete(
        self,
        folder_id: str,
        path: list[tuple[str, str]] | None,
        error: str,
    ) -> None:
        """Handle navigate_to path fetch completion."""
        self._fetch_thread = None

        if error or not path:
            logger.error(f"Navigate to error: {error}")
            return

        self._state.current_path = path
        self._state.current_folder_id = folder_id
        self._load_current_folder()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Data models
    "FolderInfo",
    "FolderNavigatorState",
    "FolderCache",
    "NavigatorMode",
    # API helpers
    "fetch_folder_children",
    "fetch_folders_recursive",
    "search_folders",
    "validate_folder_id",
    "get_folder_path",
    "extract_folder_id_from_url",
    # Widgets
    "PathBreadcrumb",
    "FolderSearchInput",
    "GoogleDriveFolderNavigator",
    "GraphicsSceneDropdownButton",
]
