"""
Configuration Loader Utility

Provides support for loading configuration from multiple file formats:
- YAML (.yaml, .yml)
- TOML (.toml)
- JSON (.json)
- Environment variables

Supports configuration merging, validation, and environment-specific overrides.
"""

import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from loguru import logger

# Optional dependencies - gracefully degrade if not installed
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

try:
    import tomllib  # Python 3.11+

    TOML_AVAILABLE = True
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python

        TOML_AVAILABLE = True
    except ImportError:
        tomllib = None
        TOML_AVAILABLE = False


T = TypeVar("T")


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""

    pass


@dataclass
class ConfigSource:
    """Represents a configuration source."""

    path: Path
    """Path to the configuration file."""

    format: str
    """File format (yaml, toml, json)."""

    priority: int = 0
    """Priority for merging (higher = overrides lower)."""

    required: bool = False
    """Whether this config source is required to exist."""

    environment: str | None = None
    """Environment name (e.g., 'development', 'production')."""


@dataclass
class ConfigSchema:
    """Schema for configuration validation."""

    required_keys: list[str] = field(default_factory=list)
    """Keys that must be present in configuration."""

    optional_keys: list[str] = field(default_factory=list)
    """Keys that may be present but are not required."""

    type_hints: dict[str, type] = field(default_factory=dict)
    """Expected types for configuration keys."""

    defaults: dict[str, Any] = field(default_factory=dict)
    """Default values for optional keys."""

    validators: dict[str, callable] = field(default_factory=dict)
    """Custom validation functions for keys."""


class ConfigLoader:
    """
    Configuration loader supporting multiple file formats.

    Example:
        loader = ConfigLoader()
        config = loader.load("config.yaml")

        # Or with multiple sources
        loader.add_source(ConfigSource(Path("base.yaml"), "yaml", priority=0))
        loader.add_source(ConfigSource(Path("local.yaml"), "yaml", priority=10))
        config = loader.load_all()
    """

    def __init__(
        self,
        base_path: Path | None = None,
        env_prefix: str = "CASARE_",
        load_env: bool = True,
    ):
        """
        Initialize configuration loader.

        Args:
            base_path: Base path for relative config file paths
            env_prefix: Prefix for environment variable overrides
            load_env: Whether to load environment variable overrides
        """
        self.base_path = base_path or Path.cwd()
        self.env_prefix = env_prefix
        self.load_env = load_env
        self._sources: list[ConfigSource] = []
        self._cache: dict[str, dict[str, Any]] = {}

    def add_source(self, source: ConfigSource) -> None:
        """Add a configuration source."""
        self._sources.append(source)
        self._sources.sort(key=lambda s: s.priority)

    def clear_sources(self) -> None:
        """Clear all configuration sources."""
        self._sources.clear()
        self._cache.clear()

    def load(
        self,
        path: str | Path,
        format: str | None = None,
        required: bool = True,
    ) -> dict[str, Any]:
        """
        Load configuration from a single file.

        Args:
            path: Path to configuration file
            format: File format (auto-detected if None)
            required: Whether file must exist

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If file doesn't exist and required=True
        """
        path = Path(path)
        if not path.is_absolute():
            path = self.base_path / path

        # Auto-detect format from extension
        if format is None:
            format = self._detect_format(path)

        if not path.exists():
            if required:
                raise ConfigurationError(f"Configuration file not found: {path}")
            logger.debug(f"Optional config file not found: {path}")
            return {}

        # Check cache
        cache_key = str(path)
        if cache_key in self._cache:
            return deepcopy(self._cache[cache_key])

        # Load based on format
        logger.info(f"Loading configuration from: {path} (format: {format})")

        try:
            if format == "yaml":
                config = self._load_yaml(path)
            elif format == "toml":
                config = self._load_toml(path)
            elif format == "json":
                config = self._load_json(path)
            else:
                raise ConfigurationError(f"Unsupported config format: {format}")

            self._cache[cache_key] = config
            return deepcopy(config)

        except Exception as e:
            raise ConfigurationError(f"Failed to load {path}: {e}")

    def load_all(self, environment: str | None = None) -> dict[str, Any]:
        """
        Load and merge configuration from all sources.

        Args:
            environment: Filter sources by environment (None = all)

        Returns:
            Merged configuration dictionary
        """
        config = {}

        for source in self._sources:
            # Skip sources not matching environment
            if environment and source.environment and source.environment != environment:
                continue

            try:
                source_config = self.load(source.path, source.format, source.required)
                config = self._deep_merge(config, source_config)
            except ConfigurationError:
                if source.required:
                    raise

        # Apply environment variable overrides
        if self.load_env:
            env_config = self._load_from_env()
            config = self._deep_merge(config, env_config)

        return config

    def validate(self, config: dict[str, Any], schema: ConfigSchema) -> dict[str, Any]:
        """
        Validate configuration against a schema.

        Args:
            config: Configuration to validate
            schema: Schema to validate against

        Returns:
            Validated configuration with defaults applied

        Raises:
            ConfigurationError: If validation fails
        """
        errors = []
        validated = deepcopy(config)

        # Apply defaults
        for key, default in schema.defaults.items():
            if key not in validated:
                validated[key] = default

        # Check required keys
        for key in schema.required_keys:
            if key not in validated:
                errors.append(f"Missing required key: {key}")

        # Check types
        for key, expected_type in schema.type_hints.items():
            if key in validated:
                if not isinstance(validated[key], expected_type):
                    errors.append(
                        f"Key '{key}' has wrong type: "
                        f"expected {expected_type.__name__}, "
                        f"got {type(validated[key]).__name__}"
                    )

        # Run custom validators
        for key, validator in schema.validators.items():
            if key in validated:
                try:
                    if not validator(validated[key]):
                        errors.append(f"Validation failed for key: {key}")
                except Exception as e:
                    errors.append(f"Validator error for '{key}': {e}")

        if errors:
            raise ConfigurationError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return validated

    def _detect_format(self, path: Path) -> str:
        """Detect configuration format from file extension."""
        suffix = path.suffix.lower()

        if suffix in (".yaml", ".yml"):
            return "yaml"
        elif suffix == ".toml":
            return "toml"
        elif suffix == ".json":
            return "json"
        else:
            raise ConfigurationError(
                f"Cannot detect config format for: {path}. "
                f"Supported extensions: .yaml, .yml, .toml, .json"
            )

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load YAML configuration."""
        if not YAML_AVAILABLE:
            raise ConfigurationError(
                "YAML support not available. Install PyYAML: pip install pyyaml"
            )

        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _load_toml(self, path: Path) -> dict[str, Any]:
        """Load TOML configuration."""
        if not TOML_AVAILABLE:
            raise ConfigurationError("TOML support not available. Install tomli: pip install tomli")

        with open(path, "rb") as f:
            return tomllib.load(f)

    def _load_json(self, path: Path) -> dict[str, Any]:
        """Load JSON configuration."""
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _load_from_env(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        prefix_len = len(self.env_prefix)

        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # Remove prefix and convert to lowercase
                config_key = key[prefix_len:].lower()

                # Handle nested keys (e.g., CASARE_DATABASE_HOST -> database.host)
                parts = config_key.split("__")

                # Try to parse value as JSON for complex types
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value

                # Set nested value
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = parsed_value

        return config

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """
        Deep merge two dictionaries.

        Override values take precedence over base values.
        Nested dictionaries are merged recursively.
        """
        result = deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)

        return result


# Convenience functions for simple use cases


def load_config(path: str | Path, required: bool = True) -> dict[str, Any]:
    """
    Load configuration from a file.

    Args:
        path: Path to configuration file
        required: Whether file must exist

    Returns:
        Configuration dictionary
    """
    loader = ConfigLoader()
    return loader.load(path, required=required)


def load_config_with_env(
    path: str | Path, env_prefix: str = "CASARE_", required: bool = True
) -> dict[str, Any]:
    """
    Load configuration from file with environment variable overrides.

    Args:
        path: Path to configuration file
        env_prefix: Prefix for environment variables
        required: Whether file must exist

    Returns:
        Configuration dictionary with env overrides applied
    """
    loader = ConfigLoader(env_prefix=env_prefix)
    base_config = loader.load(path, required=required)
    env_config = loader._load_from_env()
    return loader._deep_merge(base_config, env_config)


__all__ = [
    "ConfigurationError",
    "ConfigSource",
    "ConfigSchema",
    "ConfigLoader",
    "load_config",
    "load_config_with_env",
    "YAML_AVAILABLE",
    "TOML_AVAILABLE",
]
