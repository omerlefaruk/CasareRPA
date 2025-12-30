# Data Operation Node Templates

> File, String, List, Variable, and Dict operation templates for CasareRPA.
> **Category**: Data transformation templates

## Template 4: File Operation Node

**Use for**: Reading, writing, copying, deleting files

```python
"""
File {Operation} Node

{Brief description - single atomic file operation.}
"""

from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# File operation properties
FILE_PATH_PROP = PropertyDef(
    "file_path",
    PropertyType.FILE_PATH,
    required=True,
    label="File Path",
    tooltip="Path to the file",
    tab="properties",
)

ENCODING_PROP = PropertyDef(
    "encoding",
    PropertyType.CHOICE,
    default="utf-8",
    choices=["utf-8", "utf-16", "ascii", "latin-1"],
    label="Encoding",
    tooltip="Text encoding for the file",
    tab="advanced",
)

CREATE_IF_NOT_EXISTS_PROP = PropertyDef(
    "create_if_not_exists",
    PropertyType.BOOLEAN,
    default=False,
    label="Create If Not Exists",
    tooltip="Create parent directories if they don't exist",
    tab="advanced",
)


@node_schema(
    FILE_PATH_PROP,
    ENCODING_PROP,
    CREATE_IF_NOT_EXISTS_PROP,
)
@executable_node
class File{Operation}Node(BaseNode):
    """
    {One-line description of file operation}.

    Config (via @node_schema):
        file_path: Path to the file (required)
        encoding: Text encoding (default: utf-8)
        create_if_not_exists: Create directories if needed (default: False)

    Inputs:
        file_path: File path (overrides config)
        content: Content to write (for write operations)

    Outputs:
        content: File content (for read operations)
        success: Whether operation succeeded
        file_path: Absolute path to the file
    """

    NODE_NAME = "File {Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "File {Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "File{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("content", PortType.INPUT, DataType.STRING, required=False)
        self.add_output_port("content", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the file operation."""
        file_path = self.get_parameter("file_path", context)
        encoding = self.get_parameter("encoding", context)
        create_dirs = self.get_parameter("create_if_not_exists", context)

        if not file_path:
            raise ValueError("File path is required")

        path = Path(file_path)
        logger.info(f"[{self.name}] {Operation} file: {path}")

        try:
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            # ===== YOUR ATOMIC FILE OPERATION HERE =====
            content = path.read_text(encoding=encoding)
            # ============================================

            return self.success_result(
                content=content,
                success=True,
                file_path=str(path.absolute()),
            )

        except FileNotFoundError:
            logger.error(f"[{self.name}] File not found: {path}")
            self.status = NodeStatus.ERROR
            raise
        except Exception as e:
            logger.error(f"[{self.name}] File operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

## Template 8: String Operation Node

**Use for**: String manipulation, parsing, formatting

```python
"""
String {Operation} Node

{Brief description - single atomic string operation.}
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# String operation properties
CASE_SENSITIVE_PROP = PropertyDef(
    "case_sensitive",
    PropertyType.BOOLEAN,
    default=True,
    label="Case Sensitive",
    tooltip="Whether operation is case-sensitive",
    tab="properties",
)

PATTERN_PROP = PropertyDef(
    "pattern",
    PropertyType.STRING,
    default="",
    label="Pattern",
    tooltip="Search pattern or regex",
    tab="properties",
)


@node_schema(CASE_SENSITIVE_PROP, PATTERN_PROP)
@executable_node
class String{Operation}Node(BaseNode):
    """
    {One-line description of string operation}.

    Config (via @node_schema):
        case_sensitive: Case-sensitive operation (default: True)
        pattern: Search pattern or regex

    Inputs:
        text: Input string to process

    Outputs:
        result: Processed string result
        success: Whether operation succeeded
    """

    NODE_NAME = "String {Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "String {Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "String{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the string operation."""
        text = self.get_input_value("text")
        case_sensitive = self.get_parameter("case_sensitive", context)
        pattern = self.get_parameter("pattern", context)

        if text is None:
            raise ValueError("Input text is required")

        logger.debug(f"[{self.name}] Processing string of length {len(text)}")

        try:
            # ===== YOUR ATOMIC STRING OPERATION HERE =====
            result = text.upper()  # Example: uppercase
            # =============================================

            return self.success_result(result=result, success=True)

        except Exception as e:
            logger.error(f"[{self.name}] String operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

## Template 9: List Operation Node

**Use for**: List manipulation, filtering, sorting

```python
"""
List {Operation} Node

{Brief description - single atomic list operation.}
"""

from typing import Any, Dict, List as ListType, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# List operation properties
INDEX_PROP = PropertyDef(
    "index",
    PropertyType.INTEGER,
    default=0,
    label="Index",
    tooltip="Index position (0-based)",
    tab="properties",
)

REVERSE_PROP = PropertyDef(
    "reverse",
    PropertyType.BOOLEAN,
    default=False,
    label="Reverse",
    tooltip="Reverse the operation",
    tab="properties",
)


@node_schema(INDEX_PROP, REVERSE_PROP)
@executable_node
class List{Operation}Node(BaseNode):
    """
    {One-line description of list operation}.

    Config (via @node_schema):
        index: Index position for operation (default: 0)
        reverse: Reverse the operation (default: False)

    Inputs:
        list: Input list to process
        item: Item for add/insert operations

    Outputs:
        result: Processed list or extracted item
        count: Number of items in result
    """

    NODE_NAME = "List {Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "List {Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "List{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("item", PortType.INPUT, DataType.ANY, required=False)
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the list operation."""
        input_list = self.get_input_value("list")
        item = self.get_input_value("item")
        index = self.get_parameter("index", context)
        reverse = self.get_parameter("reverse", context)

        if input_list is None:
            input_list = []

        logger.debug(f"[{self.name}] Processing list of {len(input_list)} items")

        try:
            # ===== YOUR ATOMIC LIST OPERATION HERE =====
            result = sorted(input_list, reverse=reverse)  # Example: sort
            # ============================================

            count = len(result) if isinstance(result, list) else 1
            return self.success_result(result=result, count=count)

        except Exception as e:
            logger.error(f"[{self.name}] List operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

## Template 10: Variable Node

**Use for**: Getting/setting workflow variables

```python
"""
{Operation} Variable Node

{Brief description - single atomic variable operation.}
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# Variable operation properties
VARIABLE_NAME_PROP = PropertyDef(
    "variable_name",
    PropertyType.STRING,
    required=True,
    label="Variable Name",
    tooltip="Name of the workflow variable",
    tab="properties",
)

DEFAULT_VALUE_PROP = PropertyDef(
    "default_value",
    PropertyType.STRING,
    default="",
    label="Default Value",
    tooltip="Default value if variable not found",
    tab="properties",
)

VARIABLE_TYPE_PROP = PropertyDef(
    "variable_type",
    PropertyType.CHOICE,
    default="String",
    choices=["String", "Integer", "Float", "Boolean", "List", "Dict"],
    label="Variable Type",
    tooltip="Type to cast the value to",
    tab="properties",
)


@node_schema(
    VARIABLE_NAME_PROP,
    DEFAULT_VALUE_PROP,
    VARIABLE_TYPE_PROP,
)
@executable_node
class {Operation}VariableNode(BaseNode):
    """
    {One-line description of variable operation}.

    Config (via @node_schema):
        variable_name: Name of variable (required)
        default_value: Default if not found
        variable_type: Type to cast to (default: String)

    Inputs:
        value: Value to set (for set operations)
        variable_name: Name (overrides config)

    Outputs:
        value: The variable value
    """

    NODE_NAME = "{Operation} Variable"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "{Operation} Variable",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "{Operation}VariableNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("value", PortType.INPUT, DataType.ANY, required=False)
        self.add_input_port("variable_name", PortType.INPUT, DataType.STRING, required=False)
        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the variable operation."""
        var_name = self.get_parameter("variable_name", context)
        default = self.get_parameter("default_value", context)
        var_type = self.get_parameter("variable_type", context)

        if not var_name:
            raise ValueError("Variable name is required")

        logger.debug(f"[{self.name}] {Operation} variable: {var_name}")

        try:
            # ===== YOUR ATOMIC VARIABLE OPERATION HERE =====
            variables = getattr(context, "variables", {})
            value = variables.get(var_name, default)
            # ===============================================

            value = self._cast_value(value, var_type)
            return self.success_result(value=value)

        except Exception as e:
            logger.error(f"[{self.name}] Variable operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise

    def _cast_value(self, value: Any, var_type: str) -> Any:
        """Cast value to specified type."""
        if value is None:
            return None
        if var_type == "Integer":
            return int(value)
        elif var_type == "Float":
            return float(value)
        elif var_type == "Boolean":
            return bool(value)
        elif var_type == "List":
            return list(value) if not isinstance(value, list) else value
        elif var_type == "Dict":
            return dict(value) if not isinstance(value, dict) else value
        return str(value)
```

## PropertyDef Quick Reference (Data Types)

| Type | Use Case | Example Value |
|------|----------|---------------|
| STRING | Single-line text | "hello world" |
| TEXT | Multi-line text | "Line 1\nLine 2" |
| INTEGER | Whole numbers | 42 |
| FLOAT | Decimal numbers | 3.14 |
| BOOLEAN | True/False | True |
| LIST | Array/list | [1, 2, 3] |
| DICT | Object/dict | {"key": "value"} |
| FILE_PATH | File picker path | "C:/data/file.txt" |
| DIRECTORY_PATH | Folder picker path | "C:/data/" |

---

**See also**: `node-templates-core.md` | `node-templates-services.md` | `node-checklist.md`
