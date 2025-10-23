# 인수 기준: SPEC-ORDER-PARSER-001

## Acceptance Criteria

### AC-001: 정상적인 발주서 파싱 (정규식 모드)

**Given**: OCR 텍스트가 표준 형식으로 제공된다
```
발주일자: 2025-10-15
공급사: 아크릴 공업사
수령지: 서울시 강남구 테헤란로 123

품목           수량    단가
아크릴 5T 투명    10개   50,000원
아크릴 3T 백색    5개    30,000원

소계: 650,000원
```

**When**: OrderParserService.parse()를 호출하면

**Then**:
- ✅ `parsed_order.metadata.order_date == "2025-10-15"`
- ✅ `parsed_order.metadata.supplier == "아크릴 공업사"`
- ✅ `parsed_order.metadata.receiver == "서울시 강남구 테헤란로 123"`
- ✅ `parsed_order.line_items.length == 2`
- ✅ `parsed_order.line_items[0].product_name == "아크릴 5T 투명"`
- ✅ `parsed_order.line_items[0].quantity == 10`
- ✅ `parsed_order.line_items[0].unit_price == 50000`
- ✅ `parsed_order.line_items[0].total_price == 500000`
- ✅ `parsed_order.totals.subtotal == 650000`
- ✅ `parsed_order.confidence >= 0.9`
- ✅ `parsed_order.parser_used == "regex"`
- ✅ 응답 시간 < 2초 (p95)

**우선순위**: 최고 (핵심 기능)

---

### AC-002: 필수 필드 누락 처리

**Given**: OCR 텍스트에 필수 필드 (발주일자)가 누락된다
```
공급사: 아크릴 공업사
수령지: 서울시 강남구

아크릴 5T 투명 10개 50,000원
```

**When**: OrderParserService.parse()를 호출하면

**Then**:
- ✅ `parsed_order.confidence == 0.0`
- ✅ `parsed_order.errors.includes("필수 필드 누락: order_date")`
- ✅ `parsed_order.metadata.supplier == "아크릴 공업사"` (다른 필드는 정상 추출)
- ❌ 시스템은 오류를 반환하지 않는다 (신뢰도 0.0만 반환)

**우선순위**: 높음

---

### AC-003: 정규식 실패 시 LLM 전환

**Given**: OCR 텍스트가 비표준 형식이다
```
10월 15일자로 아크릴 판을 주문합니다.
공급사는 아크릴 공업사이고,
배송지는 서울시 강남구입니다.

아크릴 5T 투명을 10장 주문합니다. 단가는 5만원입니다.
```

**When**: OrderParserService.parse()를 호출하면

**Then**:
- ✅ 정규식 파서가 먼저 시도된다
- ✅ `regex_result.confidence < 0.7`이므로 LLM 파서로 전환된다
- ✅ `parsed_order.parser_used == "llm"`
- ✅ `parsed_order.metadata.order_date == "2025-10-15"` (날짜 정규화)
- ✅ `parsed_order.line_items[0].product_name == "아크릴 5T 투명"`
- ✅ `parsed_order.line_items[0].quantity == 10`
- ✅ `parsed_order.confidence >= 0.7`
- ✅ 응답 시간 < 5초 (p95)

**우선순위**: 최고 (핵심 기능)

---

### AC-004: LLM 강제 사용 옵션

**Given**: OCR 텍스트는 정상이지만 사용자가 LLM 사용을 강제한다
```
발주일자: 2025-10-15
공급사: 아크릴 공업사

아크릴 5T 투명 10개 50,000원
```

**When**: `OrderParserService.parse(ocr_result, { force_llm: true })`를 호출하면

**Then**:
- ✅ 정규식 파서가 생략된다
- ✅ `parsed_order.parser_used == "llm"`
- ✅ `parsed_order.confidence >= 0.9`
- ✅ 파싱 결과는 정규식 모드와 동일하다

**우선순위**: 중간 (선택 기능)

---

### AC-005: 품목 금액 교차 검증

**Given**: OCR 텍스트의 품목 금액이 불일치한다
```
발주일자: 2025-10-15
공급사: 아크릴 공업사

아크릴 5T 투명 10개 50,000원  (실제: 10 * 50,000 = 500,000원이어야 함)
```

**When**: FieldValidator가 검증을 수행하면

**Then**:
- ✅ `validation_result.warnings.includes('품목 "아크릴 5T 투명" 금액 불일치')`
- ✅ `validation_result.confidence < 1.0` (신뢰도 하향)
- ✅ `validation_result.confidence >= 0.9` (경고 1개 → 10% 하향)
- ✅ 시스템은 파싱을 계속 진행한다 (오류가 아닌 경고)

**우선순위**: 중간

---

### AC-006: 날짜 형식 다양성 처리

**Given**: 발주일자가 다양한 형식으로 제공된다

**Scenario 1**: `발주일자: 2025-10-15` (하이픈)
**Scenario 2**: `발주일자: 2025.10.15` (점)
**Scenario 3**: `발주일자: 2025/10/15` (슬래시)

**When**: RegexExtractor.extract_metadata()를 호출하면

**Then**:
- ✅ 모든 형식이 `"2025-10-15"`로 정규화된다
- ✅ `result.confidence >= 0.9` (모든 경우)

**우선순위**: 높음

---

### AC-007: 품목명 표준화 (선택 기능)

**Given**: OCR 텍스트에 유사한 품목명이 있다
```
아크릴 5T 투명
아크릴 5mm CLEAR
```

**When**: `OrderParserService.parse(ocr_result, { enable_normalization: true })`를 호출하면

**Then**:
- ✅ `parsed_order.line_items[0].product_name == "아크릴 5mm 투명"` (표준 품목명)
- ✅ `parsed_order.line_items[1].product_name == "아크릴 5mm 투명"` (동일하게 표준화)
- ✅ NormalizationService가 N-gram 유사도 ≥ 0.8인 품목을 동일 품목으로 간주한다

**우선순위**: 낮음 (향후 개선)

---

### AC-008: 대량 품목 처리

**Given**: 발주서에 50개 품목이 있다

**When**: OrderParserService.parse()를 호출하면

**Then**:
- ✅ `parsed_order.line_items.length == 50`
- ✅ 모든 품목이 정상 파싱된다
- ✅ 응답 시간 < 3초 (정규식 모드)
- ✅ 응답 시간 < 7초 (LLM 모드)

**우선순위**: 중간

---

### AC-009: 품목 수 제한 경고

**Given**: 발주서에 100개 이상 품목이 있다

**When**: OrderParserService.parse()를 호출하면

**Then**:
- ✅ `parsed_order.warnings.includes("품목 수 초과 (100개 이상), 배치 처리 권장")`
- ✅ 시스템은 파싱을 계속 진행한다 (경고만 발생)
- ✅ 100개 초과 품목도 모두 파싱된다

**우선순위**: 낮음

---

### AC-010: LLM API 타임아웃 처리

**Given**: LLM API가 30초 이상 응답하지 않는다

**When**: LLMExtractor.extract()를 호출하면

**Then**:
- ✅ 30초 후 타임아웃 에러가 발생한다
- ✅ `error.type == "TIMEOUT"`
- ✅ `error.message.includes("LLM API 타임아웃")`
- ✅ 시스템은 원본 OCR 텍스트를 포함한 에러를 반환한다

**우선순위**: 중간

---

### AC-011: LLM API 실패 시 재시도

**Given**: LLM API가 1회 실패한다 (네트워크 오류)

**When**: LLMExtractor.extract()를 호출하면

**Then**:
- ✅ 시스템은 1초 후 자동으로 1회 재시도한다
- ✅ 재시도 성공 시 정상 결과를 반환한다
- ✅ 재시도 실패 시 PARSING_FAILED 에러를 반환한다

**우선순위**: 중간

---

### AC-012: 금액 소수점 정확도

**Given**: 품목 단가가 소수점 2자리 이상이다
```
아크릴 5T 투명 10개 5,123.456원
```

**When**: RegexExtractor.extract_line_items()를 호출하면

**Then**:
- ✅ `line_item.unit_price == 5123.46` (소수점 2자리 반올림)
- ✅ `line_item.total_price == 51234.60` (quantity * unit_price)

**우선순위**: 낮음

---

### AC-013: 성능 벤치마크

**Given**: 100개 발주서 샘플이 있다 (50개 정상, 50개 비표준)

**When**: 모든 샘플을 파싱하면

**Then**:
- ✅ 정규식 모드 성공률 ≥ 90% (50개 중 45개 이상)
- ✅ 정규식 모드 p95 latency < 2초
- ✅ LLM 모드 성공률 100% (50개 전부)
- ✅ LLM 모드 p95 latency < 5초
- ✅ 전체 정확도 ≥ 95% (필수 필드 기준)

**우선순위**: 최고 (프로덕션 준비)

---

### AC-014: 비용 효율성

**Given**: 1,000개 발주서를 파싱한다

**When**: LLM 전환율이 10%라고 가정하면

**Then**:
- ✅ 정규식 모드: 900개 (비용 ₩0)
- ✅ LLM 모드: 100개 (비용 ₩5,000, 문서당 ₩50)
- ✅ 총 비용: ₩5,000 (평균 문서당 ₩5)
- ✅ 비용 목표 달성: 문서당 평균 ≤ ₩50 ✅

**우선순위**: 중간

---

### AC-015: 에러 메시지 명확성

**Given**: 다양한 에러 상황이 발생한다

**Scenario 1**: 필수 필드 누락
**Then**: `errors: ["필수 필드 누락: order_date, supplier"]`

**Scenario 2**: LLM API 타임아웃
**Then**: `error: { type: "TIMEOUT", message: "LLM API 타임아웃 (30초)" }`

**Scenario 3**: JSON 파싱 실패
**Then**: `error: { type: "PARSING_FAILED", message: "LLM 응답 JSON 파싱 실패", raw_response: "..." }`

**우선순위**: 중간

---

## Definition of Done (완료 조건)

### 기능 완료
- [ ] RegexExtractor 구현 완료 (메타데이터 + 품목 추출)
- [ ] LLMExtractor 구현 완료 (GPT-4 Turbo 통합)
- [ ] FieldValidator 구현 완료 (Zod 검증 + 교차 검증)
- [ ] OrderParserService 구현 완료 (2단계 파싱 전략)
- [ ] NormalizationService 구현 완료 (선택 기능)

### 테스트 완료
- [ ] 단위 테스트 커버리지 ≥ 90%
- [ ] 통합 테스트 15개 시나리오 통과
- [ ] 성능 벤치마크 통과 (p95 < 2초/5초)
- [ ] 비용 효율성 검증 (문서당 평균 ≤ ₩50)

### 문서 완료
- [ ] API 문서 작성 (`docs/api/order-parser.md`)
- [ ] 아키텍처 문서 작성 (`docs/architecture/parser-strategy.md`)
- [ ] 사용자 가이드 작성 (정규식 vs LLM 모드 선택 기준)

### 품질 게이트
- [ ] ESLint 경고 0개
- [ ] TypeScript 타입 에러 0개
- [ ] 코드 리뷰 승인 (최소 1명)

### 프로덕션 준비
- [ ] 환경 변수 설정 (OPENAI_API_KEY)
- [ ] 에러 추적 설정 (Sentry 연동)
- [ ] 성능 모니터링 설정 (Prometheus 메트릭)
- [ ] SPEC-OCR-CASCADE-001과 통합 테스트

---

## 검증 시나리오 우선순위

### P0 (필수 - 출시 전 반드시 통과)
- AC-001: 정상적인 발주서 파싱
- AC-002: 필수 필드 누락 처리
- AC-003: 정규식 실패 시 LLM 전환
- AC-013: 성능 벤치마크

### P1 (중요 - 출시 전 통과 권장)
- AC-005: 품목 금액 교차 검증
- AC-006: 날짜 형식 다양성 처리
- AC-010: LLM API 타임아웃 처리
- AC-011: LLM API 실패 시 재시도

### P2 (선택 - 향후 개선)
- AC-004: LLM 강제 사용 옵션
- AC-007: 품목명 표준화
- AC-009: 품목 수 제한 경고
- AC-014: 비용 효율성

---

## 인수 테스트 실행 방법

### 자동 테스트
```bash
# 전체 인수 테스트 실행
npm run test:acceptance

# 특정 AC만 실행
npm run test:acceptance -- --grep "AC-001"

# 성능 벤치마크
npm run test:performance
```

### 수동 테스트
1. 발주서 샘플 50개 준비 (`.moai/test-data/orders/`)
2. 각 AC에 대해 수동 파싱 실행
3. 결과를 예상 출력과 비교
4. 체크리스트 작성

### 통합 테스트 (SPEC-OCR-CASCADE-001 연동)
```bash
# OCR → Parser 파이프라인 테스트
npm run test:integration -- --grep "OCR to Parser"
```

---

_이 인수 기준은 `/alfred:2-build SPEC-ORDER-PARSER-001` 구현 완료 후 검증에 사용됩니다._
