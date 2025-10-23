# SPEC-OCR-001 인수 기준

> **OCR 기반 발주서 데이터 추출 시스템**
>
> 사용자 관점의 상세 인수 테스트 시나리오

---

## Scenario 1: 정상 한국어 발주서 처리

### Given (전제 조건)
- 표준 한국어 발주서 이미지 (JPG, 300+ DPI)
- 발주일자, 고객사명, 담당자 정보, 품목 목록이 명확히 표시된 문서
- 파일 크기 2MB, 해상도 2480x3508 (A4 크기, 300 DPI)

### When (사용자 행동)
- 사용자가 발주서 이미지를 업로드한다
- API 엔드포인트: `POST /api/v1/ocr/upload`

### Then (예상 결과)
1. **즉시 응답 (< 0.1초)**:
   ```json
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "status": "processing",
     "estimated_time": 3
   }
   ```

2. **3초 이내 처리 완료**:
   ```json
   {
     "status": "completed",
     "data": {
       "order_date": "2025-01-10",
       "customer_name": "주식회사 ABC",
       "contact_name": "김철수",
       "contact_phone": "010-1234-5678",
       "items": [
         {
           "product_name": "냉동 새우",
           "quantity": 100,
           "unit": "kg",
           "unit_price": 15000,
           "total_price": 1500000
         },
         {
           "product_name": "냉동 오징어",
           "quantity": 50,
           "unit": "kg",
           "unit_price": 12000,
           "total_price": 600000
         }
       ],
       "total_amount": 2100000,
       "confidence_score": 0.96
     },
     "processing_time_ms": 2800
   }
   ```

### And (추가 검증)
- ✅ 추출 정확도: 99% 이상 (신뢰도 점수 0.95+)
- ✅ 모든 필수 필드 존재: order_date, customer_name, contact_name, contact_phone, items
- ✅ 품목 합계 금액 정확: items[].total_price 합계 = total_amount
- ✅ JSON 스키마 검증 통과

---

## Scenario 2: 다국어 발주서 처리 (한국어+베트남어)

### Given
- 한국어+베트남어 혼용 발주서 이미지
- 고객사명: 한국어 ("주식회사 ABC")
- 품목명: 베트남어 ("Tôm đông lạnh", "Mực đông lạnh")
- 파일 형식: PNG, 해상도 350 DPI

### When
- 사용자가 발주서를 업로드한다

### Then
1. **언어 자동 감지**:
   ```json
   {
     "detected_languages": ["korean", "vietnamese"],
     "primary_language": "korean"
   }
   ```

2. **두 언어 모두 인식**:
   ```json
   {
     "data": {
       "customer_name": "주식회사 ABC",
       "items": [
         {
           "product_name": "Tôm đông lạnh",
           "product_name_ko": "냉동 새우",
           "quantity": 100,
           "unit": "kg"
         },
         {
           "product_name": "Mực đông lạnh",
           "product_name_ko": "냉동 오징어",
           "quantity": 50,
           "unit": "kg"
         }
       ],
       "confidence_score": 0.94
     }
   }
   ```

### And
- ✅ 베트남어 특수문자 정확히 인식 (ô, ơ, ă, ê, etc.)
- ✅ 품목명 한국어 정규화 제공 (`product_name_ko`)
- ✅ 신뢰도 점수 0.90 이상

---

## Scenario 3: 저화질 이미지 처리

### Given
- 저해상도 이미지 (150 DPI, 권장 300 DPI 미달)
- 흐릿한 스캔 이미지 (노이즈 多)
- 파일 크기 1MB, 해상도 1240x1754

### When
- 사용자가 저화질 이미지를 업로드한다

### Then
1. **품질 경고 반환**:
   ```json
   {
     "status": "completed_with_warning",
     "warnings": [
       {
         "code": "LOW_IMAGE_QUALITY",
         "message": "이미지 품질이 낮습니다. 정확도가 떨어질 수 있습니다.",
         "recommendation": "300 DPI 이상 이미지를 다시 업로드해주세요.",
         "detected_dpi": 150
       }
     ],
     "data": { ... },
     "confidence_score": 0.87
   }
   ```

2. **처리는 계속 진행**:
   - 시스템은 경고를 표시하지만 OCR 처리를 중단하지 않음
   - 신뢰도 점수는 낮아질 수 있음 (0.85~0.90)

3. **자동 재처리 트리거**:
   - 신뢰도 0.90 미만 → GPT-4 Vision으로 재처리
   - 재처리 후 신뢰도 0.92로 향상

### And
- ✅ 사용자에게 재업로드 권장 UI 표시
- ✅ 추출 결과는 반환됨 (완전 실패 아님)
- ✅ 신뢰도 점수와 함께 제공

---

## Scenario 4: PDF 복합 문서 처리

### Given
- 5페이지 PDF 문서
- 1페이지: 커버 레터
- 2페이지: 발주서 (추출 대상)
- 3-5페이지: 제품 카탈로그

### When
- 사용자가 PDF를 업로드한다

### Then
1. **발주서 페이지 자동 감지**:
   ```json
   {
     "detected_order_page": 2,
     "total_pages": 5,
     "processing_strategy": "single_page_extraction"
   }
   ```

2. **2페이지만 OCR 처리**:
   ```json
   {
     "data": {
       "order_date": "2025-01-10",
       "customer_name": "주식회사 ABC",
       ...
     },
     "metadata": {
       "source_page": 2,
       "source_file": "order_document_5pages.pdf"
     }
   }
   ```

3. **나머지 페이지 무시**:
   - 커버 레터, 카탈로그는 OCR 처리하지 않음
   - 처리 시간 절약 (5배 빠름)

### And
- ✅ 발주서 페이지만 정확히 추출
- ✅ 페이지 번호 메타데이터 포함
- ✅ 다중 페이지 PDF도 3초 이내 처리

---

## Scenario 5: 엑셀 구조화 데이터 처리

### Given
- XLS 형식 발주서
- 표 형식으로 구조화된 데이터
- 발주일자: A1, 고객사명: A2, 품목: A5:E10

### When
- 사용자가 엑셀 파일을 업로드한다

### Then
1. **OCR 우회, 직접 파싱**:
   ```json
   {
     "processing_method": "excel_direct_parsing",
     "ocr_bypassed": true
   }
   ```

2. **1초 이내 처리 완료**:
   ```json
   {
     "status": "completed",
     "data": {
       "order_date": "2025-01-10",
       "customer_name": "주식회사 ABC",
       "items": [...]
     },
     "processing_time_ms": 800,
     "confidence_score": 1.0
   }
   ```

3. **100% 정확도 보장**:
   - 구조화된 데이터이므로 오인식 없음
   - 신뢰도 점수 1.0 (완벽)

### And
- ✅ 엑셀 파일은 OCR 없이 직접 파싱
- ✅ 처리 시간 1초 미만 (초고속)
- ✅ 100% 정확도 보장

---

## Scenario 6: OCR 엔진 캐스케이드 (낮은 신뢰도)

### Given
- 복잡한 레이아웃의 발주서 (표, 로고, 워터마크 혼재)
- Tesseract OCR로는 정확도 낮음 (< 0.90)

### When
- 사용자가 복잡한 발주서를 업로드한다

### Then
1. **1차 시도: Tesseract OCR**:
   ```json
   {
     "engine": "tesseract",
     "confidence_score": 0.82,
     "status": "low_confidence_detected"
   }
   ```

2. **2차 시도: GPT-4 Vision**:
   ```json
   {
     "engine": "gpt4_vision",
     "confidence_score": 0.94,
     "status": "completed"
   }
   ```

3. **최종 결과 반환**:
   ```json
   {
     "data": { ... },
     "confidence_score": 0.94,
     "engine_used": "gpt4_vision",
     "fallback_triggered": true
   }
   ```

### And
- ✅ 낮은 신뢰도 자동 감지
- ✅ 대체 엔진으로 자동 재처리
- ✅ 최종 신뢰도 0.90 이상 달성
- ✅ 사용자는 재처리 과정 인지 불필요 (투명한 자동화)

---

## Scenario 7: 대용량 파일 처리

### Given
- 발주서 이미지 파일 크기 15MB (10MB 초과)
- 고해상도 스캔 이미지 (600 DPI, 5000x7000)

### When
- 사용자가 대용량 파일을 업로드한다

### Then
1. **자동 압축/리사이징**:
   ```json
   {
     "original_file_size": 15728640,
     "compressed_file_size": 4194304,
     "compression_ratio": 3.75,
     "resized_resolution": "4096x5793"
   }
   ```

2. **압축 후 정상 처리**:
   ```json
   {
     "status": "completed",
     "data": { ... },
     "confidence_score": 0.95
   }
   ```

### And
- ✅ 10MB 초과 파일 자동 압축
- ✅ 최대 해상도 4096x4096 유지
- ✅ 정확도 손실 없음 (0.95 유지)

---

## Scenario 8: 동시 요청 대기열 처리

### Given
- 동시에 15개 발주서 업로드 (시스템 제한 10개)

### When
- 사용자가 15개 파일을 한 번에 업로드한다

### Then
1. **처음 10개 즉시 처리**:
   ```json
   {
     "accepted_jobs": 10,
     "queued_jobs": 5,
     "estimated_wait_time": 6
   }
   ```

2. **나머지 5개 대기열 추가**:
   ```json
   {
     "job_ids": ["job-11", "job-12", "job-13", "job-14", "job-15"],
     "queue_position": [1, 2, 3, 4, 5],
     "estimated_start_time": ["3s", "6s", "9s", "12s", "15s"]
   }
   ```

3. **순차 처리 완료**:
   - 처음 10개: 3초 이내 완료
   - 나머지 5개: 6초~18초 사이 완료

### And
- ✅ 동시 처리 제한 준수 (10개)
- ✅ 대기열 자동 관리
- ✅ 예상 대기 시간 제공

---

## Scenario 9: API Rate Limit 처리

### Given
- OpenAI API Rate Limit 도달 (분당 100회 제한)
- 현재 95회 호출 완료, 5회 남음

### When
- 사용자가 발주서를 업로드하여 GPT-4 Vision 호출 필요

### Then
1. **Rate Limit 감지**:
   ```json
   {
     "error": "RATE_LIMIT_EXCEEDED",
     "retry_after": 2,
     "retry_count": 1
   }
   ```

2. **Exponential Backoff 재시도**:
   - 1차 재시도: 1초 대기 후 재호출
   - 2차 재시도: 2초 대기 후 재호출
   - 3차 재시도: 4초 대기 후 재호출

3. **재시도 성공**:
   ```json
   {
     "status": "completed",
     "data": { ... },
     "retry_succeeded": true,
     "retry_count": 2
   }
   ```

### And
- ✅ Rate Limit 자동 감지
- ✅ Exponential Backoff 전략 적용
- ✅ 최대 3회 재시도
- ✅ 재시도 성공 시 정상 처리

---

## Scenario 10: 캐시 히트 (중복 업로드)

### Given
- 동일한 발주서를 1시간 전에 업로드한 이력 있음
- Redis 캐시에 이전 결과 저장됨 (TTL: 24시간)

### When
- 사용자가 동일한 파일을 다시 업로드한다

### Then
1. **캐시 히트 확인**:
   ```json
   {
     "cache_hit": true,
     "cached_at": "2025-01-14T10:30:00Z"
   }
   ```

2. **즉시 결과 반환 (< 0.1초)**:
   ```json
   {
     "status": "completed",
     "data": { ... },
     "processing_time_ms": 50,
     "from_cache": true
   }
   ```

### And
- ✅ OCR 재처리 없이 캐시 결과 반환
- ✅ 응답 시간 0.1초 미만 (60배 빠름)
- ✅ API 비용 절감 (재호출 없음)

---

## Definition of Done (완료 조건)

### 기능 완료
- [ ] 10개 시나리오 모두 통과
- [ ] 정확도 99% 이상 달성 (100건 검증 세트)
- [ ] p95 응답 시간 3초 이하
- [ ] 에러율 1% 이하 (3회 재시도 후)

### 품질 게이트
- [ ] 단위 테스트 커버리지 90% 이상
- [ ] 통합 테스트 10개 시나리오 모두 통과
- [ ] E2E 테스트 3개 시나리오 통과
- [ ] API 문서화 완료 (Swagger UI)

### 프로덕션 준비
- [ ] Redis 캐싱 활성화
- [ ] Celery 비동기 처리 활성화
- [ ] Prometheus 메트릭 수집 활성화
- [ ] Sentry 오류 추적 활성화
- [ ] 로그 구조화 (structlog)

---

**문서 버전**: v0.1.0
**최종 수정**: 2025-01-14
**다음 업데이트**: 인수 테스트 실행 결과 반영
