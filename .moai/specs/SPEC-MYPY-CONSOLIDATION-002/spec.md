---
id: MYPY-CONSOLIDATION-002
version: 0.1.0
status: draft
created: 2025-10-28
updated: 2025-10-28
author: @sonheungmin
priority: critical
category: refactor
labels:
  - mypy
  - type-safety
  - consolidation
  - quality-gate
  - ci-cd
  - python
depends_on: []
blocks: []
related_specs:
  - MYPY-001
  - CICD-001
  - CONSOLIDATION-001
related_issue: null
scope:
  packages:
    - apps/
    - tests/
  files:
    - pyproject.toml
    - .github/workflows/ci.yml
---

# @SPEC:MYPY-CONSOLIDATION-002: MyPy Strict Mode Resolution - Post-Consolidation Phase

## HISTORY

### v0.10.0 (2025-11-05) - Session 9: Call Arguments & Pydantic Integration Complete
- **SESSION**: Pydantic MyPy plugin integration + [call-arg] error fixes
- **PROGRESS**: 213 → 166 errors (-47, 22.1% reduction), 80.3% → 84.6% complete (+4.3%)
- **RESULTS**:
  - [call-arg] errors fixed: 5 (100% of remaining call-arg errors after plugin)
  - Pydantic plugin integration: 42 errors eliminated instantly
  - Files cleared: 5 files (55 → 50)
  - Files modified: 5 files (3 tests + 2 apps)
- **IMPLEMENTATION**:
  - **CRITICAL**: Added `plugins = ["pydantic.mypy"]` to pyproject.toml (42 error reduction!)
  - Fixed BackgroundTasks.add_task: added db_session parameter to classify_batch call
  - Modernized httpx AsyncClient: `app=app` → `transport=ASGITransport(app=app)` (2 files)
  - Fixed Langfuse client: removed "enabled" parameter, changed base_url → _base_url
  - Fixed RedisManager: redis_url parameter → RedisConfig object initialization
- **TIME**: 30 minutes (0.16 errors/minute with 42 errors from one line!)
- **PATTERN**: Configuration fix > code changes. Proper tool integration eliminates entire error categories.
- **BREAKTHROUGH**: Pydantic plugin is the single biggest impact fix in the entire project!
- **MILESTONE**: 84%+ completion - approaching 90% threshold!
- **NEXT**: Session 10 - Remaining error types: [attr-defined], [assignment], [arg-type] (~166 errors)

### v0.9.0 (2025-11-05) - Session 8: Optional/None Handling Complete
- **SESSION**: Optional type handling - Systematic None guards for all [union-attr] errors
- **PROGRESS**: 253 → 213 errors (-40, 15.8% reduction), 76.6% → 80.3% complete (+3.7%)
- **RESULTS**:
  - [union-attr] errors fixed: 41 (100% of Optional type errors)
  - Files cleared: 5 files (60 → 55)
  - Files modified: 8 files (6 tests + 2 apps)
- **IMPLEMENTATION**:
  - Added `assert obj is not None` before Optional[T] attribute access
  - Fixed test_agent_background_tasks.py (17 BackgroundTask checks)
  - Fixed test_agent_dao_xp.py (7 Agent checks)
  - Fixed test_tool_executor.py (4 error message checks)
  - Fixed test_agent_xp_integration.py (5 Agent checks)
  - Fixed test_agent_api_phase3.py (4 BackgroundTask checks)
  - Fixed apps files (4 Address/str checks)
- **TIME**: 45 minutes (0.9 errors/minute, moderate speed)
- **PATTERN**: Consistent None guard pattern across all Optional types
- **MILESTONE**: 80%+ completion - only 213 errors remaining!
- **NEXT**: Session 9 - [call-arg] errors (~45 errors) - function signature mismatches

### v0.8.0 (2025-11-05) - Session 7: Object Indexing in tests/ Complete
- **SESSION**: Object indexing fixes - Type annotations for nested dict/list structures
- **PROGRESS**: 283 → 253 errors (-30, 10.6% reduction), 73.8% → 76.6% complete (+2.8%)
- **RESULTS**:
  - [index] errors fixed: 30 (100% of tests/ indexing errors)
  - Files cleared: 3 files (63 → 60)
  - Files modified: 4 test files
- **IMPLEMENTATION**:
  - Added `List[Dict[str, Any]]` type annotations to test data structures
  - Fixed test_ingestion_metrics.py (19 errors), test_complete_workflow.py (5 errors)
  - Fixed test_user_scenarios.py (4 errors), test_caching_system_integration.py (2 errors)
  - Leveraged MyPy's top-down type inference for loop variables
- **TIME**: 20 minutes (fastest session, 1.5 errors/minute)
- **PATTERN**: Container type annotation → automatic nested element inference
- **NEXT**: Session 8 - [union-attr] errors (~41 errors) or [call-arg] errors (~45 errors)

### v0.7.0 (2025-11-05) - Session 6: Row[Any] Type Hints Complete
- **SESSION**: Row[Any] type annotations - Explicit SQLAlchemy Row type hints
- **PROGRESS**: 285 → 283 errors (-2, 0.7% reduction), 73.6% → 73.8% complete (+0.2%)
- **RESULTS**:
  - Row[Any] errors fixed: 2 (100% of Row[Any] errors)
  - Files cleared: 1 file (64 → 63)
  - Files modified: 2 monitoring files
- **IMPLEMENTATION**:
  - Added `from sqlalchemy import Row` imports
  - Added explicit type annotations: `query_row: Optional[Row[Any]]`
  - Fixed async/sync confusion (removed incorrect `await` from fetchone())
  - Resolved variable name conflict in performance_monitor.py
- **TIME**: 30 minutes (2 manual fixes)
- **DISCOVERY**: Only 2 Row[Any] errors found (estimated 17 was incorrect)
- **NEXT**: Session 7 - Object indexing in tests/ (~10 errors) or arg-type errors

### v0.6.0 (2025-11-05) - Session 5: Object Indexing Fixes Complete
- **SESSION**: Object indexing fixes - None guards for SQLAlchemy row access
- **PROGRESS**: 300 → 285 errors (-15, 5.0% reduction), 72.2% → 73.6% complete (+1.4%)
- **RESULTS**:
  - [index] errors fixed: 15 (100% of apps/ indexing errors)
  - Files cleared: 3 files (67 → 64)
  - Files modified: 3 apps/ files (core business logic)
- **IMPLEMENTATION**:
  - Added `if row is not None` checks before SQLAlchemy row indexing
  - Proper fallback dictionaries for None cases
  - Improved error handling in hitl_queue.py, dashboard.py, evaluation_router.py
- **TIME**: 45 minutes (manual fixes with careful testing)
- **NEXT**: Session 6 - Optional/None handling (~40 errors) or remaining error types

### v0.5.0 (2025-11-05) - Session 4: Manual Quick Wins Complete
- **SESSION**: Manual Quick Wins - removal of all unused type:ignore comments
- **PROGRESS**: 375 → 300 errors (-75, 20.0% reduction), 65.3% → 72.2% complete (+6.9%)
- **RESULTS**:
  - Unused type:ignore removed: 75 comments (100% success rate)
  - Files cleared: 4 files (71 → 67)
  - Files modified: 10 apps/ files (core business logic quality improved)
- **AUTOMATION**:
  - Created `remove_unused_type_ignore_v3.py` (enhanced from Session 2 v2 script)
  - Pattern recognition: inline, standalone, trailing type:ignore comments
  - Verification: 0 new errors introduced, MyPy confirms all removals safe
- **TIME**: 30 minutes (highly efficient automation)
- **NEXT**: Session 5 - Object indexing fixes (15 errors in apps/) or Optional/None handling (40 errors)

### v0.4.0 (2025-11-05) - Session 3: Return Type Annotations Complete
- **SESSION**: Return type annotations - systematic addition to all test functions
- **PROGRESS**: 458 → 375 errors (-83, 18.1% reduction), 57.6% → 65.3% complete (+7.7%)
- **RESULTS**:
  - Return type annotations added: 91 functions (all no-untyped-def errors resolved)
  - Automated: 77 single-line functions (77/91, 84.6% success rate)
  - Manual: 14 multi-line function signatures (100% success rate)
  - Files cleared: 6 files (77 → 71)
- **AUTOMATION**:
  - Created `add_return_types.py` (handles both `def` and `async def` patterns)
  - Pattern recognition: simple, trailing comment, multi-line signatures
  - Verification: 0 remaining no-untyped-def errors confirmed by MyPy
- **TIME**: 1 hour (automation + manual review pattern highly efficient)
- **NEXT**: Session 4 - Manual Quick Wins (75 decorator-line type:ignore) or Object indexing fixes (15 errors in apps/)

### v0.3.0 (2025-11-05) - Session 2: Quick Wins (Phase 0 Partial)
- **SESSION**: Quick Wins execution - automated cleanup of low-hanging fruit
- **PROGRESS**: 590 → 458 errors (-132, 22.4% reduction), 45.4% → 57.6% complete (+12.2%)
- **RESULTS**:
  - Unused type:ignore removed: 108 errors (75 skipped for safety - decorator lines)
  - Union syntax fixed: 24 errors (X | Y → Optional[X] in 4 test files)
  - Files cleared: 11 files (88 → 77)
- **AUTOMATION**:
  - Created `remove_unused_type_ignore_v2.py` (safe trailing comment removal)
  - Created `fix_union_syntax.py` (Python 3.10 union syntax converter)
  - Both scripts verified: no syntax errors, reversible changes
- **TIME**: 1 hour (exceeded timeline: completed in 1 hour vs estimated 1-2 days)
- **NEXT**: Session 3 - Return Type Annotations (91 errors) or manual review of 75 decorator-line type:ignore

### v0.2.0 (2025-11-05) - Session 1: Planning & Preparation
- **SESSION**: Preparation complete for systematic MyPy error resolution
- **PROGRESS**: Baseline established: 590 errors in 88 files (1,079 → 590, 45.4% complete)
- **DELIVERABLES**:
  - Created `progress.md` tracking document (file priority list, session log)
  - Created `mypy-progress.sh` automation script (error tracking, reporting)
  - Analyzed error distribution: 183 unused type:ignore, 91 missing return types, 40 Optional/None issues
  - Identified Quick Wins: 207 errors removable in 1 session
- **STRATEGY UPDATED**:
  - Phase 0: Quick Wins (183 unused type:ignore + 24 union syntax) - 1-2 days
  - Phase 1: Return Type Annotations (91 errors) - 2-3 days
  - Phase 2-4: Optional/Object/SearchConfig issues - 3-4 days each
  - Daily file-by-file commits with progress tracking
- **NEXT**: Session 2 - Remove 183 unused type:ignore comments (expected: 590 → 407 errors)

### v0.1.0 (2025-10-28)
- **INITIAL**: MyPy strict mode resolution SPEC 작성 (post-codebase consolidation)
- **AUTHOR**: @sonheungmin
- **CONTEXT**: 42-branch consolidation 완료 후 1,079 MyPy 오류 발견
- **SCOPE**: 83 Python files, 5-Phase systematic approach
- **STRATEGY**: SQLAlchemy type casting → Critical errors → Type annotations → Pattern fixes → Import cleanup
- **GOAL**: MyPy strict mode compliance (1,079 → 0 errors) + CI/CD integration

---

## Overview

본 SPEC은 코드베이스 통합(v2.0.0) 완료 후 발견된 1,079개의 MyPy strict mode 오류를 체계적으로 해결하는 전략을 정의한다. 83개 Python 파일에 걸친 타입 안전성 문제를 5단계 전략으로 해결하여 CI/CD 파이프라인에서 MyPy strict mode를 품질 게이트로 통합한다.

### Problem Statement

**현재 상태**:
- 1,079개 MyPy strict mode 오류 (83 files)
- CI/CD에서 MyPy가 `continue-on-error: true`로 우회됨
- 타입 안전성 보장 없음

**목표 상태**:
- MyPy strict mode 완전 준수 (0 errors)
- CI/CD 품질 게이트 통합 (`continue-on-error: false`)
- 모든 함수/메서드에 명시적 타입 힌트

### Error Distribution

```
Total: 1,079 errors across 83 files

Phase 1 - SQLAlchemy Casting: 81 errors
  - assignment [incompatible types]

Phase 2 - Critical Errors: 163 errors
  - call-arg [argument type mismatch] (87)
  - attr-defined [undefined attribute] (76)

Phase 3 - Type Annotations: 464 errors
  - no-untyped-def [missing type hints] (464)

Phase 4 - Pattern Fixes: 105 errors
  - union-attr [union attribute access] (75)
  - no-any-return [Any return type] (30)

Phase 5 - Import & Misc: 266 errors
  - import-not-found (128)
  - import-untyped (98)
  - misc errors (40)
```

---

## Environment

### System Requirements

WHEN 이 SPEC이 실행되면, 시스템은 다음 환경을 제공해야 한다:

- Python 3.12+ 런타임
- MyPy 1.13.0+ 설치
- SQLAlchemy 2.0+ (ORM 타입 지원)
- pyproject.toml에 MyPy strict mode 설정
- CI/CD 환경 (GitHub Actions)

### Configuration

시스템은 다음 MyPy 설정을 적용해야 한다:

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict = true
```

### Tools

- **MyPy**: 타입 검사 엔진
- **libCST** (optional): Python 소스 코드 자동 리팩토링
- **rope** (optional): 코드 탐색 및 리팩토링 지원
- **rg (ripgrep)**: 오류 패턴 검색

---

## Assumptions

본 SPEC은 다음을 가정한다:

1. **코드베이스 안정성**: v2.0.0 통합 완료, 모든 테스트 통과
2. **런타임 동작 불변**: 타입 힌트 추가는 런타임 동작에 영향을 주지 않음
3. **점진적 수정**: Phase별 독립적 수정 가능
4. **테스트 커버리지**: 기존 테스트 85%+ 커버리지 유지
5. **SQLAlchemy 2.0**: 최신 SQLAlchemy ORM 타입 지원 사용 가능

---

## Requirements

### Ubiquitous Requirements (기본 요구사항)

시스템은 다음을 제공해야 한다:

- **R1**: 모든 함수/메서드에 명시적 타입 힌트
- **R2**: MyPy strict mode 완전 준수 (0 errors)
- **R3**: CI/CD 파이프라인에서 MyPy 품질 게이트 통합
- **R4**: 모든 SQLAlchemy 모델에 타입 안전 Column 정의
- **R5**: 타입 무시 주석(`# type: ignore`)에 정당화 사유 필수

### Event-driven Requirements (이벤트 기반)

- **E1**: WHEN Phase가 완료되면, 해당 Phase의 타겟 오류는 0이어야 한다
- **E2**: WHEN MyPy가 실행되면, exit code 0을 반환해야 한다
- **E3**: WHEN CI/CD에서 MyPy 실패 시, 빌드는 실패해야 한다 (`continue-on-error: false`)
- **E4**: WHEN 타입 변경이 커밋되면, 모든 테스트가 통과해야 한다
- **E5**: WHEN `# type: ignore` 추가 시, 주석에 justification이 포함되어야 한다

### State-driven Requirements (상태 기반)

- **S1**: WHILE Phase가 진행 중일 때, 오류 감소 추적이 제공되어야 한다
- **S2**: WHILE 타입 변경이 적용 중일 때, 기존 테스트는 계속 통과해야 한다
- **S3**: WHILE SQLAlchemy 모델 수정 중일 때, 데이터베이스 스키마는 불변이어야 한다

### Optional Features (선택적 기능)

- **O1**: WHERE libCST가 사용 가능하면, 자동화된 리팩토링을 사용할 수 있다
- **O2**: WHERE rope가 사용 가능하면, 타입 추론을 지원할 수 있다
- **O3**: WHERE 복잡한 제네릭 타입이 필요하면, TypeVar를 사용할 수 있다

### Constraints (제약사항)

- **C1**: IF 타입 변경이 적용되면, 런타임 동작은 100% 보존되어야 한다
- **C2**: IF `# type: ignore` 사용 시, 주석에 이유가 명시되어야 한다
- **C3**: IF SQLAlchemy Column 수정 시, Alembic 마이그레이션은 생성되지 않아야 한다
- **C4**: IF 테스트가 실패하면, 타입 변경은 롤백되어야 한다
- **C5**: 각 Phase는 독립적으로 완료 가능해야 한다

---

## Specifications

### 5-Phase Resolution Strategy

#### Phase 1: SQLAlchemy Column Type Casting (81 errors → 0)

**목표**: SQLAlchemy Column 정의에 명시적 타입 캐스팅 추가

**패턴**:
```python
# Before
id = Column(Integer, primary_key=True)
name = Column(String(255), nullable=False)

# After
id: Mapped[int] = mapped_column(Integer, primary_key=True)
name: Mapped[str] = mapped_column(String(255), nullable=False)
```

**전략**:
- `Mapped[]` 제네릭 타입 사용
- `mapped_column()` 함수로 전환
- nullable 명시적 처리 (`Mapped[Optional[str]]`)

**검증**:
```bash
rg "assignment.*\[incompatible types\]" --type python
```

#### Phase 2: Critical Type Errors (163 errors → 0)

**목표**: 함수 호출 인자 불일치 및 undefined attribute 해결

**call-arg (87 errors)**:
```python
# Before
def process(data: dict) -> None:
    result = transform(data["items"])  # error: Expected str

# After
def process(data: dict[str, Any]) -> None:
    items: list[Item] = data["items"]
    result = transform(items)
```

**attr-defined (76 errors)**:
```python
# Before
result = obj.field  # error: "Base" has no attribute "field"

# After
if hasattr(obj, "field"):
    result = obj.field
# OR
result = cast(Derived, obj).field
```

**검증**:
```bash
rg "(call-arg|attr-defined)" --type python
```

#### Phase 3: Type Annotations (464 errors → 0)

**목표**: 모든 함수/메서드에 타입 힌트 추가

**패턴**:
```python
# Before
def calculate(x, y):
    return x + y

# After
def calculate(x: float, y: float) -> float:
    return x + y
```

**전략**:
- 함수 시그니처 스캔
- 반환 타입 추론
- 제네릭 타입 적용 (list, dict, Optional, Union)

**자동화 (optional)**:
```bash
libcst-tool codemod add_type_hints.py apps/
```

**검증**:
```bash
rg "no-untyped-def" --type python
```

#### Phase 4: Pattern Fixes (105 errors → 0)

**목표**: Union 타입 속성 접근 및 Any 반환 타입 제거

**union-attr (75 errors)**:
```python
# Before
def process(value: str | int) -> str:
    return value.upper()  # error: int has no attribute upper

# After
def process(value: str | int) -> str:
    if isinstance(value, str):
        return value.upper()
    return str(value).upper()
```

**no-any-return (30 errors)**:
```python
# Before
def get_data() -> Any:  # error: Any return type
    return fetch_from_db()

# After
def get_data() -> list[Record]:
    return fetch_from_db()
```

**검증**:
```bash
rg "(union-attr|no-any-return)" --type python
```

#### Phase 5: Import & Misc Cleanup (266 errors → 0)

**목표**: 미해결 import 및 기타 오류 해결

**import-not-found (128 errors)**:
- 누락된 `py.typed` 파일 추가
- stub 파일 생성 (`.pyi`)
- `# type: ignore[import-not-found]` (정당화 필수)

**import-untyped (98 errors)**:
- 타입 힌트 있는 대안 라이브러리 사용
- 로컬 stub 생성
- `# type: ignore[import-untyped]` (정당화 필수)

**misc errors (40 errors)**:
- 케이스별 개별 검토
- 패턴 분석 후 일괄 수정

**검증**:
```bash
mypy --strict apps/ tests/ 2>&1 | tee mypy-report.txt
```

---

## Traceability

### TAG Chain

```
@SPEC:MYPY-CONSOLIDATION-002 (본 문서)
    ↓
@TEST:MYPY-CONSOLIDATION-002 (tests/type_safety/)
    ├─ test_phase1_sqlalchemy_types.py
    ├─ test_phase2_critical_errors.py
    ├─ test_phase3_type_annotations.py
    ├─ test_phase4_pattern_fixes.py
    └─ test_phase5_import_cleanup.py
    ↓
@CODE:MYPY-CONSOLIDATION-002 (apps/)
    ├─ apps/fastapi_app/ (models, routes, services)
    ├─ apps/gradio_app/ (interface, handlers)
    └─ apps/streamlit_app/ (components, utils)
    ↓
@DOC:MYPY-CONSOLIDATION-002 (docs/)
    └─ mypy-strict-mode-guide.md
```

### File Locations

**SPEC**: `.moai/specs/SPEC-MYPY-CONSOLIDATION-002/spec.md`
**PLAN**: `.moai/specs/SPEC-MYPY-CONSOLIDATION-002/plan.md`
**ACCEPTANCE**: `.moai/specs/SPEC-MYPY-CONSOLIDATION-002/acceptance.md`
**TESTS**: `tests/type_safety/test_mypy_*.py`
**CODE**: `apps/**/*.py` (83 files)
**DOCS**: `docs/mypy-strict-mode-guide.md`

### Verification Commands

```bash
# TAG 체인 검증
rg "@(SPEC|TEST|CODE|DOC):MYPY-CONSOLIDATION-002" -n

# 오류 카운트 확인
mypy --strict apps/ tests/ 2>&1 | grep "error:" | wc -l

# Phase별 진행률
rg "assignment.*incompatible" --type python | wc -l  # Phase 1
rg "call-arg|attr-defined" --type python | wc -l     # Phase 2
rg "no-untyped-def" --type python | wc -l            # Phase 3
rg "union-attr|no-any-return" --type python | wc -l  # Phase 4
rg "import-not-found|import-untyped" --type python | wc -l  # Phase 5
```

---

## Success Criteria

1. **Zero MyPy Errors**: `mypy --strict apps/ tests/` exits with code 0
2. **Test Pass Rate**: 100% test pass, 85%+ coverage maintained
3. **CI/CD Integration**: GitHub Actions enforces MyPy strict mode
4. **Documentation**: All `# type: ignore` have justification comments
5. **Performance**: MyPy runtime < 30 seconds for full codebase scan

---

## References

- **MyPy Documentation**: https://mypy.readthedocs.io/
- **SQLAlchemy 2.0 Type Annotations**: https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#orm-declarative-mapped-column
- **PEP 484**: Type Hints
- **PEP 526**: Syntax for Variable Annotations
- **Project CLAUDE.md**: Type safety principles
- **development-guide.md**: TRUST 5원칙

---

**END OF SPEC**
