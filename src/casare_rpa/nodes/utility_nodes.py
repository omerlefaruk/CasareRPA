"""
Utility nodes for common operations.

This module provides nodes for HTTP requests, data validation, data transformation,
and explicit logging within workflows.
"""

import json
import re
import asyncio
from typing import Any, Dict, Optional
from enum import Enum

import aiohttp
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


class HttpMethod(str, Enum):
    """HTTP request methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@executable_node
class HttpRequestNode(BaseNode):
    """
    HTTP Request node - makes HTTP/HTTPS requests to APIs and web services.

    Supports all common HTTP methods, headers, body, and authentication.
    Uses aiohttp for async requests.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "HTTP Request",
        url: str = "",
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: str = "",
        timeout: float = 30.0,
        **kwargs,
    ) -> None:
        """
        Initialize HTTP request node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            url: Request URL
            method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
            headers: Request headers as dict
            body: Request body (for POST, PUT, PATCH)
            timeout: Request timeout in seconds
        """
        config = kwargs.get("config", {})
        config.setdefault("url", url)
        config.setdefault("method", method)
        config.setdefault("headers", headers or {})
        config.setdefault("body", body)
        config.setdefault("timeout", timeout)
        config.setdefault("verify_ssl", True)
        config.setdefault("follow_redirects", True)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpRequestNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers", PortType.INPUT, DataType.ANY)
        self.add_input_port("body", PortType.INPUT, DataType.STRING)
        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("headers", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute HTTP request.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with response data
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get URL from input or config
            url = self.get_input_value("url") or self.config.get("url", "")
            if not url:
                raise ValueError("URL is required")

            # Get method
            method = self.config.get("method", "GET").upper()
            if method not in [m.value for m in HttpMethod]:
                raise ValueError(f"Invalid HTTP method: {method}")

            # Get headers
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            # Get body
            body = self.get_input_value("body") or self.config.get("body", "")

            # Get timeout
            timeout = aiohttp.ClientTimeout(total=self.config.get("timeout", 30.0))

            # SSL verification
            ssl_context = None if self.config.get("verify_ssl", True) else False

            logger.info(f"Making {method} request to: {url}")

            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Prepare request kwargs
                request_kwargs = {
                    "headers": headers,
                    "ssl": ssl_context,
                    "allow_redirects": self.config.get("follow_redirects", True),
                }

                # Add body for methods that support it
                if method in ["POST", "PUT", "PATCH"] and body:
                    # Try to parse as JSON
                    try:
                        json_body = json.loads(body)
                        request_kwargs["json"] = json_body
                    except json.JSONDecodeError:
                        # Send as raw data
                        request_kwargs["data"] = body

                # Make request
                async with session.request(method, url, **request_kwargs) as response:
                    status_code = response.status
                    response_headers = dict(response.headers)

                    # Read response body
                    try:
                        response_body = await response.text()
                    except Exception:
                        response_body = ""

                    # Determine success
                    success = 200 <= status_code < 300

                    logger.info(f"HTTP {method} {url} -> {status_code}")

                    # Set outputs
                    self.set_output_value("response_body", response_body)
                    self.set_output_value("status_code", status_code)
                    self.set_output_value("headers", response_headers)
                    self.set_output_value("success", success)
                    self.set_output_value(
                        "error", "" if success else f"HTTP {status_code}"
                    )

                    # Store in context variable
                    variable_name = self.config.get("variable_name", "http_response")
                    context.set_variable(
                        variable_name,
                        {
                            "body": response_body,
                            "status_code": status_code,
                            "headers": response_headers,
                            "success": success,
                        },
                    )

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "response_body": response_body,
                        "status_code": status_code,
                        "headers": response_headers,
                        "next_nodes": ["exec_out"],
                    }

        except asyncio.TimeoutError:
            error_msg = f"Request timed out after {self.config.get('timeout', 30.0)}s"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg}

        except aiohttp.ClientError as e:
            error_msg = f"HTTP request failed: {e}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"HTTP request error: {e}"
            logger.exception(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg}


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


@executable_node
class ValidateNode(BaseNode):
    """
    Validate node - validates data against rules.

    Routes to different outputs based on validation success/failure.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Validate",
        validation_type: str = "not_empty",
        validation_param: Any = None,
        **kwargs,
    ) -> None:
        """
        Initialize validate node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            validation_type: Type of validation to perform
            validation_param: Parameter for validation (e.g., regex pattern, min value)
        """
        config = kwargs.get("config", {})
        config.setdefault("validation_type", validation_type)
        config.setdefault("validation_param", validation_param)
        config.setdefault("error_message", "Validation failed")
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ValidateNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("value", PortType.INPUT, DataType.ANY)

        self.add_output_port("valid", PortType.EXEC_OUTPUT)  # Route when valid
        self.add_output_port("invalid", PortType.EXEC_OUTPUT)  # Route when invalid
        self.add_output_port("is_valid", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error_message", PortType.OUTPUT, DataType.STRING)

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
            value = self.get_input_value("value")
            validation_type = self.config.get("validation_type", "not_empty")
            validation_param = self.config.get("validation_param")

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


@executable_node
class TransformNode(BaseNode):
    """
    Transform node - transforms data from one format to another.

    Supports type conversions, string operations, and collection transformations.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Transform",
        transform_type: str = "to_string",
        transform_param: Any = None,
        **kwargs,
    ) -> None:
        """
        Initialize transform node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            transform_type: Type of transformation to perform
            transform_param: Parameter for transformation
        """
        config = kwargs.get("config", {})
        config.setdefault("transform_type", transform_type)
        config.setdefault("transform_param", transform_param)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TransformNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("value", PortType.INPUT, DataType.ANY)
        self.add_input_port("param", PortType.INPUT, DataType.ANY)
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

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
            value = self.get_input_value("value")
            transform_type = self.config.get("transform_type", "to_string")
            transform_param = self.get_input_value("param") or self.config.get(
                "transform_param"
            )

            result = self._transform(value, transform_type, transform_param)

            self.set_output_value("result", result)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            # Store in context
            variable_name = self.config.get("variable_name", "transformed")
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


@executable_node
class LogNode(BaseNode):
    """
    Log node - explicit logging within workflows.

    Outputs messages to the log with configurable level and formatting.
    Useful for debugging and audit trails.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Log",
        message: str = "",
        level: str = "critical",
        **kwargs,
    ) -> None:
        """
        Initialize log node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            message: Message to log (can include {variable} placeholders)
            level: Log level (debug, info, warning, error, critical)
        """
        config = kwargs.get("config", {})
        config.setdefault("message", message)
        config.setdefault("level", level)
        config.setdefault("include_timestamp", True)
        config.setdefault("include_node_id", True)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "LogNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("message", PortType.INPUT, DataType.STRING)
        self.add_input_port("data", PortType.INPUT, DataType.ANY)

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
            message_input = self.get_input_value("message") or self.config.get(
                "message", ""
            )
            # Ensure message is a string (could be Page object or other type from connected node)
            message = str(message_input) if message_input else ""

            # Get optional data to log
            data = self.get_input_value("data")

            # Get log level
            level_str = self.config.get("level", "critical").lower()
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
            if self.config.get("include_node_id", True):
                formatted_message = f"[{self.node_id}] {formatted_message}"

            # Add data if provided
            if data is not None:
                formatted_message += f" | Data: {data}"

            # Log at appropriate level
            log_func = getattr(logger, level.value)
            log_func(formatted_message)

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


# Export all nodes
__all__ = [
    "HttpMethod",
    "HttpRequestNode",
    "ValidationType",
    "ValidateNode",
    "TransformType",
    "TransformNode",
    "LogLevel",
    "LogNode",
]
