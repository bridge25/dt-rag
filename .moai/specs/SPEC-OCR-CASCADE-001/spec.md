---
id: OCR-CASCADE-001
version: 0.1.0
status: draft
created: 2025-10-14
updated: 2025-10-14
author: @sonheungmin
priority: critical
category: feature
labels:
  - ocr
  - cascade
  - tesseract
  - easyocr
  - opencv
scope:
  packages:
    - backend/src/services/ocr
  files:
    - cascade_orchestrator.py
    - confidence_calculator.py
    - image_preprocessor.py
---

# @SPEC:OCR-CASCADE-001: OCR Cascade 전략 오케스트레이터

## HISTORY

### v0.1.0 (2025-10-14)
- **INITIAL**: OCR Cascade 전략 오케스트레이터 명세 최초 작성
- **AUTHOR**: @sonheungmin
- **SCOPE**: Tesseract → EasyOCR → AI 순차 실행, 신뢰도 기반 자동 전환
- **CONTEXT**: 오픈소스 활용 전략(OCR_OPENSOURCE_STRATEGY.md) 기반으로 작성

## Environment (환경)

### 런타임 환경
- **Python**: 3.11+
- **OS**: Ubuntu 20.04+ / Windows 10+ (WSL2 지원)
- **메모리**: 최소 4GB (EasyOCR 딥러닝 모델 로딩 시)

### OCR 엔진
- **Tesseract**: 5.0+ (레이어 1)
- **EasyOCR**: 1.7+ (레이어 2)
- **AI 엔진**: OpenAI GPT-4 Vision, Anthropic Claude 3.5 Sonnet (레이어 3, 선택적)

### 이미지 처리
- **OpenCV**: 4.10+ (전처리 파이프라인)
- **PIL/Pillow**: 10.0+ (이미지 로딩)

### 언어 지원
- **한국어**: ko, kor, Korean
- **베트남어**: vi, vie, Vietnamese
- **영어**: en, eng, English

## Assumptions (가정)

### 라이브러리 사용 방식
1. 오픈소스 라이브러리(pytesseract, easyocr, opencv-python)는 **직접 호출**하여 사용
2. 상용 AI API(OpenAI, Anthropic)는 **선택적**으로 사용 (비용 최적화)

### 이미지 품질
1. **권장 해상도**: 최소 300 DPI
2. **최소 이미지 크기**: 800x600 픽셀
3. **지원 포맷**: PNG, JPEG, TIFF, BMP

### 신뢰도 임계값
1. **Tesseract**: 95% 이상 → 즉시 반환
2. **EasyOCR**: 90% 이상 → 즉시 반환
3. **AI 엔진**: 신뢰도 계산 없음 (최종 레이어)

### 성능 목표
1. **전체 처리 시간**: p95 ≤ 5초
2. **Tesseract 처리 시간**: ≤ 2초
3. **EasyOCR 처리 시간**: ≤ 4초
4. **AI 처리 시간**: ≤ 5초

## Requirements (요구사항)

### Ubiquitous (필수 기능)
- 시스템은 Tesseract → EasyOCR → AI 순서로 **3단계 Cascade**를 제공해야 한다
- 시스템은 각 레이어의 **신뢰도 점수**를 계산하고 자동 전환 결정을 해야 한다
- 시스템은 사용된 **엔진명**, **처리 시간**, **시도한 엔진 목록**을 로깅해야 한다
- 시스템은 OpenCV 기반 **이미지 전처리**를 제공해야 한다
- 시스템은 전처리 적용 여부를 **선택 가능**하게 해야 한다

### Event-driven (이벤트 기반)
- **WHEN** OCR 요청이 들어오면, **THEN** OpenCV로 이미지를 전처리해야 한다 (preprocess=True 시)
- **WHEN** Tesseract 신뢰도가 95% 미만이면, **THEN** 자동으로 EasyOCR로 전환해야 한다
- **WHEN** EasyOCR 신뢰도가 90% 미만이면, **THEN** 자동으로 AI 엔진으로 전환해야 한다
- **WHEN** 모든 레이어가 실패하면, **THEN** 사용자에게 "처리 불가" 알림을 전송해야 한다
- **WHEN** force_cascade=True이면, **THEN** 신뢰도와 관계없이 모든 레이어를 실행해야 한다

### State-driven (상태 기반)
- **WHILE** 레이어 1 (Tesseract) 실행 중일 때, **THEN** 1-2초 이내에 완료되어야 한다
- **WHILE** 레이어 2 (EasyOCR) 실행 중일 때, **THEN** 2-4초 이내에 완료되어야 한다
- **WHILE** 레이어 3 (AI) 실행 중일 때, **THEN** 3-5초 이내에 완료되어야 한다
- **WHILE** EasyOCR 모델이 로딩 중일 때, **THEN** 애플리케이션 시작 시 미리 로딩되어야 한다

### Constraints (제약사항)
1. **성능 제약**: 전체 처리 시간은 5초를 초과하지 않아야 한다 (p95 기준)
2. **신뢰도 범위**: 신뢰도 점수는 0.0~1.0 범위여야 한다
3. **테스트 가능성**: 각 레이어는 독립적으로 테스트 가능해야 한다
4. **메모리 제약**: EasyOCR 모델 메모리 사용량은 2GB를 초과하지 않아야 한다
5. **비용 제약**: AI 엔진은 마지막 수단으로만 사용해야 한다

## Specifications (상세 명세)

### 1. CascadeOrchestratorService

**역할**: 3단계 Cascade 전략을 관리하는 메인 서비스

#### 1.1 주요 메서드

##### extract_text()
```python
def extract_text(
    image_path: str,
    language: str = "kor",
    preprocess: bool = True,
    force_cascade: bool = False
) -> OCRResult
```

**파라미터**:
- `image_path`: 입력 이미지 경로
- `language`: OCR 언어 (기본값: "kor")
- `preprocess`: 전처리 적용 여부 (기본값: True)
- `force_cascade`: 강제로 모든 레이어 실행 (기본값: False)

**반환값**: `OCRResult`
```python
@dataclass
class OCRResult:
    text: str  # 추출된 텍스트
    confidence: float  # 신뢰도 (0.0~1.0)
    engine: str  # "tesseract" | "easyocr" | "gpt4-vision" | "claude"
    duration: float  # 처리 시간 (초)
    engines_tried: List[str]  # 시도한 엔진 목록
    cascade_used: bool  # Cascade 전환 여부
    metadata: Dict[str, Any]  # 추가 메타데이터
```

##### _try_tesseract()
```python
def _try_tesseract(image: np.ndarray, language: str) -> Tuple[str, float]
```

**기능**: Tesseract OCR 실행 및 신뢰도 계산

**반환값**: (추출된 텍스트, 신뢰도)

##### _try_easyocr()
```python
def _try_easyocr(image: np.ndarray, language: str) -> Tuple[str, float]
```

**기능**: EasyOCR 실행 및 신뢰도 계산

**반환값**: (추출된 텍스트, 신뢰도)

##### _try_ai()
```python
def _try_ai(image: np.ndarray, language: str) -> Tuple[str, float]
```

**기능**: AI 엔진 (GPT-4 Vision 또는 Claude) 실행

**반환값**: (추출된 텍스트, 신뢰도 0.99 고정)

#### 1.2 Cascade 전환 로직

```
┌─────────────────┐
│ 이미지 입력     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ OpenCV 전처리   │ (optional)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Layer 1:        │
│ Tesseract OCR   │
└────────┬────────┘
         │
    신뢰도 ≥ 95%? ──Yes──► 반환
         │
        No
         │
         ▼
┌─────────────────┐
│ Layer 2:        │
│ EasyOCR         │
└────────┬────────┘
         │
    신뢰도 ≥ 90%? ──Yes──► 반환
         │
        No
         │
         ▼
┌─────────────────┐
│ Layer 3:        │
│ AI Engine       │
└────────┬────────┘
         │
         ▼
       반환
```

### 2. ImagePreprocessor

**역할**: OpenCV 기반 이미지 전처리

#### 2.1 주요 메서드

##### preprocess_pipeline()
```python
def preprocess_pipeline(image: np.ndarray) -> np.ndarray
```

**기능**: 전체 전처리 파이프라인 실행

**처리 순서**:
1. 그레이스케일 변환
2. 노이즈 제거 (Gaussian Blur)
3. 이진화 (Adaptive Threshold)
4. 모폴로지 연산 (선택적)

##### convert_to_grayscale()
```python
def convert_to_grayscale(image: np.ndarray) -> np.ndarray
```

**기능**: BGR/RGB → 그레이스케일 변환

**OpenCV 함수**: `cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)`

##### denoise()
```python
def denoise(image: np.ndarray, kernel_size: int = 5) -> np.ndarray
```

**기능**: 가우시안 블러로 노이즈 제거

**OpenCV 함수**: `cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)`

##### binarize()
```python
def binarize(
    image: np.ndarray,
    block_size: int = 11,
    c: int = 2
) -> np.ndarray
```

**기능**: 적응형 이진화

**OpenCV 함수**: `cv2.adaptiveThreshold()`

**파라미터**:
- `block_size`: 이웃 픽셀 영역 크기
- `c`: 임계값 보정 상수

##### validate_image_quality()
```python
def validate_image_quality(image: np.ndarray) -> bool
```

**기능**: 이미지 품질 검증

**검증 항목**:
- 최소 크기: 800x600 픽셀
- 이미지 읽기 성공 여부
- 채널 수: 1 (grayscale) 또는 3 (color)

### 3. ConfidenceCalculator

**역할**: 신뢰도 계산 유틸리티

#### 3.1 주요 메서드

##### calculate_tesseract_confidence()
```python
def calculate_tesseract_confidence(ocr_data: Dict[str, Any]) -> float
```

**기능**: Tesseract의 `image_to_data()` 결과에서 신뢰도 계산

**계산 방식**:
```python
# 단어별 신뢰도 평균
confidences = [float(conf) for conf in ocr_data['conf'] if int(conf) != -1]
average_confidence = sum(confidences) / len(confidences) / 100.0
```

##### calculate_easyocr_confidence()
```python
def calculate_easyocr_confidence(ocr_result: List[Tuple]) -> float
```

**기능**: EasyOCR의 `readtext()` 결과에서 신뢰도 계산

**계산 방식**:
```python
# bounding_box, text, confidence 형식
confidences = [conf for bbox, text, conf in ocr_result]
average_confidence = sum(confidences) / len(confidences)
```

##### should_cascade()
```python
def should_cascade(confidence: float, threshold: float) -> bool
```

**기능**: Cascade 전환 결정

**반환값**: `confidence < threshold`

## Traceability (@TAG)

### SPEC 관계
- **현재 SPEC**: @SPEC:OCR-CASCADE-001
- **관련 SPEC**: @SPEC:OCR-001 (OCR 통합 전략)

### 구현 파일
- **메인 서비스**: `backend/src/services/ocr/cascade_orchestrator.py`
- **전처리**: `backend/src/services/ocr/image_preprocessor.py`
- **신뢰도**: `backend/src/services/ocr/confidence_calculator.py`

### 테스트 파일
- **오케스트레이터 테스트**: `tests/services/ocr/test_cascade_orchestrator.py`
- **전처리 테스트**: `tests/services/ocr/test_image_preprocessor.py`
- **신뢰도 테스트**: `tests/services/ocr/test_confidence_calculator.py`

### 문서
- **전략 문서**: `.moai/project/OCR_OPENSOURCE_STRATEGY.md`
- **가이드**: `docs/guides/ocr_cascade_guide.md`

### 데이터
- **테스트 이미지**: `test_data/ocr/cascade/`
  - `clean_order.jpg`: 깨끗한 문서 (Tesseract 전용)
  - `complex_order.jpg`: 복잡한 문서 (EasyOCR 필요)
  - `very_complex_order.jpg`: 매우 복잡한 문서 (AI 필요)
  - `noisy_image.jpg`: 노이즈가 많은 이미지 (전처리 효과 검증)
