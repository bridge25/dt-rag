"""
A팀 API 공통 의존성
- API Key 검증
- Request ID 생성
- 공통 응답 필드
"""

from fastapi import Header, HTTPException
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Bridge Pack 스펙: X-API-Key 헤더 필수"""
    if not x_api_key:
        raise HTTPException(
            status_code=403, 
            detail="API key required. Include 'X-API-Key' header."
        )
    
    # MVP: 모든 키 허용 (프로덕션에서는 실제 검증 로직)
    if len(x_api_key) < 3:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key format"
        )
    
    return x_api_key

def generate_request_id() -> str:
    """요청 ID 생성 (Bridge Pack 스펙 준수)"""
    return str(uuid4())

def get_current_timestamp() -> str:
    """ISO 8601 타임스탬프 생성"""
    return datetime.now(timezone.utc).isoformat()

def get_taxonomy_version() -> str:
    """현재 taxonomy 버전 (Bridge Pack 스펙)"""
    return "1.8.1"