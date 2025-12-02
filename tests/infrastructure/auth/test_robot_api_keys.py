"""
Tests for Robot API Key Service.

Tests cover:
- Happy path: Key generation, validation, revocation, rotation
- Sad path: Invalid keys, revoked keys, expired keys, errors
- Edge cases: Key format validation, hash verification, datetime parsing
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from casare_rpa.infrastructure.auth.robot_api_keys import (
    API_KEY_PREFIX,
    API_KEY_TOKEN_BYTES,
    ApiKeyExpiredError,
    ApiKeyNotFoundError,
    ApiKeyRevokedError,
    ApiKeyValidationResult,
    RobotApiKey,
    RobotApiKeyError,
    RobotApiKeyService,
    extract_key_prefix,
    generate_api_key_raw,
    hash_api_key,
    validate_api_key_format,
)


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestGenerateApiKeyRaw:
    """Test raw API key generation."""

    def test_generates_key_with_correct_prefix(self):
        """Generated key starts with crpa_ prefix."""
        raw_key = generate_api_key_raw()
        assert raw_key.startswith(f"{API_KEY_PREFIX}_")

    def test_generates_key_with_sufficient_length(self):
        """Generated key has sufficient length for security."""
        raw_key = generate_api_key_raw()
        # prefix (4) + underscore (1) + base64url token (~43)
        assert len(raw_key) >= 40

    def test_generates_unique_keys(self):
        """Each call generates a unique key."""
        keys = {generate_api_key_raw() for _ in range(100)}
        assert len(keys) == 100

    def test_key_is_base64url_safe(self):
        """Key token uses URL-safe characters."""
        raw_key = generate_api_key_raw()
        token = raw_key.split("_", 1)[1]
        # base64url uses A-Z, a-z, 0-9, -, _
        valid_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_="
        )
        assert all(c in valid_chars for c in token)


class TestHashApiKey:
    """Test API key hashing."""

    def test_produces_hex_digest(self):
        """Hash produces 64-character hex digest."""
        raw_key = generate_api_key_raw()
        key_hash = hash_api_key(raw_key)

        assert len(key_hash) == 64
        assert all(c in "0123456789abcdef" for c in key_hash)

    def test_same_key_produces_same_hash(self):
        """Hashing same key produces identical hash."""
        raw_key = generate_api_key_raw()
        hash1 = hash_api_key(raw_key)
        hash2 = hash_api_key(raw_key)

        assert hash1 == hash2

    def test_different_keys_produce_different_hashes(self):
        """Different keys produce different hashes."""
        key1 = generate_api_key_raw()
        key2 = generate_api_key_raw()
        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)

        assert hash1 != hash2

    def test_hash_is_consistent_with_sha256(self):
        """Hash matches expected SHA-256 output."""
        import hashlib

        raw_key = "crpa_testkey123"
        expected = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        actual = hash_api_key(raw_key)

        assert actual == expected


class TestValidateApiKeyFormat:
    """Test API key format validation."""

    def test_valid_key_accepted(self):
        """Valid key format returns True."""
        raw_key = generate_api_key_raw()
        assert validate_api_key_format(raw_key) is True

    def test_empty_string_rejected(self):
        """Empty string returns False."""
        assert validate_api_key_format("") is False

    def test_none_rejected(self):
        """None returns False."""
        assert validate_api_key_format(None) is False

    def test_wrong_prefix_rejected(self):
        """Key with wrong prefix returns False."""
        assert validate_api_key_format("wrong_prefix_key") is False
        assert validate_api_key_format("crp_almostright") is False
        assert validate_api_key_format("CRPA_uppercase") is False

    def test_short_key_rejected(self):
        """Key that is too short returns False."""
        assert validate_api_key_format("crpa_short") is False
        assert validate_api_key_format("crpa_") is False

    def test_minimum_length_accepted(self):
        """Key at minimum length is accepted."""
        # 40 characters minimum
        min_key = "crpa_" + "a" * 35  # 5 + 35 = 40
        assert validate_api_key_format(min_key) is True


class TestExtractKeyPrefix:
    """Test key prefix extraction."""

    def test_extracts_default_length(self):
        """Extracts 12 characters by default."""
        raw_key = generate_api_key_raw()
        prefix = extract_key_prefix(raw_key)

        assert len(prefix) == 12
        assert prefix == raw_key[:12]

    def test_extracts_custom_length(self):
        """Extracts custom number of characters."""
        raw_key = generate_api_key_raw()
        prefix = extract_key_prefix(raw_key, length=20)

        assert len(prefix) == 20
        assert prefix == raw_key[:20]

    def test_empty_string_returns_empty(self):
        """Empty string returns empty string."""
        assert extract_key_prefix("") == ""

    def test_none_returns_empty(self):
        """None returns empty string."""
        assert extract_key_prefix(None) == ""


# ============================================================================
# RobotApiKey Dataclass Tests
# ============================================================================


class TestRobotApiKeyDataclass:
    """Test RobotApiKey dataclass properties."""

    def test_is_expired_false_when_no_expiry(self, sample_robot_api_key: RobotApiKey):
        """Key without expiration is not expired."""
        assert sample_robot_api_key.is_expired is False

    def test_is_expired_true_when_past_expiry(
        self, sample_expired_api_key: RobotApiKey
    ):
        """Key with past expiration is expired."""
        assert sample_expired_api_key.is_expired is True

    def test_is_expired_false_when_future_expiry(
        self, sample_key_with_future_expiry: RobotApiKey
    ):
        """Key with future expiration is not expired."""
        assert sample_key_with_future_expiry.is_expired is False

    def test_is_valid_true_for_active_key(self, sample_robot_api_key: RobotApiKey):
        """Active key (not revoked, not expired) is valid."""
        assert sample_robot_api_key.is_valid is True

    def test_is_valid_false_for_revoked_key(self, sample_revoked_api_key: RobotApiKey):
        """Revoked key is not valid."""
        assert sample_revoked_api_key.is_valid is False

    def test_is_valid_false_for_expired_key(self, sample_expired_api_key: RobotApiKey):
        """Expired key is not valid."""
        assert sample_expired_api_key.is_valid is False

    def test_status_valid_for_active_key(self, sample_robot_api_key: RobotApiKey):
        """Active key has VALID status."""
        assert sample_robot_api_key.status == ApiKeyValidationResult.VALID

    def test_status_revoked_for_revoked_key(self, sample_revoked_api_key: RobotApiKey):
        """Revoked key has REVOKED status."""
        assert sample_revoked_api_key.status == ApiKeyValidationResult.REVOKED

    def test_status_expired_for_expired_key(self, sample_expired_api_key: RobotApiKey):
        """Expired key has EXPIRED status."""
        assert sample_expired_api_key.status == ApiKeyValidationResult.EXPIRED

    def test_to_dict_includes_all_fields(self, sample_robot_api_key: RobotApiKey):
        """to_dict includes all public fields."""
        data = sample_robot_api_key.to_dict()

        assert data["id"] == "key-uuid-12345678"
        assert data["robot_id"] == "robot-uuid-12345678"
        assert data["name"] == "Test API Key"
        assert data["description"] == "API key for testing"
        assert data["is_revoked"] is False
        assert data["status"] == "valid"
        assert "created_at" in data

    def test_to_dict_excludes_hash(self, sample_robot_api_key: RobotApiKey):
        """to_dict does not include API key hash."""
        data = sample_robot_api_key.to_dict()
        assert "api_key_hash" not in data


# ============================================================================
# RobotApiKeyService Tests - Generation
# ============================================================================


class TestRobotApiKeyServiceGeneration:
    """Test API key generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_api_key_with_supabase(self, mock_supabase_client):
        """Generate key using Supabase client."""
        # Configure mock response
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [{"id": "new-key-uuid"}]
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        raw_key, key_record = await service.generate_api_key(
            robot_id="robot-123",
            name="New Key",
            description="Test key",
            created_by="test-user",
        )

        assert raw_key.startswith("crpa_")
        assert key_record.id == "new-key-uuid"
        assert key_record.robot_id == "robot-123"
        assert key_record.name == "New Key"

    @pytest.mark.asyncio
    async def test_generate_api_key_with_asyncpg(
        self, mock_asyncpg_pool, mock_asyncpg_connection
    ):
        """Generate key using asyncpg pool."""
        # Configure mock - pool has acquire attribute
        mock_asyncpg_connection.set_fetchrow_result({"id": "new-key-uuid-asyncpg"})

        service = RobotApiKeyService(mock_asyncpg_pool)

        raw_key, key_record = await service.generate_api_key(
            robot_id="robot-456",
            name="Asyncpg Key",
            created_by="test-user",
        )

        assert raw_key.startswith("crpa_")
        assert key_record.id == "new-key-uuid-asyncpg"

    @pytest.mark.asyncio
    async def test_generate_api_key_with_expiration(self, mock_supabase_client):
        """Generate key with expiration date."""
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [{"id": "expiring-key"}]
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)
        expiry = datetime.now(timezone.utc) + timedelta(days=30)

        raw_key, key_record = await service.generate_api_key(
            robot_id="robot-123",
            name="Expiring Key",
            expires_at=expiry,
        )

        assert key_record.expires_at == expiry

    @pytest.mark.asyncio
    async def test_generate_api_key_returns_raw_key_only_once(
        self, mock_supabase_client
    ):
        """Raw key is returned only during generation."""
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [{"id": "one-time-key"}]
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        raw_key, key_record = await service.generate_api_key(
            robot_id="robot-123",
            name="One-time visible key",
        )

        # Key record does not contain raw key
        assert hasattr(key_record, "api_key_hash")
        assert key_record.api_key_hash != raw_key
        # Raw key was returned for display
        assert raw_key.startswith("crpa_")

    @pytest.mark.asyncio
    async def test_generate_api_key_database_error(self, mock_supabase_client):
        """Database error raises RobotApiKeyError."""
        mock_table = mock_supabase_client.table.return_value
        mock_table.execute.side_effect = Exception("Database connection failed")

        service = RobotApiKeyService(mock_supabase_client)

        with pytest.raises(RobotApiKeyError, match="Failed to generate API key"):
            await service.generate_api_key(
                robot_id="robot-123",
                name="Failed Key",
            )


# ============================================================================
# RobotApiKeyService Tests - Validation
# ============================================================================


class TestRobotApiKeyServiceValidation:
    """Test API key validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_valid_key(
        self,
        mock_supabase_client,
        sample_raw_api_key: str,
        sample_api_key_row: Dict[str, Any],
    ):
        """Valid key returns RobotApiKey record."""
        # Configure mock
        sample_api_key_row["api_key_hash"] = hash_api_key(sample_raw_api_key)
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [sample_api_key_row]
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        result = await service.validate_api_key(sample_raw_api_key)

        assert result is not None
        assert result.id == sample_api_key_row["id"]
        assert result.robot_id == sample_api_key_row["robot_id"]

    @pytest.mark.asyncio
    async def test_validate_invalid_format_returns_none(self, mock_supabase_client):
        """Invalid key format returns None."""
        service = RobotApiKeyService(mock_supabase_client)

        result = await service.validate_api_key("invalid_key_format")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_nonexistent_key_returns_none(self, mock_supabase_client):
        """Non-existent key returns None."""
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = []  # No results
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)
        raw_key = generate_api_key_raw()

        result = await service.validate_api_key(raw_key)

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_revoked_key_raises_error(
        self,
        mock_supabase_client,
        sample_raw_api_key: str,
        sample_api_key_row_revoked: Dict[str, Any],
    ):
        """Revoked key raises ApiKeyRevokedError."""
        sample_api_key_row_revoked["api_key_hash"] = hash_api_key(sample_raw_api_key)
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [sample_api_key_row_revoked]
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        with pytest.raises(ApiKeyRevokedError):
            await service.validate_api_key(sample_raw_api_key)

    @pytest.mark.asyncio
    async def test_validate_expired_key_raises_error(
        self,
        mock_supabase_client,
        sample_raw_api_key: str,
        sample_api_key_row_expired: Dict[str, Any],
    ):
        """Expired key raises ApiKeyExpiredError."""
        sample_api_key_row_expired["api_key_hash"] = hash_api_key(sample_raw_api_key)
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [sample_api_key_row_expired]
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        with pytest.raises(ApiKeyExpiredError):
            await service.validate_api_key(sample_raw_api_key)

    @pytest.mark.asyncio
    async def test_validate_updates_last_used(
        self,
        mock_supabase_client,
        sample_raw_api_key: str,
        sample_api_key_row: Dict[str, Any],
    ):
        """Validation updates last_used_at by default."""
        sample_api_key_row["api_key_hash"] = hash_api_key(sample_raw_api_key)
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [sample_api_key_row]
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        await service.validate_api_key(sample_raw_api_key, update_last_used=True)

        # Should have called update
        mock_table.update.assert_called()

    @pytest.mark.asyncio
    async def test_validate_skips_update_when_disabled(
        self,
        mock_supabase_client,
        sample_raw_api_key: str,
        sample_api_key_row: Dict[str, Any],
    ):
        """Validation skips last_used update when disabled."""
        sample_api_key_row["api_key_hash"] = hash_api_key(sample_raw_api_key)
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [sample_api_key_row]
        mock_table.execute.return_value = mock_response

        # Reset the update mock to track calls
        mock_table.update.reset_mock()

        service = RobotApiKeyService(mock_supabase_client)

        await service.validate_api_key(sample_raw_api_key, update_last_used=False)

        # Update should not be called
        mock_table.update.assert_not_called()


# ============================================================================
# RobotApiKeyService Tests - Revocation
# ============================================================================


class TestRobotApiKeyServiceRevocation:
    """Test API key revocation functionality."""

    @pytest.mark.asyncio
    async def test_revoke_api_key_success(self, mock_supabase_client):
        """Successful revocation returns True."""
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [{"id": "key-123"}]  # Non-empty = success
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        result = await service.revoke_api_key(
            key_id="key-123",
            revoked_by="admin",
            reason="Security policy",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_api_key_not_found(self, mock_supabase_client):
        """Revocation of non-existent key returns False."""
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = []  # Empty = not found
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        result = await service.revoke_api_key(key_id="nonexistent-key")

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_api_key_database_error(self, mock_supabase_client):
        """Database error raises RobotApiKeyError."""
        mock_table = mock_supabase_client.table.return_value
        mock_table.execute.side_effect = Exception("Database error")

        service = RobotApiKeyService(mock_supabase_client)

        with pytest.raises(RobotApiKeyError, match="Failed to revoke"):
            await service.revoke_api_key(key_id="key-123")


# ============================================================================
# RobotApiKeyService Tests - Rotation
# ============================================================================


class TestRobotApiKeyServiceRotation:
    """Test API key rotation functionality."""

    @pytest.mark.asyncio
    async def test_rotate_key_creates_new_key(self, mock_supabase_client):
        """Rotation creates new key and revokes old."""
        mock_table = mock_supabase_client.table.return_value

        # First call - get old key
        old_key_data = {
            "id": "old-key-123",
            "robot_id": "robot-123",
            "api_key_hash": "oldhash",
            "name": "Old Key",
            "description": "Description",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": None,
            "is_revoked": False,
        }

        # Mock multiple execute calls
        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            response = Mock()
            if call_count[0] == 1:  # get_key_by_id
                response.data = [old_key_data]
            elif call_count[0] == 2:  # revoke
                response.data = [{"id": "old-key-123"}]
            else:  # insert new key
                response.data = [{"id": "new-key-456"}]
            return response

        mock_table.execute = mock_execute

        service = RobotApiKeyService(mock_supabase_client)

        raw_key, new_key = await service.rotate_key(
            key_id="old-key-123",
            rotated_by="admin",
        )

        assert raw_key.startswith("crpa_")
        assert new_key.id == "new-key-456"
        assert "(rotated)" in new_key.name

    @pytest.mark.asyncio
    async def test_rotate_nonexistent_key_raises_error(self, mock_supabase_client):
        """Rotating non-existent key raises ApiKeyNotFoundError."""
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = []  # Key not found
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        with pytest.raises(ApiKeyNotFoundError):
            await service.rotate_key(key_id="nonexistent-key")


# ============================================================================
# RobotApiKeyService Tests - Listing
# ============================================================================


class TestRobotApiKeyServiceListing:
    """Test listing API keys for robots."""

    @pytest.mark.asyncio
    async def test_list_keys_for_robot(
        self, mock_supabase_client, sample_api_key_row: Dict[str, Any]
    ):
        """List keys returns all keys for robot."""
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [sample_api_key_row]
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        keys = await service.list_keys_for_robot("robot-uuid-12345678")

        assert len(keys) == 1
        assert keys[0].id == sample_api_key_row["id"]

    @pytest.mark.asyncio
    async def test_list_keys_excludes_revoked_by_default(self, mock_supabase_client):
        """Listing excludes revoked keys by default."""
        mock_table = mock_supabase_client.table.return_value
        # Reset eq mock to track calls
        mock_table.eq.reset_mock()
        mock_response = Mock()
        mock_response.data = []
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        await service.list_keys_for_robot("robot-123", include_revoked=False)

        # eq should be called twice: robot_id and is_revoked
        calls = mock_table.eq.call_args_list
        assert len(calls) == 2
        assert calls[1][0] == ("is_revoked", False)

    @pytest.mark.asyncio
    async def test_list_keys_includes_revoked_when_requested(
        self, mock_supabase_client
    ):
        """Listing includes revoked keys when requested."""
        mock_table = mock_supabase_client.table.return_value
        # Reset eq mock to track calls
        mock_table.eq.reset_mock()
        mock_response = Mock()
        mock_response.data = []
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        await service.list_keys_for_robot("robot-123", include_revoked=True)

        # eq should only be called once for robot_id
        calls = mock_table.eq.call_args_list
        assert len(calls) == 1
        assert calls[0][0] == ("robot_id", "robot-123")


# ============================================================================
# RobotApiKeyService Tests - Get By ID
# ============================================================================


class TestRobotApiKeyServiceGetById:
    """Test getting API key by ID."""

    @pytest.mark.asyncio
    async def test_get_key_by_id_found(
        self, mock_supabase_client, sample_api_key_row: Dict[str, Any]
    ):
        """Get key by ID returns key when found."""
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = [sample_api_key_row]
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        key = await service.get_key_by_id("key-uuid-12345678")

        assert key is not None
        assert key.id == sample_api_key_row["id"]

    @pytest.mark.asyncio
    async def test_get_key_by_id_not_found(self, mock_supabase_client):
        """Get key by ID returns None when not found."""
        mock_table = mock_supabase_client.table.return_value
        mock_response = Mock()
        mock_response.data = []
        mock_table.execute.return_value = mock_response

        service = RobotApiKeyService(mock_supabase_client)

        key = await service.get_key_by_id("nonexistent-key")

        assert key is None

    @pytest.mark.asyncio
    async def test_get_key_by_id_error_returns_none(self, mock_supabase_client):
        """Database error returns None."""
        mock_table = mock_supabase_client.table.return_value
        mock_table.execute.side_effect = Exception("Database error")

        service = RobotApiKeyService(mock_supabase_client)

        key = await service.get_key_by_id("key-123")

        assert key is None


# ============================================================================
# Exception Tests
# ============================================================================


class TestRobotApiKeyExceptions:
    """Test custom exceptions."""

    def test_robot_api_key_error_message(self):
        """RobotApiKeyError stores message."""
        error = RobotApiKeyError("Test error", {"key": "value"})

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {"key": "value"}

    def test_api_key_not_found_error_message(self):
        """ApiKeyNotFoundError formats message correctly."""
        error = ApiKeyNotFoundError("crpa_test...")

        assert "not found" in str(error).lower()
        assert "crpa_test..." in str(error)

    def test_api_key_revoked_error_stores_key_id(self):
        """ApiKeyRevokedError stores key_id."""
        error = ApiKeyRevokedError("key-123")

        assert error.key_id == "key-123"
        assert "revoked" in str(error).lower()

    def test_api_key_expired_error_stores_details(self):
        """ApiKeyExpiredError stores key_id and expired_at."""
        expired_at = datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc)
        error = ApiKeyExpiredError("key-123", expired_at)

        assert error.key_id == "key-123"
        assert error.expired_at == expired_at
        assert "expired" in str(error).lower()


# ============================================================================
# Datetime Parsing Tests
# ============================================================================


class TestDatetimeParsing:
    """Test datetime parsing in service."""

    def test_parse_iso_format(self, mock_supabase_client):
        """ISO format datetime is parsed correctly."""
        service = RobotApiKeyService(mock_supabase_client)

        result = service._parse_datetime("2024-01-15T10:30:00+00:00")

        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_parse_z_suffix(self, mock_supabase_client):
        """Z-suffix datetime is parsed correctly."""
        service = RobotApiKeyService(mock_supabase_client)

        result = service._parse_datetime("2024-01-15T10:30:00Z")

        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_parse_none_returns_none(self, mock_supabase_client):
        """None value returns None."""
        service = RobotApiKeyService(mock_supabase_client)

        result = service._parse_datetime(None)

        assert result is None

    def test_parse_datetime_object_returns_as_is(self, mock_supabase_client):
        """Datetime object is returned unchanged."""
        service = RobotApiKeyService(mock_supabase_client)
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

        result = service._parse_datetime(dt)

        assert result is dt

    def test_parse_invalid_string_returns_none(self, mock_supabase_client):
        """Invalid string returns None."""
        service = RobotApiKeyService(mock_supabase_client)

        result = service._parse_datetime("not-a-date")

        assert result is None


# ============================================================================
# Edge Cases
# ============================================================================


class TestRobotApiKeyServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_unsupported_db_client_raises_error(self):
        """Unsupported database client raises error."""
        # Client without table() or acquire()
        fake_client = Mock(spec=[])

        service = RobotApiKeyService(fake_client)

        with pytest.raises(RobotApiKeyError, match="Unsupported database client"):
            await service.generate_api_key(
                robot_id="robot-123",
                name="Test Key",
            )

    @pytest.mark.asyncio
    async def test_delete_expired_keys_with_asyncpg(
        self, mock_asyncpg_pool, mock_asyncpg_connection
    ):
        """Delete expired keys with asyncpg pool."""
        mock_asyncpg_connection.set_execute_result("DELETE 5")

        service = RobotApiKeyService(mock_asyncpg_pool)

        count = await service.delete_expired_keys(days_old=30)

        assert count == 5

    @pytest.mark.asyncio
    async def test_delete_expired_keys_with_supabase_returns_zero(
        self, mock_supabase_client
    ):
        """Delete expired keys with Supabase returns 0 (not supported)."""
        service = RobotApiKeyService(mock_supabase_client)

        count = await service.delete_expired_keys(days_old=30)

        assert count == 0

    @pytest.mark.asyncio
    async def test_validation_error_returns_none(self, mock_supabase_client):
        """Validation database error returns None."""
        mock_table = mock_supabase_client.table.return_value
        mock_table.execute.side_effect = Exception("Database error")

        service = RobotApiKeyService(mock_supabase_client)
        raw_key = generate_api_key_raw()

        result = await service.validate_api_key(raw_key)

        assert result is None
