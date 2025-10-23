# 구현 계획: SPEC-ORDER-PARSER-001

## TDD 단계별 구현

### Phase 0: 프로젝트 설정 및 의존성

**목표**: 개발 환경 구축 및 필수 의존성 설치

**작업 항목**:
1. TypeScript 프로젝트 초기화
   ```bash
   npm init -y
   npm install --save-dev typescript @types/node ts-node
   npm install zod axios
   ```

2. 테스트 프레임워크 설정
   ```bash
   npm install --save-dev vitest @vitest/ui
   ```

3. 디렉토리 구조 생성
   ```
   src/
   ├── services/
   │   └── order/
   │       └── parser/
   │           ├── order-parser-service.ts
   │           ├── regex-extractor.ts
   │           ├── llm-extractor.ts
   │           ├── field-validator.ts
   │           └── normalization-service.ts
   tests/
   ├── unit/
   │   └── services/
   │       └── order/
   │           └── test_parser.spec.ts
   └── integration/
       └── services/
           └── order/
               └── test_parser_integration.spec.ts
   ```

**완료 기준**:
- ✅ `npm test` 실행 시 "No tests found" 메시지 출력
- ✅ TypeScript 컴파일 정상 동작 (`tsc --noEmit`)

---

### Phase 1: RED 단계 - 테스트 케이스 정의

**목표**: 실패하는 테스트 작성 (TDD Red 단계)

#### 1.1 RegexExtractor 테스트 (우선순위 1)

**테스트 파일**: `tests/unit/services/order/test_regex_extractor.spec.ts`

**테스트 케이스**:
```typescript
import { describe, it, expect } from 'vitest';
import { RegexExtractor } from '@/services/order/parser/regex-extractor';

describe('RegexExtractor', () => {
  const extractor = new RegexExtractor();

  it('정상적인 발주서 텍스트에서 메타데이터 추출', () => {
    const ocr_text = `
      발주일자: 2025-10-15
      공급사: 아크릴 공업사
      수령지: 서울시 강남구 테헤란로 123
    `;

    const result = extractor.extract_metadata(ocr_text);

    expect(result.order_date).toBe('2025-10-15');
    expect(result.supplier).toBe('아크릴 공업사');
    expect(result.receiver).toBe('서울시 강남구 테헤란로 123');
    expect(result.confidence).toBeGreaterThanOrEqual(0.9);
  });

  it('품목 목록 추출', () => {
    const ocr_text = `
      아크릴 5T 투명 10개 50,000원
      아크릴 3T 백색 5개 30,000원
    `;

    const result = extractor.extract_line_items(ocr_text);

    expect(result.line_items).toHaveLength(2);
    expect(result.line_items[0].product_name).toBe('아크릴 5T 투명');
    expect(result.line_items[0].quantity).toBe(10);
    expect(result.line_items[0].unit_price).toBe(50000);
    expect(result.confidence).toBeGreaterThanOrEqual(0.9);
  });

  it('필수 필드 누락 시 신뢰도 0.0 반환', () => {
    const ocr_text = `
      공급사: 아크릴 공업사
      (발주일자 누락)
    `;

    const result = extractor.extract_metadata(ocr_text);

    expect(result.confidence).toBe(0.0);
    expect(result.errors).toContain('필수 필드 누락: order_date');
  });

  it('날짜 형식 다양성 처리 (2025-10-15, 2025.10.15, 2025/10/15)', () => {
    const formats = [
      '발주일자: 2025-10-15',
      '발주일자: 2025.10.15',
      '발주일자: 2025/10/15',
    ];

    for (const text of formats) {
      const result = extractor.extract_metadata(text);
      expect(result.order_date).toBe('2025-10-15');  // 정규화된 형식
    }
  });
});
```

**예상 결과**: ❌ 모든 테스트 실패 (RegexExtractor 미구현)

---

#### 1.2 FieldValidator 테스트 (우선순위 2)

**테스트 파일**: `tests/unit/services/order/test_field_validator.spec.ts`

**테스트 케이스**:
```typescript
import { describe, it, expect } from 'vitest';
import { FieldValidator } from '@/services/order/parser/field-validator';

describe('FieldValidator', () => {
  const validator = new FieldValidator();

  it('유효한 ParsedOrder 검증 통과', () => {
    const parsed_order = {
      metadata: {
        order_date: '2025-10-15',
        supplier: '아크릴 공업사',
        receiver: '서울시 강남구',
      },
      line_items: [
        { product_name: '아크릴 5T', quantity: 10, unit_price: 5000, total_price: 50000 },
      ],
    };

    const result = validator.validate(parsed_order);

    expect(result.is_valid).toBe(true);
    expect(result.confidence).toBe(1.0);
    expect(result.errors).toHaveLength(0);
  });

  it('품목 금액 불일치 시 경고 및 신뢰도 하향', () => {
    const parsed_order = {
      metadata: { order_date: '2025-10-15', supplier: 'Test', receiver: 'Test' },
      line_items: [
        { product_name: '아크릴 5T', quantity: 10, unit_price: 5000, total_price: 60000 },  // 불일치
      ],
    };

    const result = validator.validate(parsed_order);

    expect(result.confidence).toBeLessThan(1.0);
    expect(result.warnings).toContain('품목 "아크릴 5T" 금액 불일치');
  });

  it('필수 필드 누락 시 신뢰도 0.0', () => {
    const parsed_order = {
      metadata: { supplier: 'Test', receiver: 'Test' },  // order_date 누락
      line_items: [],
    };

    const result = validator.validate(parsed_order);

    expect(result.is_valid).toBe(false);
    expect(result.confidence).toBe(0.0);
    expect(result.errors).toContain('필수 필드 누락: order_date');
  });
});
```

**예상 결과**: ❌ 모든 테스트 실패 (FieldValidator 미구현)

---

#### 1.3 OrderParserService 통합 테스트 (우선순위 3)

**테스트 파일**: `tests/integration/services/order/test_parser_integration.spec.ts`

**테스트 케이스**:
```typescript
import { describe, it, expect } from 'vitest';
import { OrderParserService } from '@/services/order/parser/order-parser-service';

describe('OrderParserService Integration', () => {
  const parser = new OrderParserService();

  it('정규식 모드로 정상 파싱 (신뢰도 ≥ 0.7)', async () => {
    const ocr_result = {
      text: `
        발주일자: 2025-10-15
        공급사: 아크릴 공업사
        수령지: 서울시 강남구

        아크릴 5T 투명 10개 50,000원
        아크릴 3T 백색 5개 30,000원
      `,
      confidence: 0.95,
      bboxes: [],
    };

    const result = await parser.parse(ocr_result);

    expect(result.parser_used).toBe('regex');
    expect(result.confidence).toBeGreaterThanOrEqual(0.9);
    expect(result.line_items).toHaveLength(2);
  });

  it('정규식 실패 시 LLM 백업 파서 전환', async () => {
    const ocr_result = {
      text: `
        복잡한 발주서 형식
        날짜는 10월 15일이고
        아크릴 판 10개를 주문합니다
      `,
      confidence: 0.8,
      bboxes: [],
    };

    const result = await parser.parse(ocr_result);

    expect(result.parser_used).toBe('llm');
    expect(result.confidence).toBeGreaterThanOrEqual(0.7);
  });

  it('LLM 강제 사용 옵션', async () => {
    const ocr_result = {
      text: `발주일자: 2025-10-15\n공급사: Test`,
      confidence: 0.95,
      bboxes: [],
    };

    const result = await parser.parse(ocr_result, { force_llm: true });

    expect(result.parser_used).toBe('llm');
  });
});
```

**예상 결과**: ❌ 모든 테스트 실패 (OrderParserService 미구현)

---

### Phase 2: GREEN 단계 - 최소 기능 구현

**목표**: 테스트를 통과시키는 최소한의 구현

#### 2.1 RegexExtractor 구현

**파일**: `src/services/order/parser/regex-extractor.ts`

**구현 우선순위**:
1. **메타데이터 추출** (1일)
   - 정규식 패턴 정의 (order_date, supplier, receiver)
   - 신뢰도 계산 로직

2. **품목 목록 추출** (1일)
   - 품목 패턴 정의 (product_name, quantity, unit_price)
   - 여러 품목 처리 (multi-line)

3. **날짜 정규화** (0.5일)
   - 다양한 날짜 형식 지원 (-, ., /)

**구현 스니펫**:
```typescript
export class RegexExtractor {
  private readonly PATTERNS = {
    order_date: /발주일자[:\s]*(\d{4}[-./]\d{2}[-./]\d{2})/,
    supplier: /공급사[:\s]*([^\n]+)/,
    receiver: /수령지[:\s]*([^\n]+)/,
    line_item: /^(.+?)\s+(\d+)개?\s+([\d,]+)원/gm,
  };

  extract_metadata(text: string): MetadataResult {
    const matches = {
      order_date: text.match(this.PATTERNS.order_date)?.[1],
      supplier: text.match(this.PATTERNS.supplier)?.[1],
      receiver: text.match(this.PATTERNS.receiver)?.[1],
    };

    const extracted_count = Object.values(matches).filter(Boolean).length;
    const confidence = extracted_count / 3;

    return {
      ...matches,
      confidence,
      errors: this.get_missing_fields(matches),
    };
  }

  // ... (나머지 구현)
}
```

**완료 기준**:
- ✅ RegexExtractor 테스트 90% 이상 통과

---

#### 2.2 FieldValidator 구현

**파일**: `src/services/order/parser/field-validator.ts`

**구현 우선순위**:
1. **Zod 스키마 검증** (1일)
   - 필수 필드 검증
   - 타입 검증 (string, number, Date)

2. **교차 검증** (1일)
   - 품목 금액 일치 여부 (quantity * unit_price = total_price)
   - 신뢰도 조정 로직

**구현 스니펫**:
```typescript
import { z } from 'zod';

export class FieldValidator {
  private readonly schema = z.object({
    metadata: z.object({
      order_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      supplier: z.string().min(2),
      receiver: z.string().min(2),
    }),
    line_items: z.array(
      z.object({
        product_name: z.string().min(1),
        quantity: z.number().int().positive(),
        unit_price: z.number().positive(),
        total_price: z.number().positive(),
      })
    ),
  });

  validate(parsed_order: any): ValidationResult {
    // Zod 검증
    const validation = this.schema.safeParse(parsed_order);

    if (!validation.success) {
      return {
        is_valid: false,
        confidence: 0.0,
        errors: validation.error.errors.map(e => e.message),
      };
    }

    // 교차 검증
    const warnings = this.cross_validate(parsed_order);
    const confidence = 1.0 * Math.pow(0.9, warnings.length);

    return {
      is_valid: true,
      confidence,
      warnings,
    };
  }

  // ... (나머지 구현)
}
```

**완료 기준**:
- ✅ FieldValidator 테스트 100% 통과

---

#### 2.3 LLMExtractor 구현 (Mock)

**파일**: `src/services/order/parser/llm-extractor.ts`

**구현 우선순위**:
1. **LLM API 클라이언트** (1일)
   - OpenAI GPT-4 Turbo 호출
   - 프롬프트 템플릿 정의

2. **JSON 파싱 및 검증** (1일)
   - LLM 응답을 ParsedOrder로 변환
   - Zod 스키마 검증

**구현 스니펫**:
```typescript
import axios from 'axios';

export class LLMExtractor {
  private readonly api_key = process.env.OPENAI_API_KEY;
  private readonly model = 'gpt-4-turbo';

  async extract(ocr_text: string): Promise<ParsedOrder> {
    const prompt = this.build_prompt(ocr_text);

    const response = await axios.post(
      'https://api.openai.com/v1/chat/completions',
      {
        model: this.model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 2000,
        temperature: 0.3,
      },
      {
        headers: { Authorization: `Bearer ${this.api_key}` },
        timeout: 30000,
      }
    );

    const json_text = response.data.choices[0].message.content;
    const parsed_order = JSON.parse(json_text);

    return {
      ...parsed_order,
      confidence: 0.95,
      parser_used: 'llm',
    };
  }

  private build_prompt(ocr_text: string): string {
    return `
당신은 한국어 발주서 파싱 전문가입니다.
다음 OCR 텍스트에서 JSON 형식으로 발주서 데이터를 추출하세요.

OCR 텍스트:
${ocr_text}

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
    `.trim();
  }
}
```

**완료 기준**:
- ✅ LLMExtractor 테스트 80% 이상 통과 (Mock API 사용)

---

#### 2.4 OrderParserService 구현

**파일**: `src/services/order/parser/order-parser-service.ts`

**구현 우선순위**:
1. **2단계 파싱 전략** (2일)
   - RegexExtractor → LLMExtractor 자동 전환
   - 신뢰도 임계값 처리 (0.7)

2. **옵션 처리** (1일)
   - force_llm: LLM 강제 사용
   - enable_normalization: 품목명 표준화

**구현 스니펫**:
```typescript
export class OrderParserService {
  constructor(
    private readonly regex_extractor = new RegexExtractor(),
    private readonly llm_extractor = new LLMExtractor(),
    private readonly field_validator = new FieldValidator(),
    private readonly normalization_service = new NormalizationService()
  ) {}

  async parse(
    ocr_result: OCRResult,
    options?: ParseOrderOptions
  ): Promise<ParsedOrder> {
    let parsed_order: ParsedOrder;

    // Phase 1: 정규식 파싱
    if (!options?.force_llm) {
      const regex_result = this.regex_extractor.extract(ocr_result.text);

      if (regex_result.confidence >= 0.7) {
        parsed_order = regex_result;
        parsed_order.parser_used = 'regex';
      }
    }

    // Phase 2: LLM 백업 파싱
    if (!parsed_order || options?.force_llm) {
      parsed_order = await this.llm_extractor.extract(ocr_result.text);
      parsed_order.parser_used = 'llm';
    }

    // 검증
    const validation = this.field_validator.validate(parsed_order);
    parsed_order.confidence = validation.confidence;
    parsed_order.errors = validation.errors;
    parsed_order.warnings = validation.warnings;

    // 품목명 표준화 (선택)
    if (options?.enable_normalization) {
      parsed_order = this.normalization_service.normalize(parsed_order);
    }

    return parsed_order;
  }
}
```

**완료 기준**:
- ✅ OrderParserService 통합 테스트 90% 이상 통과

---

### Phase 3: REFACTOR 단계 - 고도화

**목표**: 코드 품질 개선 및 성능 최적화

#### 3.1 성능 최적화

**작업 항목**:
1. **정규식 컴파일 캐싱** (0.5일)
   - RegexExtractor 생성자에서 정규식 미리 컴파일
   - 성능 향상: 20~30%

2. **LLM 응답 캐싱** (1일)
   - 동일 OCR 텍스트에 대한 LLM 응답 캐싱 (Redis)
   - 비용 절감: 50% 이상

3. **품목명 표준화 인덱싱** (1일)
   - N-gram 유사도 계산 시 인덱스 활용
   - 성능 향상: 10배 이상

**완료 기준**:
- ✅ p95 latency < 2초 (정규식 모드)
- ✅ p95 latency < 5초 (LLM 모드)

---

#### 3.2 에러 처리 강화

**작업 항목**:
1. **타임아웃 처리** (0.5일)
   - LLM API 타임아웃: 30초
   - 전체 파싱 타임아웃: 5초

2. **재시도 로직** (0.5일)
   - LLM API 실패 시 1회 재시도
   - Exponential backoff: 1초, 2초

3. **상세 에러 메시지** (0.5일)
   - 에러 타입 명확화 (PARSING_FAILED, TIMEOUT, VALIDATION_ERROR)
   - 디버깅 정보 포함 (원본 텍스트, 중간 결과)

**완료 기준**:
- ✅ 에러 처리 테스트 100% 통과

---

#### 3.3 코드 품질 개선

**작업 항목**:
1. **타입 안정성 강화** (1일)
   - 모든 함수에 명시적 타입 정의
   - `any` 타입 제거

2. **단위 테스트 커버리지** (1일)
   - 목표: 90% 이상
   - Edge case 테스트 추가

3. **린터 규칙 준수** (0.5일)
   - ESLint + Prettier
   - 순환 의존성 제거

**완료 기준**:
- ✅ ESLint 경고 0개
- ✅ 테스트 커버리지 ≥ 90%

---

## 마일스톤

### 1차 목표: 정규식 파서 완성
- **내용**: RegexExtractor + FieldValidator + OrderParserService (정규식 모드만)
- **검증**: 정규식 모드 테스트 90% 통과
- **산출물**: 정규식 기반 파서 프로토타입

### 2차 목표: LLM 백업 파서 통합
- **내용**: LLMExtractor + 2단계 파싱 전략
- **검증**: 통합 테스트 90% 통과
- **산출물**: 완전한 발주서 파서 시스템

### 최종 목표: 고도화 및 최적화
- **내용**: 성능 최적화, 에러 처리 강화, 품목명 표준화
- **검증**: 성능 목표 달성 (p95 < 2초/5초), 테스트 커버리지 ≥ 90%
- **산출물**: 프로덕션 준비 완료 파서

---

## 예상 리소스

### 개발자
- **Backend 개발자**: 1명 (TypeScript 경험자)
- **ML 엔지니어**: 0.5명 (LLM 프롬프트 최적화, 파트타임)

### 인프라
- **OpenAI API**: GPT-4 Turbo (월 100,000 토큰 예상)
- **Redis**: 캐싱용 (선택 사항)

### 테스트 데이터
- **발주서 샘플**: 50개 이상 (다양한 형식)
- **OCR 결과**: SPEC-OCR-CASCADE-001에서 제공

---

## 리스크 및 대응

### 리스크 1: LLM API 비용 초과
- **확률**: 중간
- **영향**: 높음
- **대응**: 정규식 패턴 확장으로 LLM 전환율 10% 이하 유지 + 캐싱 활용

### 리스크 2: 발주서 형식 다양성
- **확률**: 높음
- **영향**: 중간
- **대응**: LLM 백업 파서로 자동 대응 + 주간 패턴 리뷰

### 리스크 3: 성능 목표 미달
- **확률**: 낮음
- **영향**: 중간
- **대응**: 정규식 캐싱, LLM 응답 캐싱, 병렬 처리 도입

---

## 다음 단계

1. **Phase 1 완료 후**: `/alfred:2-build SPEC-ORDER-PARSER-001` 실행하여 TDD 구현 시작
2. **Phase 2 완료 후**: 통합 테스트 및 성능 벤치마크
3. **Phase 3 완료 후**: 프로덕션 배포 준비 (SPEC-OCR-CASCADE-001과 통합)

---

_이 계획은 TDD 방식으로 진행되며, 각 단계에서 테스트 통과를 우선합니다._
