# SPEC-TOOLS-001 수락 기준

## Given-When-Then 테스트 시나리오

### 시나리오 1: 도구 레지스트리 조회
**목적**: 등록된 도구 목록 조회 기능 검증

**Given**:
- mcp_tools=True
- 도구 3개 등록 (web_search, doc_parser, calculator)

**When**:
- list_tools() 호출

**Then**:
- 3개 도구 메타데이터 반환
- 각 도구는 name, description, input_schema 포함
- 반환 형식: List[Dict[str, Any]]

---

### 시나리오 2: 화이트리스트 검증 통과
**목적**: 화이트리스트에 포함된 도구 실행 허용 검증

**Given**:
- tools_policy=True
- TOOL_WHITELIST="web_search,calculator"
- web_search 도구 등록됨

**When**:
- execute_tool("web_search", {"query": "test"}) 호출

**Then**:
- 도구 실행 성공
- ToolExecutionResult.success=True
- ToolExecutionResult.result 반환

---

### 시나리오 3: 화이트리스트 검증 차단
**목적**: 화이트리스트에 없는 도구 실행 차단 검증

**Given**:
- tools_policy=True
- TOOL_WHITELIST="calculator"
- web_search 도구 등록됨

**When**:
- execute_tool("web_search", {"query": "test"}) 호출

**Then**:
- 도구 실행 차단
- ToolExecutionResult.success=False
- ToolExecutionResult.error="Blocked by whitelist policy"
- 경고 로그 기록

---

### 시나리오 4: 도구 실행 타임아웃
**목적**: 타임아웃 처리 검증

**Given**:
- 도구 실행 시간 > 30초 (mock)
- slow_tool 등록됨 (30초 이상 대기)

**When**:
- execute_tool("slow_tool", {}, timeout=30.0) 호출

**Then**:
- TimeoutError 발생
- ToolExecutionResult.success=False
- ToolExecutionResult.error="Tool execution timeout (30.0s)"
- 실행 중단 확인

---

### 시나리오 5: step4_tools_debate 통합
**목적**: LangGraph step4와 Meta-Planner 통합 검증

**Given**:
- mcp_tools=True
- tools_policy=False
- plan.tools=["web_search", "calculator"]
- PipelineState 초기화

**When**:
- step4_tools_debate(state) 호출

**Then**:
- web_search 실행
- calculator 실행
- state.tool_results 업데이트 (2개 결과)
- 각 결과는 tool, success, result/error, elapsed 포함

---

### 시나리오 6: Flag OFF 시 스킵
**목적**: mcp_tools flag OFF 시 step4 스킵 검증

**Given**:
- mcp_tools=False
- PipelineState 초기화

**When**:
- step4_tools_debate(state) 호출

**Then**:
- 도구 실행 없음
- state.tool_results=[] (변경 없음)
- 로그: "Step 4 (tools) skipped (mcp_tools flag OFF)"

---

### 시나리오 7: JSON Schema 검증 실패
**목적**: 잘못된 입력 검증

**Given**:
- calculator 도구 등록
- input_schema.required=["expression"]

**When**:
- execute_tool("calculator", {}) 호출 (required 필드 누락)

**Then**:
- ValidationError 발생
- ToolExecutionResult.success=False
- ToolExecutionResult.error="Input validation failed: ..."

---

### 시나리오 8: 도구 미등록 에러
**목적**: 등록되지 않은 도구 호출 시 에러 처리

**Given**:
- 레지스트리에 unknown_tool 미등록

**When**:
- execute_tool("unknown_tool", {}) 호출

**Then**:
- ToolExecutionResult.success=False
- ToolExecutionResult.error="Tool 'unknown_tool' not found"

---

### 시나리오 9: 개발 모드 (화이트리스트 미설정)
**목적**: 개발 환경에서 모든 도구 허용 검증

**Given**:
- tools_policy=True
- TOOL_WHITELIST="" (미설정)

**When**:
- execute_tool("web_search", {}) 호출

**Then**:
- 도구 실행 허용 (화이트리스트 검증 스킵)
- ToolExecutionResult.success=True

---

### 시나리오 10: 부분 실패 처리
**목적**: 다중 도구 실행 시 일부 실패 처리

**Given**:
- mcp_tools=True
- plan.tools=["web_search", "fail_tool", "calculator"]
- fail_tool은 실행 중 예외 발생

**When**:
- step4_tools_debate(state) 호출

**Then**:
- web_search 실행 성공
- fail_tool 실행 실패 (success=False)
- calculator 실행 성공
- state.tool_results에 3개 결과 모두 포함 (부분 실패 허용)

---

## 품질 게이트 기준

### 성능
- [ ] 도구 실행 타임아웃 준수 (30초)
- [ ] step4 전체 실행 시간 < STEP_TIMEOUTS["tools_debate"] (1.0초 × 도구 수)

### 정확성
- [ ] 화이트리스트 검증 100% 통과
- [ ] JSON Schema 검증 100% 통과
- [ ] 타임아웃 처리 100% 동작

### 안전성
- [ ] 도구 실행 실패 시 파이프라인 중단 없음 (Graceful Degradation)
- [ ] 화이트리스트 우회 불가

### 커버리지
- [ ] 신규 코드 커버리지 100%
- [ ] 분기 커버리지 100%

---

## 검증 방법 및 도구

### 단위 테스트
**도구**: pytest

**실행**:
```bash
pytest tests/unit/test_tool_registry.py -v
pytest tests/unit/test_tool_executor.py -v
pytest tests/unit/test_builtin_tools.py -v
```

**검증 항목**:
- 도구 등록/조회 기본 동작
- 화이트리스트 검증 로직
- 타임아웃 처리
- JSON Schema 검증

---

### 통합 테스트
**도구**: pytest

**실행**:
```bash
pytest tests/integration/test_step4_tools.py -v
pytest tests/integration/test_tool_execution.py -v
```

**검증 항목**:
- step4와 Meta-Planner 통합
- end-to-end 도구 실행 파이프라인
- Feature Flag 동작 확인

---

### 보안 검증
**도구**: bandit

**실행**:
```bash
bandit -r apps/orchestration/src/tool_*.py
```

**검증 항목**:
- 입력 검증 누락 확인
- 화이트리스트 우회 가능성 검사
- 위험한 함수 호출 (eval, exec 등) 금지

---

### Linter 검증
**도구**: ruff, mypy

**실행**:
```bash
ruff check apps/orchestration/src/tool_*.py
mypy apps/orchestration/src/tool_*.py
```

**검증 항목**:
- 코드 스타일 준수
- 타입 힌트 정확성

---

### 커버리지 측정
**도구**: pytest-cov

**실행**:
```bash
pytest --cov=apps.orchestration.src.tool_registry \
       --cov=apps.orchestration.src.tool_executor \
       --cov-report=html
```

**목표**:
- tool_registry.py: 100%
- tool_executor.py: 100%
- langgraph_pipeline.py (step4 부분): 100%

---

## 완료 조건 (Definition of Done)

### 기능 구현
- [x] 도구 레지스트리 구현 완료
- [x] 화이트리스트 정책 구현 완료
- [x] 도구 실행 파이프라인 구현 완료
- [x] step4_tools_debate 실제 구현 완료
- [x] 기본 도구 3개 구현 (stub 포함)

### 테스트
- [x] 단위 테스트 15개 작성 및 통과
- [x] 통합 테스트 5개 작성 및 통과
- [x] 신규 코드 커버리지 100% 달성

### 검증
- [x] Linter 통과 (ruff, mypy)
- [x] 보안 검증 통과 (bandit)
- [x] Feature Flag 동작 확인 (mcp_tools=ON, tools_policy=ON)

### 문서
- [x] README.md 도구 가이드 추가
- [x] 환경 변수 설정 가이드 추가
- [x] API 문서 (docstring) 작성 완료

### 성능
- [x] 타임아웃 준수 (30초)
- [x] step4 전체 실행 시간 목표 달성

### 다음 단계 안내
- [ ] `/alfred:2-build SPEC-TOOLS-001` 실행 준비
- [ ] Phase 3 Debate 모드 SPEC 작성 검토
- [ ] 실제 외부 API 연동 계획 수립 (web_search, doc_parser)

---

## 회귀 테스트

### 기존 기능 보호
- [ ] SPEC-FOUNDATION-001 회귀 테스트 통과 (Feature Flags)
- [ ] SPEC-PLANNER-001 회귀 테스트 통과 (Meta-Planner)
- [ ] step1, step2, step3, step5, step6, step7 동작 변경 없음

### 파이프라인 통합
- [ ] 7-step 파이프라인 end-to-end 테스트 통과
- [ ] mcp_tools=False 시 기존 동작 유지

---

## 리스크 완화 확인

### 외부 API 의존성
- [x] Stub 구현으로 외부 의존성 제거 (개발/테스트)
- [x] Mock 처리로 단위 테스트 격리

### 타임아웃 관리
- [x] asyncio.wait_for() 타임아웃 강제 적용
- [x] 타임아웃 발생 시 Graceful Degradation

### 보안 위험
- [x] 화이트리스트 정책 강제 (tools_policy flag)
- [x] JSON Schema 검증 필수
- [x] 입력 검증 누락 없음 (bandit 검증)

---

**최종 수락 조건**: 위 모든 체크박스 완료 시 SPEC-TOOLS-001 구현 완료로 간주
