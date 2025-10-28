# @SPEC:MYPY-CONSOLIDATION-002: Implementation Plan

> **Implementation Strategy**: 5-Phase Systematic Type Safety Resolution
>
> **Goal**: 1,079 MyPy errors → 0 errors + CI/CD integration

---

## Overview

본 문서는 SPEC-MYPY-CONSOLIDATION-002의 구현 계획을 정의한다. 83개 Python 파일에 걸친 1,079개의 MyPy strict mode 오류를 5단계 전략으로 체계적으로 해결한다.

### Implementation Principles

1. **Phase Independence**: 각 Phase는 독립적으로 완료 가능
2. **Error Reduction Tracking**: Phase별 오류 감소 추적
3. **Test-First**: 타입 변경 전 기존 테스트 100% 통과 확인
4. **Incremental Commits**: Phase별 또는 파일별 commit
5. **Documentation**: 모든 `# type: ignore`에 justification 추가

### Phase Execution Order

```
Phase 1: SQLAlchemy Casting (81 errors)
    ↓
Phase 2: Critical Errors (163 errors)
    ↓
Phase 3: Type Annotations (464 errors)
    ↓
Phase 4: Pattern Fixes (105 errors)
    ↓
Phase 5: Import Cleanup (266 errors)
    ↓
CI/CD Integration (MyPy strict mode enforcement)
```

---

## Phase 1: SQLAlchemy Column Type Casting

### Goal

SQLAlchemy Column 정의에 명시적 타입 캐스팅 추가 (81 errors → 0)

### Strategy

1. **Error Identification**:
   ```bash
   mypy --strict apps/ 2>&1 | grep "assignment.*incompatible" > phase1-errors.txt
   ```

2. **Pattern Analysis**:
   - `Column(Integer)` → `mapped_column(Integer)`
   - `Mapped[int]` 타입 힌트 추가
   - nullable 필드: `Mapped[Optional[str]]`

3. **Transformation**:
   ```python
   # Before
   from sqlalchemy import Column, Integer, String

   class User(Base):
       id = Column(Integer, primary_key=True)
       name = Column(String(255), nullable=False)
       email = Column(String(255), nullable=True)

   # After
   from sqlalchemy.orm import Mapped, mapped_column
   from typing import Optional

   class User(Base):
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       name: Mapped[str] = mapped_column(String(255), nullable=False)
       email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
   ```

4. **File-by-File Process**:
   - Scan all SQLAlchemy models (`rg "class.*\(Base\)" --type python`)
   - Update Column definitions
   - Run MyPy on updated file
   - Verify error count reduced
   - Run tests
   - Commit

### Affected Files

```bash
# Identify SQLAlchemy model files
rg "from sqlalchemy import.*Column" --files-with-matches --type python

# Expected files (from previous analysis):
# - apps/fastapi_app/models/*.py
# - apps/streamlit_app/models/*.py
# - tests/fixtures/*.py
```

### Validation

```bash
# Phase 1 completion check
mypy --strict apps/ 2>&1 | grep "assignment.*incompatible" | wc -l
# Expected: 0

# Test verification
pytest tests/ -v
# Expected: All tests pass
```

### Milestones

- [ ] Error identification complete
- [ ] Pattern transformation applied to all models
- [ ] MyPy errors reduced to 0 for assignment category
- [ ] All tests pass
- [ ] Commit: `♻️ REFACTOR: Phase 1 - SQLAlchemy type casting complete`

---

## Phase 2: Critical Type Errors

### Goal

함수 호출 인자 불일치 및 undefined attribute 해결 (163 errors → 0)

### Strategy

#### 2.1 call-arg Errors (87 errors)

1. **Error Identification**:
   ```bash
   mypy --strict apps/ 2>&1 | grep "call-arg" > phase2a-errors.txt
   ```

2. **Common Patterns**:
   - 함수 시그니처 불일치
   - 딕셔너리 키 접근 타입 불일치
   - 제네릭 타입 명시 누락

3. **Fix Strategy**:
   ```python
   # Pattern 1: Function signature mismatch
   # Before
   def process(data: dict) -> str:
       return transform(data["items"])  # Expected List[Item], got Any

   # After
   def process(data: dict[str, Any]) -> str:
       items: list[Item] = data["items"]
       return transform(items)

   # Pattern 2: Optional parameter handling
   # Before
   def fetch(id: int, params: dict | None) -> Result:
       return query(id, params)  # Expected dict, got dict | None

   # After
   def fetch(id: int, params: dict | None) -> Result:
       return query(id, params or {})
   ```

#### 2.2 attr-defined Errors (76 errors)

1. **Error Identification**:
   ```bash
   mypy --strict apps/ 2>&1 | grep "attr-defined" > phase2b-errors.txt
   ```

2. **Common Patterns**:
   - 베이스 클래스에 정의되지 않은 속성 접근
   - Union 타입에서 특정 타입 속성 접근
   - Dynamic attribute access

3. **Fix Strategy**:
   ```python
   # Pattern 1: Hasattr guard
   # Before
   result = obj.field  # Base has no attribute field

   # After
   if hasattr(obj, "field"):
       result = obj.field
   else:
       result = default_value

   # Pattern 2: Type narrowing with cast
   # Before
   def process(obj: Base) -> str:
       return obj.name  # Base has no attribute name

   # After
   from typing import cast

   def process(obj: Base) -> str:
       derived = cast(Derived, obj)
       return derived.name

   # Pattern 3: Protocol/ABC definition
   # Before
   class Base:
       pass

   class Derived(Base):
       name: str

   # After
   from typing import Protocol

   class HasName(Protocol):
       name: str

   def process(obj: HasName) -> str:
       return obj.name
   ```

### Validation

```bash
# Phase 2 completion check
mypy --strict apps/ 2>&1 | grep -E "(call-arg|attr-defined)" | wc -l
# Expected: 0

# Test verification
pytest tests/ -v --cov=apps --cov-report=term-missing
# Expected: All tests pass, 85%+ coverage
```

### Milestones

- [ ] call-arg errors identified and categorized
- [ ] attr-defined errors identified and categorized
- [ ] Fix strategies applied file-by-file
- [ ] MyPy errors reduced to 0 for critical category
- [ ] All tests pass with 85%+ coverage
- [ ] Commit: `♻️ REFACTOR: Phase 2 - Critical type errors resolved`

---

## Phase 3: Type Annotations

### Goal

모든 함수/메서드에 타입 힌트 추가 (464 errors → 0)

### Strategy

1. **Error Identification**:
   ```bash
   mypy --strict apps/ 2>&1 | grep "no-untyped-def" > phase3-errors.txt
   ```

2. **Prioritization**:
   - Public API 함수 (우선순위 높음)
   - 내부 helper 함수 (우선순위 중간)
   - Test fixtures (우선순위 낮음)

3. **Type Inference**:
   ```python
   # Pattern 1: Simple types
   # Before
   def add(x, y):
       return x + y

   # After
   def add(x: int, y: int) -> int:
       return x + y

   # Pattern 2: Collections
   # Before
   def process_items(items):
       return [item.id for item in items]

   # After
   def process_items(items: list[Item]) -> list[int]:
       return [item.id for item in items]

   # Pattern 3: Optional/Union
   # Before
   def fetch(id, cache=None):
       return cache.get(id) if cache else db.query(id)

   # After
   from typing import Optional

   def fetch(id: int, cache: Optional[Cache] = None) -> Record | None:
       return cache.get(id) if cache else db.query(id)

   # Pattern 4: Generic types
   # Before
   def transform(data):
       return {k: v.upper() for k, v in data.items()}

   # After
   def transform(data: dict[str, str]) -> dict[str, str]:
       return {k: v.upper() for k, v in data.items()}
   ```

4. **Automated Tooling (Optional)**:
   ```bash
   # Use MonkeyType for runtime type collection
   pip install monkeytype
   monkeytype run pytest tests/
   monkeytype apply apps.module

   # Use pytype for type inference
   pip install pytype
   pytype apps/module.py
   ```

### File Processing Order

1. **Models** (SQLAlchemy, Pydantic)
2. **Services** (Business logic)
3. **Routes/Handlers** (API endpoints)
4. **Utils/Helpers** (Utility functions)
5. **Tests** (Test functions)

### Validation

```bash
# Phase 3 completion check
mypy --strict apps/ 2>&1 | grep "no-untyped-def" | wc -l
# Expected: 0

# Verify no new errors introduced
mypy --strict apps/ 2>&1 | grep "error:" | wc -l
# Expected: <= 371 (Phase 4 + 5 remaining)
```

### Milestones

- [ ] All functions have parameter type hints
- [ ] All functions have return type hints
- [ ] Complex types use generics (list, dict, Optional, Union)
- [ ] MyPy no-untyped-def errors reduced to 0
- [ ] All tests pass
- [ ] Commit: `♻️ REFACTOR: Phase 3 - Type annotations complete`

---

## Phase 4: Pattern Fixes

### Goal

Union 타입 속성 접근 및 Any 반환 타입 제거 (105 errors → 0)

### Strategy

#### 4.1 union-attr Errors (75 errors)

1. **Error Identification**:
   ```bash
   mypy --strict apps/ 2>&1 | grep "union-attr" > phase4a-errors.txt
   ```

2. **Fix Patterns**:
   ```python
   # Pattern 1: Type narrowing with isinstance
   # Before
   def process(value: str | int) -> str:
       return value.upper()  # int has no attribute upper

   # After
   def process(value: str | int) -> str:
       if isinstance(value, str):
           return value.upper()
       return str(value).upper()

   # Pattern 2: Match statement (Python 3.10+)
   # Before
   def format(value: str | int | float) -> str:
       return value.strip()  # int/float have no attribute strip

   # After
   def format(value: str | int | float) -> str:
       match value:
           case str():
               return value.strip()
           case int() | float():
               return str(value)

   # Pattern 3: Overload
   from typing import overload

   @overload
   def process(value: str) -> str: ...
   @overload
   def process(value: int) -> str: ...

   def process(value: str | int) -> str:
       if isinstance(value, str):
           return value.upper()
       return str(value).upper()
   ```

#### 4.2 no-any-return Errors (30 errors)

1. **Error Identification**:
   ```bash
   mypy --strict apps/ 2>&1 | grep "no-any-return" > phase4b-errors.txt
   ```

2. **Fix Patterns**:
   ```python
   # Pattern 1: Replace Any with specific type
   # Before
   from typing import Any

   def get_data() -> Any:
       return fetch_from_db()

   # After
   def get_data() -> list[Record]:
       return fetch_from_db()

   # Pattern 2: Generic function
   # Before
   def identity(x: Any) -> Any:
       return x

   # After
   from typing import TypeVar

   T = TypeVar('T')

   def identity(x: T) -> T:
       return x

   # Pattern 3: Union for heterogeneous returns
   # Before
   def parse(data: str) -> Any:
       return json.loads(data)

   # After
   JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None

   def parse(data: str) -> JsonValue:
       return json.loads(data)
   ```

### Validation

```bash
# Phase 4 completion check
mypy --strict apps/ 2>&1 | grep -E "(union-attr|no-any-return)" | wc -l
# Expected: 0

# Verify remaining errors are Phase 5 only
mypy --strict apps/ 2>&1 | grep "error:" | wc -l
# Expected: <= 266
```

### Milestones

- [ ] All union-attr errors resolved with type narrowing
- [ ] All no-any-return errors resolved with specific types
- [ ] No new MyPy errors introduced
- [ ] All tests pass
- [ ] Commit: `♻️ REFACTOR: Phase 4 - Pattern fixes complete`

---

## Phase 5: Import & Misc Cleanup

### Goal

미해결 import 및 기타 오류 해결 (266 errors → 0)

### Strategy

#### 5.1 import-not-found Errors (128 errors)

1. **Error Identification**:
   ```bash
   mypy --strict apps/ 2>&1 | grep "import-not-found" > phase5a-errors.txt
   ```

2. **Fix Strategies**:
   ```python
   # Strategy 1: Add py.typed marker
   # For local packages
   touch apps/fastapi_app/py.typed

   # Strategy 2: Create stub file
   # For third-party packages without type hints
   # stubs/untyped_lib/__init__.pyi
   def function(param: str) -> int: ...

   # Strategy 3: Type ignore with justification
   # Before
   import untyped_lib  # error: Cannot find implementation or library stub

   # After
   import untyped_lib  # type: ignore[import-not-found]  # Third-party lib without stubs
   ```

3. **pyproject.toml Configuration**:
   ```toml
   [tool.mypy]
   mypy_path = "stubs"
   ignore_missing_imports = false

   [[tool.mypy.overrides]]
   module = "untyped_lib.*"
   ignore_missing_imports = true
   ```

#### 5.2 import-untyped Errors (98 errors)

1. **Error Identification**:
   ```bash
   mypy --strict apps/ 2>&1 | grep "import-untyped" > phase5b-errors.txt
   ```

2. **Fix Strategies**:
   ```python
   # Strategy 1: Use typed alternative
   # Before
   import requests  # untyped

   # After
   import httpx  # typed

   # Strategy 2: Install type stubs
   pip install types-requests

   # Strategy 3: Create local stub
   # stubs/requests/__init__.pyi
   from typing import Any

   def get(url: str, **kwargs: Any) -> Response: ...

   class Response:
       status_code: int
       text: str
       def json(self) -> Any: ...
   ```

#### 5.3 Misc Errors (40 errors)

1. **Error Identification**:
   ```bash
   mypy --strict apps/ 2>&1 | grep -v -E "(import-|call-arg|attr-defined|no-untyped-def|union-attr|no-any-return|assignment)" > phase5c-errors.txt
   ```

2. **Case-by-Case Review**:
   - List comprehension type inference issues
   - Decorator type signature issues
   - Metaclass compatibility issues
   - Async function return types
   - Context manager types

### Validation

```bash
# Phase 5 completion check
mypy --strict apps/ tests/ 2>&1 | tee mypy-final-report.txt
echo $?
# Expected: 0 (success)

# Count remaining errors
mypy --strict apps/ tests/ 2>&1 | grep "error:" | wc -l
# Expected: 0
```

### Milestones

- [ ] All import errors resolved (stubs or type: ignore)
- [ ] All misc errors resolved
- [ ] MyPy strict mode exits with code 0
- [ ] All tests pass with 85%+ coverage
- [ ] Commit: `♻️ REFACTOR: Phase 5 - Import cleanup complete`

---

## CI/CD Integration

### Goal

GitHub Actions에서 MyPy strict mode 강제 적용

### Implementation

1. **Update .github/workflows/ci.yml**:
   ```yaml
   name: CI

   on: [push, pull_request]

   jobs:
     type-check:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.12'
         - name: Install dependencies
           run: |
             pip install -e ".[dev]"
         - name: Run MyPy strict mode
           run: |
             mypy --strict apps/ tests/
           # IMPORTANT: continue-on-error MUST be false
           continue-on-error: false

     test:
       needs: type-check
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.12'
         - name: Install dependencies
           run: |
             pip install -e ".[dev]"
         - name: Run tests with coverage
           run: |
             pytest tests/ -v --cov=apps --cov-report=term-missing --cov-fail-under=85
   ```

2. **Validation**:
   - Push to feature branch
   - Verify GitHub Actions runs MyPy
   - Verify build fails if MyPy errors exist
   - Verify build passes when MyPy clean

### Milestones

- [ ] CI workflow updated with MyPy strict mode
- [ ] `continue-on-error: false` confirmed
- [ ] Local MyPy pass before push (pre-commit hook)
- [ ] CI/CD enforces MyPy as quality gate
- [ ] Commit: `🔧 CI: Enforce MyPy strict mode in CI/CD pipeline`

---

## Technical Approach

### Type Hierarchy Strategy

```python
# Use Protocol for duck typing
from typing import Protocol

class Readable(Protocol):
    def read(self) -> str: ...

def process(source: Readable) -> str:
    return source.read()

# Use TypeVar for generics
from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

# Use Literal for constrained values
from typing import Literal

Status = Literal["pending", "active", "completed"]

def update_status(status: Status) -> None:
    ...
```

### Complex Type Patterns

```python
# Recursive types
from typing import Union

JsonValue = Union[
    dict[str, 'JsonValue'],
    list['JsonValue'],
    str,
    int,
    float,
    bool,
    None
]

# Type aliases
RecordId = int
UserId = int
Timestamp = float

def fetch_record(record_id: RecordId) -> Record:
    ...

# NewType for type safety
from typing import NewType

UserId = NewType('UserId', int)
GroupId = NewType('GroupId', int)

def get_user(user_id: UserId) -> User:
    ...

# Cannot mix UserId and GroupId even though both are int
```

### Error Suppression Guidelines

**When to use `# type: ignore`**:
1. Third-party library without type stubs (with justification)
2. Known MyPy bug (with bug tracker link)
3. Complex dynamic code (with explanation)

**Format**:
```python
import untyped_lib  # type: ignore[import-not-found]  # Third-party lib, no stubs available

result = complex_dynamic_operation()  # type: ignore[misc]  # Dynamic attr access required for plugin system
```

**Never use without justification**:
```python
# ❌ BAD
result = obj.field  # type: ignore

# ✅ GOOD
result = obj.field  # type: ignore[attr-defined]  # Dynamic plugin attr, validated at runtime
```

---

## Risks and Mitigation

### Risk 1: Breaking Runtime Behavior

**Mitigation**:
- Run full test suite after each Phase
- Manual testing of critical paths
- Staging deployment before production

### Risk 2: Type Annotation Overhead

**Mitigation**:
- Use TypeVar for generic functions
- Use Protocol for duck typing
- Avoid over-specification (use broader types when appropriate)

### Risk 3: CI/CD Pipeline Slowdown

**Mitigation**:
- MyPy caching enabled (`cache_dir = ".mypy_cache"`)
- Parallel MyPy runs on multiple files
- Target MyPy runtime < 30 seconds

### Risk 4: Third-Party Library Incompatibility

**Mitigation**:
- Create local stubs for critical libraries
- Use `# type: ignore` with justification
- Contribute stubs to typeshed project

---

## Success Metrics

### Quantitative

- MyPy error count: 1,079 → 0
- Test pass rate: 100%
- Test coverage: ≥ 85%
- MyPy runtime: < 30 seconds
- CI/CD build time increase: < 10%

### Qualitative

- All functions have explicit type hints
- No unjustified `# type: ignore`
- Type safety enforced in CI/CD
- Documentation updated with type examples

---

## Next Steps After Completion

1. **Enable stricter MyPy flags**:
   ```toml
   [tool.mypy]
   strict = true
   warn_unreachable = true
   warn_unused_ignores = true
   disallow_any_explicit = true
   ```

2. **Integrate additional type checkers**:
   - Pyright (Microsoft)
   - Pyre (Meta)

3. **Type-Driven Development**:
   - Write type stubs before implementation
   - Use types to guide API design

4. **Performance Optimization**:
   - Profile MyPy with `--performance-profile`
   - Optimize import structure

---

**END OF PLAN**
