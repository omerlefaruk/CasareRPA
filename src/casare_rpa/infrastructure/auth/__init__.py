"""
CasareRPA Infrastructure - Robot Authentication.

Provides secure API key management for robot-to-orchestrator authentication.
API keys are SHA-256 hashed before storage - raw keys are never persisted.

Usage:
    from casare_rpa.infrastructure.auth import (
        RobotApiKeyService,
        RobotApiKey,
        RobotApiKeyError,
    )

    # Generate a new key
    service = RobotApiKeyService(supabase_client)
    raw_key, key_record = await service.generate_api_key(
        robot_id="robot-uuid",
        name="Production Key",
        created_by="admin-user"
    )

    # Display raw_key to user ONCE - it cannot be recovered

    # Validate on robot connection
    key_record = await service.validate_api_key(raw_key)
    if key_record:
        robot_id = key_record.robot_id
        # Proceed with authentication
"""

from casare_rpa.infrastructure.auth.robot_api_keys import (
    ApiKeyValidationResult,
    RobotApiKey,
    RobotApiKeyError,
    RobotApiKeyService,
    generate_api_key_raw,
    hash_api_key,
)

__all__ = [
    "RobotApiKey",
    "RobotApiKeyService",
    "RobotApiKeyError",
    "ApiKeyValidationResult",
    "generate_api_key_raw",
    "hash_api_key",
]
