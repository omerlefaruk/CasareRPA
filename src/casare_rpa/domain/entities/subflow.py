"""
CasareRPA - Domain Entity: Subflow

Represents a reusable workflow fragment that can be embedded in other workflows.
A subflow encapsulates a group of nodes with defined inputs and outputs.

Features:
- Input/output port definitions with type information
- Version tracking for change management
- Nesting support (subflows can contain subflows, max depth: 3)
- Circular reference detection
- Serialization to/from JSON files in workflows/subflows/
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import uuid

import orjson
import logging

logger = logging.getLogger(__name__)

from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.value_objects.types import (
    DataType,
    NodeId,
    SerializedNode,
)
from casare_rpa.domain.schemas.property_types import PropertyType


# =============================================================================
# CONSTANTS
# =============================================================================

SUBFLOW_SCHEMA_VERSION: str = "1.0.0"
MAX_NESTING_DEPTH: int = 3
SUBFLOWS_DIRECTORY: str = "subflows"


def generate_subflow_id() -> str:
    """Generate unique subflow identifier."""
    return f"subflow_{uuid.uuid4().hex[:12]}"


# Type alias for serialized connection data
SerializedConnection = Dict[str, Any]


@dataclass
class SubflowPort:
    """
    Defines an input or output port for a subflow.

    Ports define the interface contract for data flowing in/out of the subflow.
    Can be auto-detected from unconnected ports of boundary nodes, or manually defined.

    Attributes:
        name: Port name (must be valid Python identifier)
        data_type: Type of data this port accepts/emits (DataType enum)
        description: Human-readable description of the port's purpose
        default_value: Default value for input ports (None for outputs)
        required: If True, this input must be connected (inputs only)
        internal_node_id: Reference to internal node this port maps to
        internal_port_name: Reference to internal port this maps to
    """

    name: str
    data_type: DataType = DataType.ANY
    description: str = ""
    default_value: Any = None
    required: bool = False
    internal_node_id: str = ""
    internal_port_name: str = ""

    def __post_init__(self) -> None:
        """Validate port attributes after initialization."""
        if not self.name:
            raise ValueError("SubflowPort name cannot be empty")
        if not self.name.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"SubflowPort name '{self.name}' contains invalid characters"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize port to dictionary."""
        return {
            "name": self.name,
            "type": self.data_type.name
            if isinstance(self.data_type, DataType)
            else str(self.data_type),
            "description": self.description,
            "default_value": self.default_value,
            "required": self.required,
            "internal_node_id": self.internal_node_id,
            "internal_port_name": self.internal_port_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubflowPort":
        """Create port from dictionary."""
        # Handle both old format (port_type/data_type strings) and new format (type as DataType)
        data_type_str = data.get("type") or data.get("data_type", "ANY")
        try:
            if isinstance(data_type_str, str):
                data_type = DataType[data_type_str.upper()]
            else:
                data_type = DataType.ANY
        except KeyError:
            logger.warning(f"Unknown DataType '{data_type_str}', defaulting to ANY")
            data_type = DataType.ANY

        return cls(
            name=data.get("name", ""),
            data_type=data_type,
            description=data.get("description", ""),
            default_value=data.get("default_value"),
            required=data.get("required", False),
            internal_node_id=data.get("internal_node_id", ""),
            internal_port_name=data.get("internal_port_name", ""),
        )


@dataclass
class SubflowParameter:
    """
    Definition of a promoted parameter exposed at the subflow level.

    Maps a subflow-level parameter to an internal node's configuration property.
    Allows users to configure internal nodes without opening the subflow editor.

    Attributes:
        name: Unique qualified name (e.g., "navigate_123_url")
        display_name: User-facing label (e.g., "Login URL")
        internal_node_id: Which internal node owns this property
        internal_property_name: Property name on the internal node
        property_type: Type (STRING, INTEGER, FILE_PATH, etc.)
        default_value: Override for internal node's default
        label: UI label (falls back to display_name)
        description: Tooltip text
        placeholder: Placeholder for input widgets
        required: Whether value must be provided
        min_value: For numeric types
        max_value: For numeric types
        choices: For CHOICE type
        chain: For nested promotion: ["subflow_id", "param_name"]
    """

    # Identity
    name: str
    display_name: str

    # Mapping to internal node
    internal_node_id: str
    internal_property_name: str

    # Type info (locked from source PropertyDef)
    property_type: PropertyType

    # Value handling
    default_value: Any = None

    # UI configuration
    label: str = ""
    description: str = ""
    placeholder: str = ""

    # Validation
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    choices: Optional[List[str]] = None

    # Nested subflow chaining (max depth = 2)
    chain: Optional[List[str]] = None

    def __post_init__(self) -> None:
        """Validate and set defaults after initialization."""
        if not self.name:
            raise ValueError("SubflowParameter name cannot be empty")
        if not self.internal_node_id:
            raise ValueError("SubflowParameter internal_node_id cannot be empty")
        if not self.internal_property_name:
            raise ValueError("SubflowParameter internal_property_name cannot be empty")
        if not self.label:
            self.label = self.display_name

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "internal_node_id": self.internal_node_id,
            "internal_property_name": self.internal_property_name,
            "property_type": self.property_type.value
            if isinstance(self.property_type, PropertyType)
            else str(self.property_type),
            "default_value": self.default_value,
            "label": self.label,
            "description": self.description,
            "placeholder": self.placeholder,
            "required": self.required,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "choices": self.choices,
            "chain": self.chain,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubflowParameter":
        """Create from dictionary."""
        property_type_str = data.get("property_type", "string")
        try:
            if isinstance(property_type_str, str):
                property_type = PropertyType(property_type_str)
            elif isinstance(property_type_str, PropertyType):
                property_type = property_type_str
            else:
                property_type = PropertyType.STRING
        except ValueError:
            logger.warning(
                f"Unknown PropertyType '{property_type_str}', defaulting to STRING"
            )
            property_type = PropertyType.STRING

        return cls(
            name=data.get("name", ""),
            display_name=data.get("display_name", data.get("name", "")),
            internal_node_id=data.get("internal_node_id", ""),
            internal_property_name=data.get("internal_property_name", ""),
            property_type=property_type,
            default_value=data.get("default_value"),
            label=data.get("label", ""),
            description=data.get("description", ""),
            placeholder=data.get("placeholder", ""),
            required=data.get("required", False),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            choices=data.get("choices"),
            chain=data.get("chain"),
        )

    def to_property_def(self) -> "PropertyDef":
        """
        Convert to PropertyDef for widget generation.

        Returns:
            PropertyDef matching this parameter's configuration
        """
        from casare_rpa.domain.schemas.property_schema import PropertyDef

        return PropertyDef(
            name=self.name,
            type=self.property_type,
            default=self.default_value,
            label=self.label or self.display_name,
            placeholder=self.placeholder,
            choices=self.choices,
            tooltip=self.description,
            required=self.required,
            min_value=self.min_value,
            max_value=self.max_value,
        )


@dataclass
class SubflowMetadata:
    """
    Metadata for a subflow including categorization and authorship.

    Attributes:
        icon: Icon name/path for visual representation
        author: Creator of the subflow
        tags: List of tags for searchability
        color: Header color (hex string)
    """

    icon: str = "subflow"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    color: str = "#6366F1"  # Indigo default for subflows

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to dictionary."""
        return {
            "icon": self.icon,
            "author": self.author,
            "tags": self.tags,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubflowMetadata":
        """Create metadata from dictionary."""
        return cls(
            icon=data.get("icon", "subflow"),
            author=data.get("author", ""),
            tags=data.get("tags", []),
            color=data.get("color", "#6366F1"),
        )


@dataclass
class Subflow:
    """
    Domain entity representing a reusable workflow fragment.

    A subflow contains:
    - Metadata (id, name, version, description, timestamps)
    - Input/output port definitions
    - Internal nodes and connections
    - Category for organization

    Features:
    - Version tracking (semantic versioning)
    - Nesting support (subflows can contain subflows, max depth: 3)
    - Circular reference detection
    - Serialization to JSON files in workflows/subflows/

    Attributes:
        id: Unique identifier (subflow_<uuid>)
        name: Human-readable name
        version: Semantic version string (e.g., "1.0.0")
        description: Purpose and usage description
        category: Category for organizing in node palette
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        inputs: List of input port definitions
        outputs: List of output port definitions
        nodes: Dict of serialized node data
        connections: List of serialized connection data
        metadata: Additional metadata (icon, author, tags, color)
        bounds: Visual layout hints for the subflow boundary
        schema_version: Schema version for serialization compatibility
    """

    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    category: str = "subflows"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Port definitions (detected from unconnected boundary ports)
    inputs: List[SubflowPort] = field(default_factory=list)
    outputs: List[SubflowPort] = field(default_factory=list)

    # Internal structure (serialized nodes and connections)
    nodes: Dict[NodeId, SerializedNode] = field(default_factory=dict)
    connections: List[SerializedConnection] = field(default_factory=list)

    # Promoted parameters (expose internal node properties at subflow level)
    parameters: List[SubflowParameter] = field(default_factory=list)

    # Additional metadata
    metadata: SubflowMetadata = field(default_factory=SubflowMetadata)

    # Visual layout hints
    bounds: Optional[Dict[str, float]] = None  # {"x", "y", "width", "height"}

    # Schema version for compatibility
    schema_version: str = SUBFLOW_SCHEMA_VERSION

    # Runtime properties (not serialized)
    _path: Optional[Path] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Validate subflow attributes after initialization."""
        if not self.id:
            raise ValueError("Subflow id cannot be empty")
        if not self.name:
            raise ValueError("Subflow name cannot be empty")
        if len(self.name) > 128:
            raise ValueError(f"Subflow name too long: {len(self.name)} chars (max 128)")
        self._validate_unique_port_names()

    def _validate_unique_port_names(self) -> None:
        """Validate that port names are unique within inputs and outputs."""
        input_names = [p.name for p in self.inputs]
        if len(input_names) != len(set(input_names)):
            raise ValueError("Duplicate input port names detected")

        output_names = [p.name for p in self.outputs]
        if len(output_names) != len(set(output_names)):
            raise ValueError("Duplicate output port names detected")

    def _touch(self) -> None:
        """Update modified timestamp."""
        self.updated_at = datetime.now()

    @property
    def path(self) -> Optional[Path]:
        """Get subflow file path."""
        return self._path

    @path.setter
    def path(self, value: Path) -> None:
        """Set subflow file path."""
        self._path = value

    def add_input(self, port: SubflowPort) -> None:
        """
        Add an input port to the subflow.

        Args:
            port: SubflowPort to add as input

        Raises:
            ValueError: If port name already exists in inputs
        """
        if any(p.name == port.name for p in self.inputs):
            raise ValueError(f"Input port '{port.name}' already exists")
        self.inputs.append(port)
        self._touch()

    def add_output(self, port: SubflowPort) -> None:
        """
        Add an output port to the subflow.

        Args:
            port: SubflowPort to add as output

        Raises:
            ValueError: If port name already exists in outputs
        """
        if any(p.name == port.name for p in self.outputs):
            raise ValueError(f"Output port '{port.name}' already exists")
        self.outputs.append(port)
        self._touch()

    def remove_input(self, port_name: str) -> bool:
        """
        Remove an input port by name.

        Args:
            port_name: Name of the port to remove

        Returns:
            True if port was removed, False if not found
        """
        for i, port in enumerate(self.inputs):
            if port.name == port_name:
                self.inputs.pop(i)
                self._touch()
                return True
        return False

    def remove_output(self, port_name: str) -> bool:
        """
        Remove an output port by name.

        Args:
            port_name: Name of the port to remove

        Returns:
            True if port was removed, False if not found
        """
        for i, port in enumerate(self.outputs):
            if port.name == port_name:
                self.outputs.pop(i)
                self._touch()
                return True
        return False

    def get_input(self, port_name: str) -> Optional[SubflowPort]:
        """Get input port by name."""
        for port in self.inputs:
            if port.name == port_name:
                return port
        return None

    def get_output(self, port_name: str) -> Optional[SubflowPort]:
        """Get output port by name."""
        for port in self.outputs:
            if port.name == port_name:
                return port
        return None

    def add_node(self, node_data: SerializedNode) -> None:
        """
        Add a node to the subflow.

        Args:
            node_data: Serialized node data
        """
        node_id = node_data["node_id"]
        self.nodes[node_id] = node_data
        self._touch()

    def remove_node(self, node_id: NodeId) -> bool:
        """
        Remove a node and its connections from the subflow.

        Args:
            node_id: ID of node to remove

        Returns:
            True if node was removed, False if not found
        """
        if node_id not in self.nodes:
            return False

        del self.nodes[node_id]
        # Remove connections involving this node
        self.connections = [
            conn
            for conn in self.connections
            if conn.get("source_node") != node_id and conn.get("target_node") != node_id
        ]
        self._touch()
        return True

    def add_connection(self, connection: NodeConnection) -> None:
        """
        Add a connection between internal nodes.

        Args:
            connection: NodeConnection to add
        """
        self.connections.append(connection.to_dict())
        self._touch()

    def add_connection_dict(self, connection_data: Dict[str, Any]) -> None:
        """
        Add a connection from dictionary data.

        Args:
            connection_data: Serialized connection data
        """
        self.connections.append(connection_data)
        self._touch()

    # =========================================================================
    # PROMOTED PARAMETERS
    # =========================================================================

    def add_parameter(self, param: SubflowParameter) -> None:
        """
        Add a promoted parameter to the subflow.

        Args:
            param: SubflowParameter to add

        Raises:
            ValueError: If parameter name already exists
        """
        if any(p.name == param.name for p in self.parameters):
            raise ValueError(f"Parameter '{param.name}' already exists")
        self.parameters.append(param)
        self._touch()

    def remove_parameter(self, param_name: str) -> bool:
        """
        Remove a promoted parameter by name.

        Args:
            param_name: Name of the parameter to remove

        Returns:
            True if parameter was removed, False if not found
        """
        for i, param in enumerate(self.parameters):
            if param.name == param_name:
                self.parameters.pop(i)
                self._touch()
                return True
        return False

    def get_parameter(self, param_name: str) -> Optional[SubflowParameter]:
        """
        Get a promoted parameter by name.

        Args:
            param_name: Name of the parameter

        Returns:
            SubflowParameter if found, None otherwise
        """
        for param in self.parameters:
            if param.name == param_name:
                return param
        return None

    def validate_parameters(self) -> List[str]:
        """
        Validate that all promoted parameters still reference valid internal nodes.

        Returns:
            List of warning messages for invalid parameters
        """
        warnings: List[str] = []
        for param in self.parameters:
            if param.internal_node_id not in self.nodes:
                warnings.append(
                    f"Parameter '{param.display_name}' references missing node '{param.internal_node_id}'"
                )
        return warnings

    # =========================================================================
    # NESTING AND CIRCULAR REFERENCE DETECTION
    # =========================================================================

    def get_nested_subflow_ids(self) -> Set[str]:
        """
        Get IDs of all subflows nested within this subflow.

        Returns:
            Set of subflow IDs referenced by SubflowNode instances
        """
        subflow_ids: Set[str] = set()
        for node_data in self.nodes.values():
            node_type = node_data.get("node_type", "")
            if node_type == "SubflowNode":
                subflow_id = node_data.get("properties", {}).get("subflow_id")
                if subflow_id:
                    subflow_ids.add(subflow_id)
        return subflow_ids

    def validate_nesting_depth(
        self,
        subflow_registry: Dict[str, "Subflow"],
        current_depth: int = 0,
    ) -> tuple[bool, str]:
        """
        Validate that nesting depth does not exceed MAX_NESTING_DEPTH.

        Args:
            subflow_registry: Dictionary mapping subflow IDs to Subflow instances
            current_depth: Current nesting level (starts at 0)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if current_depth > MAX_NESTING_DEPTH:
            return False, (
                f"Nesting depth {current_depth} exceeds maximum of {MAX_NESTING_DEPTH}"
            )

        nested_ids = self.get_nested_subflow_ids()
        for nested_id in nested_ids:
            nested_subflow = subflow_registry.get(nested_id)
            if nested_subflow is None:
                return False, f"Referenced subflow '{nested_id}' not found"

            is_valid, error = nested_subflow.validate_nesting_depth(
                subflow_registry, current_depth + 1
            )
            if not is_valid:
                return False, error

        return True, ""

    def detect_circular_reference(
        self,
        subflow_registry: Dict[str, "Subflow"],
        visited: Optional[Set[str]] = None,
    ) -> tuple[bool, List[str]]:
        """
        Detect circular references in subflow nesting.

        Args:
            subflow_registry: Dictionary mapping subflow IDs to Subflow instances
            visited: Set of already visited subflow IDs (for recursion tracking)

        Returns:
            Tuple of (has_cycle, cycle_path) where cycle_path shows the cycle
        """
        if visited is None:
            visited = set()

        if self.id in visited:
            return True, [self.id]

        visited = visited | {self.id}

        nested_ids = self.get_nested_subflow_ids()
        for nested_id in nested_ids:
            nested_subflow = subflow_registry.get(nested_id)
            if nested_subflow is None:
                continue

            has_cycle, cycle_path = nested_subflow.detect_circular_reference(
                subflow_registry, visited
            )
            if has_cycle:
                return True, [self.id] + cycle_path

        return False, []

    # =========================================================================
    # VERSION MANAGEMENT
    # =========================================================================

    def increment_version(self, level: str = "patch") -> str:
        """
        Increment the subflow version.

        Args:
            level: Version level to increment ('major', 'minor', or 'patch')

        Returns:
            New version string

        Raises:
            ValueError: If version format is invalid or level is unknown
        """
        parts = self.version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {self.version}")

        try:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(f"Invalid version format: {self.version}")

        if level == "major":
            major += 1
            minor = 0
            patch = 0
        elif level == "minor":
            minor += 1
            patch = 0
        elif level == "patch":
            patch += 1
        else:
            raise ValueError(f"Unknown version level: {level}")

        self.version = f"{major}.{minor}.{patch}"
        self._touch()

        return self.version

    def clone(
        self, new_id: Optional[str] = None, new_name: Optional[str] = None
    ) -> "Subflow":
        """
        Create a deep copy of this subflow with a new ID.

        Args:
            new_id: Optional new ID. If None, generates a new one.
            new_name: Optional new name. If None, appends " (Copy)" to current name.

        Returns:
            New Subflow instance with copied data
        """
        import copy

        cloned = Subflow(
            id=new_id or generate_subflow_id(),
            name=new_name or f"{self.name} (Copy)",
            version="1.0.0",  # Reset version for clones
            description=self.description,
            category=self.category,
            inputs=[copy.deepcopy(p) for p in self.inputs],
            outputs=[copy.deepcopy(p) for p in self.outputs],
            nodes=copy.deepcopy(self.nodes),
            connections=copy.deepcopy(self.connections),
            parameters=[copy.deepcopy(p) for p in self.parameters],
            metadata=SubflowMetadata(
                icon=self.metadata.icon,
                author=self.metadata.author,
                tags=list(self.metadata.tags),
                color=self.metadata.color,
            ),
            bounds=copy.deepcopy(self.bounds) if self.bounds else None,
        )

        return cloned

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize subflow to dictionary for JSON storage.

        Returns:
            Complete subflow data structure
        """
        return {
            "$schema_version": self.schema_version,
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "inputs": [p.to_dict() for p in self.inputs],
            "outputs": [p.to_dict() for p in self.outputs],
            "parameters": [p.to_dict() for p in self.parameters],
            "nodes": self.nodes,
            "connections": self.connections,
            "metadata": self.metadata.to_dict(),
            "bounds": self.bounds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Subflow":
        """
        Create subflow from dictionary.

        Args:
            data: Serialized subflow data

        Returns:
            Subflow instance
        """
        # Parse timestamps
        created_at = None
        updated_at = None

        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid created_at timestamp: {data.get('created_at')}"
                )

        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid updated_at timestamp: {data.get('updated_at')}"
                )

        # Parse ports using SubflowPort.from_dict for consistent handling
        inputs = [SubflowPort.from_dict(p) for p in data.get("inputs", [])]
        outputs = [SubflowPort.from_dict(p) for p in data.get("outputs", [])]

        # Parse promoted parameters
        parameters = [SubflowParameter.from_dict(p) for p in data.get("parameters", [])]

        # Parse metadata
        metadata = SubflowMetadata.from_dict(data.get("metadata", {}))

        subflow = cls(
            id=data.get("id", generate_subflow_id()),
            name=data.get("name", "Untitled Subflow"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            category=data.get("category", "subflows"),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            inputs=inputs,
            outputs=outputs,
            nodes=data.get("nodes", {}),
            connections=data.get("connections", []),
            parameters=parameters,
            metadata=metadata,
            bounds=data.get("bounds"),
            schema_version=data.get("$schema_version", SUBFLOW_SCHEMA_VERSION),
        )

        return subflow

    def save_to_file(self, file_path: Optional[str] = None) -> Path:
        """
        Save subflow to JSON file.

        Args:
            file_path: Optional path override. If None, uses self._path.

        Returns:
            Path where the file was saved

        Raises:
            ValueError: If no path provided and no default path set
        """
        save_path: Path
        if file_path:
            save_path = Path(file_path)
        elif self._path:
            save_path = self._path
        else:
            raise ValueError(
                "No path specified and no default path set. "
                "Either provide file_path argument or set subflow.path first."
            )

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # Update modified timestamp
            self._touch()

            data = self.to_dict()
            json_bytes = orjson.dumps(data, option=orjson.OPT_INDENT_2)

            with open(save_path, "wb") as f:
                f.write(json_bytes)

            self._path = save_path
            logger.debug(f"Saved subflow '{self.name}' to {save_path}")

            return save_path
        except Exception as e:
            logger.error(f"Failed to save subflow to {save_path}: {e}")
            raise

    @classmethod
    def load_from_file(cls, file_path: str) -> "Subflow":
        """
        Load subflow from JSON file.

        Args:
            file_path: Path to the subflow JSON file

        Returns:
            Subflow instance

        Raises:
            FileNotFoundError: If file does not exist
            orjson.JSONDecodeError: If file is not valid JSON
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Subflow file not found: {path}")

        try:
            with open(path, "rb") as f:
                data = orjson.loads(f.read())

            subflow = cls.from_dict(data)
            subflow._path = path
            logger.debug(f"Loaded subflow '{subflow.name}' from {file_path}")
            return subflow
        except orjson.JSONDecodeError as e:
            logger.error(f"Invalid JSON in subflow file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load subflow from {file_path}: {e}")
            raise

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Subflow(id='{self.id}', name='{self.name}', "
            f"version='{self.version}', "
            f"inputs={len(self.inputs)}, outputs={len(self.outputs)}, "
            f"nodes={len(self.nodes)})"
        )
