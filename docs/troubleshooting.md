# 프로젝트 트러블슈팅 가이드

> **목적**: 반복적으로 발생하는 문제들의 해결 패턴을 기록하여 빠른 문제 해결 및 회귀 방지
> **대상**: Alfred SuperAgent, 개발자, 미래 세션
> **최종 업데이트**: 2025-10-24

---

## 📚 목차

1. [PR Merge 후 Import 오류](#pr-merge-후-import-오류)
2. [Alembic Migration 충돌](#alembic-migration-충돌)
3. [Missing Import/Export 패턴](#missing-importexport-패턴)
4. [회귀 방지 전략](#회귀-방지-전략)
5. [debug-helper 에이전트 활용법](#debug-helper-에이전트-활용법)

---

## PR Merge 후 Import 오류

### 🔍 증상

PR merge 후 다음과 같은 import 오류가 발생:
- `ModuleNotFoundError: No module named 'xxx'`
- `ImportError: cannot import name 'XXX' from 'yyy'`
- 코드는 존재하지만 import 경로가 맞지 않음

### 🎯 근본 원인

- 병렬 개발 중 서로 다른 브랜치에서 동일 모듈을 리팩터링
- Merge 시 파일은 병합되었지만 import 참조가 업데이트되지 않음
- 일부 파일이 merge conflict 없이 병합되었으나 의미적으로 불일치

### ✅ 해결 프로세스

#### 1단계: debug-helper 에이전트로 체계적 분석

```python
# Task 도구로 debug-helper 호출
Task(
    subagent_type="debug-helper",
    description="Analyze import dependency errors",
    prompt="""프로젝트에서 발생하고 있는 import 오류들을 체계적으로 분석하고 해결 방안을 제시해주세요.

현재 발견된 문제들:
1. XXX import 오류 - 위치: YYY
2. ZZZ import 오류 - 위치: AAA

요청사항:
1. 모든 import 의존성 체계적 분석
2. 누락된 파일/함수 자동 감지
3. 각 오류에 대한 구체적인 수정 방안 제시
4. 회귀 방지를 위한 테스트 전략 제안"""
)
```

#### 2단계: 영향 범위 파악

```bash
# 특정 import를 사용하는 모든 위치 검색
rg "from.*import.*XXX" -n
rg "import.*XXX" -n
rg "XXX\." -n  # 사용처 검색
```

#### 3단계: 누락된 모듈/클래스 확인

```bash
# 실제 존재하는 클래스/함수 확인
rg "^class XXX" -n
rg "^def xxx" -n
```

#### 4단계: 수정 및 검증

```python
# Python import 검증 스크립트
python3 -c "
import sys
sys.path.insert(0, 'apps')

# 수정된 import 테스트
from api.module import FixedClass
print('✅ Import successful')
"
```

### 📝 실제 사례: PR #48 Merge 후 Import 오류 (2025-10-24)

**발생한 문제들:**

1. **search_metrics 누락**
   - **증상**: `NameError: name 'search_metrics' is not defined`
   - **위치**: `apps/api/routers/search.py` 15개 위치
   - **원인**: database.py에서 search_metrics가 제거되었으나 search.py에서 계속 참조
   - **해결**:
     ```python
     # apps/api/monitoring/search_metrics.py 생성
     class SearchMetrics:
         def __init__(self):
             self.metrics_collector = get_metrics_collector()

         def record_search(self, search_type, latency_seconds, error=False):
             latency_ms = latency_seconds * 1000
             self.metrics_collector.record_latency(f"search_{search_type}", latency_ms)
             status = "error" if error else "success"
             self.metrics_collector.increment_counter(f"search_{status}", {"search_type": search_type})

     # 전역 인스턴스
     _search_metrics = None
     def get_search_metrics() -> SearchMetrics:
         global _search_metrics
         if _search_metrics is None:
             _search_metrics = SearchMetrics()
         return _search_metrics
     ```

     ```python
     # apps/api/routers/search.py
     from ..monitoring.search_metrics import get_search_metrics
     search_metrics = get_search_metrics()
     ```

2. **APIKeyStorage 잘못된 export**
   - **증상**: `ImportError: cannot import name 'APIKeyStorage'`
   - **위치**: `apps/api/security/__init__.py`
   - **원인**: 실제 클래스명은 `APIKeyManager`인데 `APIKeyStorage`로 export 시도
   - **해결**:
     ```python
     # apps/api/security/__init__.py
     from .api_key_storage import (
         APIKeyManager,  # 실제 클래스명
         APIKey,
         APIKeyUsage,
         APIKeyAuditLog,
         APIKeyInfo,
         APIKeyCreateRequest
     )
     ```

### 🛡️ 예방 조치

1. **Pre-commit Hook 추가**
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: check-imports
           name: Check Python imports
           entry: python3 -m compileall
           language: system
           types: [python]
   ```

2. **CI/CD Import 검증**
   ```yaml
   # .github/workflows/import-check.yml
   - name: Static import analysis
     run: python3 -m compileall -q apps/

   - name: Runtime import test
     run: |
       python3 -c "
       import importlib
       for module in ['apps.api.routers.search', 'apps.api.security']:
           importlib.import_module(module)
       "
   ```

---

## Alembic Migration 충돌

### 🔍 증상

```bash
$ alembic heads
0012 (head)
da725cdb420a (head)
```

여러 개의 head가 존재하여 migration 적용 불가.

### 🎯 근본 원인

- 병렬 개발 중 두 브랜치에서 동시에 migration 생성
- PR merge 시 migration 파일들은 병합되었지만 히스토리가 분기됨
- 각 브랜치의 down_revision이 서로 다른 parent를 가리킴

### ✅ 해결 방법

```bash
# 1. 현재 heads 확인
alembic heads

# 2. Merge migration 생성
alembic merge heads -m "Merge migration branches after PR #XX"

# 3. 생성된 merge migration 확인
cat alembic/versions/[새로운_revision]_merge_migration_branches.py
# down_revision = ('0012', 'da725cdb420a')  # 두 head를 병합

# 4. 단일 head 검증
alembic heads
# 1361849bf32d (head)  # ✅ 하나의 head만 존재

# 5. Migration 적용 (프로덕션 환경)
alembic upgrade head
```

### 🛡️ 예방 조치

1. **Migration 생성 전 최신 master pull**
   ```bash
   git checkout master
   git pull origin master
   alembic upgrade head  # 로컬 DB를 최신 상태로
   git checkout feature/your-branch
   git merge master  # Master의 최신 migrations 가져오기
   alembic revision --autogenerate -m "Your migration"
   ```

2. **Alembic Head 검증 테스트**
   ```python
   # tests/fixtures/test_alembic_migrations.py
   def test_single_alembic_head():
       """Alembic head가 하나만 존재하는지 검증"""
       from alembic.config import Config
       from alembic.script import ScriptDirectory

       config = Config("alembic.ini")
       script = ScriptDirectory.from_config(config)
       heads = script.get_heads()

       assert len(heads) == 1, f"Multiple heads found: {heads}"
   ```

3. **Pre-commit Hook**
   ```yaml
   - id: check-alembic
     name: Verify single Alembic head
     entry: bash -c 'test $(alembic heads | wc -l) -eq 1'
     language: system
     pass_filenames: false
   ```

---

## Missing Import/Export 패턴

### 패턴 1: 모듈 리팩터링 후 Import 미업데이트

**증상**: 모듈 A에서 B로 클래스를 이동했지만 기존 import 참조가 남아있음

**해결**:
```bash
# 1. 모든 import 참조 찾기
rg "from.*old_module.*import" -n
rg "import.*old_module" -n

# 2. 일괄 수정 (신중하게!)
# Edit 도구 사용 또는 수동 수정

# 3. 검증
python3 -m compileall apps/
```

### 패턴 2: __init__.py Export 불일치

**증상**: 모듈에는 클래스가 있지만 __init__.py에서 export하지 않음

**체크리스트**:
```python
# 1. 실제 클래스 확인
# apps/api/security/api_key_storage.py
class APIKeyManager:  # ✅ 실제 클래스명
    pass

# 2. __init__.py export 확인
# apps/api/security/__init__.py
from .api_key_storage import APIKeyManager  # ✅ 일치
# NOT: from .api_key_storage import APIKeyStorage  # ❌ 존재하지 않음

# 3. __all__ 업데이트
__all__ = [
    "APIKeyManager",  # ✅ export 목록에 추가
]
```

### 패턴 3: 순환 Import (Circular Import)

**증상**: `ImportError: cannot import name 'X' from partially initialized module`

**해결**:
```python
# 잘못된 예
# a.py
from b import ClassB
class ClassA:
    pass

# b.py
from a import ClassA  # ❌ 순환 import
class ClassB:
    pass

# 올바른 예 - Late import 사용
# b.py
class ClassB:
    def method(self):
        from a import ClassA  # ✅ 함수 내부에서 import
        pass
```

---

## 회귀 방지 전략

### 1. 세션 시작 시 Import 검증

```python
# conftest.py
@pytest.fixture(scope="session", autouse=True)
def verify_all_imports():
    """세션 시작 시 모든 import 검증"""
    import importlib
    import pkgutil

    errors = []
    for importer, modname, ispkg in pkgutil.walk_packages(
        path=['apps'],
        prefix='apps.'
    ):
        try:
            importlib.import_module(modname)
        except Exception as e:
            errors.append(f"{modname}: {e}")

    if errors:
        pytest.fail(f"Import errors found:\n" + "\n".join(errors))
```

### 2. CI/CD 파이프라인 강화

```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on: [pull_request]

jobs:
  import-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Compile all Python files
        run: python3 -m compileall -q apps/

      - name: Runtime import test
        run: |
          python3 -c "
          import sys
          import importlib
          errors = []
          modules = [
              'apps.api.routers.search',
              'apps.api.security',
              'apps.api.database',
              'apps.api.monitoring.metrics'
          ]
          for module in modules:
              try:
                  importlib.import_module(module)
              except Exception as e:
                  errors.append(f'{module}: {e}')
          if errors:
              print('\n'.join(errors))
              sys.exit(1)
          print('✅ All critical imports verified')
          "

      - name: Verify single Alembic head
        run: |
          heads=$(alembic heads | wc -l)
          if [ $heads -ne 1 ]; then
              echo "❌ Multiple Alembic heads found"
              alembic heads
              exit 1
          fi
          echo "✅ Single Alembic head verified"
```

### 3. Git Pre-commit Hook

```bash
# .git/hooks/pre-commit (또는 .pre-commit-config.yaml)
#!/bin/bash

echo "Running pre-commit checks..."

# 1. Python syntax check
echo "Checking Python syntax..."
python3 -m compileall apps/ 2>&1 | grep -v "Listing" | grep -v "Compiling"
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "❌ Python syntax errors found"
    exit 1
fi
echo "✅ Python syntax check passed"

# 2. Alembic head check
echo "Checking Alembic heads..."
heads=$(alembic heads 2>/dev/null | wc -l)
if [ $heads -gt 1 ]; then
    echo "❌ Multiple Alembic heads detected"
    alembic heads
    exit 1
fi
echo "✅ Single Alembic head verified"

# 3. Import quick test
echo "Quick import test..."
python3 -c "
import sys
sys.path.insert(0, 'apps')
try:
    from api.routers import search
    from api.security import api_key_storage
    print('✅ Quick import test passed')
except Exception as e:
    print(f'❌ Import test failed: {e}')
    sys.exit(1)
"

echo "✅ All pre-commit checks passed"
```

---

## debug-helper 에이전트 활용법

### 언제 사용하는가?

- ✅ 런타임 에러 발생 시
- ✅ Import/의존성 오류 발견 시
- ✅ PR merge 후 통합 이슈 발생 시
- ✅ 여러 파일에 걸친 복잡한 버그
- ❌ 단순 syntax 오류 (직접 수정이 더 빠름)
- ❌ 로직 설계 (spec-builder 사용)

### 효과적인 프롬프트 작성법

#### 좋은 예 ✅

```python
Task(
    subagent_type="debug-helper",
    description="Analyze import dependency errors",
    prompt="""프로젝트에서 발생하고 있는 import 오류들을 체계적으로 분석하고 해결 방안을 제시해주세요.

**현재 발견된 문제들:**
1. search_metrics import 오류
   - 위치: database.py
   - 증상: search_metrics를 찾을 수 없음
   - 영향: search.py의 15개 위치에서 사용 중

2. APIKeyStorage import 오류
   - 위치: api_key_storage.py
   - 증상: APIKeyStorage 클래스를 찾을 수 없음

**근본 원인:**
Master branch merge (PR #48) 중 코드베이스 불일치 발생

**요청 사항:**
1. 모든 import 의존성 체계적 분석
2. 누락된 파일/함수 자동 감지
3. 각 오류에 대한 구체적인 수정 방안 제시
4. 회귀 방지를 위한 테스트 전략 제안

프로젝트 구조:
- apps/api/: FastAPI 애플리케이션
- tests/: 테스트 파일들
- alembic/: 데이터베이스 마이그레이션
"""
)
```

#### 나쁜 예 ❌

```python
Task(
    subagent_type="debug-helper",
    description="Fix imports",
    prompt="import 오류 고쳐줘"  # 너무 모호함
)
```

### debug-helper 결과 활용

debug-helper가 반환하는 분석 보고서는 다음을 포함:
1. **진단 결과**: 각 오류의 근본 원인
2. **영향 범위**: 관련된 모든 파일 목록
3. **수정 방안**: 구체적인 코드 예시
4. **우선순위**: Blocker → P0 → P1 순서
5. **회귀 방지**: 테스트 및 검증 전략

**활용 패턴**:
```bash
1. debug-helper 실행 → 분석 보고서 획득
2. 우선순위 순서대로 수정
3. 각 수정 후 즉시 검증
4. 모든 수정 완료 후 회귀 방지 전략 구현
5. Commit & 문서화
```

---

## 체크리스트: Import 오류 해결

PR merge 후 import 오류 발생 시 다음 체크리스트를 따르세요:

- [ ] **1단계: 문제 파악**
  - [ ] 에러 메시지 전체 수집
  - [ ] 영향받는 파일 목록 작성
  - [ ] 최근 merge된 PR 확인

- [ ] **2단계: debug-helper 실행**
  - [ ] Task 도구로 debug-helper 호출
  - [ ] 모든 import 오류 나열
  - [ ] 분석 보고서 저장

- [ ] **3단계: 체계적 수정**
  - [ ] Blocker 문제부터 해결 (Alembic heads 등)
  - [ ] P0 문제 해결 (Missing imports)
  - [ ] 각 수정 후 import 검증 실행

- [ ] **4단계: 검증**
  - [ ] `python3 -m compileall apps/` 통과
  - [ ] Import 테스트 스크립트 실행
  - [ ] `alembic heads` 단일 head 확인

- [ ] **5단계: Commit**
  - [ ] Git commit with detailed message
  - [ ] 해결된 문제 목록 기록
  - [ ] 검증 결과 포함

- [ ] **6단계: 회귀 방지**
  - [ ] Pre-commit hook 추가
  - [ ] CI/CD 검증 강화
  - [ ] 이 가이드 업데이트

---

## 참고 자료

### 관련 문서
- [CLAUDE.md](../CLAUDE.md): MoAI-ADK 워크플로우 및 Alfred SuperAgent 가이드
- Development Guide: TRUST 5 원칙 및 코드 품질 기준
- GitFlow Protection Policy: 브랜치 전략 및 PR 정책

### 외부 링크
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Python Import System](https://docs.python.org/3/reference/import.html)
- [Pre-commit Hooks](https://pre-commit.com/)

---

## 버전 히스토리

### v1.0.0 (2025-10-24)
- **INITIAL**: PR #48 merge 후 import 오류 해결 경험 기반 작성
- debug-helper 에이전트 활용법 추가
- Alembic multiple heads 해결 패턴 추가
- 회귀 방지 전략 체계화
