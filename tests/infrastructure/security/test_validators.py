"""
Security validator unit tests.

Tests for SQL injection prevention, identifier validation, and input sanitization.
"""

import pytest
from casare_rpa.infrastructure.security.validators import (
    validate_sql_identifier,
    validate_robot_id,
    validate_workflow_id,
    validate_job_id,
    sanitize_for_logging,
)


class TestSQLIdentifierValidation:
    """Test SQL identifier validation to prevent injection attacks (CWE-89)."""

    def test_valid_table_names(self):
        """Test that valid table names pass validation."""
        valid_names = [
            "workflow_checkpoints",
            "job_queue",
            "robots",
            "table_name_123",
            "_private_table",
            "CamelCaseTable",
        ]

        for name in valid_names:
            result = validate_sql_identifier(name)
            assert result == name

    def test_sql_injection_attempts_rejected(self):
        """Test that SQL injection attempts are blocked."""
        injection_attempts = [
            "users; DROP TABLE users; --",
            "table'; DELETE FROM users WHERE '1'='1",
            'table"; DROP TABLE users; --',
            "table OR 1=1",
            "table; EXEC sp_executesql",
            "table UNION SELECT * FROM passwords",
            "table--comment",
            "table/*comment*/",
        ]

        for attempt in injection_attempts:
            with pytest.raises(ValueError, match="Invalid SQL"):
                validate_sql_identifier(attempt)

    def test_reserved_keywords_rejected(self):
        """Test that SQL reserved keywords are rejected as table names."""
        keywords = [
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "CREATE",
            "ALTER",
            "TRUNCATE",
            "UNION",
            "EXEC",
            "EXECUTE",
        ]

        for keyword in keywords:
            with pytest.raises(ValueError, match="reserved keyword"):
                validate_sql_identifier(keyword)

            # Test case-insensitive
            with pytest.raises(ValueError, match="reserved keyword"):
                validate_sql_identifier(keyword.lower())

    def test_special_characters_rejected(self):
        """Test that special characters are rejected."""
        invalid_names = [
            "table name",  # space
            "table-name",  # dash (allowed in robot_id, not SQL identifiers)
            "table.name",  # dot
            "table@name",  # at sign
            "table#name",  # hash
            "table$name",  # dollar sign
            "table%name",  # percent
            "table&name",  # ampersand
            "table*name",  # asterisk
            "table(name)",  # parentheses
            "table[name]",  # brackets
            "table{name}",  # braces
            "table<name>",  # angle brackets
            "table=name",  # equals
            "table+name",  # plus
            "table|name",  # pipe
            "table\\name",  # backslash
            "table/name",  # forward slash
            "table:name",  # colon
            "table;name",  # semicolon
            "table'name",  # single quote
            'table"name',  # double quote
            "table`name",  # backtick
            "table,name",  # comma
        ]

        for name in invalid_names:
            with pytest.raises(ValueError, match="Invalid SQL"):
                validate_sql_identifier(name)

    def test_empty_string_rejected(self):
        """Test that empty string is rejected."""
        with pytest.raises(ValueError, match="empty string"):
            validate_sql_identifier("")

    def test_length_limit_enforced(self):
        """Test that PostgreSQL 63-character limit is enforced."""
        # 63 characters is OK
        valid = "a" * 63
        assert validate_sql_identifier(valid) == valid

        # 64 characters is too long
        with pytest.raises(ValueError):
            validate_sql_identifier("a" * 64)

    def test_must_start_with_letter_or_underscore(self):
        """Test that identifiers must start with letter or underscore."""
        # Valid starts
        assert validate_sql_identifier("_table") == "_table"
        assert validate_sql_identifier("table") == "table"

        # Invalid starts
        invalid_starts = [
            "1table",  # number
            "9table",
            "0table",
        ]

        for name in invalid_starts:
            with pytest.raises(ValueError):
                validate_sql_identifier(name)


class TestRobotIDValidation:
    """Test robot_id validation to prevent injection attacks."""

    def test_valid_robot_ids(self):
        """Test that valid robot IDs pass validation."""
        valid_ids = [
            "robot-001",
            "robot_001",
            "worker-abc123",
            "ROBOT-123",
            "robot-hostname-12345678",
            "a",  # minimum length 1
            "a" * 64,  # maximum length 64
        ]

        for robot_id in valid_ids:
            result = validate_robot_id(robot_id)
            assert result == robot_id

    def test_sql_injection_attempts_rejected(self):
        """Test that SQL injection attempts in robot_id are blocked."""
        injection_attempts = [
            "'; DROP TABLE robots; --",
            "robot'; DELETE FROM robots WHERE '1'='1",
            "robot OR 1=1",
            "robot; EXEC sp_executesql",
            "robot UNION SELECT * FROM passwords",
        ]

        for attempt in injection_attempts:
            with pytest.raises(ValueError, match="Invalid robot_id"):
                validate_robot_id(attempt)

    def test_empty_or_none_rejected(self):
        """Test that empty string or None is rejected."""
        with pytest.raises(ValueError, match="required"):
            validate_robot_id("")

        with pytest.raises(ValueError, match="required"):
            validate_robot_id(None)

    def test_special_characters_rejected(self):
        """Test that special characters (except dash and underscore) are rejected."""
        invalid_ids = [
            "robot@host",
            "robot#123",
            "robot$name",
            "robot name",  # space
            "robot.name",  # dot
            "robot/name",  # slash
            "robot\\name",  # backslash
            "robot'name",  # quote
            'robot"name',  # double quote
            "robot;name",  # semicolon
            "robot:name",  # colon
        ]

        for robot_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid robot_id"):
                validate_robot_id(robot_id)

    def test_length_limits(self):
        """Test that length limits are enforced."""
        # 64 characters is OK
        valid = "a" * 64
        assert validate_robot_id(valid) == valid

        # 65 characters is too long
        with pytest.raises(ValueError, match="Invalid robot_id"):
            validate_robot_id("a" * 65)


class TestWorkflowIDValidation:
    """Test workflow_id validation."""

    def test_valid_workflow_ids(self):
        """Test that valid workflow IDs pass validation."""
        valid_ids = [
            "workflow-123",
            "workflow_abc",
            "wf-12345678-1234-1234-1234-123456789012",  # UUID-like
            "a",
            "a" * 128,  # max length
        ]

        for wf_id in valid_ids:
            result = validate_workflow_id(wf_id)
            assert result == wf_id

    def test_sql_injection_rejected(self):
        """Test that SQL injection attempts are rejected."""
        injection_attempts = [
            "'; DROP TABLE workflows; --",
            "wf OR 1=1",
            "wf; DELETE FROM workflows",
        ]

        for attempt in injection_attempts:
            with pytest.raises(ValueError, match="Invalid workflow_id"):
                validate_workflow_id(attempt)

    def test_empty_rejected(self):
        """Test that empty string is rejected."""
        with pytest.raises(ValueError, match="required"):
            validate_workflow_id("")

    def test_length_limit(self):
        """Test length limit enforcement."""
        # 128 is OK
        assert validate_workflow_id("a" * 128)

        # 129 is too long
        with pytest.raises(ValueError):
            validate_workflow_id("a" * 129)


class TestJobIDValidation:
    """Test job_id (UUID) validation."""

    def test_valid_uuids(self):
        """Test that valid UUIDs pass validation."""
        valid_uuids = [
            "12345678-1234-1234-1234-123456789012",
            "abcdefab-cdef-abcd-efab-cdefabcdefab",
            "ABCDEFAB-CDEF-ABCD-EFAB-CDEFABCDEFAB",
            "00000000-0000-0000-0000-000000000000",
            "ffffffff-ffff-ffff-ffff-ffffffffffff",
        ]

        for uuid_str in valid_uuids:
            result = validate_job_id(uuid_str)
            assert result == uuid_str

    def test_invalid_uuids_rejected(self):
        """Test that invalid UUID formats are rejected."""
        invalid_uuids = [
            "not-a-uuid",
            "12345678-1234-1234-1234",  # too short
            "12345678-1234-1234-1234-12345678901",  # too short
            "12345678-1234-1234-1234-1234567890123",  # too long
            "12345678_1234_1234_1234_123456789012",  # underscores
            "123456781234123412341234567890 12",  # no dashes
            "'; DROP TABLE jobs; --",  # injection attempt
            "",  # empty
        ]

        for uuid_str in invalid_uuids:
            with pytest.raises(ValueError, match="Invalid job_id"):
                validate_job_id(uuid_str)


class TestLoggingSanitization:
    """Test log injection prevention."""

    def test_sanitize_removes_newlines(self):
        """Test that newlines are escaped."""
        malicious = "normal text\nINJECTED LOG LINE"
        sanitized = sanitize_for_logging(malicious)

        assert "\n" not in sanitized
        assert "\\n" in sanitized

    def test_sanitize_removes_carriage_returns(self):
        """Test that carriage returns are escaped."""
        malicious = "normal text\rINJECTED"
        sanitized = sanitize_for_logging(malicious)

        assert "\r" not in sanitized
        assert "\\r" in sanitized

    def test_sanitize_truncates_long_strings(self):
        """Test that long strings are truncated."""
        long_string = "a" * 100
        sanitized = sanitize_for_logging(long_string, max_length=50)

        assert len(sanitized) <= 53  # 50 + "..."
        assert sanitized.endswith("...")

    def test_sanitize_escapes_tabs(self):
        """Test that tabs are escaped."""
        text_with_tab = "column1\tcolumn2"
        sanitized = sanitize_for_logging(text_with_tab)

        assert "\t" not in sanitized
        assert "\\t" in sanitized

    def test_sanitize_preserves_normal_text(self):
        """Test that normal text is preserved."""
        normal = "normal log message"
        sanitized = sanitize_for_logging(normal)

        assert sanitized == normal
