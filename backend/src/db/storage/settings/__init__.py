"""
Settings Storage Package - Modular settings management.

This package provides a unified SettingsStorage class composed of mixins:
- SettingsStorageBase: Core AI settings
- CredentialsMixin: API credentials and secrets
- SiteConfigMixin: Landing page configuration
- DataSourceMixin: Data source priority settings
"""

from .base import SettingsStorageBase, DEFAULT_SETTINGS
from .credentials import CredentialsMixin
from .site_config import SiteConfigMixin
from .data_source import DataSourceMixin
from .logto_config import LogtoConfigMixin


class SettingsStorage(
    LogtoConfigMixin,
    DataSourceMixin,
    SiteConfigMixin,
    CredentialsMixin,
    SettingsStorageBase
):
    """
    Unified settings storage combining all configuration domains.

    Inherits from mixins in reverse MRO order so methods are resolved correctly.
    """
    pass


__all__ = [
    "SettingsStorage",
    "DEFAULT_SETTINGS",
]
