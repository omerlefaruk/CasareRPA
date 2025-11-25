"""
CasareRPA - Snippet Definition
Defines the structure for reusable node snippets with parameter mapping and variable scoping.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import orjson
from loguru import logger

from .types import (
    DataType,
    NodeId,
    SerializedNode,
    SCHEMA_VERSION,
)
from .workflow_schema import NodeConnection


@dataclass
class ParameterMapping:
    """
    Maps a snippet parameter to an internal node configuration.

    This allows exposing internal node configs as snippet-level parameters
    that can be set from outside the snippet.

    Example:
        ParameterMapping(
            snippet_param_name="website_url",
            target_node_id="navigate_node_1",
            target_config_key="url",
            param_type=DataType.STRING,
            default_value="https://example.com",
            description="URL to navigate to",
            required=True
        )
    """

    snippet_param_name: str  # Name exposed to snippet users (e.g., "website_url")
    target_node_id: str  # Internal node ID to configure
    target_config_key: str  # Config key to set (e.g., "url")
    param_type: DataType  # Parameter data type
    default_value: Any  # Default value if not provided
    description: str  # Description for UI
    required: bool = True  # Whether parameter must be provided

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "snippet_param_name": self.snippet_param_name,
            "target_node_id": self.target_node_id,
            "target_config_key": self.target_config_key,
            "param_type": self.param_type.name,
            "default_value": self.default_value,
            "description": self.description,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterMapping":
        """Create from dictionary."""
        return cls(
            snippet_param_name=data["snippet_param_name"],
            target_node_id=data["target_node_id"],
            target_config_key=data["target_config_key"],
            param_type=DataType[data["param_type"]],
            default_value=data["default_value"],
            description=data.get("description", ""),
            required=data.get("required", True),
        )


@dataclass
class VariableScopeConfig:
    """
    Defines variable inheritance and export behavior for snippet execution.

    Controls how variables flow between parent workflow and snippet subgraph:
    - inherit_parent_scope: Can snippet read parent workflow variables?
    - export_local_vars: Do snippet's new variables go to parent scope?
    - isolated_vars: List of variables that stay private to snippet
    - input_mappings: Map parent variable names to snippet variable names
    - output_mappings: Map snippet variable names back to parent names

    Examples:
        # Isolated scope (library snippets)
        VariableScopeConfig(
            inherit_parent_scope=False,
            export_local_vars=False,
            input_mappings={"parent_url": "url"},
            output_mappings={"result": "login_result"}
        )

        # Transparent scope (inline snippets)
        VariableScopeConfig(
            inherit_parent_scope=True,
            export_local_vars=True
        )
    """

    inherit_parent_scope: bool = True  # Read parent workflow variables
    export_local_vars: bool = False  # Write new vars to parent scope
    isolated_vars: List[str] = None  # Private variables (list of names)
    input_mappings: Dict[str, str] = None  # Parent var -> Snippet var
    output_mappings: Dict[str, str] = None  # Snippet var -> Parent var

    def __post_init__(self):
        """Initialize mutable default values."""
        if self.isolated_vars is None:
            self.isolated_vars = []
        if self.input_mappings is None:
            self.input_mappings = {}
        if self.output_mappings is None:
            self.output_mappings = {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "inherit_parent_scope": self.inherit_parent_scope,
            "export_local_vars": self.export_local_vars,
            "isolated_vars": self.isolated_vars,
            "input_mappings": self.input_mappings,
            "output_mappings": self.output_mappings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariableScopeConfig":
        """Create from dictionary."""
        return cls(
            inherit_parent_scope=data.get("inherit_parent_scope", True),
            export_local_vars=data.get("export_local_vars", False),
            isolated_vars=data.get("isolated_vars", []),
            input_mappings=data.get("input_mappings", {}),
            output_mappings=data.get("output_mappings", {}),
        )


class SnippetDefinition:
    """
    Complete specification of a reusable node snippet.

    A snippet is a group of nodes that can be collapsed into a single container node
    with a parameterized interface. Snippets can be saved to a library and reused
    across workflows.

    Attributes:
        snippet_id: Unique identifier (UUID)
        name: Human-readable name
        description: Detailed description
        category: Organization category (e.g., "browser", "data_processing")
        version: Semantic version (e.g., "1.0.0")
        author: Creator name
        tags: List of tags for search
        created_at: Creation timestamp
        modified_at: Last modification timestamp
        nodes: Internal node definitions
        connections: Connections between internal nodes
        node_positions: Visual positions of internal nodes
        parameters: Exposed parameters for configuration
        entry_node_ids: Nodes that connect to snippet's exec_in
        exit_node_ids: Nodes that connect to snippet's exec_out
        variable_scope: Variable inheritance configuration
        icon_name: Icon identifier for visual representation
        color: RGB color tuple for visual representation
    """

    def __init__(
        self,
        snippet_id: str,
        name: str,
        description: str = "",
        category: str = "custom",
        version: str = "1.0.0",
        author: str = "",
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize snippet definition.

        Args:
            snippet_id: Unique identifier
            name: Snippet name
            description: Snippet description
            category: Category for organization
            version: Semantic version
            author: Creator name
            tags: List of tags
        """
        self.snippet_id = snippet_id
        self.name = name
        self.description = description
        self.category = category
        self.version = version
        self.author = author
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()

        # Structure
        self.nodes: Dict[NodeId, SerializedNode] = {}
        self.connections: List[NodeConnection] = []
        self.node_positions: Dict[NodeId, Tuple[float, float]] = {}

        # Interface
        self.parameters: List[ParameterMapping] = []
        self.entry_node_ids: List[NodeId] = []
        self.exit_node_ids: List[NodeId] = []

        # Execution
        self.variable_scope = VariableScopeConfig()

        # Visual
        self.icon_name: str = "snippet"
        self.color: Tuple[int, int, int] = (100, 150, 200)

    def add_parameter(self, param: ParameterMapping) -> None:
        """Add a parameter mapping to the snippet."""
        self.parameters.append(param)
        logger.debug(f"Added parameter '{param.snippet_param_name}' to snippet '{self.name}'")

    def remove_parameter(self, param_name: str) -> None:
        """Remove a parameter mapping by name."""
        self.parameters = [p for p in self.parameters if p.snippet_param_name != param_name]
        logger.debug(f"Removed parameter '{param_name}' from snippet '{self.name}'")

    def get_parameter(self, param_name: str) -> Optional[ParameterMapping]:
        """Get a parameter mapping by name."""
        for param in self.parameters:
            if param.snippet_param_name == param_name:
                return param
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize snippet definition to dictionary.

        Returns:
            Complete snippet data structure
        """
        return {
            "snippet_id": self.snippet_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "schema_version": SCHEMA_VERSION,
            "nodes": self.nodes,
            "connections": [conn.to_dict() for conn in self.connections],
            "node_positions": {
                node_id: {"x": pos[0], "y": pos[1]} for node_id, pos in self.node_positions.items()
            },
            "parameters": [param.to_dict() for param in self.parameters],
            "entry_node_ids": self.entry_node_ids,
            "exit_node_ids": self.exit_node_ids,
            "variable_scope": self.variable_scope.to_dict(),
            "icon_name": self.icon_name,
            "color": list(self.color),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnippetDefinition":
        """
        Create snippet definition from dictionary.

        Args:
            data: Serialized snippet data

        Returns:
            SnippetDefinition instance
        """
        snippet = cls(
            snippet_id=data["snippet_id"],
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "custom"),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            tags=data.get("tags", []),
        )

        # Restore timestamps
        snippet.created_at = data.get("created_at", snippet.created_at)
        snippet.modified_at = data.get("modified_at", snippet.modified_at)

        # Restore structure
        snippet.nodes = data.get("nodes", {})
        snippet.connections = [NodeConnection.from_dict(conn) for conn in data.get("connections", [])]

        # Restore node positions
        node_positions = data.get("node_positions", {})
        for node_id, pos in node_positions.items():
            if isinstance(pos, dict):
                snippet.node_positions[node_id] = (pos["x"], pos["y"])
            else:
                snippet.node_positions[node_id] = tuple(pos)

        # Restore interface
        snippet.parameters = [ParameterMapping.from_dict(p) for p in data.get("parameters", [])]
        snippet.entry_node_ids = data.get("entry_node_ids", [])
        snippet.exit_node_ids = data.get("exit_node_ids", [])

        # Restore execution config
        if "variable_scope" in data:
            snippet.variable_scope = VariableScopeConfig.from_dict(data["variable_scope"])

        # Restore visual
        snippet.icon_name = data.get("icon_name", "snippet")
        color_data = data.get("color", [100, 150, 200])
        snippet.color = tuple(color_data) if isinstance(color_data, list) else color_data

        return snippet

    def save_to_file(self, file_path: Path) -> None:
        """
        Save snippet definition to JSON file.

        Args:
            file_path: Path to save file
        """
        try:
            # Update modified timestamp
            self.modified_at = datetime.now().isoformat()

            # Serialize to JSON using orjson
            json_data = orjson.dumps(
                self.to_dict(), option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
            )

            # Write to file
            file_path.write_bytes(json_data)
            logger.info(f"Snippet '{self.name}' saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save snippet: {e}")
            raise

    @classmethod
    def load_from_file(cls, file_path: Path) -> "SnippetDefinition":
        """
        Load snippet definition from JSON file.

        Args:
            file_path: Path to snippet file

        Returns:
            SnippetDefinition instance
        """
        try:
            # Read file
            json_data = file_path.read_bytes()

            # Parse JSON using orjson
            data = orjson.loads(json_data)

            # Create snippet
            snippet = cls.from_dict(data)
            logger.info(f"Snippet '{snippet.name}' loaded from {file_path}")

            return snippet

        except Exception as e:
            logger.error(f"Failed to load snippet from {file_path}: {e}")
            raise

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SnippetDefinition(name='{self.name}', "
            f"category='{self.category}', "
            f"nodes={len(self.nodes)}, "
            f"parameters={len(self.parameters)}, "
            f"version='{self.version}')"
        )
