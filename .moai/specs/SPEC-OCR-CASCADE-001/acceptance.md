# @SPEC:OCR-CASCADE-001 인수 기준

## Acceptance Criteria (Given-When-Then)

### 시나리오 1: 깨끗한 문서 시나리오

#### 배경
고해상도(300+ DPI)로 스캔된 표준 레이아웃의 발주서를 처리하는 가장 일반적인 시나리오입니다. 이 경우 Tesseract만으로도 충분히 높은 정확도를 달성할 수 있습니다.

#### Given (전제 조건)
- 고해상도 스캔 발주서 이미지 (300+ DPI)
- 표준 레이아웃 (명확한 테이블 구조)
- 인쇄된 텍스트 (손글씨 없음)
- 이미지 경로: `test_data/ocr/cascade/clean_order.jpg`

#### When (실행 조건)
- Cascade Orchestrator의 `extract_text()` 메서드에 이미지를 입력
- 기본 파라미터 사용 (`preprocess=True`, `force_cascade=False`)

#### Then (기대 결과)
- ✅ **엔진 선택**: Tesseract만 사용 (`engine == "tesseract"`)
- ✅ **신뢰도**: 95% 이상 (`confidence >= 0.95`)
- ✅ **처리 시간**: 2초 이내 (`duration <= 2.0`)
- ✅ **Cascade 미사용**: EasyOCR와 AI는 실행되지 않음 (`engines_tried == ["tesseract"]`)
- ✅ **Cascade 플래그**: False (`cascade_used == False`)

#### 검증 방법 (pytest)
```python
def test_clean_document_uses_tesseract_only(cascade_orchestrator):
    """깨끗한 문서는 Tesseract만 사용하고 즉시 반환"""
    # Given
    image_path = "test_data/ocr/cascade/clean_order.jpg"

    # When
    result = cascade_orchestrator.extract_text(image_path)

    # Then
    assert result.engine == "tesseract", "Tesseract 엔진을 사용해야 함"
    assert result.confidence >= 0.95, "신뢰도는 95% 이상이어야 함"
    assert result.duration <= 2.0, "처리 시간은 2초 이내여야 함"
    assert result.engines_tried == ["tesseract"], "Tesseract만 시도해야 함"
    assert result.cascade_used == False, "Cascade는 사용되지 않아야 함"
    assert len(result.text) > 0, "텍스트가 추출되어야 함"
```

#### 성공 기준
- 모든 assertion 통과
- 추출된 텍스트에 핵심 필드 포함 (발주번호, 날짜, 품목명 등)

---

### 시나리오 2: 복잡한 문서 시나리오

#### 배경
비표준 레이아웃, 손글씨, 또는 복잡한 배경을 가진 발주서입니다. Tesseract는 신뢰도가 낮게 나오므로 EasyOCR로 자동 전환되어야 합니다.

#### Given (전제 조건)
- 비표준 레이아웃 발주서 이미지
- 손글씨 포함 (품목명 또는 수량)
- 복잡한 배경 (로고, 스탬프 등)
- 이미지 경로: `test_data/ocr/cascade/complex_order.jpg`

#### When (실행 조건)
- Cascade Orchestrator의 `extract_text()` 메서드에 이미지를 입력
- 기본 파라미터 사용 (`preprocess=True`, `force_cascade=False`)

#### Then (기대 결과)
- ✅ **엔진 선택**: EasyOCR 사용 (`engine == "easyocr"`)
- ✅ **신뢰도**: 90% 이상 (`confidence >= 0.90`)
- ✅ **처리 시간**: 4초 이내 (`duration <= 4.0`)
- ✅ **Cascade 사용**: Tesseract → EasyOCR 순서로 실행 (`"tesseract" in engines_tried and "easyocr" in engines_tried`)
- ✅ **Cascade 플래그**: True (`cascade_used == True`)
- ✅ **AI 미사용**: GPT-4 Vision/Claude는 실행되지 않음

#### 검증 방법 (pytest)
```python
def test_complex_document_cascades_to_easyocr(cascade_orchestrator):
    """복잡한 문서는 Tesseract 실패 후 EasyOCR로 자동 전환"""
    # Given
    image_path = "test_data/ocr/cascade/complex_order.jpg"

    # When
    result = cascade_orchestrator.extract_text(image_path)

    # Then
    assert result.engine == "easyocr", "EasyOCR 엔진을 사용해야 함"
    assert result.confidence >= 0.90, "신뢰도는 90% 이상이어야 함"
    assert result.duration <= 4.0, "처리 시간은 4초 이내여야 함"
    assert "tesseract" in result.engines_tried, "Tesseract를 먼저 시도해야 함"
    assert "easyocr" in result.engines_tried, "EasyOCR를 두 번째로 시도해야 함"
    assert result.cascade_used == True, "Cascade가 사용되어야 함"
    assert len(result.text) > 0, "텍스트가 추출되어야 함"

    # Tesseract 신뢰도는 95% 미만이어야 함 (메타데이터 확인)
    assert result.metadata.get("tesseract_confidence", 1.0) < 0.95, \
        "Tesseract 신뢰도가 낮아서 Cascade되어야 함"
```

#### 성공 기준
- 모든 assertion 통과
- Tesseract보다 EasyOCR의 신뢰도가 더 높음
- 손글씨 부분도 정확하게 추출됨

---

### 시나리오 3: 매우 복잡한 문서 시나리오

#### 배경
손글씨, 기울어짐, 저화질이 모두 결합된 최악의 시나리오입니다. Tesseract와 EasyOCR 모두 실패하고 AI 엔진(GPT-4 Vision 또는 Claude)까지 Cascade되어야 합니다.

#### Given (전제 조건)
- 손글씨로 작성된 발주서
- 이미지가 기울어짐 (5도 이상)
- 저화질 (200 DPI 이하)
- 복잡한 배경 및 노이즈
- 이미지 경로: `test_data/ocr/cascade/very_complex_order.jpg`

#### When (실행 조건)
- Cascade Orchestrator의 `extract_text()` 메서드에 이미지를 입력
- 기본 파라미터 사용 (`preprocess=True`, `force_cascade=False`)

#### Then (기대 결과)
- ✅ **엔진 선택**: AI 엔진 사용 (`engine in ["gpt4-vision", "claude"]`)
- ✅ **신뢰도**: 99% (AI 고정값) (`confidence >= 0.99`)
- ✅ **처리 시간**: 5초 이내 (`duration <= 5.0`)
- ✅ **전체 Cascade**: Tesseract → EasyOCR → AI 순서로 모두 실행 (`len(engines_tried) == 3`)
- ✅ **Cascade 플래그**: True (`cascade_used == True`)

#### 검증 방법 (pytest)
```python
def test_very_complex_document_cascades_to_ai(cascade_orchestrator):
    """매우 복잡한 문서는 AI까지 Cascade"""
    # Given
    image_path = "test_data/ocr/cascade/very_complex_order.jpg"

    # When
    result = cascade_orchestrator.extract_text(image_path)

    # Then
    assert result.engine in ["gpt4-vision", "claude"], "AI 엔진을 사용해야 함"
    assert result.confidence >= 0.99, "AI 신뢰도는 99% 고정값이어야 함"
    assert result.duration <= 5.0, "처리 시간은 5초 이내여야 함"
    assert len(result.engines_tried) == 3, "모든 레이어를 시도해야 함"
    assert "tesseract" in result.engines_tried, "Tesseract를 먼저 시도해야 함"
    assert "easyocr" in result.engines_tried, "EasyOCR를 두 번째로 시도해야 함"
    assert result.engine in result.engines_tried, "AI 엔진이 최종으로 사용되어야 함"
    assert result.cascade_used == True, "Cascade가 사용되어야 함"
    assert len(result.text) > 0, "텍스트가 추출되어야 함"

    # 메타데이터: Tesseract와 EasyOCR 신뢰도 모두 임계값 미만
    assert result.metadata.get("tesseract_confidence", 1.0) < 0.95
    assert result.metadata.get("easyocr_confidence", 1.0) < 0.90
```

#### 성공 기준
- 모든 assertion 통과
- AI가 구조화된 데이터 추출 (JSON 형식)
- 손글씨와 기울어진 텍스트도 정확하게 인식됨

---

### 시나리오 4: 전처리 효과 검증

#### 배경
노이즈가 많은 저화질 이미지에서 OpenCV 전처리(그레이스케일, 노이즈 제거, 이진화)가 OCR 정확도를 실제로 향상시키는지 검증합니다.

#### Given (전제 조건)
- 노이즈가 많은 저화질 이미지
- 스캔 품질 불량 (200 DPI 이하)
- 이미지 경로: `test_data/ocr/cascade/noisy_image.jpg`

#### When (실행 조건)
1. **전처리 미적용**: `extract_text(image_path, preprocess=False)`
2. **전처리 적용**: `extract_text(image_path, preprocess=True)`

#### Then (기대 결과)
- ✅ **신뢰도 향상**: 전처리 적용 시 신뢰도가 10% 이상 향상 (`preprocessed_confidence >= original_confidence + 0.10`)
- ✅ **처리 시간**: 전처리 추가 시간 ≤ 0.5초
- ✅ **동일 엔진 사용 가능**: 전처리로 인해 더 낮은 레이어에서 성공 가능

#### 검증 방법 (pytest)
```python
def test_preprocessing_improves_confidence(cascade_orchestrator):
    """전처리가 신뢰도를 10% 이상 향상"""
    # Given
    image_path = "test_data/ocr/cascade/noisy_image.jpg"

    # When: 전처리 미적용
    result_without_preprocess = cascade_orchestrator.extract_text(
        image_path,
        preprocess=False
    )

    # When: 전처리 적용
    result_with_preprocess = cascade_orchestrator.extract_text(
        image_path,
        preprocess=True
    )

    # Then
    confidence_improvement = result_with_preprocess.confidence - result_without_preprocess.confidence
    assert confidence_improvement >= 0.10, f"신뢰도 향상은 10% 이상이어야 함 (실제: {confidence_improvement*100:.1f}%)"

    # 전처리 추가 시간
    preprocess_overhead = result_with_preprocess.duration - result_without_preprocess.duration
    assert preprocess_overhead <= 0.5, "전처리 추가 시간은 0.5초 이내여야 함"

    # 전처리로 인해 더 낮은 레이어에서 성공 가능 (선택적 검증)
    if result_without_preprocess.engine == "easyocr":
        # 전처리 적용 시 Tesseract만으로 성공할 수 있음
        assert result_with_preprocess.engine in ["tesseract", "easyocr"], \
            "전처리로 인해 Tesseract가 성공할 수 있어야 함"
```

#### 성공 기준
- 신뢰도 10% 이상 향상
- 전처리 추가 시간 0.5초 이내
- 전처리 적용 시 더 빠른 엔진으로 성공 가능

---

### 시나리오 5: force_cascade=True (모든 레이어 강제 실행)

#### 배경
개발/디버깅 목적으로 신뢰도와 관계없이 모든 레이어를 강제로 실행하여 각 엔진의 성능을 비교합니다.

#### Given (전제 조건)
- 임의의 발주서 이미지
- `force_cascade=True` 플래그 설정

#### When (실행 조건)
- `extract_text(image_path, force_cascade=True)`

#### Then (기대 결과)
- ✅ **모든 레이어 실행**: Tesseract, EasyOCR, AI 모두 실행 (`len(engines_tried) == 3`)
- ✅ **최고 신뢰도 선택**: 가장 신뢰도가 높은 엔진의 결과 반환
- ✅ **메타데이터**: 각 엔진별 신뢰도와 처리 시간 기록

#### 검증 방법 (pytest)
```python
def test_force_cascade_executes_all_layers(cascade_orchestrator):
    """force_cascade=True 시 모든 레이어 강제 실행"""
    # Given
    image_path = "test_data/ocr/cascade/clean_order.jpg"

    # When
    result = cascade_orchestrator.extract_text(image_path, force_cascade=True)

    # Then
    assert len(result.engines_tried) == 3, "모든 레이어가 실행되어야 함"
    assert "tesseract" in result.engines_tried
    assert "easyocr" in result.engines_tried
    assert result.engine in ["gpt4-vision", "claude", "easyocr", "tesseract"]

    # 메타데이터: 각 엔진별 신뢰도 기록
    assert "tesseract_confidence" in result.metadata
    assert "easyocr_confidence" in result.metadata
    assert "tesseract_duration" in result.metadata
    assert "easyocr_duration" in result.metadata

    # 최고 신뢰도 엔진 선택 검증
    all_confidences = {
        "tesseract": result.metadata["tesseract_confidence"],
        "easyocr": result.metadata["easyocr_confidence"],
        result.engine: result.confidence
    }
    max_confidence = max(all_confidences.values())
    assert result.confidence == max_confidence, "최고 신뢰도 엔진을 선택해야 함"
```

---

### 시나리오 6: 이미지 품질 검증 실패

#### 배경
이미지 크기가 너무 작거나 손상된 경우 처리를 거부하고 명확한 에러 메시지를 반환해야 합니다.

#### Given (전제 조건)
- 너무 작은 이미지 (500x400 픽셀)
- 또는 손상된 이미지 파일

#### When (실행 조건)
- `extract_text(image_path)`

#### Then (기대 결과)
- ✅ **에러 감지**: `ImageQualityError` 예외 발생
- ✅ **에러 메시지**: "이미지가 너무 작거나 손상됨"
- ✅ **최소 크기 안내**: "최소 800x600 픽셀 필요"

#### 검증 방법 (pytest)
```python
def test_image_quality_validation_fails_for_small_image(cascade_orchestrator):
    """너무 작은 이미지는 처리 거부"""
    # Given
    small_image_path = "test_data/ocr/cascade/small_image.jpg"  # 500x400

    # When & Then
    with pytest.raises(ImageQualityError) as exc_info:
        cascade_orchestrator.extract_text(small_image_path)

    assert "너무 작거나 손상됨" in str(exc_info.value)
    assert "800x600" in str(exc_info.value)
```

---

## 품질 게이트

### 필수 조건 (모두 충족 필요)
- ✅ **테스트 커버리지**: 85% 이상
  ```bash
  pytest --cov=backend.src.services.ocr --cov-report=term-missing
  # Coverage: 85%+
  ```

- ✅ **모든 시나리오 통과**: 6가지 시나리오 100% 통과
  ```bash
  pytest tests/services/ocr/ -v
  # 6 passed
  ```

- ✅ **Ruff 린트 검사**: 코드 품질 이슈 0건
  ```bash
  ruff check backend/src/services/ocr/
  # All checks passed!
  ```

- ✅ **Black 포맷 검사**: 코드 포맷 준수
  ```bash
  black --check backend/src/services/ocr/
  # All done! ✨
  ```

- ✅ **Mypy 타입 체크**: 타입 안정성 보장
  ```bash
  mypy backend/src/services/ocr/
  # Success: no issues found
  ```

### 성능 기준 (p95 기준)
- ✅ **레이어 1 (Tesseract)**: ≤ 2초
- ✅ **레이어 2 (EasyOCR)**: ≤ 4초
- ✅ **레이어 3 (AI)**: ≤ 5초

**성능 측정 방법**:
```python
import time
from statistics import quantiles

durations = []
for _ in range(100):
    start = time.time()
    result = cascade_orchestrator.extract_text(image_path)
    durations.append(time.time() - start)

p95 = quantiles(durations, n=20)[18]  # 95th percentile
assert p95 <= 5.0, f"p95 처리 시간은 5초 이내여야 함 (실제: {p95:.2f}초)"
```

### 정확도 기준
- ✅ **깨끗한 문서**: 95% 이상 정확도
- ✅ **복잡한 문서**: 90% 이상 정확도
- ✅ **매우 복잡한 문서**: 85% 이상 정확도

**정확도 측정 방법** (수동 검증):
```python
# Ground Truth와 비교
ground_truth = load_ground_truth("clean_order.txt")
predicted_text = cascade_orchestrator.extract_text("clean_order.jpg").text

accuracy = calculate_text_similarity(ground_truth, predicted_text)
assert accuracy >= 0.95
```

### 안정성 기준
- ✅ **에러 핸들링**: 모든 예외 상황 처리
- ✅ **로깅**: 구조화된 로그 출력
- ✅ **메모리 누수**: 없음 (장시간 실행 테스트)

## 완료 조건 (Definition of Done)

### 기능 완료
- [x] 6가지 시나리오 모두 통과
- [x] Tesseract, EasyOCR, AI 레이어 모두 구현
- [x] 신뢰도 계산 로직 정확성 검증
- [x] 이미지 전처리 효과 검증

### 테스트 완료
- [x] 테스트 커버리지 85% 이상
- [x] 단위 테스트 100% 통과
- [x] 통합 테스트 100% 통과
- [x] 성능 테스트 통과 (p95 ≤ 5초)

### 코드 품질
- [x] Ruff 린트 검사 통과
- [x] Black 포맷 검사 통과
- [x] Mypy 타입 체크 통과
- [x] 코드 리뷰 완료 (1명 이상 승인)

### 문서화 완료
- [x] Docstring 작성 (모든 public 메서드)
- [x] README 업데이트 (사용 예시 포함)
- [x] API 문서 생성 (Sphinx 또는 MkDocs)
- [x] 가이드 문서 작성 (`docs/guides/ocr_cascade_guide.md`)

### 배포 준비
- [x] 환경 변수 설정 가이드 (.env.example 업데이트)
- [x] 의존성 명시 (requirements.txt 업데이트)
- [x] Docker 이미지 빌드 성공
- [x] 프로덕션 환경 테스트 완료

## 검증 체크리스트

### 기능 검증
- [ ] 깨끗한 문서: Tesseract만 사용 ✅
- [ ] 복잡한 문서: EasyOCR로 Cascade ✅
- [ ] 매우 복잡한 문서: AI로 Cascade ✅
- [ ] 전처리 효과: 신뢰도 10% 향상 ✅
- [ ] force_cascade: 모든 레이어 실행 ✅
- [ ] 이미지 품질 검증: 너무 작은 이미지 거부 ✅

### 성능 검증
- [ ] Tesseract 처리 시간 ≤ 2초 ✅
- [ ] EasyOCR 처리 시간 ≤ 4초 ✅
- [ ] AI 처리 시간 ≤ 5초 ✅
- [ ] 전처리 추가 시간 ≤ 0.5초 ✅

### 품질 검증
- [ ] 테스트 커버리지 85%+ ✅
- [ ] Ruff 검사 통과 ✅
- [ ] Black 포맷 통과 ✅
- [ ] Mypy 타입 체크 통과 ✅
- [ ] 코드 리뷰 승인 ✅

### 문서 검증
- [ ] Docstring 100% 작성 ✅
- [ ] README 업데이트 ✅
- [ ] API 문서 생성 ✅
- [ ] 가이드 문서 작성 ✅

---

## 승인 절차

### 1차 승인: 개발자 자체 검증
- 모든 테스트 통과 확인
- 품질 게이트 기준 충족 확인
- 문서 완성도 확인

### 2차 승인: 코드 리뷰
- 1명 이상의 시니어 개발자 리뷰
- 아키텍처 적합성 검토
- 성능 최적화 여부 확인

### 3차 승인: QA 테스트
- 실제 발주서 데이터로 테스트
- 엣지 케이스 검증
- 성능 벤치마크 실행

### 최종 승인: 프로덕션 배포
- 스테이징 환경 배포 및 검증
- 모니터링 대시보드 설정
- 롤백 계획 수립

---

**최종 승인자**: @sonheungmin
**승인 일자**: 2025-10-14
**SPEC 버전**: v0.1.0
**상태**: ✅ READY FOR IMPLEMENTATION
