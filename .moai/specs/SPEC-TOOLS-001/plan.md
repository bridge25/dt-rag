# SPEC-TOOLS-001 구현 계획

## 마일스톤

### Phase 2B.1: 도구 레지스트리 및 Tool 클래스 구현
**우선순위**: High

**구현 내용**:
- Tool 클래스 (Pydantic BaseModel)
  - name, description, input_schema, execute() 메서드
- ToolRegistry 클래스
  - register(), get_tool(), list_tools() 메서드
- 전역 레지스트리 인스턴스 및 get_tool_registry() 함수

**결과물**:
- `apps/orchestration/src/tool_registry.py` (약 100 LOC)
- 단위 테스트: test_tool_registry.py (7개 테스트)

---

### Phase 2B.2: 화이트리스트 정책 및 검증 로직
**우선순위**: High

**구현 내용**:
- get_tool_whitelist() 함수 (환경 변수 TOOL_WHITELIST 읽기)
- validate_tool() 함수 (화이트리스트 검증)
- 개발 모드 지원 (whitelist 미설정 시 모든 도구 허용)

**결과물**:
- `apps/orchestration/src/tool_executor.py` (일부, 약 30 LOC)
- 단위 테스트: test_tool_whitelist.py (5개 테스트)

---

### Phase 2B.3: 도구 실행 파이프라인 (타임아웃, 에러 처리)
**우선순위**: High

**구현 내용**:
- ToolExecutionResult 클래스
- execute_tool() 함수
  - JSON Schema 검증 (jsonschema 라이브러리)
  - asyncio.wait_for() 타임아웃 처리 (30초)
  - 예외 처리 (ValidationError, TimeoutError, Exception)

**결과물**:
- `apps/orchestration/src/tool_executor.py` (완성, 약 80 LOC)
- 단위 테스트: test_tool_executor.py (8개 테스트)

---

### Phase 2B.4: LangGraph step4 통합
**우선순위**: High

**구현 내용**:
- step4_tools_debate() 실제 구현
  - mcp_tools flag 확인
  - Meta-Planner의 plan.tools 활용
  - 화이트리스트 검증 (tools_policy flag 확인)
  - 도구 실행 및 결과 state 저장
- PipelineState.tool_results 필드 추가

**결과물**:
- `apps/orchestration/src/langgraph_pipeline.py` (수정, 약 50 LOC 추가)
- 통합 테스트: test_step4_tools.py (3개 테스트)

---

### Phase 2B.5: 기본 도구 구현 (web_search, doc_parser, calculator)
**우선순위**: Medium

**구현 내용**:
- web_search 도구 (stub, 실제 API 연동은 향후)
- doc_parser 도구 (stub)
- calculator 도구 (간단한 수식 평가)
- 각 도구의 input_schema 정의

**결과물**:
- `apps/orchestration/src/tools/web_search.py` (신규, stub)
- `apps/orchestration/src/tools/doc_parser.py` (신규, stub)
- `apps/orchestration/src/tools/calculator.py` (신규, 실제 구현)
- 단위 테스트: test_builtin_tools.py (3개 테스트)

---

## 기술적 접근 방법

### Pydantic BaseModel 활용
- Tool, ToolSchema, ToolExecutionResult 모두 Pydantic 모델로 정의
- 자동 검증 및 타입 안전성 확보

### JSON Schema 검증
- jsonschema 라이브러리 사용
- 도구 입력 검증 (execute_tool에서 수행)

### asyncio 타임아웃 처리
- asyncio.wait_for(timeout=30.0) 사용
- 타임아웃 시 TimeoutError 발생 → ToolExecutionResult로 변환

### 도구 모듈 구조
```
apps/orchestration/src/
├── tool_registry.py      # 레지스트리 및 Tool 클래스
├── tool_executor.py      # 실행 파이프라인 및 화이트리스트
└── tools/                # 기본 도구 (향후 확장)
    ├── __init__.py
    ├── web_search.py
    ├── doc_parser.py
    └── calculator.py
```

### 의존성 추가
- `jsonschema` 라이브러리 (requirements.txt 추가)

---

## 리스크 및 대응 방안

### 리스크 1: 외부 API 의존성
**영향**: 도구 실행 실패 시 전체 파이프라인 실패 가능성

**대응**:
- Mock 처리 및 Stub 구현 (Phase 2B.5)
- Fallback 전략 (도구 실패 시 부분 결과 반환)
- 타임아웃 강제 적용 (30초)

### 리스크 2: 타임아웃 관리
**영향**: 도구별 실행 시간 차이로 인한 타임아웃 미스매치

**대응**:
- 도구별 타임아웃 설정 가능하도록 확장 (향후)
- 현재는 일괄 30초 적용

### 리스크 3: 보안 위험
**영향**: 악의적인 도구 입력으로 인한 시스템 손상

**대응**:
- 화이트리스트 정책 강제 (tools_policy flag)
- JSON Schema 검증
- 입력 크기 제한 (향후 추가)

### 리스크 4: 화이트리스트 미설정
**영향**: 의도하지 않은 도구 실행 허용

**대응**:
- 개발 모드에서만 허용 (환경별 설정 가이드)
- 프로덕션 환경에서는 반드시 TOOL_WHITELIST 설정 요구

---

## 테스트 전략

### 단위 테스트 (15개)
- test_tool_registry.py: 7개 (레지스트리 기본 동작)
- test_tool_whitelist.py: 5개 (화이트리스트 검증)
- test_tool_executor.py: 8개 (실행 파이프라인)
- test_builtin_tools.py: 3개 (기본 도구)

### 통합 테스트 (5개)
- test_step4_tools.py: 3개 (step4 통합)
- test_tool_execution.py: 2개 (end-to-end 도구 실행)

### 목표 커버리지
- 신규 코드: 100%
- 전체 프로젝트: 기존 대비 유지

---

## 의존성 및 선후 관계

### 필수 선행 작업
- ✅ SPEC-FOUNDATION-001 완료 (mcp_tools, tools_policy flags)
- ✅ SPEC-PLANNER-001 완료 (plan.tools 출력)

### 차단하는 작업
- 없음 (Phase 3 Debate 모드와는 독립적)

### 관련 작업
- SPEC-ORCHESTRATION-001: LangGraph 파이프라인 전체 구조
- SPEC-API-001: API 엔드포인트와의 통합

---

## 완료 조건 (Definition of Done)

### 코드
- [ ] tool_registry.py 구현 완료 (100 LOC)
- [ ] tool_executor.py 구현 완료 (110 LOC)
- [ ] langgraph_pipeline.py step4 실제 구현 (50 LOC)
- [ ] 기본 도구 3개 구현 (stub 포함)

### 테스트
- [ ] 20개 테스트 작성 (단위 15개 + 통합 5개)
- [ ] 모든 테스트 통과 (100%)
- [ ] 신규 코드 커버리지 100%

### 문서
- [ ] README.md에 도구 등록 및 사용 가이드 추가
- [ ] 환경 변수 TOOL_WHITELIST 설정 가이드

### 검증
- [ ] Linter 통과 (ruff, mypy)
- [ ] 보안 검증 (bandit)
- [ ] Feature Flag 동작 확인 (mcp_tools, tools_policy ON/OFF)

### 다음 단계
- [ ] Phase 3 Debate 모드 구현 (SPEC-DEBATE-001)
- [ ] 실제 외부 도구 API 연동 (web_search, doc_parser)
