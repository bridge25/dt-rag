"""
Shared Utilities Package

Cross-cutting concerns and shared utilities for the API.

@CODE:CLEAN-ARCHITECTURE-SHARED
"""

from .config import get_settings, Settings
from .di_container import Container, get_container

__all__ = [
    "get_settings",
    "Settings",
    "Container",
    "get_container",
]
