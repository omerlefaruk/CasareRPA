"""
Tests for new features implemented:
- Template validation/sandboxing
- HTTP Request Node
- Validate Node
- Transform Node
- Log Node
- ErrorCode enum
- Rate limiting
- YAML/TOML config support
- Selector healing
- Stale element detection
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# =============================================================================
# Template Validation Tests
# =============================================================================

class TestTemplateValidation:
    """Tests for template validation and sandboxing."""

    def test_validate_safe_template(self, tmp_path):
        """Test that safe templates pass validation."""
        from casare_rpa.utils.template_loader import validate_template_code

        safe_code = '''
"""Safe template example."""
from typing import List
from casare_rpa.core.workflow_schema import Workflow

def create_example_workflow() -> Workflow:
    return Workflow()
'''
        template_file = tmp_path / "safe_template.py"
        template_file.write_text(safe_code)

        issues = validate_template_code(template_file)
        assert issues == [], f"Safe template should have no issues: {issues}"

    def test_validate_dangerous_eval(self, tmp_path):
        """Test that eval() is detected."""
        from casare_rpa.utils.template_loader import validate_template_code

        dangerous_code = '''
def execute():
    result = eval("2 + 2")
    return result
'''
        template_file = tmp_path / "dangerous.py"
        template_file.write_text(dangerous_code)

        issues = validate_template_code(template_file)
        assert any("eval" in issue for issue in issues)

    def test_validate_dangerous_exec(self, tmp_path):
        """Test that exec() is detected."""
        from casare_rpa.utils.template_loader import validate_template_code

        dangerous_code = '''
def execute():
    exec("print('hello')")
'''
        template_file = tmp_path / "dangerous.py"
        template_file.write_text(dangerous_code)

        issues = validate_template_code(template_file)
        assert any("exec" in issue for issue in issues)

    def test_validate_disallowed_import(self, tmp_path):
        """Test that disallowed imports are detected."""
        from casare_rpa.utils.template_loader import validate_template_code

        dangerous_code = '''
import subprocess
import os

def execute():
    subprocess.run(["ls"])
'''
        template_file = tmp_path / "dangerous.py"
        template_file.write_text(dangerous_code)

        issues = validate_template_code(template_file)
        assert any("subprocess" in issue or "Disallowed import" in issue for issue in issues)

    def test_allowed_modules(self):
        """Test that allowed modules list is correct."""
        from casare_rpa.utils.template_loader import ALLOWED_TEMPLATE_MODULES

        assert "casare_rpa.core" in ALLOWED_TEMPLATE_MODULES
        assert "casare_rpa.nodes" in ALLOWED_TEMPLATE_MODULES
        assert "typing" in ALLOWED_TEMPLATE_MODULES
        assert "datetime" in ALLOWED_TEMPLATE_MODULES


# =============================================================================
# ErrorCode Tests
# =============================================================================

class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_error_code_values(self):
        """Test that error codes have expected values."""
        from casare_rpa.core.types import ErrorCode

        # General errors (1xxx)
        assert ErrorCode.UNKNOWN_ERROR.value == 1000
        assert ErrorCode.TIMEOUT.value == 1001

        # Browser errors (2xxx)
        assert ErrorCode.BROWSER_NOT_FOUND.value == 2000
        assert ErrorCode.ELEMENT_NOT_FOUND.value == 2005

        # Desktop errors (3xxx)
        assert ErrorCode.WINDOW_NOT_FOUND.value == 3000

        # Network errors (6xxx)
        assert ErrorCode.NETWORK_ERROR.value == 6000

    def test_error_code_categories(self):
        """Test error code category property."""
        from casare_rpa.core.types import ErrorCode

        assert ErrorCode.TIMEOUT.category == "General"
        assert ErrorCode.BROWSER_CLOSED.category == "Browser/Web"
        assert ErrorCode.WINDOW_NOT_FOUND.category == "Desktop"
        assert ErrorCode.VALIDATION_FAILED.category == "Data/Validation"
        assert ErrorCode.CONFIG_NOT_FOUND.category == "Configuration"
        assert ErrorCode.NETWORK_ERROR.category == "Network"
        assert ErrorCode.FILE_NOT_FOUND.category == "Resource"

    def test_error_code_is_retryable(self):
        """Test is_retryable property."""
        from casare_rpa.core.types import ErrorCode

        assert ErrorCode.TIMEOUT.is_retryable is True
        assert ErrorCode.CONNECTION_TIMEOUT.is_retryable is True
        assert ErrorCode.ELEMENT_STALE.is_retryable is True
        assert ErrorCode.INVALID_INPUT.is_retryable is False
        assert ErrorCode.PERMISSION_DENIED.is_retryable is False

    def test_from_exception_timeout(self):
        """Test mapping timeout exceptions."""
        from casare_rpa.core.types import ErrorCode

        error_code = ErrorCode.from_exception(TimeoutError("Operation timed out"))
        assert error_code == ErrorCode.TIMEOUT

    def test_from_exception_value_error(self):
        """Test mapping ValueError."""
        from casare_rpa.core.types import ErrorCode

        error_code = ErrorCode.from_exception(ValueError("Invalid input"))
        assert error_code == ErrorCode.INVALID_INPUT

    def test_from_exception_file_not_found(self):
        """Test mapping FileNotFoundError."""
        from casare_rpa.core.types import ErrorCode

        error_code = ErrorCode.from_exception(FileNotFoundError("File not found"))
        assert error_code == ErrorCode.FILE_NOT_FOUND

    def test_from_exception_permission_error(self):
        """Test mapping PermissionError."""
        from casare_rpa.core.types import ErrorCode

        error_code = ErrorCode.from_exception(PermissionError("Access denied"))
        assert error_code == ErrorCode.PERMISSION_DENIED


# =============================================================================
# Rate Limiter Tests
# =============================================================================

class TestRateLimiter:
    """Tests for rate limiting functionality."""

    def test_rate_limit_config(self):
        """Test rate limit configuration."""
        from casare_rpa.utils.rate_limiter import RateLimitConfig

        config = RateLimitConfig(requests_per_second=5.0, burst_size=2)
        assert config.requests_per_second == 5.0
        assert config.burst_size == 2
        assert config.min_interval == 0.2  # 1/5

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_burst(self):
        """Test that rate limiter allows burst requests."""
        from casare_rpa.utils.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_second=10.0, burst_size=3)
        limiter = RateLimiter(config)

        # Should allow 3 requests immediately (burst)
        for _ in range(3):
            result = limiter.try_acquire()
            assert result is True

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_over_limit(self):
        """Test that rate limiter blocks requests over limit."""
        from casare_rpa.utils.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_second=10.0, burst_size=1)
        limiter = RateLimiter(config)

        # First request should succeed
        assert limiter.try_acquire() is True

        # Second request should fail (no burst)
        assert limiter.try_acquire() is False

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_waits(self):
        """Test that acquire waits for tokens."""
        from casare_rpa.utils.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_second=100.0, burst_size=1)
        limiter = RateLimiter(config)

        # First request
        await limiter.acquire()

        # Second request should wait
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # Should have waited at least ~10ms
        assert elapsed >= 0.005

    def test_rate_limit_stats(self):
        """Test rate limit statistics."""
        from casare_rpa.utils.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_second=10.0, burst_size=2)
        limiter = RateLimiter(config)

        limiter.try_acquire()
        limiter.try_acquire()
        limiter.try_acquire()  # Should fail

        stats = limiter.stats.to_dict()
        assert stats["total_requests"] == 2  # Only successful ones count in try_acquire
        assert "requests_delayed" in stats

    def test_sliding_window_limiter(self):
        """Test sliding window rate limiter."""
        from casare_rpa.utils.rate_limiter import SlidingWindowRateLimiter

        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=1.0)

        # Should allow 3 requests
        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is True

        # Fourth should fail
        assert limiter.try_acquire() is False

    def test_get_rate_limiter(self):
        """Test global rate limiter registry."""
        from casare_rpa.utils.rate_limiter import get_rate_limiter, clear_rate_limiters

        clear_rate_limiters()

        limiter1 = get_rate_limiter("test", requests_per_second=5.0)
        limiter2 = get_rate_limiter("test")

        assert limiter1 is limiter2


# =============================================================================
# Config Loader Tests
# =============================================================================

class TestConfigLoader:
    """Tests for YAML/TOML/JSON config loading."""

    def test_load_json_config(self, tmp_path):
        """Test loading JSON configuration."""
        from casare_rpa.utils.config_loader import load_config

        config_data = {"database": {"host": "localhost", "port": 5432}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        config = load_config(config_file)
        assert config["database"]["host"] == "localhost"
        assert config["database"]["port"] == 5432

    def test_load_missing_optional_config(self, tmp_path):
        """Test loading non-existent optional config."""
        from casare_rpa.utils.config_loader import load_config

        config = load_config(tmp_path / "missing.json", required=False)
        assert config == {}

    def test_load_missing_required_config_raises(self, tmp_path):
        """Test that missing required config raises error."""
        from casare_rpa.utils.config_loader import load_config, ConfigurationError

        with pytest.raises(ConfigurationError):
            load_config(tmp_path / "missing.json", required=True)

    def test_config_deep_merge(self, tmp_path):
        """Test deep merging of configurations."""
        from casare_rpa.utils.config_loader import ConfigLoader

        loader = ConfigLoader()

        base = {"a": 1, "nested": {"x": 1, "y": 2}}
        override = {"b": 2, "nested": {"y": 3, "z": 4}}

        merged = loader._deep_merge(base, override)

        assert merged["a"] == 1
        assert merged["b"] == 2
        assert merged["nested"]["x"] == 1
        assert merged["nested"]["y"] == 3  # Overridden
        assert merged["nested"]["z"] == 4

    def test_config_validation(self, tmp_path):
        """Test configuration validation."""
        from casare_rpa.utils.config_loader import ConfigLoader, ConfigSchema

        loader = ConfigLoader()

        config = {"name": "test", "count": 5}
        schema = ConfigSchema(
            required_keys=["name"],
            type_hints={"name": str, "count": int},
            defaults={"enabled": True}
        )

        validated = loader.validate(config, schema)

        assert validated["name"] == "test"
        assert validated["count"] == 5
        assert validated["enabled"] is True  # Default applied

    def test_config_validation_fails_missing_required(self, tmp_path):
        """Test that validation fails for missing required keys."""
        from casare_rpa.utils.config_loader import ConfigLoader, ConfigSchema, ConfigurationError

        loader = ConfigLoader()

        config = {"count": 5}
        schema = ConfigSchema(required_keys=["name"])

        with pytest.raises(ConfigurationError) as exc_info:
            loader.validate(config, schema)

        assert "name" in str(exc_info.value)

    def test_env_variable_loading(self, tmp_path, monkeypatch):
        """Test loading config from environment variables."""
        from casare_rpa.utils.config_loader import ConfigLoader

        monkeypatch.setenv("CASARE_DATABASE__HOST", "env-host")
        monkeypatch.setenv("CASARE_DATABASE__PORT", "5433")

        loader = ConfigLoader(env_prefix="CASARE_")
        env_config = loader._load_from_env()

        assert env_config["database"]["host"] == "env-host"
        assert env_config["database"]["port"] == 5433  # Parsed as int


# =============================================================================
# Selector Healing Tests
# =============================================================================

class TestSelectorHealing:
    """Tests for selector healing functionality."""

    def test_element_fingerprint_creation(self):
        """Test ElementFingerprint creation."""
        from casare_rpa.utils.selector_healing import ElementFingerprint

        fp = ElementFingerprint(
            tag_name="button",
            text_content="Submit",
            id_attr="submit-btn",
            class_list=["btn", "btn-primary"]
        )

        assert fp.tag_name == "button"
        assert fp.text_content == "Submit"
        assert fp.id_attr == "submit-btn"
        assert "btn" in fp.class_list

    def test_element_fingerprint_hash(self):
        """Test fingerprint hash consistency."""
        from casare_rpa.utils.selector_healing import ElementFingerprint

        fp1 = ElementFingerprint(tag_name="button", id_attr="test")
        fp2 = ElementFingerprint(tag_name="button", id_attr="test")

        assert fp1.fingerprint_hash == fp2.fingerprint_hash

    def test_element_fingerprint_serialization(self):
        """Test fingerprint serialization."""
        from casare_rpa.utils.selector_healing import ElementFingerprint

        fp = ElementFingerprint(
            tag_name="input",
            name_attr="email",
            type_attr="email"
        )

        data = fp.to_dict()
        restored = ElementFingerprint.from_dict(data)

        assert restored.tag_name == fp.tag_name
        assert restored.name_attr == fp.name_attr
        assert restored.type_attr == fp.type_attr

    def test_selector_healer_generate_alternatives(self):
        """Test alternative selector generation."""
        from casare_rpa.utils.selector_healing import SelectorHealer, ElementFingerprint

        healer = SelectorHealer()

        fp = ElementFingerprint(
            tag_name="button",
            text_content="Submit",
            id_attr="submit-btn",
            data_testid="submit-button",
            aria_label="Submit form"
        )

        alternatives = healer._generate_alternatives(fp)

        # Should have alternatives based on various attributes
        selectors = [a[0] for a in alternatives]

        assert any("data-testid" in s for s in selectors)
        assert any("#submit-btn" in s for s in selectors)
        assert any("aria-label" in s for s in selectors)

    def test_selector_healer_similarity_calculation(self):
        """Test similarity calculation between fingerprints."""
        from casare_rpa.utils.selector_healing import SelectorHealer, ElementFingerprint

        healer = SelectorHealer()

        fp1 = ElementFingerprint(tag_name="button", id_attr="test", text_content="Click")
        fp2 = ElementFingerprint(tag_name="button", id_attr="test", text_content="Click")
        fp3 = ElementFingerprint(tag_name="div", id_attr="other", text_content="Different")

        # Same fingerprints should have reasonable similarity
        sim_same = healer._calculate_similarity(fp1, fp2)
        assert sim_same > 0.4  # At least 40% similar (tag+id+text match)

        # Different fingerprints should have low similarity
        sim_diff = healer._calculate_similarity(fp1, fp3)
        assert sim_diff < sim_same

    def test_selector_healer_storage(self, tmp_path):
        """Test fingerprint storage and loading."""
        from casare_rpa.utils.selector_healing import SelectorHealer, ElementFingerprint

        storage_file = tmp_path / "fingerprints.json"
        healer = SelectorHealer(storage_path=storage_file)

        fp = ElementFingerprint(tag_name="button", id_attr="test")
        healer.store_fingerprint("#test", fp)

        # Create new healer that loads from storage
        healer2 = SelectorHealer(storage_path=storage_file)
        healer2._load_fingerprints()

        loaded_fp = healer2.get_fingerprint("#test")
        assert loaded_fp is not None
        assert loaded_fp.id_attr == "test"


# =============================================================================
# Utility Node Tests
# =============================================================================

class TestValidateNode:
    """Tests for ValidateNode."""

    @pytest.mark.asyncio
    async def test_validate_not_empty_valid(self):
        """Test not_empty validation with valid value."""
        from casare_rpa.nodes.utility_nodes import ValidateNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = ValidateNode("test", validation_type="not_empty")
        node.set_input_value("value", "hello")

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["success"] is True
        assert result["is_valid"] is True
        assert "valid" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_validate_not_empty_invalid(self):
        """Test not_empty validation with empty value."""
        from casare_rpa.nodes.utility_nodes import ValidateNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = ValidateNode("test", validation_type="not_empty")
        node.set_input_value("value", "")

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["is_valid"] is False
        assert "invalid" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_validate_is_email(self):
        """Test email validation."""
        from casare_rpa.nodes.utility_nodes import ValidateNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = ValidateNode("test", validation_type="is_email")
        context = ExecutionContext()

        # Valid email
        node.set_input_value("value", "test@example.com")
        result = await node.execute(context)
        assert result["is_valid"] is True

        # Invalid email
        node.set_input_value("value", "not-an-email")
        result = await node.execute(context)
        assert result["is_valid"] is False

    @pytest.mark.asyncio
    async def test_validate_min_length(self):
        """Test minimum length validation."""
        from casare_rpa.nodes.utility_nodes import ValidateNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = ValidateNode("test", validation_type="min_length", validation_param=5)
        context = ExecutionContext()

        node.set_input_value("value", "hello")
        result = await node.execute(context)
        assert result["is_valid"] is True

        node.set_input_value("value", "hi")
        result = await node.execute(context)
        assert result["is_valid"] is False


class TestTransformNode:
    """Tests for TransformNode."""

    @pytest.mark.asyncio
    async def test_transform_to_string(self):
        """Test to_string transformation."""
        from casare_rpa.nodes.utility_nodes import TransformNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = TransformNode("test", transform_type="to_string")
        node.set_input_value("value", 123)

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["success"] is True
        assert result["result"] == "123"

    @pytest.mark.asyncio
    async def test_transform_uppercase(self):
        """Test uppercase transformation."""
        from casare_rpa.nodes.utility_nodes import TransformNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = TransformNode("test", transform_type="uppercase")
        node.set_input_value("value", "hello")

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["result"] == "HELLO"

    @pytest.mark.asyncio
    async def test_transform_split(self):
        """Test split transformation."""
        from casare_rpa.nodes.utility_nodes import TransformNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = TransformNode("test", transform_type="split", transform_param=",")
        node.set_input_value("value", "a,b,c")

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["result"] == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_transform_to_json(self):
        """Test to_json transformation."""
        from casare_rpa.nodes.utility_nodes import TransformNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = TransformNode("test", transform_type="to_json")
        node.set_input_value("value", {"key": "value"})

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["result"] == '{"key": "value"}'

    @pytest.mark.asyncio
    async def test_transform_from_json(self):
        """Test from_json transformation."""
        from casare_rpa.nodes.utility_nodes import TransformNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = TransformNode("test", transform_type="from_json")
        node.set_input_value("value", '{"key": "value"}')

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["result"] == {"key": "value"}


class TestLogNode:
    """Tests for LogNode."""

    @pytest.mark.asyncio
    async def test_log_node_basic(self):
        """Test basic logging."""
        from casare_rpa.nodes.utility_nodes import LogNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = LogNode("test", message="Test message", level="info")

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["success"] is True
        assert "Test message" in result["message"]

    @pytest.mark.asyncio
    async def test_log_node_with_variables(self):
        """Test logging with variable substitution."""
        from casare_rpa.nodes.utility_nodes import LogNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = LogNode("test", message="User: {username}", level="info")

        context = ExecutionContext()
        context.set_variable("username", "john")
        result = await node.execute(context)

        assert result["success"] is True
        assert "john" in result["message"]


# =============================================================================
# Stale Element Detection Tests
# =============================================================================

class TestStaleElementDetection:
    """Tests for stale element detection in desktop automation."""

    def test_stale_element_error_exists(self):
        """Test that StaleElementError exists."""
        from casare_rpa.desktop.element import StaleElementError

        error = StaleElementError("Element is stale")
        assert str(error) == "Element is stale"

    def test_desktop_element_locator_capture(self):
        """Test that locator info is captured."""
        # This would require mocking uiautomation
        pass  # Skipped - requires actual Windows UI

    def test_with_stale_check_decorator_exists(self):
        """Test that stale check decorator exists."""
        from casare_rpa.desktop.element import with_stale_check

        assert callable(with_stale_check)


# =============================================================================
# Execution Context Desktop Cleanup Tests
# =============================================================================

class TestExecutionContextCleanup:
    """Tests for ExecutionContext cleanup including desktop context."""

    @pytest.mark.asyncio
    async def test_context_has_desktop_context_attribute(self):
        """Test that ExecutionContext has desktop_context attribute."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext()
        assert hasattr(context, "desktop_context")
        assert context.desktop_context is None

    @pytest.mark.asyncio
    async def test_context_cleanup_handles_desktop(self):
        """Test that cleanup handles desktop context."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext()

        # Mock desktop context with cleanup method
        mock_desktop = MagicMock()
        mock_desktop.cleanup = MagicMock()
        context.desktop_context = mock_desktop

        await context.cleanup()

        mock_desktop.cleanup.assert_called_once()
        assert context.desktop_context is None


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for multiple new features."""

    def test_all_new_exports_available(self):
        """Test that all new exports are available."""
        from casare_rpa.utils import (
            RateLimiter,
            RateLimitConfig,
            ConfigLoader,
            ConfigurationError,
            SelectorHealer,
            ElementFingerprint,
            TemplateValidationError,
        )

        assert RateLimiter is not None
        assert RateLimitConfig is not None
        assert ConfigLoader is not None
        assert SelectorHealer is not None

    def test_error_code_in_types(self):
        """Test ErrorCode is accessible from types."""
        from casare_rpa.core.types import ErrorCode

        assert hasattr(ErrorCode, "TIMEOUT")
        assert hasattr(ErrorCode, "ELEMENT_NOT_FOUND")

    def test_utility_nodes_in_registry(self):
        """Test utility nodes are in the node registry."""
        from casare_rpa.nodes import _NODE_REGISTRY

        assert "HttpRequestNode" in _NODE_REGISTRY
        assert "ValidateNode" in _NODE_REGISTRY
        assert "TransformNode" in _NODE_REGISTRY
        assert "LogNode" in _NODE_REGISTRY


# =============================================================================
# Extended Comparison Node Tests
# =============================================================================

class TestComparisonNodeExtended:
    """Tests for extended ComparisonNode operators."""

    @pytest.mark.asyncio
    async def test_comparison_and_operator(self):
        """Test 'and' operator."""
        from casare_rpa.nodes.data_operation_nodes import ComparisonNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = ComparisonNode("test", config={"operator": "and"})
        node.set_input_value("a", True)
        node.set_input_value("b", True)

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["success"] is True
        assert result["data"]["result"] is True

        # Test with False
        node.set_input_value("a", True)
        node.set_input_value("b", False)
        result = await node.execute(context)
        assert result["data"]["result"] is False

    @pytest.mark.asyncio
    async def test_comparison_or_operator(self):
        """Test 'or' operator."""
        from casare_rpa.nodes.data_operation_nodes import ComparisonNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = ComparisonNode("test", config={"operator": "or"})
        node.set_input_value("a", False)
        node.set_input_value("b", True)

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["success"] is True
        assert result["data"]["result"] is True

    @pytest.mark.asyncio
    async def test_comparison_in_operator(self):
        """Test 'in' operator."""
        from casare_rpa.nodes.data_operation_nodes import ComparisonNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = ComparisonNode("test", config={"operator": "in"})
        node.set_input_value("a", "hello")
        node.set_input_value("b", "hello world")

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["success"] is True
        assert result["data"]["result"] is True

        # Test with list
        node.set_input_value("a", 2)
        node.set_input_value("b", [1, 2, 3])
        result = await node.execute(context)
        assert result["data"]["result"] is True

    @pytest.mark.asyncio
    async def test_comparison_not_in_operator(self):
        """Test 'not in' operator."""
        from casare_rpa.nodes.data_operation_nodes import ComparisonNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = ComparisonNode("test", config={"operator": "not in"})
        node.set_input_value("a", "xyz")
        node.set_input_value("b", "hello world")

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["success"] is True
        assert result["data"]["result"] is True

    @pytest.mark.asyncio
    async def test_comparison_custom_operator(self):
        """Test custom_operator overrides dropdown."""
        from casare_rpa.nodes.data_operation_nodes import ComparisonNode
        from casare_rpa.core.execution_context import ExecutionContext

        # custom_operator should override the dropdown operator
        node = ComparisonNode("test", config={"operator": "==", "custom_operator": ">"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["success"] is True
        assert result["data"]["result"] is True
        assert result["data"]["operator"] == ">"

    @pytest.mark.asyncio
    async def test_comparison_is_operator(self):
        """Test 'is' operator."""
        from casare_rpa.nodes.data_operation_nodes import ComparisonNode
        from casare_rpa.core.execution_context import ExecutionContext

        node = ComparisonNode("test", config={"operator": "is"})
        node.set_input_value("a", None)
        node.set_input_value("b", None)

        context = ExecutionContext()
        result = await node.execute(context)

        assert result["success"] is True
        assert result["data"]["result"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
