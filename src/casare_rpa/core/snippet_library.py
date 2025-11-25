"""
CasareRPA - Snippet Library Manager
Provides CRUD operations, search, and versioning for reusable node snippets.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import orjson
from loguru import logger

from .snippet_definition import SnippetDefinition
from ..utils.config import SNIPPETS_DIR
from ..utils.fuzzy_search import SearchIndex


@dataclass
class SnippetInfo:
    """
    Metadata about a snippet for browsing and searching.

    Attributes:
        snippet_id: Unique identifier
        name: Display name
        category: Category for organization
        description: Short description
        file_path: Path to snippet JSON file
        version: Snippet version
        tags: List of tags for searching
        node_count: Number of nodes in snippet
        parameter_count: Number of exposed parameters
        created_at: Creation timestamp
        modified_at: Last modification timestamp
    """

    snippet_id: str
    name: str
    category: str
    description: str
    file_path: Path
    version: str = "1.0.0"
    tags: List[str] = None
    node_count: int = 0
    parameter_count: int = 0
    created_at: str = ""
    modified_at: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class SnippetLibrary:
    """
    Manages a library of reusable node snippets.

    Provides functionality to:
    - Discover snippets from file system
    - Save and load snippet definitions
    - Search snippets by name, description, and tags
    - Manage snippet versioning
    - Organize snippets by category
    """

    def __init__(self, library_path: Optional[Path] = None):
        """
        Initialize snippet library.

        Args:
            library_path: Path to snippets directory (defaults to config.SNIPPETS_DIR)
        """
        self.library_path = Path(library_path) if library_path else SNIPPETS_DIR
        self._snippets: Dict[str, SnippetInfo] = {}
        self._search_index: Optional[SearchIndex] = None
        self._loaded = False

    def discover_snippets(self) -> Dict[str, SnippetInfo]:
        """
        Discover all available snippets by scanning the library directory.

        Returns:
            Dictionary mapping snippet_id to SnippetInfo objects
        """
        if self._loaded:
            return self._snippets

        self._snippets = {}

        if not self.library_path.exists():
            logger.info(f"Creating snippets directory: {self.library_path}")
            self.library_path.mkdir(parents=True, exist_ok=True)
            return self._snippets

        # Scan all category subdirectories
        for category_dir in self.library_path.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name

            # Scan for .snippet.json files
            for snippet_file in category_dir.glob("*.snippet.json"):
                try:
                    snippet_info = self._load_snippet_info(snippet_file, category_name)
                    if snippet_info:
                        self._snippets[snippet_info.snippet_id] = snippet_info
                        logger.debug(
                            f"Discovered snippet: {category_name}/{snippet_info.name}"
                        )
                except Exception as e:
                    logger.error(f"Failed to load snippet {snippet_file}: {e}")

        # Build search index
        if self._snippets:
            self._build_search_index()

        self._loaded = True
        logger.info(
            f"Discovered {len(self._snippets)} snippets in {self._count_categories()} categories"
        )
        return self._snippets

    def _load_snippet_info(
        self, file_path: Path, category: str
    ) -> Optional[SnippetInfo]:
        """
        Load snippet metadata from JSON file without loading full definition.

        Args:
            file_path: Path to snippet file
            category: Category name

        Returns:
            SnippetInfo object or None if invalid
        """
        try:
            # Read and parse JSON
            json_data = file_path.read_bytes()
            data = orjson.loads(json_data)

            # Extract metadata
            snippet_id = data.get("snippet_id", "")
            name = data.get("name", "Untitled")
            description = data.get("description", "")
            version = data.get("version", "1.0.0")
            tags = data.get("tags", [])
            created_at = data.get("created_at", "")
            modified_at = data.get("modified_at", "")

            # Count nodes and parameters
            nodes = data.get("nodes", {})
            parameters = data.get("parameters", [])

            return SnippetInfo(
                snippet_id=snippet_id,
                name=name,
                category=category,
                description=description,
                file_path=file_path,
                version=version,
                tags=tags,
                node_count=len(nodes),
                parameter_count=len(parameters),
                created_at=created_at,
                modified_at=modified_at,
            )

        except Exception as e:
            logger.error(f"Failed to load snippet info from {file_path}: {e}")
            return None

    def _build_search_index(self):
        """Build search index for fast fuzzy searching."""
        items = []
        for snippet_info in self._snippets.values():
            # Build searchable string with tags
            search_text = f"{snippet_info.name} {snippet_info.description}"
            if snippet_info.tags:
                search_text += " " + " ".join(snippet_info.tags)

            items.append(
                (snippet_info.category, snippet_info.name, snippet_info.description)
            )

        self._search_index = SearchIndex(items)
        logger.debug(f"Built search index for {len(items)} snippets")

    def _count_categories(self) -> int:
        """Count number of unique categories."""
        categories = set(info.category for info in self._snippets.values())
        return len(categories)

    def save_snippet(self, definition: SnippetDefinition) -> Path:
        """
        Save a snippet definition to the library.

        Handles:
        - Version bumping if snippet already exists and has changed
        - Category directory creation
        - Automatic timestamping

        Args:
            definition: SnippetDefinition to save

        Returns:
            Path to saved snippet file
        """
        # Check if snippet exists and has changed
        existing = self._snippets.get(definition.snippet_id)
        if existing:
            # Load full definition to compare
            existing_def = self.load_snippet(definition.snippet_id)
            if existing_def and self._has_changed(existing_def, definition):
                # Bump version
                definition.version = self._bump_version(existing_def.version)
                logger.info(
                    f"Snippet '{definition.name}' has changed, bumping version to {definition.version}"
                )

        # Create category directory
        category_dir = self.library_path / definition.category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Save snippet file
        file_path = category_dir / f"{definition.name}.snippet.json"
        definition.save_to_file(file_path)

        # Update internal registry
        snippet_info = SnippetInfo(
            snippet_id=definition.snippet_id,
            name=definition.name,
            category=definition.category,
            description=definition.description,
            file_path=file_path,
            version=definition.version,
            tags=definition.tags,
            node_count=len(definition.nodes),
            parameter_count=len(definition.parameters),
            created_at=definition.created_at,
            modified_at=definition.modified_at,
        )
        self._snippets[definition.snippet_id] = snippet_info

        # Rebuild search index
        self._build_search_index()

        logger.info(f"Saved snippet '{definition.name}' to {file_path}")
        return file_path

    def load_snippet(self, snippet_id: str) -> Optional[SnippetDefinition]:
        """
        Load a full snippet definition by ID.

        Args:
            snippet_id: Unique snippet identifier

        Returns:
            SnippetDefinition or None if not found
        """
        if not self._loaded:
            self.discover_snippets()

        snippet_info = self._snippets.get(snippet_id)
        if not snippet_info:
            logger.warning(f"Snippet not found: {snippet_id}")
            return None

        try:
            return SnippetDefinition.load_from_file(snippet_info.file_path)
        except Exception as e:
            logger.error(f"Failed to load snippet {snippet_id}: {e}")
            return None

    def delete_snippet(self, snippet_id: str) -> bool:
        """
        Delete a snippet from the library.

        Args:
            snippet_id: Unique snippet identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self._loaded:
            self.discover_snippets()

        snippet_info = self._snippets.get(snippet_id)
        if not snippet_info:
            logger.warning(f"Snippet not found for deletion: {snippet_id}")
            return False

        try:
            # Delete file
            snippet_info.file_path.unlink()

            # Remove from registry
            del self._snippets[snippet_id]

            # Rebuild search index
            self._build_search_index()

            logger.info(f"Deleted snippet '{snippet_info.name}' ({snippet_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to delete snippet {snippet_id}: {e}")
            return False

    def get_snippet_info(self, snippet_id: str) -> Optional[SnippetInfo]:
        """
        Get snippet metadata by ID.

        Args:
            snippet_id: Unique snippet identifier

        Returns:
            SnippetInfo or None if not found
        """
        if not self._loaded:
            self.discover_snippets()

        return self._snippets.get(snippet_id)

    def list_all_snippets(self) -> List[SnippetInfo]:
        """
        Get list of all available snippets.

        Returns:
            List of SnippetInfo objects
        """
        if not self._loaded:
            self.discover_snippets()

        return list(self._snippets.values())

    def list_snippets_by_category(self, category: str) -> List[SnippetInfo]:
        """
        Get all snippets in a specific category.

        Args:
            category: Category name

        Returns:
            List of SnippetInfo objects
        """
        if not self._loaded:
            self.discover_snippets()

        return [info for info in self._snippets.values() if info.category == category]

    def get_categories(self) -> List[str]:
        """
        Get list of all categories.

        Returns:
            List of category names, sorted alphabetically
        """
        if not self._loaded:
            self.discover_snippets()

        categories = set(info.category for info in self._snippets.values())
        return sorted(categories)

    def search_snippets(
        self, query: str, category: Optional[str] = None, max_results: int = 15
    ) -> List[SnippetInfo]:
        """
        Search snippets using fuzzy matching.

        Args:
            query: Search query string
            category: Optional category filter
            max_results: Maximum number of results

        Returns:
            List of matching SnippetInfo objects, sorted by relevance
        """
        if not self._loaded:
            self.discover_snippets()

        if not query:
            # Return all snippets (optionally filtered by category)
            results = self.list_all_snippets()
            if category:
                results = [s for s in results if s.category == category]
            return results[:max_results]

        # Use fuzzy search
        if self._search_index:
            search_results = self._search_index.search(query, max_results)

            # Convert search results to SnippetInfo objects
            snippet_infos = []
            for cat, name, desc, score, positions in search_results:
                # Find matching snippet
                for snippet_info in self._snippets.values():
                    if snippet_info.name == name and snippet_info.category == cat:
                        # Apply category filter if specified
                        if category is None or snippet_info.category == category:
                            snippet_infos.append(snippet_info)
                        break

            return snippet_infos

        else:
            # Fallback: simple case-insensitive substring search
            query_lower = query.lower()
            results = []

            for snippet_info in self._snippets.values():
                if category and snippet_info.category != category:
                    continue

                if (
                    query_lower in snippet_info.name.lower()
                    or query_lower in snippet_info.description.lower()
                    or any(query_lower in tag.lower() for tag in snippet_info.tags)
                ):
                    results.append(snippet_info)

                    if len(results) >= max_results:
                        break

            return results

    def _has_changed(
        self, old_definition: SnippetDefinition, new_definition: SnippetDefinition
    ) -> bool:
        """
        Check if snippet definition has changed (excluding version and timestamps).

        Args:
            old_definition: Previous snippet definition
            new_definition: New snippet definition

        Returns:
            True if changed, False otherwise
        """
        # Compare serialized data excluding version and timestamps
        old_data = old_definition.to_dict()
        new_data = new_definition.to_dict()

        # Remove fields that should not trigger version bump
        for data in [old_data, new_data]:
            data.pop("version", None)
            data.pop("created_at", None)
            data.pop("modified_at", None)

        return old_data != new_data

    def _bump_version(self, current_version: str) -> str:
        """
        Bump semantic version number (patch level).

        Args:
            current_version: Current version string (e.g., "1.2.3")

        Returns:
            New version string with patch incremented
        """
        try:
            parts = current_version.split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0

            # Increment patch version
            patch += 1

            return f"{major}.{minor}.{patch}"

        except (ValueError, IndexError):
            logger.warning(
                f"Invalid version format '{current_version}', defaulting to '1.0.1'"
            )
            return "1.0.1"

    def __repr__(self) -> str:
        """String representation."""
        if not self._loaded:
            return f"SnippetLibrary(path='{self.library_path}', not loaded)"
        return (
            f"SnippetLibrary(snippets={len(self._snippets)}, "
            f"categories={self._count_categories()})"
        )


# Global snippet library instance
_global_library: Optional[SnippetLibrary] = None


def get_snippet_library() -> SnippetLibrary:
    """
    Get the global snippet library instance.

    Returns:
        SnippetLibrary instance
    """
    global _global_library
    if _global_library is None:
        _global_library = SnippetLibrary()
        _global_library.discover_snippets()
    return _global_library
