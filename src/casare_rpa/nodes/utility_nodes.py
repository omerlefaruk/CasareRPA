"""
Utility nodes for common operations.

This module provides nodes for data validation, data transformation,
and explicit logging within workflows.
"""

import json
import re
import asyncio
from typing import Any, Dict, Optional
from enum import Enum

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


class ValidationType(str, Enum):
    """Data validation types."""

    NOT_EMPTY = "not_empty"
    IS_STRING = "is_string"
    IS_NUMBER = "is_number"
    IS_INTEGER = "is_integer"
    IS_BOOLEAN = "is_boolean"
    IS_LIST = "is_list"
    IS_DICT = "is_dict"
    MATCHES_REGEX = "matches_regex"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    IN_LIST = "in_list"
    IS_EMAIL = "is_email"
    IS_URL = "is_url"
    CUSTOM = "custom"


@properties(
    PropertyDef(
        "validation_type",
        PropertyType.CHOICE,
        default="not_empty",
        choices=[
            "not_empty",
            "is_string",
            "is_number",
            "is_integer",
            "is_boolean",
            "is_list",
            "is_dict",
            "matches_regex",
            "min_length",
            "max_length",
            "min_value",
            "max_value",
            "in_list",
            "is_email",
            "is_url",
            "custom",
        ],
        label="Validation Type",
        tooltip="Type of validation to perform",
    ),
    PropertyDef(
        "validation_param",
        PropertyType.ANY,
        default=None,
        label="Validation Parameter",
        tooltip="Parameter for validation (e.g., regex pattern, min value)",
    ),
    PropertyDef(
        "error_message",
        PropertyType.STRING,
        default="Validation failed",
        label="Error Message",
        tooltip="Custom error message on validation failure",
    ),
)
@node(category="utility")
class ValidateNode(BaseNode):
    """
    Validate node - validates data against rules.

    Routes to different outputs based on validation success/failure.

    Config (via @properties):
        validation_type: Type of validation to perform
        validation_param: Parameter for validation
        error_message: Custom error message
    """

    # @category: data
    # @requires: requests
    # @ports: value -> valid, invalid, is_valid, error_message

    def __init__(
        self,
        node_id: str,
        name: str = "Validate",
        **kwargs,
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ValidateNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("value", DataType.ANY)

        self.add_output_port("valid", DataType.EXECUTION)  # Route when valid
        self.add_output_port("invalid", DataType.EXECUTION)  # Route when invalid
        self.add_output_port("is_valid", DataType.BOOLEAN)
        self.add_output_port("error_message", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute validation.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with validation status and routing
        """
        self.status = NodeStatus.RUNNING

        try:
            value = self.get_parameter("value")
            validation_type = self.get_parameter("validation_type", "not_empty")
            validation_param = self.get_parameter("validation_param")

            is_valid, error_msg = self._validate(
                value, validation_type, validation_param
            )

            self.set_output_value("is_valid", is_valid)
            self.set_output_value("error_message", error_msg if not is_valid else "")

            logger.info(
                f"Validation '{validation_type}': {'passed' if is_valid else 'failed'}"
            )

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "is_valid": is_valid,
                "error_message": error_msg,
                "next_nodes": ["valid" if is_valid else "invalid"],
            }

        except Exception as e:
            error_msg = f"Validation error: {e}"
            logger.exception(error_msg)
            self.set_output_value("is_valid", False)
            self.set_output_value("error_message", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": ["invalid"]}

    def _validate(
        self, value: Any, validation_type: str, param: Any
    ) -> tuple[bool, str]:
        """Perform validation and return (is_valid, error_message)."""
        try:
            vtype = ValidationType(validation_type)
        except ValueError:
            return False, f"Unknown validation type: {validation_type}"

        if vtype == ValidationType.NOT_EMPTY:
            if value is None or value == "" or value == [] or value == {}:
                return False, "Value is empty"
            return True, ""

        elif vtype == ValidationType.IS_STRING:
            if not isinstance(value, str):
                return False, f"Expected string, got {type(value).__name__}"
            return True, ""

        elif vtype == ValidationType.IS_NUMBER:
            if not isinstance(value, (int, float)):
                return False, f"Expected number, got {type(value).__name__}"
            return True, ""

        elif vtype == ValidationType.IS_INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                return False, f"Expected integer, got {type(value).__name__}"
            return True, ""

        elif vtype == ValidationType.IS_BOOLEAN:
            if not isinstance(value, bool):
                return False, f"Expected boolean, got {type(value).__name__}"
            return True, ""

        elif vtype == ValidationType.IS_LIST:
            if not isinstance(value, list):
                return False, f"Expected list, got {type(value).__name__}"
            return True, ""

        elif vtype == ValidationType.IS_DICT:
            if not isinstance(value, dict):
                return False, f"Expected dict, got {type(value).__name__}"
            return True, ""

        elif vtype == ValidationType.MATCHES_REGEX:
            if param is None:
                return False, "Regex pattern required"
            if not isinstance(value, str):
                return False, "Value must be string for regex match"
            if not re.match(param, value):
                return False, f"Value does not match pattern: {param}"
            return True, ""

        elif vtype == ValidationType.MIN_LENGTH:
            if param is None:
                return False, "Minimum length required"
            if not hasattr(value, "__len__"):
                return False, "Value has no length"
            if len(value) < param:
                return False, f"Length {len(value)} < minimum {param}"
            return True, ""

        elif vtype == ValidationType.MAX_LENGTH:
            if param is None:
                return False, "Maximum length required"
            if not hasattr(value, "__len__"):
                return False, "Value has no length"
            if len(value) > param:
                return False, f"Length {len(value)} > maximum {param}"
            return True, ""

        elif vtype == ValidationType.MIN_VALUE:
            if param is None:
                return False, "Minimum value required"
            if not isinstance(value, (int, float)):
                return False, "Value must be numeric"
            if value < param:
                return False, f"Value {value} < minimum {param}"
            return True, ""

        elif vtype == ValidationType.MAX_VALUE:
            if param is None:
                return False, "Maximum value required"
            if not isinstance(value, (int, float)):
                return False, "Value must be numeric"
            if value > param:
                return False, f"Value {value} > maximum {param}"
            return True, ""

        elif vtype == ValidationType.IN_LIST:
            if param is None:
                return False, "List of allowed values required"
            if value not in param:
                return False, f"Value not in allowed list: {param}"
            return True, ""

        elif vtype == ValidationType.IS_EMAIL:
            if not isinstance(value, str):
                return False, "Value must be string"
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, value):
                return False, "Invalid email format"
            return True, ""

        elif vtype == ValidationType.IS_URL:
            if not isinstance(value, str):
                return False, "Value must be string"
            url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
            if not re.match(url_pattern, value):
                return False, "Invalid URL format"
            return True, ""

        return False, f"Validation type not implemented: {validation_type}"


class TransformType(str, Enum):
    """Data transformation types."""

    TO_STRING = "to_string"
    TO_INTEGER = "to_integer"
    TO_FLOAT = "to_float"
    TO_BOOLEAN = "to_boolean"
    TO_LIST = "to_list"
    TO_JSON = "to_json"
    FROM_JSON = "from_json"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    TRIM = "trim"
    SPLIT = "split"
    JOIN = "join"
    REPLACE = "replace"
    REGEX_EXTRACT = "regex_extract"
    GET_KEY = "get_key"
    GET_INDEX = "get_index"
    MAP_VALUES = "map_values"
    FILTER_VALUES = "filter_values"


@properties(
    PropertyDef(
        "transform_type",
        PropertyType.CHOICE,
        default="to_string",
        choices=[
            "to_string",
            "to_integer",
            "to_float",
            "to_boolean",
            "to_list",
            "to_json",
            "from_json",
            "uppercase",
            "lowercase",
            "trim",
            "split",
            "join",
            "replace",
            "regex_extract",
            "get_key",
            "get_index",
            "map_values",
            "filter_values",
        ],
        label="Transform Type",
        tooltip="Type of transformation to perform",
    ),
    PropertyDef(
        "transform_param",
        PropertyType.ANY,
        default=None,
        label="Transform Parameter",
        tooltip="Parameter for transformation",
    ),
    PropertyDef(
        "variable_name",
        PropertyType.STRING,
        default="transformed",
        label="Variable Name",
        tooltip="Name of variable to store result",
    ),
)
@node(category="utility")
class TransformNode(BaseNode):
    """
    Transform node - transforms data from one format to another.

    Supports type conversions, string operations, and collection transformations.

    Config (via @properties):
        transform_type: Type of transformation to perform
        transform_param: Parameter for transformation
        variable_name: Variable name for result
    """

    # @category: data
    # @requires: requests
    # @ports: value, param -> result, success, error

    def __init__(
        self,
        node_id: str,
        name: str = "Transform",
        **kwargs,
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TransformNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("value", DataType.ANY)
        self.add_input_port("param", DataType.ANY)
        self.add_output_port("result", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute transformation.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with transformed data
        """
        self.status = NodeStatus.RUNNING

        try:
            value = self.get_parameter("value")
            transform_type = self.get_parameter("transform_type", "to_string")
            transform_param = self.get_parameter("param") or self.get_parameter(
                "transform_param"
            )

            result = self._transform(value, transform_type, transform_param)

            self.set_output_value("result", result)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            # Store in context
            variable_name = self.get_parameter("variable_name", "transformed")
            context.set_variable(variable_name, result)

            logger.info(f"Transform '{transform_type}' completed")

            self.status = NodeStatus.SUCCESS
            return {"success": True, "result": result, "next_nodes": ["exec_out"]}

        except Exception as e:
            error_msg = f"Transform error: {e}"
            logger.exception(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg}

    def _transform(self, value: Any, transform_type: str, param: Any) -> Any:
        """Perform transformation and return result."""
        try:
            ttype = TransformType(transform_type)
        except ValueError:
            raise ValueError(f"Unknown transform type: {transform_type}")

        if ttype == TransformType.TO_STRING:
            return str(value) if value is not None else ""

        elif ttype == TransformType.TO_INTEGER:
            if isinstance(value, bool):
                return 1 if value else 0
            return int(value)

        elif ttype == TransformType.TO_FLOAT:
            return float(value)

        elif ttype == TransformType.TO_BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)

        elif ttype == TransformType.TO_LIST:
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                return list(value)
            if isinstance(value, dict):
                return list(value.items())
            return [value]

        elif ttype == TransformType.TO_JSON:
            return json.dumps(value, default=str)

        elif ttype == TransformType.FROM_JSON:
            if isinstance(value, str):
                return json.loads(value)
            return value

        elif ttype == TransformType.UPPERCASE:
            return str(value).upper()

        elif ttype == TransformType.LOWERCASE:
            return str(value).lower()

        elif ttype == TransformType.TRIM:
            return str(value).strip()

        elif ttype == TransformType.SPLIT:
            delimiter = param if param else ","
            return str(value).split(delimiter)

        elif ttype == TransformType.JOIN:
            delimiter = param if param else ","
            return delimiter.join(str(v) for v in value)

        elif ttype == TransformType.REPLACE:
            if not param or not isinstance(param, dict):
                raise ValueError(
                    "Replace requires param dict with 'old' and 'new' keys"
                )
            return str(value).replace(param.get("old", ""), param.get("new", ""))

        elif ttype == TransformType.REGEX_EXTRACT:
            if not param:
                raise ValueError("Regex pattern required")
            match = re.search(param, str(value))
            return match.group(0) if match else None

        elif ttype == TransformType.GET_KEY:
            if not isinstance(value, dict):
                raise ValueError("Value must be dict for get_key")
            return value.get(param)

        elif ttype == TransformType.GET_INDEX:
            if not isinstance(value, (list, tuple, str)):
                raise ValueError("Value must be list, tuple, or string for get_index")
            idx = int(param) if param is not None else 0
            return value[idx] if abs(idx) < len(value) else None

        elif ttype == TransformType.MAP_VALUES:
            if not isinstance(value, list):
                raise ValueError("Value must be list for map_values")
            if not param:
                return value
            # param should be a key to extract from each dict in list
            return [
                item.get(param) if isinstance(item, dict) else item for item in value
            ]

        elif ttype == TransformType.FILTER_VALUES:
            if not isinstance(value, list):
                raise ValueError("Value must be list for filter_values")
            # Filter out None and empty values
            return [v for v in value if v is not None and v != ""]

        raise ValueError(f"Transform type not implemented: {transform_type}")


class LogLevel(str, Enum):
    """Log levels for LogNode."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@properties(
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="",
        label="Message",
        tooltip="Message to log (can include {variable} placeholders)",
    ),
    PropertyDef(
        "level",
        PropertyType.CHOICE,
        default="critical",
        choices=["debug", "info", "warning", "error", "critical"],
        label="Log Level",
        tooltip="Log level (debug, info, warning, error, critical)",
    ),
    PropertyDef(
        "include_timestamp",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Timestamp",
        tooltip="Include timestamp in log message",
    ),
    PropertyDef(
        "include_node_id",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Node ID",
        tooltip="Include node ID in log message",
    ),
)
@node(category="utility")
class LogNode(BaseNode):
    """
    Log node - explicit logging within workflows.

    Outputs messages to the log with configurable level and formatting.
    Useful for debugging and audit trails.

    Config (via @properties):
        message: Message to log
        level: Log level
        include_timestamp: Include timestamp
        include_node_id: Include node ID
    """

    # @category: data
    # @requires: requests
    # @ports: message, data -> none

    def __init__(
        self,
        node_id: str,
        name: str = "Log",
        **kwargs,
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "LogNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("message", DataType.STRING)
        self.add_input_port("data", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute logging.

        Args:
            context: Execution context for the workflow

        Returns:
            Result (always success unless exception)
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get message from input or config
            message_input = self.get_parameter("message", "")
            # Ensure message is a string (could be Page object or other type from connected node)
            message = str(message_input) if message_input else ""

            # Get optional data to log
            data = self.get_parameter("data")

            # Get log level
            level_str = self.get_parameter("level", "critical").lower()
            try:
                level = LogLevel(level_str)
            except ValueError:
                level = LogLevel.INFO

            # Format message with context variables
            try:
                formatted_message = message.format(**context.variables)
            except (KeyError, ValueError):
                formatted_message = message

            # Add node ID if configured
            if self.get_parameter("include_node_id", True):
                formatted_message = f"[{self.node_id}] {formatted_message}"

            # Add data if provided
            if data is not None:
                formatted_message += f" | Data: {data}"

            # Log at appropriate level
            log_func = getattr(logger, level.value)
            log_func(formatted_message)

            # Also print to terminal for visibility in Terminal tab
            # This allows users to see log output in the Terminal panel
            if self.get_parameter("print_to_terminal", True):
                print(f"[{level.value.upper()}] {formatted_message}")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "message": formatted_message,
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Log error: {e}"
            logger.exception(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg}


@properties()
@node(category="utility")
class RerouteNode(BaseNode):
    """
    Reroute Node - Houdini-style passthrough dot for organizing connections.

    A minimal node that simply passes its input value through to its output.
    Used to create clean wire routing without affecting data flow.

    Features:
    - Passes through any data type unchanged
    - Can operate in data mode (passes values) or exec mode (passes execution flow)
    - Inherits wire color from connected data type
    - Small diamond visual representation
    """

    # @category: data
    # @requires: requests
    # @ports: in -> out

    def __init__(
        self,
        node_id: str,
        name: str = "Reroute",
        **kwargs,
    ) -> None:
        """
        Initialize reroute node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        config = kwargs.get("config", {})
        config.setdefault("data_type", "ANY")
        config.setdefault("is_exec_reroute", False)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RerouteNode"
        self.category = "utility"
        self.description = "Passthrough dot for organizing connections"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Single input and output - type determined by connection
        self.add_input_port("in", DataType.ANY)
        self.add_output_port("out", DataType.ANY)

    def set_data_type(self, data_type: Optional[DataType]) -> None:
        """
        Set the data type for this reroute node.

        Called when a connection is made to update the wire color.

        Args:
            data_type: The DataType to use, or None for ANY
        """
        if data_type is None:
            self.config["data_type"] = "ANY"
        else:
            self.config["data_type"] = data_type.value

    def get_data_type(self) -> DataType:
        """
        Get the configured data type.

        Returns:
            DataType enum value
        """
        type_str = self.config.get("data_type", "ANY")
        try:
            # DataType.value is the string representation
            for dt in DataType:
                if dt.value == type_str or dt.name == type_str:
                    return dt
            return DataType.ANY
        except Exception:
            return DataType.ANY

    def set_exec_mode(self, is_exec: bool) -> None:
        """
        Set whether this reroute is for execution flow or data.

        Args:
            is_exec: True for execution flow, False for data
        """
        self.config["is_exec_reroute"] = is_exec

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute reroute node - passes input through to output unchanged.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with the passthrough value
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get input value
            value = self.get_input_value("in")

            # Pass through to output
            self.set_output_value("out", value)

            logger.debug(
                f"Reroute {self.node_id} passing through: {type(value).__name__}"
            )

            self.status = NodeStatus.SUCCESS

            # Determine next node based on mode
            is_exec = self.config.get("is_exec_reroute", False)
            next_nodes = ["exec_out"] if is_exec else ["out"]

            return {
                "success": True,
                "value": value,
                "next_nodes": next_nodes,
            }

        except Exception as e:
            error_msg = f"Reroute error: {e}"
            logger.exception(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg}


# Export all nodes
__all__ = [
    "ValidationType",
    "ValidateNode",
    "TransformType",
    "TransformNode",
    "LogLevel",
    "LogNode",
    "RerouteNode",
]
