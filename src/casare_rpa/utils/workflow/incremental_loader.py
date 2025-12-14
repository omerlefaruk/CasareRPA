"""
Incremental Workflow Loader for CasareRPA.

PERFORMANCE: Loads workflow metadata and node skeleton first,
defers full node instantiation until execution or canvas display.

Use Cases:
- Recent files list (show skeleton only)
- Workflow browser/search (preview without full load)
- Workflow validation without instantiation
- Quick workflow info extraction

Usage:
    from casare_rpa.utils.workflow.incremental_loader import (
        IncrementalLoader,
        WorkflowSkeleton,
    )

    loader = IncrementalLoader()
    skeleton = loader.load_skeleton(workflow_data)

    # Fast access to metadata
    print(f"Workflow: {skeleton.name} ({skeleton.node_count} nodes)")

    # Full load when needed
    workflow = loader.load_full(skeleton)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import threading
import time

from loguru import logger

# Lazy imports to avoid circular dependencies
_workflow_loader_module = None


def _get_workflow_loader():
    """Lazy import of workflow_loader to avoid circular imports."""
    global _workflow_loader_module
    if _workflow_loader_module is None:
        from casare_rpa.utils.workflow import workflow_loader

        _workflow_loader_module = workflow_loader
    return _workflow_loader_module


@dataclass
class WorkflowSkeleton:
    """
    Lightweight workflow representation for preview scenarios.

    Contains only metadata and counts - no instantiated nodes.
    Full workflow can be loaded on demand via load_full().
    """

    # Metadata
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""

    # Counts (fast to compute)
    node_count: int = 0
    connection_count: int = 0
    variable_count: int = 0
    frame_count: int = 0

    # Node type summary (for filtering/search)
    node_types: Set[str] = field(default_factory=set)
    node_categories: Set[str] = field(default_factory=set)

    # Variables (lightweight - just names and types)
    variable_names: List[str] = field(default_factory=list)

    # Settings
    settings: Dict[str, Any] = field(default_factory=dict)

    # Deferred loading support
    _full_data: Optional[Dict] = field(default=None, repr=False)
    _workflow: Optional[Any] = field(default=None, repr=False)
    _loaded: bool = field(default=False, repr=False)
    _file_path: Optional[str] = field(default=None, repr=False)

    # Timestamps
    created_at: Optional[str] = None
    modified_at: Optional[str] = None

    def is_loaded(self) -> bool:
        """Check if full workflow is loaded."""
        return self._loaded

    def get_full_workflow(self):
        """Get full workflow if loaded, else None."""
        return self._workflow if self._loaded else None


class IncrementalLoader:
    """
    Load workflows incrementally for performance.

    Supports two loading modes:
    1. Skeleton: Fast metadata extraction (~5-10ms)
    2. Full: Complete workflow with instantiated nodes (~200-500ms)
    """

    # Category mappings for node types
    NODE_CATEGORY_MAP = {
        "Browser": ["LaunchBrowser", "CloseBrowser", "GoToURL", "Click", "Type"],
        "File": ["ReadFile", "WriteFile", "FileSystem", "CSV", "JSON"],
        "Control": ["If", "ForLoop", "While", "Switch", "Try"],
        "Data": ["SetVariable", "GetVariable", "Transform", "Filter"],
        "API": ["HttpRequest", "REST", "GraphQL", "SOAP"],
        "Database": ["Query", "Execute", "Connect"],
        "UI": ["MessageBox", "InputDialog", "Screenshot"],
    }

    def __init__(self):
        """Initialize the incremental loader."""
        pass  # No state needed currently

    def load_skeleton(
        self,
        workflow_data: Dict[str, Any],
        file_path: Optional[str] = None,
    ) -> WorkflowSkeleton:
        """
        Fast load - extract metadata and counts only.

        This is ~20-50x faster than full loading because it:
        - Does NOT instantiate any node classes
        - Does NOT validate config values
        - Does NOT resolve node type aliases
        - Does NOT create connections

        Args:
            workflow_data: Raw workflow dictionary
            file_path: Optional source file path for caching

        Returns:
            WorkflowSkeleton with metadata and counts
        """
        start = time.perf_counter()

        # Extract metadata
        metadata = workflow_data.get("metadata", {})
        nodes = workflow_data.get("nodes", {})
        connections = workflow_data.get("connections", [])
        variables = workflow_data.get("variables", {})
        frames = workflow_data.get("frames", [])
        settings = workflow_data.get("settings", {})

        # Extract node types
        node_types: Set[str] = set()
        for node_data in nodes.values():
            node_type = node_data.get("node_type")
            if node_type:
                node_types.add(node_type)

        # Infer categories from node types
        categories = self._infer_categories(node_types)

        skeleton = WorkflowSkeleton(
            name=metadata.get("name", "Untitled"),
            description=metadata.get("description", ""),
            version=metadata.get("version", "1.0.0"),
            author=metadata.get("author", ""),
            node_count=len(nodes),
            connection_count=len(connections),
            variable_count=len(variables),
            frame_count=len(frames),
            node_types=node_types,
            node_categories=categories,
            variable_names=list(variables.keys()),
            settings=settings,
            created_at=metadata.get("created_at"),
            modified_at=metadata.get("modified_at"),
            _full_data=workflow_data,
            _file_path=file_path,
        )

        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(
            f"Skeleton loaded: {skeleton.name} "
            f"({skeleton.node_count} nodes) in {elapsed:.1f}ms"
        )

        return skeleton

    def load_skeleton_from_file(self, file_path: str) -> Optional[WorkflowSkeleton]:
        """
        Load skeleton from workflow file.

        Args:
            file_path: Path to workflow JSON file

        Returns:
            WorkflowSkeleton or None if failed
        """
        try:
            from casare_rpa.utils.workflow.compressed_io import load_workflow

            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Workflow file not found: {file_path}")
                return None

            workflow_data = load_workflow(path)
            if workflow_data is None:
                return None

            return self.load_skeleton(workflow_data, file_path=file_path)

        except Exception as e:
            logger.error(f"Failed to load skeleton from {file_path}: {e}")
            return None

    def load_full(self, skeleton: WorkflowSkeleton) -> Optional[Any]:
        """
        Full load - instantiate all nodes and connections.

        Uses the deferred data stored in the skeleton.

        Args:
            skeleton: WorkflowSkeleton to fully load

        Returns:
            WorkflowSchema or None if failed
        """
        if skeleton._loaded and skeleton._workflow is not None:
            logger.debug(f"Returning cached full workflow: {skeleton.name}")
            return skeleton._workflow

        if skeleton._full_data is None:
            logger.error(f"No deferred data for skeleton: {skeleton.name}")
            return None

        start = time.perf_counter()

        try:
            loader = _get_workflow_loader()
            workflow = loader.load_workflow_from_dict(skeleton._full_data)

            skeleton._workflow = workflow
            skeleton._loaded = True

            elapsed = (time.perf_counter() - start) * 1000
            logger.debug(f"Full workflow loaded: {skeleton.name} in {elapsed:.1f}ms")

            return workflow

        except Exception as e:
            logger.error(f"Failed to load full workflow {skeleton.name}: {e}")
            return None

    def load_full_async(self, skeleton: WorkflowSkeleton, callback=None):
        """
        Load full workflow asynchronously.

        Useful for UI scenarios where you don't want to block.

        THREAD SAFETY WARNING: The callback is invoked from a background thread.
        If updating UI components (PySide6/Qt), use signals/slots to marshal
        the callback result to the main thread. Do NOT update Qt widgets directly
        from the callback.

        Example for Qt:
            # In your widget class:
            workflow_loaded = Signal(object)  # Define signal

            def on_load_complete(self, workflow, error):
                self.workflow_loaded.emit((workflow, error))  # Marshal to main thread

            loader.load_full_async(skeleton, callback=self.on_load_complete)

        Args:
            skeleton: WorkflowSkeleton to load
            callback: Function to call with result (workflow, error).
                      WARNING: Called from background thread!
        """

        def _load():
            try:
                workflow = self.load_full(skeleton)
                if callback:
                    callback(workflow, None)
            except Exception as e:
                logger.warning(f"Async workflow load failed: {e}")
                if callback:
                    callback(None, e)

        thread = threading.Thread(target=_load, daemon=True, name="WorkflowLoader")
        thread.start()

    def _infer_categories(self, node_types: Set[str]) -> Set[str]:
        """
        Infer workflow categories from node types.

        Args:
            node_types: Set of node type names

        Returns:
            Set of category names
        """
        categories = set()

        for node_type in node_types:
            for category, keywords in self.NODE_CATEGORY_MAP.items():
                for keyword in keywords:
                    if keyword.lower() in node_type.lower():
                        categories.add(category)
                        break

        return categories

    def get_workflow_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get quick workflow info without full loading.

        Args:
            file_path: Path to workflow file

        Returns:
            Dictionary with workflow info
        """
        skeleton = self.load_skeleton_from_file(file_path)
        if skeleton is None:
            return None

        return {
            "name": skeleton.name,
            "description": skeleton.description,
            "version": skeleton.version,
            "author": skeleton.author,
            "node_count": skeleton.node_count,
            "connection_count": skeleton.connection_count,
            "variable_count": skeleton.variable_count,
            "node_types": list(skeleton.node_types),
            "categories": list(skeleton.node_categories),
            "variables": skeleton.variable_names,
            "created_at": skeleton.created_at,
            "modified_at": skeleton.modified_at,
            "file_path": file_path,
        }

    def scan_directory(
        self,
        directory: str,
        pattern: str = "*.json",
    ) -> List[WorkflowSkeleton]:
        """
        Scan directory for workflows and load skeletons.

        Useful for building workflow browser/search.

        Args:
            directory: Directory to scan
            pattern: Glob pattern for files

        Returns:
            List of WorkflowSkeleton objects
        """
        skeletons = []
        dir_path = Path(directory)

        if not dir_path.exists():
            return skeletons

        for file_path in dir_path.glob(pattern):
            skeleton = self.load_skeleton_from_file(str(file_path))
            if skeleton:
                skeletons.append(skeleton)

        # Sort by modification time (newest first)
        skeletons.sort(
            key=lambda s: s.modified_at or "",
            reverse=True,
        )

        return skeletons


# =============================================================================
# Global instance (thread-safe singleton)
# =============================================================================

_incremental_loader: Optional[IncrementalLoader] = None
_incremental_loader_lock = threading.Lock()


def get_incremental_loader() -> IncrementalLoader:
    """
    Get global incremental loader singleton.

    Thread-safe using double-checked locking pattern.
    """
    global _incremental_loader
    if _incremental_loader is None:
        with _incremental_loader_lock:
            if _incremental_loader is None:
                _incremental_loader = IncrementalLoader()
    return _incremental_loader


# =============================================================================
# Convenience functions
# =============================================================================


def load_workflow_skeleton(workflow_data: Dict[str, Any]) -> WorkflowSkeleton:
    """Load workflow skeleton from data."""
    return get_incremental_loader().load_skeleton(workflow_data)


def load_workflow_skeleton_from_file(file_path: str) -> Optional[WorkflowSkeleton]:
    """Load workflow skeleton from file."""
    return get_incremental_loader().load_skeleton_from_file(file_path)


def get_workflow_info(file_path: str) -> Optional[Dict[str, Any]]:
    """Get quick workflow info from file."""
    return get_incremental_loader().get_workflow_info(file_path)


def scan_workflows(directory: str) -> List[WorkflowSkeleton]:
    """Scan directory for workflows."""
    return get_incremental_loader().scan_directory(directory)
