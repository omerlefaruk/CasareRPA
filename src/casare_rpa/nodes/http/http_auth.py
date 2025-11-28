"""
HTTP authentication nodes for CasareRPA.

This module provides nodes for configuring HTTP authentication:
- HttpAuthNode: Configure Bearer, Basic, or API Key authentication
"""

from __future__ import annotations

import base64
import json
from typing import Any

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)


class HttpAuthNode(BaseNode):
    """
    Configure HTTP authentication headers.

    Supports:
        - Bearer token authentication
        - Basic authentication (username/password)
        - API Key authentication (header or query param)

    Inputs:
        - exec_in: Execution input
        - auth_type: Type of authentication (Bearer, Basic, ApiKey)
        - token: Bearer token or API key
        - username: Username for Basic auth
        - password: Password for Basic auth
        - api_key_name: Header name for API key (default: X-API-Key)
        - base_headers: Existing headers to extend

    Outputs:
        - exec_out: Execution output
        - headers: Headers with authentication
    """

    def __init__(self, node_id: str, name: str = "HTTP Auth", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("auth_type", "Bearer")
        config.setdefault("token", "")
        config.setdefault("username", "")
        config.setdefault("password", "")
        config.setdefault("api_key_name", "X-API-Key")
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpAuthNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("auth_type", PortType.INPUT, DataType.STRING)
        self.add_input_port("token", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("api_key_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("base_headers", PortType.INPUT, DataType.DICT)

        self.add_output_port("headers", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            auth_type = self.get_input_value("auth_type") or self.config.get(
                "auth_type", "Bearer"
            )
            token = self.get_input_value("token") or self.config.get("token", "")
            username = self.get_input_value("username") or self.config.get(
                "username", ""
            )
            password = self.get_input_value("password") or self.config.get(
                "password", ""
            )
            api_key_name = self.get_input_value("api_key_name") or self.config.get(
                "api_key_name", "X-API-Key"
            )
            base_headers = self.get_input_value("base_headers") or {}

            token = context.resolve_value(token)
            username = context.resolve_value(username)
            password = context.resolve_value(password)

            headers = dict(base_headers)

            if auth_type.lower() == "bearer":
                if not token:
                    raise ValueError("Bearer token is required")
                headers["Authorization"] = f"Bearer {token}"
                logger.debug("Set Bearer token authentication")

            elif auth_type.lower() == "basic":
                if not username or not password:
                    raise ValueError(
                        "Username and password are required for Basic auth"
                    )
                credentials = base64.b64encode(
                    f"{username}:{password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"
                logger.debug("Set Basic authentication")

            elif auth_type.lower() == "apikey":
                if not token:
                    raise ValueError("API key is required")
                headers[api_key_name] = token
                logger.debug(f"Set API key in header: {api_key_name}")

            else:
                raise ValueError(f"Unknown auth type: {auth_type}")

            self.set_output_value("headers", headers)

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"auth_type": auth_type},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"HTTP auth error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = [
    "HttpAuthNode",
]
