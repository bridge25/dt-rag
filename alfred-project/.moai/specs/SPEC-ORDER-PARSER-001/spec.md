---
id: ORDER-PARSER-001
version: 0.1.0
status: draft
created: 2025-10-15
updated: 2025-10-15
author: @Goos
priority: high
category: feature
labels:
  - parser
  - ocr
  - order-automation
depends_on:
  - OCR-CASCADE-001
scope:
  packages:
    - backend/src/services/order
    - backend/src/services/parser
  files:
    - order-parser-service.ts
    - regex-extractor.ts
    - llm-extractor.ts
    - field-validator.ts
    - normalization-service.ts
---

# @SPEC:ORDER-PARSER-001: 발주서 파서

## HISTORY

### v0.1.0 (2025-10-15)
- **INITIAL**: 발주서 파서 명세 최초 작성
- **AUTHOR**: @Goos
- **SCOPE**: OCR 결과 → 구조화된 발주서 데이터 변환
- **CONTEXT**: SPEC-OCR-CASCADE-001 완료 후 다음 단계
- **STRATEGY**: 2단계 파싱 전략 (정규식 빠른 추출 → LLM 백업)

---

## Environment (환경)

### 기술 환경
- **입력**: OCRResult (from SPEC-OCR-CASCADE-001)
  - `text: string` - OCR 추출 텍스트
  - `confidence: number` - OCR 신뢰도 (0.0~1.0)
  - `bboxes: Array<BoundingBox>` - 텍스트 영역 좌표

- **출력**: ParsedOrder (구조화된 발주서 데이터)
  - `metadata: OrderMetadata` - 발주 메타데이터 (날짜, 공급사, 수령지)
  - `line_items: Array<OrderLineItem>` - 품목 목록
  - `totals: OrderTotals` - 금액 합계
  - `confidence: number` - 파싱 신뢰도 (0.0~1.0)

### 외부 의존성
- **LLM API**: GPT-4 Turbo (복잡한 경우 백업 파서)
- **정규식 엔진**: JavaScript RegExp (기본 파서)
- **검증 라이브러리**: Zod 4.1 (스키마 검증)

### 운영 환경
- **처리 시간 목표**: p95 < 2초 (정규식 모드), p95 < 5초 (LLM 모드)
- **신뢰도 임계값**: 0.7 (정규식 → LLM 전환 기준)
- **메모리 제약**: 단일 문서 처리 시 < 50MB

---

## Assumptions (가정)

### 비즈니스 가정
1. **발주서 표준 형식**: 발주서는 "발주일자", "품목", "수량", "단가" 필드를 포함한다
2. **한국어 중심**: 발주서는 주로 한국어로 작성된다 (영어 혼용 가능)
3. **OCR 품질**: OCR 신뢰도 ≥ 0.8인 경우가 90% 이상이다 (SPEC-OCR-CASCADE-001 전제)
4. **품목명 다양성**: 품목명은 자유 형식이며 표준화가 필요하다 (예: "아크릴 5T 투명" ≈ "아크릴 5mm 투명")

### 기술 가정
1. **정규식 커버리지**: 정규식 파서로 90% 케이스 커버 가능하다
2. **LLM 백업**: 정규식 실패 시 GPT-4 Turbo로 100% 파싱 가능하다
3. **품목명 표준화**: 품목명은 N-gram 유사도 기반으로 표준화 가능하다
4. **동시 처리**: 단일 문서 파싱은 순차 처리 (배치 처리는 향후 SPEC)

### 품질 가정
1. **파싱 정확도**: 정규식 모드에서 95% 이상 정확도 달성
2. **LLM 신뢰도**: GPT-4 Turbo는 99% 이상 정확도 제공
3. **필드 검증**: 필수 필드 누락 시 신뢰도 0.0 반환 (재처리 필요)

---

## Requirements (요구사항)

### Ubiquitous (필수 기능)

**REQ-001**: 시스템은 OCR 텍스트에서 발주서 메타데이터를 추출해야 한다
- 발주일자 (order_date: Date)
- 공급사 (supplier: string)
- 수령지 (receiver: string)
- 담당자 (contact: string, optional)

**REQ-002**: 시스템은 OCR 텍스트에서 품목 목록을 추출해야 한다
- 품목명 (product_name: string)
- 수량 (quantity: number)
- 단가 (unit_price: number)
- 금액 (total_price: number)

**REQ-003**: 시스템은 금액 합계를 계산해야 한다
- 소계 (subtotal: number)
- 세금 (tax: number, optional)
- 총계 (total: number)

**REQ-004**: 시스템은 파싱 신뢰도를 0.0~1.0 범위로 반환해야 한다
- 1.0: 모든 필수 필드 추출 + 검증 통과
- 0.7~0.9: 일부 필드 누락 또는 검증 경고
- < 0.7: LLM 백업 파서 전환 필요

### Event-driven (이벤트 기반)

**REQ-101**: WHEN 정규식 파서의 신뢰도 < 0.7이면, 시스템은 LLM 백업 파서로 자동 전환해야 한다

**REQ-102**: WHEN 필수 필드가 누락되면, 시스템은 신뢰도 0.0을 반환하고 오류 메시지를 포함해야 한다
- 오류 메시지 예: `"필수 필드 누락: order_date, supplier"`

**REQ-103**: WHEN LLM 파서가 실패하면, 시스템은 원본 OCR 텍스트와 함께 에러를 반환해야 한다
- 에러 타입: `PARSING_FAILED`
- 원본 텍스트 포함 (디버깅용)

### State-driven (상태 기반)

**REQ-201**: WHILE OCR 신뢰도 ≥ 0.9일 때, 시스템은 정규식 파서만 사용해야 한다 (LLM 생략)

**REQ-202**: WHILE 품목 수 ≥ 10개일 때, 시스템은 품목명 표준화 서비스를 활성화해야 한다

### Optional (선택 기능)

**REQ-301**: WHERE 품목명 유사도 분석이 활성화되면, 시스템은 기존 품목명과 유사도를 계산할 수 있다
- 유사도 알고리즘: N-gram Cosine Similarity
- 임계값: 0.8 (유사한 품목으로 간주)

**REQ-302**: WHERE 배치 처리 모드가 활성화되면, 시스템은 여러 발주서를 병렬 파싱할 수 있다 (향후 SPEC)

### Constraints (제약사항)

**REQ-401**: IF 파싱 시간이 5초를 초과하면, 시스템은 타임아웃 에러를 반환해야 한다

**REQ-402**: IF 품목 수가 100개를 초과하면, 시스템은 경고 메시지를 반환해야 한다
- 경고: `"품목 수 초과 (100개 이상), 배치 처리 권장"`

**REQ-403**: 금액 계산 정확도는 소수점 2자리까지 보장해야 한다 (반올림)

---

## Specifications (상세 명세)

### 1. OrderParserService (메인 오케스트레이터)

**책임**: 2단계 파싱 전략 실행 및 결과 병합

**입력**:
```typescript
interface ParseOrderInput {
  ocr_result: OCRResult;
  options?: {
    force_llm?: boolean;        // LLM 강제 사용
    enable_normalization?: boolean;  // 품목명 표준화
  };
}
```

**출력**:
```typescript
interface ParsedOrder {
  metadata: OrderMetadata;
  line_items: Array<OrderLineItem>;
  totals: OrderTotals;
  confidence: number;
  parser_used: 'regex' | 'llm';
  errors?: Array<string>;
}
```

**알고리즘**:
```
1. RegexExtractor로 1차 파싱 시도
2. IF confidence >= 0.7 AND NOT force_llm:
     RETURN regex_result
3. ELSE:
     LLMExtractor로 2차 파싱 시도
     RETURN llm_result
4. FieldValidator로 검증
5. IF enable_normalization:
     NormalizationService로 품목명 표준화
6. RETURN final_result
```

**성능 목표**:
- 정규식 모드: p95 < 2초
- LLM 모드: p95 < 5초

---

### 2. RegexExtractor (정규식 기반 빠른 추출)

**책임**: 정규식 패턴으로 발주서 필드 추출 (90% 커버리지)

**패턴 정의**:
```typescript
const PATTERNS = {
  order_date: /발주일자[:\s]*(\d{4}[-./]\d{2}[-./]\d{2})/,
  supplier: /공급사[:\s]*([^\n]+)/,
  receiver: /수령지[:\s]*([^\n]+)/,
  line_item: /^(.+?)\s+(\d+)개?\s+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)원/gm,
};
```

**신뢰도 계산**:
```typescript
confidence = (extracted_fields / total_required_fields) * base_confidence;
// base_confidence = 1.0 (모든 필드 매칭), 0.8 (일부 경고), 0.5 (필드 누락)
```

**예외 처리**:
- 패턴 미매칭 → 신뢰도 0.5 반환
- 날짜 형식 오류 → Date 파싱 실패 경고
- 금액 파싱 오류 → Number 변환 실패 경고

---

### 3. LLMExtractor (복잡한 경우 GPT-4 백업)

**책임**: 정규식 실패 시 LLM 기반 파싱 (99% 정확도)

**LLM 프롬프트**:
```
당신은 한국어 발주서 파싱 전문가입니다.
다음 OCR 텍스트에서 JSON 형식으로 발주서 데이터를 추출하세요.

OCR 텍스트:
{ocr_text}

JSON 스키마:
{
  "metadata": {
    "order_date": "YYYY-MM-DD",
    "supplier": "string",
    "receiver": "string"
  },
  "line_items": [
    {
      "product_name": "string",
      "quantity": number,
      "unit_price": number,
      "total_price": number
    }
  ]
}

추출된 JSON (스키마 준수):
```

**신뢰도 계산**:
```typescript
llm_confidence = 0.95;  // GPT-4 Turbo 기본 신뢰도
if (validation_errors.length > 0) {
  llm_confidence = 0.7;  // 검증 오류 시 하향 조정
}
```

**에러 처리**:
- LLM API 타임아웃 (30초) → PARSING_FAILED 에러
- JSON 파싱 실패 → 재시도 1회
- 스키마 검증 실패 → 오류 메시지와 함께 신뢰도 0.7 반환

---

### 4. FieldValidator (필드 검증)

**책임**: 추출된 필드 검증 및 신뢰도 조정

**검증 규칙**:
```typescript
const VALIDATION_RULES = {
  order_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  supplier: z.string().min(2),
  receiver: z.string().min(2),
  quantity: z.number().int().positive(),
  unit_price: z.number().positive(),
  total_price: z.number().positive(),
};
```

**교차 검증**:
```typescript
// 품목별 금액 검증
for (const item of line_items) {
  const calculated = item.quantity * item.unit_price;
  if (Math.abs(calculated - item.total_price) > 0.01) {
    warnings.push(`품목 "${item.product_name}" 금액 불일치`);
    confidence *= 0.9;  // 신뢰도 10% 하향
  }
}
```

**신뢰도 조정**:
- 검증 통과: confidence 유지
- 경고 1개: confidence *= 0.9
- 경고 3개 이상: confidence = 0.7 (LLM 전환 권장)
- 필수 필드 누락: confidence = 0.0

---

### 5. NormalizationService (품목명 표준화)

**책임**: 품목명 유사도 분석 및 표준화

**알고리즘**: N-gram Cosine Similarity
```typescript
function normalize_product_name(name: string): string {
  // 1. 공백 정규화
  let normalized = name.replace(/\s+/g, ' ').trim();

  // 2. 단위 표준화
  normalized = normalized.replace(/5T/g, '5mm');
  normalized = normalized.replace(/투명/g, 'CLEAR');

  // 3. 기존 품목명과 유사도 계산
  const similar_items = db.find_similar_products(normalized, threshold=0.8);

  if (similar_items.length > 0) {
    return similar_items[0].standard_name;  // 가장 유사한 표준 품목명 반환
  }

  return normalized;
}
```

**성능**:
- 품목 1개 표준화: < 50ms
- 품목 10개 표준화: < 500ms

---

## Traceability (@TAG)

### SPEC Tag
- **@SPEC:ORDER-PARSER-001**: 발주서 파서 명세

### Test Tag
- **@TEST:ORDER-PARSER-001:UNIT**: `tests/unit/services/order/test_parser.spec.ts`
- **@TEST:ORDER-PARSER-001:INTEGRATION**: `tests/integration/services/order/test_parser_integration.spec.ts`

### Code Tag
- **@CODE:ORDER-PARSER-001:DOMAIN**: `src/services/order/parser/order-parser-service.ts`
- **@CODE:ORDER-PARSER-001:DOMAIN**: `src/services/order/parser/regex-extractor.ts`
- **@CODE:ORDER-PARSER-001:DOMAIN**: `src/services/order/parser/llm-extractor.ts`
- **@CODE:ORDER-PARSER-001:DOMAIN**: `src/services/order/parser/field-validator.ts`
- **@CODE:ORDER-PARSER-001:DOMAIN**: `src/services/order/parser/normalization-service.ts`

### Doc Tag
- **@DOC:ORDER-PARSER-001**: `docs/api/order-parser.md` (API 문서)
- **@DOC:ORDER-PARSER-001**: `docs/architecture/parser-strategy.md` (2단계 파싱 전략)

---

## 성공 지표

### 파싱 정확도
- **정규식 모드**: 95% 이상 정확도 (필수 필드 기준)
- **LLM 모드**: 99% 이상 정확도

### 성능
- **정규식 모드**: p95 < 2초
- **LLM 모드**: p95 < 5초
- **LLM 전환율**: < 10% (90% 케이스는 정규식으로 처리)

### 비용
- **LLM API 비용**: 문서당 평균 ≤ ₩50 (LLM 전환율 10% 가정)

---

## 위험 요소 및 대응

### 위험 1: 발주서 형식 다양성
- **증상**: 공급사마다 발주서 형식이 달라 정규식 커버리지 저하
- **대응**: LLM 백업 파서로 자동 전환 + 신규 패턴 학습 (주간 업데이트)

### 위험 2: OCR 품질 저하
- **증상**: OCR 신뢰도 < 0.8인 경우 파싱 정확도 급감
- **대응**: SPEC-OCR-CASCADE-001 강화 (EasyOCR + PaddleOCR 병렬 처리)

### 위험 3: LLM API 비용 증가
- **증상**: LLM 전환율이 10% → 30%로 증가하면 비용 3배 증가
- **대응**: 정규식 패턴 확장 (주간 리뷰) + LLM 캐싱 (동일 텍스트 재사용)

---

_이 SPEC은 `/alfred:2-build SPEC-ORDER-PARSER-001`로 TDD 구현을 시작합니다._
