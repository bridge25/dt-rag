"""
Database Middleware
데이터베이스 연결 관리 미들웨어
"""

import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from ..services.database_service import get_database_service

logger = logging.getLogger(__name__)


class DatabaseMiddleware:
    """데이터베이스 연결 미들웨어"""
    
    def __init__(self, app):
        self.app = app
        self.db_service = get_database_service()
    
    async def __call__(self, request: Request, call_next: Callable):
        """미들웨어 실행"""
        
        # Skip database check for health endpoint to avoid circular dependency
        if request.url.path == "/health":
            return await call_next(request)
        
        # Check if database is available
        try:
            if not self.db_service.pool:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": {
                            "type": "service_unavailable",
                            "code": 503,
                            "message": "Database service not available",
                            "timestamp": request.state.get("start_time", 0)
                        }
                    }
                )
            
            # Attach database service to request
            request.state.db_service = self.db_service
            
            # Process request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Database middleware error: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "type": "database_error", 
                        "code": 503,
                        "message": "Database error occurred",
                        "timestamp": request.state.get("start_time", 0)
                    }
                }
            )