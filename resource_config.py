"""Compatibility imports for the former top-level configuration module."""

from filekiller.config import (
    CONFIG_ENV_VAR,
    DEFAULT_CONFIG_RELATIVE_PATH,
    REQUIRED_AUDIO,
    REQUIRED_SPRITES,
    ResourceConfig,
    ResourceConfigError,
    application_base_path,
    find_config_path,
)


_application_base_path = application_base_path
_find_config_path = find_config_path

__all__ = [
    "CONFIG_ENV_VAR",
    "DEFAULT_CONFIG_RELATIVE_PATH",
    "REQUIRED_AUDIO",
    "REQUIRED_SPRITES",
    "ResourceConfig",
    "ResourceConfigError",
    "_application_base_path",
    "_find_config_path",
]
