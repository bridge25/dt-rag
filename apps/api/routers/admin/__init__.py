"""
Admin API Routers

Administrative endpoints for system management and security.
These endpoints require elevated permissions and comprehensive audit logging.
"""

from .api_keys import router as api_keys_router

__all__ = ["api_keys_router"]