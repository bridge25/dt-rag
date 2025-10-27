# @SPEC:OCR-CASCADE-001 구현 계획

## TDD 구현 전략 (RED-GREEN-REFACTOR)

### Phase 0: 테스트 작성 (RED)

#### 0.1 테스트 디렉토리 구조 생성
```
tests/
└── services/
    └── ocr/
        ├── __init__.py
        ├── test_cascade_orchestrator.py
        ├── test_confidence_calculator.py
        └── test_image_preprocessor.py
```

#### 0.2 테스트 픽스처 준비
```python
# tests/services/ocr/conftest.py
import pytest
import cv2
import numpy as np
from pathlib import Path

@pytest.fixture
def clean_order_image():
    """깨끗한 발주서 이미지 (300 DPI)"""
    return cv2.imread("test_data/ocr/cascade/clean_order.jpg")

@pytest.fixture
def complex_order_image():
    """복잡한 발주서 이미지 (손글씨 포함)"""
    return cv2.imread("test_data/ocr/cascade/complex_order.jpg")

@pytest.fixture
def very_complex_order_image():
    """매우 복잡한 발주서 (손글씨+기울어짐+저화질)"""
    return cv2.imread("test_data/ocr/cascade/very_complex_order.jpg")

@pytest.fixture
def noisy_image():
    """노이즈가 많은 저화질 이미지"""
    return cv2.imread("test_data/ocr/cascade/noisy_image.jpg")

@pytest.fixture
def cascade_orchestrator():
    """CascadeOrchestratorService 인스턴스"""
    from backend.src.services.ocr.cascade_orchestrator import CascadeOrchestratorService
    return CascadeOrchestratorService()
```

#### 0.3 핵심 테스트 시나리오

**1. 깨끗한 문서 시나리오** (Tesseract만 사용)
```python
def test_clean_document_uses_tesseract_only(cascade_orchestrator, clean_order_image):
    """깨끗한 문서는 Tesseract만 사용하고 즉시 반환"""
    result = cascade_orchestrator.extract_text("test_data/ocr/cascade/clean_order.jpg")

    assert result.engine == "tesseract"
    assert result.confidence >= 0.95
    assert result.duration <= 2.0
    assert result.engines_tried == ["tesseract"]
    assert result.cascade_used == False
```

**2. 복잡한 문서 시나리오** (EasyOCR까지 사용)
```python
def test_complex_document_cascades_to_easyocr(cascade_orchestrator, complex_order_image):
    """복잡한 문서는 Tesseract 실패 후 EasyOCR로 자동 전환"""
    result = cascade_orchestrator.extract_text("test_data/ocr/cascade/complex_order.jpg")

    assert result.engine == "easyocr"
    assert result.confidence >= 0.90
    assert result.duration <= 4.0
    assert "tesseract" in result.engines_tried
    assert "easyocr" in result.engines_tried
    assert result.cascade_used == True
```

**3. 매우 복잡한 문서 시나리오** (AI까지 사용)
```python
def test_very_complex_document_cascades_to_ai(cascade_orchestrator, very_complex_order_image):
    """매우 복잡한 문서는 AI까지 Cascade"""
    result = cascade_orchestrator.extract_text("test_data/ocr/cascade/very_complex_order.jpg")

    assert result.engine in ["gpt4-vision", "claude"]
    assert result.confidence >= 0.99
    assert result.duration <= 5.0
    assert len(result.engines_tried) == 3
    assert result.cascade_used == True
```

**4. 전처리 효과 검증 시나리오**
```python
def test_preprocessing_improves_confidence(cascade_orchestrator, noisy_image):
    """전처리가 신뢰도를 10% 이상 향상"""
    result_without_preprocess = cascade_orchestrator.extract_text(
        "test_data/ocr/cascade/noisy_image.jpg",
        preprocess=False
    )
    result_with_preprocess = cascade_orchestrator.extract_text(
        "test_data/ocr/cascade/noisy_image.jpg",
        preprocess=True
    )

    assert result_with_preprocess.confidence >= result_without_preprocess.confidence + 0.10
```

#### 0.4 신뢰도 계산 테스트
```python
# tests/services/ocr/test_confidence_calculator.py
def test_tesseract_confidence_calculation():
    """Tesseract 신뢰도 계산 정확성"""
    from backend.src.services.ocr.confidence_calculator import ConfidenceCalculator

    ocr_data = {
        'text': ['Hello', 'World'],
        'conf': ['98', '96', '-1']  # -1은 무시
    }

    calculator = ConfidenceCalculator()
    confidence = calculator.calculate_tesseract_confidence(ocr_data)

    assert confidence == pytest.approx(0.97, rel=0.01)  # (98+96)/2/100

def test_easyocr_confidence_calculation():
    """EasyOCR 신뢰도 계산 정확성"""
    from backend.src.services.ocr.confidence_calculator import ConfidenceCalculator

    ocr_result = [
        ([[0, 0], [100, 0], [100, 50], [0, 50]], 'Hello', 0.98),
        ([[0, 60], [100, 60], [100, 110], [0, 110]], 'World', 0.94)
    ]

    calculator = ConfidenceCalculator()
    confidence = calculator.calculate_easyocr_confidence(ocr_result)

    assert confidence == pytest.approx(0.96, rel=0.01)  # (0.98+0.94)/2

def test_should_cascade_decision():
    """Cascade 전환 결정 로직"""
    from backend.src.services.ocr.confidence_calculator import ConfidenceCalculator

    calculator = ConfidenceCalculator()

    assert calculator.should_cascade(0.94, 0.95) == True  # Cascade 필요
    assert calculator.should_cascade(0.96, 0.95) == False  # Cascade 불필요
```

#### 0.5 이미지 전처리 테스트
```python
# tests/services/ocr/test_image_preprocessor.py
def test_preprocess_pipeline():
    """전체 전처리 파이프라인 실행"""
    from backend.src.services.ocr.image_preprocessor import ImagePreprocessor

    preprocessor = ImagePreprocessor()
    image = cv2.imread("test_data/ocr/cascade/noisy_image.jpg")

    preprocessed = preprocessor.preprocess_pipeline(image)

    assert preprocessed.shape[0] == image.shape[0]  # 크기 유지
    assert preprocessed.shape[1] == image.shape[1]
    assert len(preprocessed.shape) == 2  # 그레이스케일

def test_validate_image_quality():
    """이미지 품질 검증"""
    from backend.src.services.ocr.image_preprocessor import ImagePreprocessor

    preprocessor = ImagePreprocessor()

    # 유효한 이미지
    valid_image = np.ones((1000, 800, 3), dtype=np.uint8)
    assert preprocessor.validate_image_quality(valid_image) == True

    # 너무 작은 이미지
    small_image = np.ones((500, 400, 3), dtype=np.uint8)
    assert preprocessor.validate_image_quality(small_image) == False
```

### Phase 1: 구현 (GREEN)

#### 1차 목표: Tesseract 레이어 구현

**우선순위**: 1 (최고)

**구현 파일**:
- `backend/src/services/ocr/cascade_orchestrator.py` (기본 구조)
- `backend/src/services/ocr/image_preprocessor.py` (OpenCV 전처리)
- `backend/src/services/ocr/confidence_calculator.py` (신뢰도 계산)

**구현 순서**:
1. **ImagePreprocessor 구현** (의존성 없음)
   ```python
   class ImagePreprocessor:
       def preprocess_pipeline(self, image: np.ndarray) -> np.ndarray:
           image = self.convert_to_grayscale(image)
           image = self.denoise(image)
           image = self.binarize(image)
           return image
   ```

2. **ConfidenceCalculator 구현** (의존성 없음)
   ```python
   class ConfidenceCalculator:
       def calculate_tesseract_confidence(self, ocr_data: Dict) -> float:
           confidences = [float(c) for c in ocr_data['conf'] if int(c) != -1]
           return sum(confidences) / len(confidences) / 100.0
   ```

3. **CascadeOrchestratorService - Tesseract 부분** (ImagePreprocessor + ConfidenceCalculator 의존)
   ```python
   class CascadeOrchestratorService:
       def __init__(self):
           self.preprocessor = ImagePreprocessor()
           self.confidence_calculator = ConfidenceCalculator()

       def extract_text(self, image_path: str, preprocess: bool = True) -> OCRResult:
           image = cv2.imread(image_path)
           if preprocess:
               image = self.preprocessor.preprocess_pipeline(image)

           # Tesseract 실행
           text, confidence = self._try_tesseract(image, language)

           if confidence >= 0.95:
               return OCRResult(
                   text=text,
                   confidence=confidence,
                   engine="tesseract",
                   duration=elapsed_time,
                   engines_tried=["tesseract"],
                   cascade_used=False
               )
   ```

**검증**:
- 테스트 시나리오 1 통과
- 신뢰도 계산 테스트 통과
- 전처리 테스트 통과

#### 2차 목표: EasyOCR 레이어 통합

**우선순위**: 2

**구현 내용**:
1. **EasyOCR 초기화** (애플리케이션 시작 시)
   ```python
   import easyocr

   class CascadeOrchestratorService:
       def __init__(self):
           # 모델 미리 로딩 (3-5초 소요)
           self.easyocr_reader = easyocr.Reader(['ko', 'en'], gpu=True)
   ```

2. **_try_easyocr() 메서드 구현**
   ```python
   def _try_easyocr(self, image: np.ndarray, language: str) -> Tuple[str, float]:
       result = self.easyocr_reader.readtext(image)
       text = ' '.join([text for bbox, text, conf in result])
       confidence = self.confidence_calculator.calculate_easyocr_confidence(result)
       return text, confidence
   ```

3. **Cascade 로직 통합**
   ```python
   # Tesseract 실패 시 EasyOCR로 전환
   if confidence < 0.95:
       text, confidence = self._try_easyocr(image, language)
       engines_tried.append("easyocr")
       cascade_used = True
   ```

**검증**:
- 테스트 시나리오 2 통과
- EasyOCR 신뢰도 계산 테스트 통과

#### 3차 목표: AI 레이어 통합

**우선순위**: 3

**구현 내용**:
1. **AI 엔진 추상화**
   ```python
   from abc import ABC, abstractmethod

   class AIEngine(ABC):
       @abstractmethod
       def extract_text(self, image: np.ndarray, language: str) -> str:
           pass

   class GPT4VisionEngine(AIEngine):
       def extract_text(self, image: np.ndarray, language: str) -> str:
           # OpenAI API 호출
           pass

   class ClaudeEngine(AIEngine):
       def extract_text(self, image: np.ndarray, language: str) -> str:
           # Anthropic API 호출
           pass
   ```

2. **_try_ai() 메서드 구현**
   ```python
   def _try_ai(self, image: np.ndarray, language: str) -> Tuple[str, float]:
       # 기본: GPT-4 Vision
       ai_engine = GPT4VisionEngine()
       text = ai_engine.extract_text(image, language)
       return text, 0.99  # AI는 신뢰도 고정
   ```

3. **최종 Cascade 로직**
   ```python
   # EasyOCR 실패 시 AI로 전환
   if confidence < 0.90:
       text, confidence = self._try_ai(image, language)
       engines_tried.append("gpt4-vision")
       cascade_used = True
   ```

**검증**:
- 테스트 시나리오 3 통과
- AI API 모킹 테스트 통과

### Phase 2: 리팩토링 (REFACTOR)

#### 2.1 중복 코드 제거

**문제**: 각 레이어의 시간 측정 코드 중복
```python
# 중복 코드
start = time.time()
result = some_ocr_function()
duration = time.time() - start
```

**해결책**: 데코레이터 패턴
```python
def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        return result, duration
    return wrapper

@measure_time
def _try_tesseract(self, image, language):
    # 실제 OCR 로직만 작성
    pass
```

#### 2.2 성능 최적화

**최적화 1**: EasyOCR 모델 미리 로딩
```python
# 애플리케이션 시작 시 (app.py)
from backend.src.services.ocr.cascade_orchestrator import CascadeOrchestratorService

@app.on_event("startup")
async def startup_event():
    app.state.cascade_orchestrator = CascadeOrchestratorService()
    # EasyOCR 모델 미리 로딩됨
```

**최적화 2**: 이미지 전처리 결과 캐싱
```python
from functools import lru_cache

class ImagePreprocessor:
    @lru_cache(maxsize=100)
    def preprocess_pipeline(self, image_hash: str, image: np.ndarray) -> np.ndarray:
        # 동일 이미지 재처리 방지
        pass
```

**최적화 3**: 병렬 처리 (force_cascade=True 시)
```python
import asyncio

async def extract_text_parallel(self, image_path: str):
    """모든 레이어를 병렬로 실행하고 가장 좋은 결과 선택"""
    results = await asyncio.gather(
        self._try_tesseract_async(image),
        self._try_easyocr_async(image),
        self._try_ai_async(image)
    )
    return max(results, key=lambda r: r.confidence)
```

#### 2.3 에러 핸들링 강화

**에러 처리 전략**:
```python
class OCRError(Exception):
    """OCR 관련 에러 베이스 클래스"""
    pass

class ImageQualityError(OCRError):
    """이미지 품질 문제"""
    pass

class OCREngineError(OCRError):
    """OCR 엔진 실행 오류"""
    pass

def extract_text(self, image_path: str) -> OCRResult:
    try:
        # 이미지 품질 검증
        if not self.preprocessor.validate_image_quality(image):
            raise ImageQualityError("이미지가 너무 작거나 손상됨")

        # OCR 실행
        # ...

    except ImageQualityError as e:
        logger.error(f"이미지 품질 문제: {e}")
        return OCRResult.error_result("image_quality_error")

    except OCREngineError as e:
        logger.error(f"OCR 엔진 오류: {e}")
        return OCRResult.error_result("ocr_engine_error")
```

#### 2.4 로깅 개선

**구조화된 로깅**:
```python
import logging
import structlog

logger = structlog.get_logger()

def extract_text(self, image_path: str) -> OCRResult:
    logger.info(
        "ocr_request_started",
        image_path=image_path,
        preprocess=preprocess,
        language=language
    )

    # ...

    logger.info(
        "ocr_request_completed",
        engine=result.engine,
        confidence=result.confidence,
        duration=result.duration,
        cascade_used=result.cascade_used
    )
```

### 기술적 접근 방법

#### 디자인 패턴

**1. Strategy 패턴**: 레이어별 OCR 전략 분리
```python
class OCRStrategy(ABC):
    @abstractmethod
    def extract_text(self, image: np.ndarray, language: str) -> Tuple[str, float]:
        pass

class TesseractStrategy(OCRStrategy):
    def extract_text(self, image, language):
        # Tesseract 실행
        pass

class EasyOCRStrategy(OCRStrategy):
    def extract_text(self, image, language):
        # EasyOCR 실행
        pass

class CascadeOrchestratorService:
    def __init__(self):
        self.strategies = [
            TesseractStrategy(),
            EasyOCRStrategy(),
            AIStrategy()
        ]
```

**2. Dependency Injection**: 엔진 교체 가능성
```python
class CascadeOrchestratorService:
    def __init__(
        self,
        preprocessor: ImagePreprocessor = None,
        confidence_calculator: ConfidenceCalculator = None,
        ai_engine: AIEngine = None
    ):
        self.preprocessor = preprocessor or ImagePreprocessor()
        self.confidence_calculator = confidence_calculator or ConfidenceCalculator()
        self.ai_engine = ai_engine or GPT4VisionEngine()
```

### 리스크 및 대응 방안

#### 리스크 1: EasyOCR 초기 모델 로딩 시간 (3-5초)
**영향도**: High
**대응**: 애플리케이션 시작 시 미리 로딩
```python
@app.on_event("startup")
async def startup_event():
    app.state.cascade_orchestrator = CascadeOrchestratorService()
    logger.info("EasyOCR 모델 로딩 완료")
```

#### 리스크 2: AI API Rate Limit
**영향도**: Medium
**대응**: Exponential Backoff + 대기열
```python
import tenacity

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(3)
)
def _try_ai(self, image, language):
    # AI API 호출
    pass
```

#### 리스크 3: 메모리 사용량 증가 (EasyOCR 딥러닝 모델)
**영향도**: Medium
**대응**: 모델 언로드 옵션 제공
```python
class CascadeOrchestratorService:
    def unload_easyocr_model(self):
        """메모리 부족 시 모델 언로드"""
        del self.easyocr_reader
        import gc
        gc.collect()
```

#### 리스크 4: 처리 시간 초과 (>5초)
**영향도**: Low
**대응**: 타임아웃 설정
```python
import asyncio

async def extract_text_with_timeout(self, image_path: str, timeout: float = 5.0):
    try:
        return await asyncio.wait_for(
            self.extract_text(image_path),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"OCR 처리 시간 초과: {timeout}초")
        return OCRResult.timeout_result()
```

### 마일스톤

**1차 마일스톤: Tesseract 레이어 완성**
- ImagePreprocessor 구현 완료
- ConfidenceCalculator 구현 완료
- CascadeOrchestratorService - Tesseract 통합 완료
- 테스트 시나리오 1 통과

**2차 마일스톤: EasyOCR 레이어 완성**
- EasyOCR 초기화 및 통합 완료
- Cascade 로직 구현 완료
- 테스트 시나리오 2 통과

**3차 마일스톤: AI 레이어 완성**
- AI 엔진 추상화 및 통합 완료
- 최종 Cascade 로직 완성
- 테스트 시나리오 3 통과

**최종 마일스톤: 리팩토링 및 최적화**
- 중복 코드 제거
- 성능 최적화 적용
- 에러 핸들링 및 로깅 개선
- 모든 테스트 통과 (커버리지 85%+)
