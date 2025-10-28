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
