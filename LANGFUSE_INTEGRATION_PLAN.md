# Langfuse 통합 설계 문서 (Phase 2)

## 1. 정보 수집 완료 (IG 임계점 검증)

### ✅ 확인된 정보
- **패키지 버전**: `langfuse==3.6.1` (최신, 2025년 v3 GA 버전)
- **설치 방법**: `pip install langfuse`
- **SDK 아키텍처**: OpenTelemetry 기반 (v3)
- **환경변수**: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`
- **통합 방법**: Decorator 패턴 (`@observe()`) 또는 Low-level SDK

### ✅ 통합 범위 결정
```python
# 통합 대상 (우선순위순)
1. apps/evaluation/ragas_engine.py - Gemini 2.5 Flash API 호출 (평가 엔진)
2. apps/api/embedding_service.py - OpenAI text-embedding-3-large (임베딩 생성)
3. apps/search/hybrid_search_engine.py - search() (검색 엔진)
4. apps/api/routers/search_router.py - search_documents() (API 엔드포인트)
```

### ✅ 현재 사용 중인 LLM 확인
- **평가(RAGAS)**: Gemini 2.5 Flash (`apps/evaluation/ragas_engine.py:51`)
  - API Key: `GEMINI_API_KEY` (환경변수 제공됨)
  - 모델: `gemini-pro` (실제 사용: gemini-2.5-flash 권장)
- **임베딩**: OpenAI text-embedding-3-large (`apps/api/embedding_service.py:61`)
  - API Key: `OPENAI_API_KEY`
  - 차원: 1536
- **생성(미사용)**: 현재 LLM 기반 텍스트 생성 없음 (평가만 사용)

---

## 2. 구현 계획

### Step 1: 의존성 추가 (1시간)
```bash
# requirements.txt에 추가
langfuse>=3.6.0
```

### Step 2: Langfuse 클라이언트 초기화 (2시간)
**파일**: `apps/api/monitoring/langfuse_client.py` (신규)

```python
"""
Langfuse LLM 비용 추적 클라이언트
OpenTelemetry 기반 v3 SDK 사용
"""
import os
from typing import Optional
from langfuse import Langfuse
from langfuse.decorators import observe

# 환경변수 기반 초기화
langfuse_client = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    enabled=os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"
)

# IG 임계점: Sentry와 충돌 확인 필요
# - Sentry는 에러 추적, Langfuse는 비용 추적 (목적 분리)
# - 두 모니터링 도구 병행 가능 (검증 필요)

def get_langfuse_client() -> Langfuse:
    """싱글톤 Langfuse 클라이언트 반환"""
    return langfuse_client
```

### Step 3: Embedding 서비스 통합 (3시간)
**파일**: `apps/api/embedding_service.py:117-145`

```python
from .monitoring.langfuse_client import observe

class EmbeddingService:
    @observe(name="generate_embedding")
    async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Langfuse 자동 추적:
        - 입력 토큰 수 (tiktoken)
        - API 호출 시간
        - 모델명 (text-embedding-3-large)
        - 비용 계산 (자동)
        """
        # 기존 로직 유지
        ...
```

**추적 메트릭**:
- 입력 텍스트 길이 → 토큰 수 변환 (tiktoken)
- OpenAI API 호출 비용 ($0.00013/1k tokens for text-embedding-3-large)
- 캐시 히트율
- 레이턴시

### Step 4: 검색 엔진 통합 (2시간)
**파일**: `apps/search/hybrid_search_engine.py:508-643`

```python
from ..api.monitoring.langfuse_client import observe

class HybridSearchEngine:
    @observe(name="hybrid_search")
    async def search(self, query: str, top_k: int = 5, ...) -> Tuple[...]:
        """
        Langfuse 자동 추적:
        - 검색 쿼리
        - BM25/Vector 후보 수
        - 최종 결과 수
        - 레이턴시
        """
        # 기존 로직 유지
        ...
```

### Step 5: 비용 대시보드 API (4시간)
**파일**: `apps/api/routers/monitoring_router.py` (수정)

```python
@router.get("/api/v1/monitoring/llm-costs")
async def get_llm_costs(
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    """
    Langfuse 비용 대시보드 (Gemini 2.5 Flash + OpenAI Embedding)

    Returns:
        - 일별 비용 (₩)
        - 쿼리당 평균 비용 (₩)
        - 모델별 비용 분포
        - 목표 비용(₩10/쿼리) 준수 여부
    """
    from .monitoring.langfuse_client import get_langfuse_client

    client = get_langfuse_client()

    # Langfuse API로 비용 조회
    traces = client.get_traces(limit=1000)  # 최근 1000개

    # 모델별 비용 분리
    gemini_cost = 0.0
    embedding_cost = 0.0

    for trace in traces:
        if "gemini" in trace.model.lower():
            gemini_cost += trace.calculated_total_cost
        elif "embedding" in trace.model.lower():
            embedding_cost += trace.calculated_total_cost

    total_cost_usd = gemini_cost + embedding_cost

    # 환율: $1 = ₩1,300 (환경변수로 관리)
    exchange_rate = float(os.getenv("USD_TO_KRW", "1300"))

    # Gemini 2.5 Flash 요금
    # - Input: $0.075 / 1M tokens ($0.000075 / 1K tokens)
    # - Output: $0.30 / 1M tokens ($0.0003 / 1K tokens)
    # - 128K context window

    # OpenAI text-embedding-3-large 요금
    # - $0.13 / 1M tokens ($0.00013 / 1K tokens)

    return {
        "total_cost_usd": total_cost_usd,
        "total_cost_krw": total_cost_usd * exchange_rate,
        "cost_breakdown_krw": {
            "gemini_2.5_flash": gemini_cost * exchange_rate,
            "openai_embedding": embedding_cost * exchange_rate
        },
        "avg_cost_per_query_krw": (total_cost_usd / len(traces) * exchange_rate) if traces else 0,
        "target_cost_krw": 10,
        "is_within_budget": (total_cost_usd / len(traces) * exchange_rate) <= 10 if traces else True,
        "pricing_info": {
            "gemini_2.5_flash": {
                "input_per_1k_tokens_usd": 0.000075,
                "output_per_1k_tokens_usd": 0.0003,
                "context_window": "128K"
            },
            "openai_embedding_3_large": {
                "per_1k_tokens_usd": 0.00013,
                "dimensions": 1536
            }
        }
    }
```

---

## 3. 리스크 분석

### ⚠️ 미확인 리스크 (Abstain 사유)

**1. Sentry 충돌 가능성**
- **현상**: 두 모니터링 SDK가 OpenTelemetry 컨텍스트 공유?
- **검증 방법**: 로컬 테스트로 확인
- **완화 전략**: Langfuse 비활성화 플래그 (`LANGFUSE_ENABLED=false`)

**2. 성능 오버헤드**
- **현상**: `@observe()` 데코레이터가 레이턴시 추가?
- **검증 방법**: 벤치마크 (목표: < 10ms)
- **완화 전략**: 샘플링 (전체 요청의 10%만 추적)

**3. 비용 계산 공식 정확성**
- **현상**: Langfuse가 자동 계산하는 비용이 실제 청구서와 일치?
- **검증 대상**:
  - Gemini 2.5 Flash: Google Cloud Console 청구서
  - OpenAI Embedding: OpenAI 사용량 페이지
- **검증 방법**: 1주일 실제 운영 후 비교 (±5% 이내 오차 허용)
- **완화 전략**: 수동 검증 스크립트 작성

**4. Gemini 모델 명시 업데이트 필요**
- **현상**: `ragas_engine.py:51`에서 `gemini-pro` 사용 중
- **권장**: `gemini-2.5-flash-latest` 또는 `gemini-2.0-flash-exp`로 업데이트
- **비용 영향**: Gemini 2.5 Flash가 더 저렴 (Input: $0.075/1M vs Pro: $0.50/1M)

---

## 4. 실행 전 체크리스트

### ✅ IG 임계점 통과 조건
- [x] langfuse 패키지 존재 확인 (v3.6.1)
- [x] 통합 지점 명확화 (embedding_service, hybrid_search_engine)
- [x] 환경변수 관리 방법 정의 (.env.local)
- [ ] Sentry 충돌 여부 로컬 테스트
- [ ] 성능 벤치마크 (목표: < 10ms 오버헤드)
- [ ] 비용 계산 공식 검증

### 🔴 Abstain 해제 조건
1. **로컬 테스트 완료**: Sentry + Langfuse 동시 동작 확인
2. **벤치마크 통과**: `@observe()` 오버헤드 < 10ms
3. **비용 공식 검증**: OpenAI 청구서와 ±5% 이내 오차

---

## 5. 바이브코딩 원칙 적용

### 혼선 제거
```yaml
# ❌ 모호한 목표
목표: "LLM 비용 추적 통합"

# ✅ 수치화된 목표
목표: "비용/쿼리 ≤ ₩10 검증 가능하도록 Langfuse 통합"
측정: "langfuse.get_traces().calculated_total_cost × 1300 (환율)"
임계값: "avg_cost_krw > 10 시 알림"
```

### 작은 커밋 (≤5 파일)
```bash
# Commit 1: Langfuse 클라이언트 초기화
git add apps/api/monitoring/langfuse_client.py requirements.txt
git commit -m "feat: Langfuse 클라이언트 초기화 (v3.6.1)"

# Commit 2: Embedding 서비스 통합
git add apps/api/embedding_service.py
git commit -m "feat: Embedding 서비스 Langfuse 통합 (@observe)"

# Commit 3: 검색 엔진 통합
git add apps/search/hybrid_search_engine.py
git commit -m "feat: 하이브리드 검색 Langfuse 통합"

# Commit 4: 비용 대시보드 API
git add apps/api/routers/monitoring_router.py
git commit -m "feat: LLM 비용 대시보드 API (/monitoring/llm-costs)"
```

---

## 6. 다음 단계 (승인 후 실행)

1. **로컬 테스트** (1일):
   - Sentry + Langfuse 충돌 확인
   - 성능 벤치마크

2. **구현** (2-3일):
   - Step 1-5 순차 실행
   - 단위 테스트 작성

3. **검증** (1주):
   - 실제 운영 데이터로 비용 계산 검증
   - OpenAI 청구서 비교

---

**최종 권장**: 로컬 테스트 완료 후 Phase 2 착수 승인 요청
