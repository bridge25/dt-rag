---
id: OCR-001
version: 0.1.0
status: draft
created: 2025-01-14
updated: 2025-01-14
author: @sonheungmin
priority: critical
category: feature
labels:
  - ocr
  - ai
  - phase-1
  - mvp
  - automation
scope:
  packages:
    - new-automation-proposal/order-automation-saas/services/ocr
  files:
    - ocr_service.py
    - image_processor.py
    - json_converter.py
---

# @SPEC:OCR-001: OCR 기반 발주서 이미지 데이터 추출

## HISTORY

### v0.1.0 (2025-01-14)
- **INITIAL**: OCR 기반 발주서 이미지 데이터 추출 명세 최초 작성
- **AUTHOR**: @sonheungmin
- **SCOPE**: 다국어(한국어, 베트남어, 영어) 발주서 자동 추출 및 JSON 변환
- **CONTEXT**: Phase 1 MVP 핵심 기능 - 해동기획 자동화 프로젝트
- **PRIORITY**: Critical - 전체 SaaS 시스템의 핵심 입력 처리 기능
- **TARGET**: 99% 이상 정확도 달성

---

## Environment (환경)

### 인프라 환경
- **파일 저장소**: AWS S3
- **런타임**: Python 3.11+
- **웹 프레임워크**: FastAPI 0.104+
- **데이터베이스**: PostgreSQL 15+ (메타데이터 저장)
- **캐싱**: Redis 7+ (중복 요청 방지)

### OCR 엔진 스택
- **1차 엔진**: Tesseract OCR 5.0+ (빠른 처리, 기본 정확도)
- **2차 엔진**: OpenAI GPT-4 Vision (고정확도, 다국어 강점)
- **3차 엔진**: Anthropic Claude 3.5 Sonnet (최종 검증, 컨텍스트 이해)

### 지원 파일 형식
- **이미지**: JPG, PNG, WEBP (300+ DPI 권장)
- **문서**: PDF (다중 페이지 지원)
- **구조화 데이터**: XLS, XLSX (OCR 우회 파싱)

### 다국어 지원
- **주요 언어**: 한국어 (기본)
- **보조 언어**: 베트남어, 영어
- **혼용 문서**: 한국어+베트남어 혼재 문서 처리 가능

---

## Assumptions (가정)

### 입력 데이터 가정
1. **발주서 형식**: 발주서는 표준화된 양식을 따르거나, 최소한 다음 필드를 포함
   - 발주일자 (order_date)
   - 고객사명 (customer_name)
   - 담당자 정보 (contact_name, contact_phone)
   - 품목 목록 (items: product_name, quantity, unit_price)

2. **이미지 품질**:
   - 최소 해상도 300 DPI 권장
   - 저화질 이미지는 경고 후 처리 시도
   - 심각하게 손상된 이미지는 재업로드 요청

3. **언어 혼용**:
   - 단일 발주서에 2개 이상 언어 동시 출현 가능
   - 품목명은 한국어로 정규화 필요

### 인프라 가정
1. **AWS S3**: 버킷 설정 완료, IAM 권한 부여
2. **API Rate Limit**: OpenAI/Anthropic API 호출량 제한 고려
3. **네트워크**: 안정적인 인터넷 연결 (외부 API 호출)

---

## Requirements (요구사항)

### Ubiquitous (필수 기능)

#### R-OCR-001: 다중 형식 파일 지원
시스템은 이미지(PNG, JPG), PDF, 엑셀(XLS, XLSX) 형식의 발주서 파일을 처리해야 한다.

#### R-OCR-002: 표준 JSON 출력
시스템은 추출된 데이터를 표준 JSON 형식으로 반환해야 한다.
```json
{
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
    }
  ],
  "total_amount": 1500000,
  "confidence_score": 0.95
}
```

#### R-OCR-003: 고정확도 보장
시스템은 99% 이상의 데이터 추출 정확도를 달성해야 한다.
- **측정 방법**: 수작업 검증 세트 100건 기준
- **실패 허용**: 1% 미만 (1건 이하)

#### R-OCR-004: 다국어 처리
시스템은 한국어, 베트남어, 영어를 동시에 인식하고 추출해야 한다.
- 언어 자동 감지
- 혼용 문서 처리 지원

---

### Event-driven (이벤트 기반)

#### R-OCR-005: 파일 업로드 시 자동 감지
WHEN 사용자가 발주서 파일을 업로드하면,
THEN 시스템은 파일 형식(이미지/PDF/엑셀)을 자동으로 감지해야 한다.

#### R-OCR-006: OCR 완료 시 검증
WHEN OCR 처리가 완료되면,
THEN 시스템은 추출 결과를 자동으로 검증하고 신뢰도 점수를 계산해야 한다.

#### R-OCR-007: 낮은 정확도 시 재처리
WHEN 추출 정확도가 90% 미만이면,
THEN 시스템은 대체 OCR 엔진(GPT-4 Vision 또는 Claude 3.5)으로 자동 재처리해야 한다.

#### R-OCR-008: 처리 실패 시 알림
WHEN OCR 처리가 3회 재시도 후에도 실패하면,
THEN 시스템은 사용자에게 오류 상세 정보와 함께 알림을 전송해야 한다.

---

### State-driven (상태 기반)

#### R-OCR-009: 처리 중 진행 상태 전송
WHILE OCR 처리가 진행 중이면,
THEN 시스템은 진행 상태(0%~100%)를 클라이언트에 실시간으로 전송해야 한다.
- **구현**: WebSocket 또는 Server-Sent Events (SSE)

#### R-OCR-010: 다국어 처리 시 엔진 선택
WHILE 다국어 텍스트를 처리 중이면,
THEN 시스템은 언어별로 최적화된 OCR 엔진을 선택해야 한다.
- 한국어: Tesseract 우선, GPT-4 Vision 대체
- 베트남어: GPT-4 Vision 또는 Claude 3.5 (특수문자 처리)
- 영어: Tesseract 충분

#### R-OCR-011: 대기열 모드 시 순차 처리
WHILE 동시 요청 수가 10개를 초과하면,
THEN 시스템은 대기열 모드로 전환하여 순차 처리해야 한다.

---

### Optional (선택 기능)

#### R-OCR-012: 엑셀 직접 파싱
WHERE 입력 파일이 엑셀(XLS/XLSX) 형식이면,
THEN 시스템은 OCR을 우회하고 직접 파싱할 수 있다.
- **이점**: 100% 정확도 보장, 1초 미만 처리

#### R-OCR-013: 캐싱 지원
WHERE 동일한 파일이 재업로드되면,
THEN 시스템은 Redis 캐시에서 이전 결과를 반환할 수 있다.
- **TTL**: 24시간
- **캐시 키**: 파일 SHA-256 해시

#### R-OCR-014: 배치 처리
WHERE 사용자가 10개 이상 파일을 동시 업로드하면,
THEN 시스템은 배치 처리 모드로 전환하여 병렬 처리할 수 있다.

---

### Constraints (제약사항)

#### C-OCR-001: 해상도 품질 검증
IF 이미지 해상도가 300 DPI 미만이면,
THEN 시스템은 "이미지 품질 부족" 경고를 반환하고 처리를 계속해야 한다.

#### C-OCR-002: 파일 크기 제한
IF 파일 크기가 10MB를 초과하면,
THEN 시스템은 압축 또는 리사이징 후 처리해야 한다.

#### C-OCR-003: 응답 시간 제한
IF OCR 처리 시간이 3초를 초과하면,
THEN 시스템은 타임아웃 경고를 반환하고 비동기 처리로 전환해야 한다.

#### C-OCR-004: API Rate Limit 준수
IF OpenAI 또는 Anthropic API 호출이 Rate Limit에 도달하면,
THEN 시스템은 Exponential Backoff 전략으로 재시도해야 한다.
- **재시도 간격**: 1초, 2초, 4초 (최대 3회)

#### C-OCR-005: 동시 처리 제한
시스템은 동시에 최대 10개의 OCR 요청만 처리해야 한다.
- **초과 시**: 대기열에 추가, 순차 처리

---

## Traceability (@TAG)

### SPEC 태그
- **SPEC**: @SPEC:OCR-001
- **CATEGORY**: feature
- **PRIORITY**: critical

### 코드 위치
- **SERVICE**: `new-automation-proposal/order-automation-saas/services/ocr/ocr_service.py`
- **PROCESSOR**: `new-automation-proposal/order-automation-saas/services/ocr/image_processor.py`
- **CONVERTER**: `new-automation-proposal/order-automation-saas/services/ocr/json_converter.py`

### 테스트
- **UNIT**: `tests/services/ocr/test_ocr_service.py`
- **INTEGRATION**: `tests/integration/test_ocr_pipeline.py`
- **E2E**: `tests/e2e/test_order_upload.py`

### 문서
- **API**: `docs/api/ocr.md`
- **USER_GUIDE**: `docs/user-guide/upload-order.md`

### 의존성
- **DEPENDS_ON**: 없음 (Phase 1 독립 기능)
- **BLOCKS**:
  - ORDER-VALIDATION-001 (발주서 검증 기능)
  - INVENTORY-SYNC-001 (재고 동기화 기능)

---

## Success Criteria (성공 기준)

### 정량적 지표
1. **정확도**: ≥ 99% (100건 검증 세트 기준)
2. **응답 시간**: p95 ≤ 3초 (단일 발주서 기준)
3. **처리량**: 시간당 1000건 이상
4. **에러율**: ≤ 1% (3회 재시도 후 실패율)

### 정성적 지표
1. 베트남어 특수문자 정확히 인식
2. 한국어+베트남어 혼용 문서 처리 성공
3. 저화질 이미지도 경고 후 처리 시도

---

**문서 버전**: v0.1.0
**최종 수정**: 2025-01-14
**다음 업데이트**: 구현 완료 시 v0.2.0으로 업데이트
