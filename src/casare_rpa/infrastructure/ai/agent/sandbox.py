"""
Headless workflow validation sandbox.
"""

import re
import time
import traceback
from typing import Any

from loguru import logger

from casare_rpa.domain.services.workflow_validator import (
    WorkflowValidator as QtWorkflowValidator,
)
from casare_rpa.domain.validation import (
    ValidationResult,
    validate_workflow,
)


class HeadlessWorkflowSandbox:
    """
    Headless validation sandbox for workflow JSON.

    Validates workflows without requiring the full UI or execution engine.
    Uses domain validation rules AND Qt-based validation to check:
    - Structure, node types, and connections (domain validation)
    - Actual port names against visual node definitions (Qt validation)
    """

    def __init__(self) -> None:
        """Initialize the headless sandbox."""
        self._node_types_cache: set[str] | None = None
        self._qt_validator: QtWorkflowValidator | None = None
        logger.debug("HeadlessWorkflowSandbox initialized")

    def _get_valid_node_types(self) -> set[str]:
        """Get set of valid node types from registry."""
        if self._node_types_cache is not None:
            return self._node_types_cache

        try:
            from casare_rpa.domain.validation.schemas import get_valid_node_types

            self._node_types_cache = get_valid_node_types()
            logger.debug(f"Loaded {len(self._node_types_cache)} valid node types")
        except ImportError as e:
            logger.warning(f"Could not load node types from registry: {e}")
            self._node_types_cache = set()
        except Exception as e:
            logger.error(f"Unexpected error loading node types: {e}")
            self._node_types_cache = set()

        return self._node_types_cache

    def _get_qt_validator(self) -> QtWorkflowValidator:
        """Get or create Qt workflow validator."""
        if self._qt_validator is None:
            self._qt_validator = QtWorkflowValidator()
            logger.debug("Qt WorkflowValidator initialized")
        return self._qt_validator

    def validate_workflow(self, workflow_dict: dict[str, Any]) -> ValidationResult:
        """
        Validate a workflow dictionary in headless mode.

        This performs both domain validation AND Qt-based validation to ensure:
        1. Workflow structure is valid (domain validation)
        2. All port names match actual visual node definitions (Qt validation)

        Args:
            workflow_dict: Workflow data to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()
        start_time = time.time()

        logger.debug(
            f"Starting headless validation for workflow with "
            f"{len(workflow_dict.get('nodes', {}))} nodes"
        )

        # Run domain validation
        try:
            domain_result = validate_workflow(workflow_dict)
            result.merge(domain_result)
            logger.debug(
                f"Domain validation: {len(domain_result.errors)} errors, "
                f"{len(domain_result.warnings)} warnings"
            )
        except Exception as e:
            logger.error(f"Domain validation threw exception: {e}")
            logger.debug(traceback.format_exc())
            result.add_error(
                "VALIDATION_EXCEPTION",
                f"Validation threw exception: {e}",
                suggestion="Check workflow structure and try again",
            )

        # Run Qt-based validation (validates port names against actual node definitions)
        try:
            qt_validator = self._get_qt_validator()
            qt_result = qt_validator.validate(workflow_dict)

            # Convert Qt validation errors to domain validation format
            for issue in qt_result.errors:
                result.add_error(
                    issue.code,
                    issue.message,
                    location=issue.location,
                    suggestion=issue.suggestion,
                )

            for issue in qt_result.warnings:
                result.add_warning(
                    issue.code,
                    issue.message,
                    location=issue.location,
                    suggestion=issue.suggestion,
                )

            logger.debug(
                f"Qt validation: {len(qt_result.errors)} errors, "
                f"{len(qt_result.warnings)} warnings"
            )
        except Exception as e:
            logger.error(f"Qt validation threw exception: {e}")
            logger.debug(traceback.format_exc())
            result.add_warning(
                "QT_VALIDATION_SKIPPED",
                f"Qt validation skipped due to error: {e}",
                suggestion="Workflow may have port name issues",
            )

        # Additional semantic checks
        try:
            self._validate_node_types(workflow_dict, result)
        except Exception as e:
            logger.error(f"Node type validation failed: {e}")
            result.add_error(
                "NODE_TYPE_VALIDATION_ERROR",
                f"Node type validation failed: {e}",
                suggestion="Ensure all node types are valid",
            )

        try:
            self._validate_connection_ports(workflow_dict, result)
        except Exception as e:
            logger.error(f"Connection port validation failed: {e}")
            result.add_error(
                "CONNECTION_VALIDATION_ERROR",
                f"Connection validation failed: {e}",
                suggestion="Check connection port names",
            )

        duration_ms = (time.time() - start_time) * 1000
        logger.debug(
            f"Headless validation completed in {duration_ms:.2f}ms: "
            f"valid={result.is_valid}, errors={len(result.errors)}"
        )

        return result

    def _validate_node_types(self, workflow_dict: dict[str, Any], result: ValidationResult) -> None:
        """Validate that all node types are registered."""
        valid_types = self._get_valid_node_types()
        if not valid_types:
            logger.warning("Skipping node type validation - no types loaded")
            return

        nodes = workflow_dict.get("nodes", {})
        for node_id, node_data in nodes.items():
            node_type = node_data.get("node_type", "")
            if node_type and node_type not in valid_types:
                logger.warning(f"Unknown node type '{node_type}' in node '{node_id}'")
                result.add_error(
                    "UNKNOWN_NODE_TYPE",
                    f"Node type '{node_type}' is not registered",
                    location=f"node:{node_id}",
                    suggestion="Use a valid node type from the manifest",
                )

    def _validate_connection_ports(
        self, workflow_dict: dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate connection port names are valid."""
        connections = workflow_dict.get("connections", [])

        for idx, conn in enumerate(connections):
            source_port = conn.get("source_port", "")
            target_port = conn.get("target_port", "")

            # Execution ports should follow naming convention
            if source_port and not self._is_valid_port_name(source_port):
                result.add_warning(
                    "INVALID_PORT_NAME",
                    f"Source port '{source_port}' may be invalid",
                    location=f"connection:{idx}",
                )

            if target_port and not self._is_valid_port_name(target_port):
                result.add_warning(
                    "INVALID_PORT_NAME",
                    f"Target port '{target_port}' may be invalid",
                    location=f"connection:{idx}",
                )

    def _is_valid_port_name(self, port_name: str) -> bool:
        """Check if port name follows valid patterns."""
        if not port_name:
            return False
        # Port names should be snake_case
        return bool(re.match(r"^[a-z][a-z0-9_]*$", port_name))
