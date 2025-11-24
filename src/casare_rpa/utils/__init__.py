"""
CasareRPA - Utilities Package
Contains configuration, helpers, and shared utilities.
"""

from .config import (
    APP_NAME,
    APP_VERSION,
    APP_AUTHOR,
    APP_DESCRIPTION,
    PROJECT_ROOT,
    LOGS_DIR,
    WORKFLOWS_DIR,
    setup_logging,
)
from .hotkey_settings import get_hotkey_settings, HotkeySettings
from .template_loader import (
    TemplateLoader,
    TemplateInfo,
    get_template_loader,
    TemplateValidationError,
    validate_template_code,
)
from .rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStats,
    RateLimitExceeded,
    SlidingWindowRateLimiter,
    rate_limited,
    get_rate_limiter,
)
from .config_loader import (
    ConfigLoader,
    ConfigSource,
    ConfigSchema,
    ConfigurationError,
    load_config,
    load_config_with_env,
)
from .selector_healing import (
    SelectorHealer,
    ElementFingerprint,
    HealingResult,
    get_selector_healer,
)

__all__ = [
    # Config
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_DESCRIPTION",
    "PROJECT_ROOT",
    "LOGS_DIR",
    "WORKFLOWS_DIR",
    "setup_logging",
    # Hotkeys
    "get_hotkey_settings",
    "HotkeySettings",
    # Templates
    "TemplateLoader",
    "TemplateInfo",
    "get_template_loader",
    "TemplateValidationError",
    "validate_template_code",
    # Rate limiting
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitStats",
    "RateLimitExceeded",
    "SlidingWindowRateLimiter",
    "rate_limited",
    "get_rate_limiter",
    # Config loader
    "ConfigLoader",
    "ConfigSource",
    "ConfigSchema",
    "ConfigurationError",
    "load_config",
    "load_config_with_env",
    # Selector healing
    "SelectorHealer",
    "ElementFingerprint",
    "HealingResult",
    "get_selector_healer",
]
