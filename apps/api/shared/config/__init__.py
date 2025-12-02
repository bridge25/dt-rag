"""
Configuration Module

Application settings and configuration management.

@CODE:CLEAN-ARCHITECTURE-CONFIG
"""

from .settings import get_settings, Settings

__all__ = ["get_settings", "Settings"]
