# SPEC-OCR-001 구현 계획

> **OCR 기반 발주서 데이터 추출 시스템**
>
> Phase 1 MVP 핵심 기능 구현 계획

---

## TDD 구현 전략

### Red (테스트 작성)

#### Phase 1: 기본 테스트 작성

```python
# tests/services/ocr/test_ocr_service.py

def test_upload_image_returns_job_id():
    """이미지 업로드 시 job_id 반환 확인"""
    pass

def test_extract_korean_order_data():
    """한국어 발주서 데이터 추출 테스트"""
    pass

def test_extract_vietnamese_order_data():
    """베트남어 발주서 데이터 추출 테스트"""
    pass

def test_mixed_language_order():
    """한국어+베트남어 혼용 발주서 테스트"""
    pass

def test_low_quality_image_warning():
    """저화질 이미지 경고 테스트"""
    pass

def test_excel_direct_parsing():
    """엑셀 파일 직접 파싱 테스트"""
    pass

def test_ocr_cascade_on_low_confidence():
    """낮은 신뢰도 시 OCR 엔진 캐스케이드 테스트"""
    pass

def test_json_output_schema():
    """JSON 출력 스키마 검증 테스트"""
    pass
```

#### Phase 2: 통합 테스트 작성

```python
# tests/integration/test_ocr_pipeline.py

def test_end_to_end_korean_order():
    """한국어 발주서 전체 파이프라인 테스트"""
    pass

def test_cache_hit_returns_cached_result():
    """캐시 히트 시 캐시 결과 반환 테스트"""
    pass

def test_batch_processing_10_files():
    """10개 파일 배치 처리 테스트"""
    pass

def test_rate_limit_exponential_backoff():
    """API Rate Limit 시 재시도 테스트"""
    pass
```

---

### Green (최소 구현)

#### 1. FastAPI 엔드포인트 생성

```python
# services/ocr/ocr_service.py

from fastapi import FastAPI, UploadFile, File
from typing import Dict, Any

app = FastAPI()

@app.post("/api/v1/ocr/upload")
async def upload_order(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    발주서 파일 업로드 및 OCR 처리

    Returns:
        {
            "job_id": "uuid-v4",
            "status": "processing",
            "estimated_time": 3
        }
    """
    job_id = generate_job_id()
    file_path = await save_to_s3(file)

    # 비동기 OCR 처리 큐에 추가
    await enqueue_ocr_task(job_id, file_path)

    return {
        "job_id": job_id,
        "status": "processing",
        "estimated_time": 3
    }

@app.get("/api/v1/ocr/result/{job_id}")
async def get_ocr_result(job_id: str) -> Dict[str, Any]:
    """
    OCR 처리 결과 조회

    Returns:
        {
            "status": "completed",
            "data": {...},
            "confidence_score": 0.95
        }
    """
    result = await get_result_from_cache(job_id)
    return result
```

#### 2. Tesseract OCR 통합

```python
# services/ocr/engines/tesseract_engine.py

import pytesseract
from PIL import Image

class TesseractEngine:
    def extract(self, image_path: str) -> Dict[str, Any]:
        """Tesseract OCR로 텍스트 추출"""
        image = Image.open(image_path)

        # 한국어+베트남어+영어 동시 인식
        text = pytesseract.image_to_string(
            image,
            lang='kor+vie+eng',
            config='--psm 6'  # Assume uniform block of text
        )

        confidence = self._calculate_confidence(text)

        return {
            "text": text,
            "confidence": confidence
        }
```

#### 3. JSON 스키마 정의

```python
# services/ocr/schemas/order_schema.py

from pydantic import BaseModel, Field
from typing import List
from datetime import date

class OrderItem(BaseModel):
    product_name: str = Field(..., description="품목명")
    quantity: int = Field(..., gt=0, description="수량")
    unit: str = Field(..., description="단위 (kg, box 등)")
    unit_price: int = Field(..., gt=0, description="단가")
    total_price: int = Field(..., description="합계금액")

class OrderData(BaseModel):
    order_date: date = Field(..., description="발주일자")
    customer_name: str = Field(..., description="고객사명")
    contact_name: str = Field(..., description="담당자명")
    contact_phone: str = Field(..., description="연락처")
    items: List[OrderItem] = Field(..., description="품목 목록")
    total_amount: int = Field(..., description="총 금액")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
```

#### 4. 기본 에러 처리

```python
# services/ocr/error_handler.py

class OCRError(Exception):
    """OCR 관련 기본 에러"""
    pass

class LowConfidenceError(OCRError):
    """낮은 신뢰도 에러"""
    pass

class TimeoutError(OCRError):
    """타임아웃 에러"""
    pass

class RateLimitError(OCRError):
    """API Rate Limit 에러"""
    pass
```

---

### Refactor (최적화)

#### 1. OCR 엔진 캐스케이드 전략

```python
# services/ocr/cascade_strategy.py

class OCRCascadeStrategy:
    """OCR 엔진 캐스케이드 전략"""

    def __init__(self):
        self.engines = [
            TesseractEngine(),
            GPT4VisionEngine(),
            Claude35Engine()
        ]
        self.confidence_threshold = 0.9

    async def extract(self, image_path: str) -> Dict[str, Any]:
        """
        1차: Tesseract (빠르지만 정확도 낮음)
        2차: GPT-4 Vision (정확도 높지만 비용)
        3차: Claude 3.5 Sonnet (최종 검증)
        """
        result = None

        for engine in self.engines:
            result = await engine.extract(image_path)

            if result["confidence"] >= self.confidence_threshold:
                return result

            logger.warning(
                f"{engine.__class__.__name__} 신뢰도 부족: "
                f"{result['confidence']:.2f}, 다음 엔진으로 전환"
            )

        # 모든 엔진 시도 후에도 신뢰도 낮으면 최종 결과 반환
        return result
```

#### 2. 성능 최적화

**Redis 캐싱**:
```python
# services/ocr/cache_manager.py

import hashlib
import redis

class CacheManager:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379)
        self.ttl = 86400  # 24시간

    def get_cache_key(self, file_path: str) -> str:
        """파일 SHA-256 해시로 캐시 키 생성"""
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return f"ocr:{file_hash}"

    async def get(self, file_path: str) -> Optional[Dict]:
        """캐시에서 결과 조회"""
        key = self.get_cache_key(file_path)
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set(self, file_path: str, result: Dict):
        """결과를 캐시에 저장"""
        key = self.get_cache_key(file_path)
        self.redis.setex(key, self.ttl, json.dumps(result))
```

**배치 처리**:
```python
# services/ocr/batch_processor.py

import asyncio

class BatchProcessor:
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size

    async def process_batch(self, file_paths: List[str]) -> List[Dict]:
        """10개 단위 배치 처리"""
        tasks = [
            self._process_single(file_path)
            for file_path in file_paths
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

**비동기 처리 (Celery)**:
```python
# services/ocr/tasks.py

from celery import Celery

celery_app = Celery('ocr_tasks', broker='redis://localhost:6379/0')

@celery_app.task(bind=True, max_retries=3)
def process_ocr_task(self, job_id: str, file_path: str):
    """비동기 OCR 처리 태스크"""
    try:
        strategy = OCRCascadeStrategy()
        result = asyncio.run(strategy.extract(file_path))

        # 결과를 Redis에 저장
        cache_manager.set(job_id, result)

        return result
    except Exception as exc:
        # Exponential backoff 재시도
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### 3. 에러 처리 강화

```python
# services/ocr/error_handler.py (개선)

class ErrorHandler:
    @staticmethod
    def handle_low_quality_image(image_path: str):
        """저화질 이미지 처리"""
        logger.warning(f"저화질 이미지 감지: {image_path}")
        return {
            "warning": "이미지 품질이 낮습니다. 정확도가 떨어질 수 있습니다.",
            "recommendation": "300 DPI 이상 이미지를 다시 업로드해주세요."
        }

    @staticmethod
    async def handle_rate_limit(exc: RateLimitError, retry_count: int):
        """API Rate Limit 처리 (Exponential Backoff)"""
        wait_time = 2 ** retry_count
        logger.warning(f"Rate Limit 도달, {wait_time}초 대기")
        await asyncio.sleep(wait_time)
```

#### 4. 로깅 및 모니터링

```python
# services/ocr/monitoring.py

import structlog
from prometheus_client import Counter, Histogram

logger = structlog.get_logger()

# Prometheus 메트릭
ocr_requests_total = Counter(
    'ocr_requests_total',
    'Total OCR requests',
    ['status', 'engine']
)

ocr_latency_seconds = Histogram(
    'ocr_latency_seconds',
    'OCR processing latency',
    ['engine']
)

def log_ocr_request(job_id: str, status: str, latency: float):
    """OCR 요청 로그 및 메트릭 기록"""
    logger.info(
        "ocr_request_completed",
        job_id=job_id,
        status=status,
        latency_ms=latency * 1000
    )

    ocr_requests_total.labels(status=status, engine='tesseract').inc()
    ocr_latency_seconds.labels(engine='tesseract').observe(latency)
```

---

## 기술 구현 세부사항

### OCR 엔진 선택 로직

```python
# services/ocr/engine_selector.py

class EngineSelector:
    """언어별 최적 OCR 엔진 선택"""

    @staticmethod
    def select_engine(detected_language: str) -> OCREngine:
        """언어에 따라 최적 엔진 선택"""
        engine_map = {
            'korean': TesseractEngine(),
            'vietnamese': GPT4VisionEngine(),  # 베트남어 특수문자
            'english': TesseractEngine(),
            'mixed': Claude35Engine()  # 다국어 혼용
        }

        return engine_map.get(detected_language, TesseractEngine())
```

### JSON 변환 로직

```python
# services/ocr/json_converter.py

import re
from typing import Dict, Any

class JSONConverter:
    """OCR 텍스트 → JSON 변환"""

    def convert(self, text: str) -> Dict[str, Any]:
        """
        OCR 텍스트에서 구조화된 JSON 추출

        패턴 매칭:
        - 발주일자: YYYY-MM-DD, YYYY.MM.DD
        - 고객사명: '주식회사', '(주)', 'Co., Ltd.' 등
        - 연락처: 010-XXXX-XXXX, 02-XXX-XXXX
        - 품목: 표 형식 파싱
        """
        data = {}

        # 발주일자 추출
        date_pattern = r'\d{4}[-./]\d{2}[-./]\d{2}'
        match = re.search(date_pattern, text)
        if match:
            data['order_date'] = match.group(0).replace('.', '-')

        # 고객사명 추출
        company_pattern = r'(주식회사|㈜|\(주\))\s*([가-힣A-Za-z]+)'
        match = re.search(company_pattern, text)
        if match:
            data['customer_name'] = match.group(0)

        # 연락처 추출
        phone_pattern = r'(\d{2,3})-(\d{3,4})-(\d{4})'
        match = re.search(phone_pattern, text)
        if match:
            data['contact_phone'] = match.group(0)

        # 품목 파싱 (표 형식)
        data['items'] = self._parse_items_table(text)

        return data
```

---

## 성능 최적화 전략

### 1. Redis 캐싱
- **대상**: 동일 파일 재업로드 시 OCR 결과 재사용
- **TTL**: 24시간
- **예상 효과**: 중복 요청 80% 감소, API 비용 절감

### 2. 배치 처리
- **대상**: 10개 이상 파일 동시 업로드
- **방법**: `asyncio.gather()` 병렬 처리
- **예상 효과**: 처리 시간 70% 단축

### 3. 비동기 처리
- **대상**: 3초 이상 소요 예상 작업
- **방법**: Celery + Redis Queue
- **예상 효과**: API 응답 시간 0.1초 미만 유지

### 4. 이미지 최적화
- **대상**: 10MB 초과 파일
- **방법**: PIL 리사이징 (최대 4096x4096)
- **예상 효과**: S3 저장 비용 절감, 전송 속도 향상

---

## 리스크 및 대응 방안

### 리스크 1: API Rate Limit
- **확률**: 높음
- **영향**: OCR 처리 중단
- **대응**:
  - Exponential Backoff 재시도 (1초, 2초, 4초)
  - API 키 로테이션 (OpenAI 3개, Anthropic 2개)
  - Fallback to Tesseract

### 리스크 2: 저화질 이미지
- **확률**: 중간
- **영향**: 정확도 90% 미만
- **대응**:
  - 경고 후 처리 시도
  - 재업로드 권장 UI 표시
  - GPT-4 Vision으로 재처리

### 리스크 3: 다국어 혼용 실패
- **확률**: 낮음
- **영향**: 베트남어 특수문자 인식 실패
- **대응**:
  - Claude 3.5 Sonnet으로 최종 검증
  - 수작업 보정 UI 제공

---

## 다음 단계

### Phase 1 완료 후 (v0.2.0)
1. **SPEC-ORDER-VALIDATION-001**: 추출된 발주서 데이터 검증 시스템
2. **SPEC-INVENTORY-SYNC-001**: 재고 시스템과 동기화

### Phase 2 고도화 (v1.0.0)
1. 학습 데이터 수집 및 Custom OCR 모델 훈련
2. 발주서 템플릿 자동 학습 (Template Matching)
3. 실시간 스트리밍 OCR (SSE)

---

**문서 버전**: v0.1.0
**최종 수정**: 2025-01-14
**예상 구현 기간**: 우선순위 High - Phase 1 MVP
