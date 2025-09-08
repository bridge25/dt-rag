# 📁 dt-rag/apps/orchestration/src/main.py (수정된 B팀 클라이언트)

from fastapi import FastAPI, HTTPException
import httpx
import asyncio
import logging
from typing import Dict, Any
import sys

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A팀 API 클라이언트 (수정된 안전한 버전)
class ATaxonomyAPIClient:
    def __init__(self, base_url: str = "http://localhost:8001", timeout: int = 10):
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)
        # Connection Pool 설정 (GPT 피드백 반영)
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        
        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )
    
    async def _request_with_retry(self, method: str, url: str, **kwargs) -> Dict[Any, Any]:
        """재시도 로직이 있는 HTTP 요청"""
        max_retries = 3
        backoff_factor = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == "POST":
                    response = await self.client.post(url, **kwargs)
                else:
                    response = await self.client.get(url, **kwargs)
                
                # ✅ 중요: HTTP 에러 처리 추가!
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.warning(f"A팀 API HTTP 오류: {e.response.status_code} - {e}")
                
                # 429 (Rate Limit) 또는 5xx 서버 에러만 재시도
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < max_retries:
                        delay = backoff_factor * (2 ** attempt)
                        logger.info(f"재시도 대기: {delay}초 (시도 {attempt + 1}/{max_retries + 1})")
                        await asyncio.sleep(delay)
                        continue
                
                # 재시도 불가능한 에러 또는 재시도 횟수 초과
                raise HTTPException(
                    status_code=503, 
                    detail=f"A팀 API 호출 실패: HTTP {e.response.status_code}"
                )
                
            except httpx.TimeoutException:
                logger.warning(f"A팀 API 타임아웃 (시도 {attempt + 1}/{max_retries + 1})")
                if attempt < max_retries:
                    await asyncio.sleep(backoff_factor * (2 ** attempt))
                    continue
                raise HTTPException(status_code=504, detail="A팀 API 타임아웃")
                
            except httpx.ConnectError:
                logger.error(f"A팀 서버 연결 실패: {url}")
                raise HTTPException(
                    status_code=503, 
                    detail="A팀 서버에 연결할 수 없습니다. A팀 서버가 실행 중인지 확인하세요."
                )
    
    async def classify(self, request: dict) -> dict:
        """A팀 /classify API 호출 (안전한 버전)"""
        return await self._request_with_retry("POST", f"{self.base_url}/classify", json=request)
    
    async def search(self, request: dict) -> dict:
        """A팀 /search API 호출 (안전한 버전)"""
        return await self._request_with_retry("POST", f"{self.base_url}/search", json=request)
    
    async def get_taxonomy_tree(self, version: str) -> dict:
        """A팀 /taxonomy/{version}/tree API 호출 (안전한 버전)"""
        return await self._request_with_retry("GET", f"{self.base_url}/taxonomy/{version}/tree")
    
    async def get_case_bank(self, category: str = None) -> dict:
        """A팀 /case_bank API 호출 (안전한 버전)"""
        params = {"category": category} if category else {}
        return await self._request_with_retry("GET", f"{self.base_url}/case_bank", params=params)
    
    async def health_check(self) -> dict:
        """A팀 서버 헬스 체크 (연결 테스트용)"""
        try:
            return await self._request_with_retry("GET", f"{self.base_url}/health")
        except HTTPException:
            return {"status": "unhealthy", "error": "A팀 서버 응답 없음"}
    
    async def close(self):
        """클라이언트 리소스 정리"""
        await self.client.aclose()

# FastAPI 앱 설정
app = FastAPI(title="B팀 Orchestration API", version="1.0.0")

# A팀 클라이언트 초기화
a_team_client = ATaxonomyAPIClient()

@app.get("/health")
async def health_check():
    """B팀 서버 헬스 체크"""
    return {"status": "healthy", "team": "B", "service": "orchestration"}

@app.get("/integration/test")
async def integration_test():
    """A팀-B팀 통합 테스트"""
    try:
        # A팀 서버 상태 확인
        a_team_health = await a_team_client.health_check()
        
        if a_team_health.get("status") != "healthy":
            return {
                "status": "failed",
                "error": "A팀 서버 비정상",
                "a_team_response": a_team_health
            }
        
        # 간단한 통합 테스트 실행
        test_classify = await a_team_client.classify({
            "chunk_id": "test-001",
            "text": "머신러닝 분류 테스트"
        })
        
        return {
            "status": "success",
            "message": "A팀-B팀 통합 정상 작동",
            "a_team_health": a_team_health,
            "test_classify": test_classify
        }
        
    except Exception as e:
        logger.error(f"통합 테스트 실패: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "troubleshooting": [
                "1. A팀 서버가 localhost:8001에서 실행 중인지 확인",
                "2. A팀 서버 로그 확인: python dt-rag/apps/taxonomy/main.py",
                "3. 방화벽/포트 차단 확인"
            ]
        }

@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 리소스 정리"""
    await a_team_client.close()

if __name__ == "__main__":
    import uvicorn
    print("🚀 B팀 Orchestration API 서버 시작")
    print("📡 포트: 8000")
    print("🔗 A팀 연결: localhost:8001")
    print("🧪 통합 테스트: GET /integration/test")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)