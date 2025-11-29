"""
Tests for security validators.

Verifies SQL injection prevention, input validation, and credential masking.
"""

import pytest

from casare_rpa.infrastructure.security.validators import (
    ValidationError,
    sanitize_log_value,
    validate_robot_id,
    validate_sql_identifier,
    validate_workflow_id,
)


class TestSQLIdentifierValidation:
    """Test SQL identifier validation (table/column names)."""

    def test_valid_table_name(self):
        """Valid table names should pass validation."""
        assert validate_sql_identifier("users") == "users"
        assert validate_sql_identifier("workflow_checkpoints") == "workflow_checkpoints"
        assert validate_sql_identifier("job_queue") == "job_queue"
        assert validate_sql_identifier("a") == "a"
        assert validate_sql_identifier("table_123") == "table_123"

    def test_reject_sql_injection_drop(self):
        """Should reject DROP TABLE injection attempt."""
        with pytest.raises(ValidationError, match="Must start with lowercase"):
            validate_sql_identifier("'; DROP TABLE users--")

    def test_reject_sql_injection_union(self):
        """Should reject UNION injection attempt."""
        with pytest.raises(ValidationError, match="Must start with lowercase"):
            validate_sql_identifier("users UNION SELECT")

    def test_reject_uppercase_start(self):
        """Should reject identifiers starting with uppercase."""
        with pytest.raises(ValidationError, match="Must start with lowercase"):
            validate_sql_identifier("Users")

    def test_reject_number_start(self):
        """Should reject identifiers starting with number."""
        with pytest.raises(ValidationError, match="Must start with lowercase"):
            validate_sql_identifier("123table")

    def test_reject_special_chars(self):
        """Should reject special characters."""
        with pytest.raises(ValidationError, match="Must start with lowercase"):
            validate_sql_identifier("table-name")
        with pytest.raises(ValidationError, match="Must start with lowercase"):
            validate_sql_identifier("table.name")

    def test_reject_semicolon(self):
        """Should reject semicolon (SQL delimiter)."""
        with pytest.raises(ValidationError, match="Must start with lowercase"):
            validate_sql_identifier("table;")

    def test_reject_comment_marker(self):
        """Should reject SQL comment markers."""
        with pytest.raises(ValidationError, match="Must start with lowercase"):
            validate_sql_identifier("table--")

    def test_reject_too_long(self):
        """Should reject identifiers longer than 63 characters."""
        long_name = "a" * 64
        with pytest.raises(ValidationError, match="max 63 chars"):
            validate_sql_identifier(long_name)

    def test_reject_empty(self):
        """Should reject empty identifier."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_sql_identifier("")

    def test_reject_non_string(self):
        """Should reject non-string input."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_sql_identifier(123)  # type: ignore


class TestRobotIDValidation:
    """Test robot ID validation."""

    def test_valid_robot_id(self):
        """Valid robot IDs should pass validation."""
        assert validate_robot_id("robot-001") == "robot-001"
        assert validate_robot_id("robot_worker_123") == "robot_worker_123"
        assert validate_robot_id("ROBOT-A1") == "ROBOT-A1"
        assert validate_robot_id("r") == "r"

    def test_reject_sql_injection_in_robot_id(self):
        """Should reject SQL injection in robot_id."""
        with pytest.raises(ValidationError, match="Must contain only alphanumeric"):
            validate_robot_id("'; DROP TABLE robots--")

    def test_reject_special_chars_in_robot_id(self):
        """Should reject special characters (except hyphen and underscore)."""
        with pytest.raises(ValidationError, match="Must contain only alphanumeric"):
            validate_robot_id("robot@work")
        with pytest.raises(ValidationError, match="Must contain only alphanumeric"):
            validate_robot_id("robot.001")

    def test_reject_empty_robot_id(self):
        """Should reject empty robot_id."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_robot_id("")

    def test_reject_too_long_robot_id(self):
        """Should reject robot_id longer than 64 characters."""
        long_id = "r" * 65
        with pytest.raises(ValidationError, match="1-64 chars"):
            validate_robot_id(long_id)

    def test_reject_non_string_robot_id(self):
        """Should reject non-string robot_id."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_robot_id(123)  # type: ignore


class TestWorkflowIDValidation:
    """Test workflow ID validation."""

    def test_valid_workflow_id(self):
        """Valid workflow IDs should pass validation."""
        assert validate_workflow_id("workflow-001") == "workflow-001"
        assert validate_workflow_id("WF_123") == "WF_123"

    def test_reject_too_long_workflow_id(self):
        """Should reject workflow_id longer than 128 characters."""
        long_id = "w" * 129
        with pytest.raises(ValidationError, match="1-128 chars"):
            validate_workflow_id(long_id)


class TestCredentialMasking:
    """Test credential sanitization for logs."""

    def test_mask_postgresql_url(self):
        """Should mask PostgreSQL connection strings."""
        url = "postgresql://user:secretpass@localhost:5432/mydb"
        masked = sanitize_log_value(url)
        assert "secretpass" not in masked
        assert "postgresql://***@***" in masked

    def test_mask_postgres_url(self):
        """Should mask postgres:// URLs."""
        url = "postgres://admin:p@ssw0rd@db.example.com:5432/prod"
        masked = sanitize_log_value(url)
        assert "p@ssw0rd" not in masked
        assert "postgres://***@***" in masked

    def test_mask_password_field(self):
        """Should mask password=... patterns."""
        config_str = "host=localhost password=secret123 dbname=test"
        masked = sanitize_log_value(config_str)
        assert "secret123" not in masked
        assert "password=***" in masked

    def test_mask_api_key(self):
        """Should mask api_key patterns."""
        config = "api_key=sk-1234567890abcdef"
        masked = sanitize_log_value(config)
        assert "sk-1234567890abcdef" not in masked
        assert "api_key=***" in masked

    def test_mask_secret(self):
        """Should mask secret patterns."""
        config = 'secret="my-secret-value"'
        masked = sanitize_log_value(config)
        assert "my-secret-value" not in masked
        assert "secret=***" in masked

    def test_mask_token(self):
        """Should mask token patterns."""
        config = "token: bearer_token_12345"
        masked = sanitize_log_value(config)
        assert "bearer_token_12345" not in masked
        assert "token=***" in masked

    def test_preserve_safe_values(self):
        """Should preserve non-sensitive values."""
        safe_str = "robot_id=robot-001 environment=production"
        masked = sanitize_log_value(safe_str)
        assert "robot-001" in masked
        assert "production" in masked

    def test_handle_none(self):
        """Should handle None input."""
        assert sanitize_log_value(None) == "None"

    def test_custom_mask_patterns(self):
        """Should support custom masking patterns."""
        value = "custom_secret=hidden_value"
        masked = sanitize_log_value(value, mask_patterns=[r"custom_secret=\w+"])
        assert "hidden_value" not in masked
        assert "***" in masked
