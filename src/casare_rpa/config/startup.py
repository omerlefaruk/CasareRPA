"""
CasareRPA Configuration Startup Hooks.

Provides startup validation for different application entry points.
"""

from typing import Optional

from loguru import logger

from casare_rpa.config.loader import ConfigurationError, get_config, validate_config
from casare_rpa.config.schema import Config


def validate_orchestrator_config() -> Config:
    """
    Validate configuration for Orchestrator API startup.

    Requires:
    - Database configuration (if enabled)
    - API secret for production

    Returns:
        Validated Config

    Raises:
        ConfigurationError: If configuration is invalid
    """
    config = validate_config(require_database=True)

    # Warn if running without API secret
    if not config.security.api_secret and not config.debug:
        logger.warning(
            "API_SECRET not set. JWT authentication will use insecure default. "
            "Set API_SECRET for production deployments."
        )

    # Warn if CORS is wide open
    if "*" in config.orchestrator.cors_origins:
        logger.warning("CORS_ORIGINS includes '*'. Restrict to specific domains for production.")

    return config


def validate_robot_config() -> Config:
    """
    Validate configuration for Robot Agent startup.

    Requires:
    - Database or queue configuration
    - Robot name or ID

    Returns:
        Validated Config

    Raises:
        ConfigurationError: If configuration is invalid
    """
    config = validate_config(require_database=True)

    # Check queue configuration
    if config.queue.use_memory_queue:
        logger.warning(
            "USE_MEMORY_QUEUE=true - jobs will be lost on restart. " "Only use for development."
        )

    return config


def validate_canvas_config() -> Config:
    """
    Validate configuration for Canvas Designer startup.

    Minimal requirements - Canvas can run in standalone mode.

    Returns:
        Validated Config
    """
    config = get_config()

    # Log mode
    if config.supabase.is_configured:
        logger.info("Canvas running with Supabase cloud sync enabled")
    else:
        logger.info("Canvas running in local-only mode (no cloud sync)")

    return config


def print_config_summary(config: Config | None = None) -> None:
    """
    Print configuration summary to console.

    Useful for debugging and startup diagnostics.

    Args:
        config: Config to summarize (loads if not provided)
    """
    if config is None:
        config = get_config()

    summary = config.get_summary(mask_secrets=True)

    print("\n" + "=" * 60)
    print("CasareRPA Configuration Summary")
    print("=" * 60)

    for section, values in summary.items():
        print(f"\n[{section}]")
        if isinstance(values, dict):
            for key, value in values.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {values}")

    print("\n" + "=" * 60 + "\n")


def check_required_env_vars(
    required: list[str],
    optional_warnings: list[str] | None = None,
) -> bool:
    """
    Check for required environment variables and warn about optional ones.

    Args:
        required: List of required environment variable names
        optional_warnings: List of optional vars to warn if missing

    Returns:
        True if all required vars are set

    Raises:
        ConfigurationError: If any required var is missing
    """
    import os

    missing = [var for var in required if not os.getenv(var)]

    if missing:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(missing)}",
            missing_fields=missing,
        )

    if optional_warnings:
        for var in optional_warnings:
            if not os.getenv(var):
                logger.warning(f"Optional environment variable {var} not set")

    return True
