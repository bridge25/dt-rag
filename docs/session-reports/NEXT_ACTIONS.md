# 다음 작업 계획 (Next Actions)

**작성 일시**: 2025-10-28
**현재 상태**: 브랜치 정리 및 코드 품질 개선 완료
**다음 세션 목표**: 커밋 및 MyPy Critical 오류 해결

---

## 🎯 즉시 실행 (현재 세션)

### ✅ 완료된 작업
1. ✅ 브랜치 정리 (42→1)
2. ✅ Black formatting (192개 파일)
3. ✅ MyPy 오류 일부 해결 (config.py, agent_task_queue.py)
4. ✅ Function complexity 개선 (50→4)
5. ✅ `.gitignore` 업데이트
6. ✅ 종합 분석 보고서 작성

### 📋 다음 단계: Git 커밋

**현재 상태:**
- 195개 파일 수정됨
- 모든 변경사항은 코드 품질 개선

**권장 커밋 순서:**

#### 1️⃣ Commit #1: Black Formatting
```bash
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone

git add -u

git commit -m "style: apply black formatting to 192 Python files

- Standardize code style across entire codebase
- No functional changes
- Line length: 88 characters (Black default)

Refs: MASTER_HEALTH_REPORT.md Priority #2"
```

#### 2️⃣ Commit #2: Type Safety Improvements
```bash
git add apps/api/config.py apps/api/env_manager.py apps/api/llm_config.py
git add apps/api/background/agent_task_queue.py apps/api/cache/redis_manager.py

git commit -m "fix(types): resolve MyPy errors in config and queue modules

- Add TypedDict for validation results (env_manager, llm_config)
- Add lrange/lrem methods to RedisManager
- Add return type annotations
- Add type: ignore comments for fallback imports

Fixes:
- config.py: 7 errors resolved
- agent_task_queue.py: 2 errors resolved

Refs: MASTER_HEALTH_REPORT.md Priority #3"
```

#### 3️⃣ Commit #3: Function Complexity Refactoring
```bash
git add apps/orchestration/src/main.py

git commit -m "refactor: reduce create_agent_from_category complexity (50→4)

- Extract 8 helper functions for validation and config building
- Improve testability and maintainability
- Complexity grade: F (50) → A (4) = 92% improvement

Helper functions:
- _validate_version, _validate_path_element, _validate_node_paths
- _validate_mcp_tools, _validate_options, _normalize_paths
- _build_retrieval_config, _build_features_config, _validate_manifest

Refs: MASTER_HEALTH_REPORT.md Priority #4"
```

#### 4️⃣ Commit #4: Gitignore Update
```bash
git add .gitignore

git commit -m "chore: add Python cache patterns to .gitignore

- Add .mypy_cache/
- Add __pycache__/
- Add *.pyc
- Add .pytest_cache/

Prevents 512+ cache files from being tracked"
```

#### 5️⃣ Push to Remote
```bash
git push origin master
```

---

## 🔥 Priority 1: MyPy Critical 오류 해결 (20개)

**타임라인**: 즉시
**목표**: 런타임 오류 가능성 있는 attr-defined, call-arg 해결

### 🛠️ 작업 리스트

#### Task 1: EnvManager 메서드 추가
**파일**: `apps/api/env_manager.py`

**문제:**
```python
# config.py:650, 683, 705
validation = env_manager.validate_environment()  # Error: attr-defined
summary = env_manager.get_environment_summary()   # Error: attr-defined
```

**해결 방법:**
```python
# env_manager.py에 추가
class EnvManager:
    def validate_environment(self) -> ValidationResult:
        """Validate current environment configuration"""
        # Implementation here
        pass

    def get_environment_summary(self) -> Dict[str, Any]:
        """Get environment configuration summary"""
        # Implementation here
        pass
```

#### Task 2: APIConfig redis_enabled 속성 추가
**파일**: `apps/api/config.py`

**문제:**
```python
# main.py:165
if config.redis_enabled:  # Error: attr-defined
```

**해결 방법:**
```python
# config.py의 APIConfig 클래스에 추가
@dataclass
class APIConfig:
    # ... existing fields ...
    redis_enabled: bool = True  # Add this field
```

#### Task 3: generate_openapi_spec 호출 수정
**파일**: `apps/api/main.py:415`

**문제:**
```python
# main.py:415
generate_openapi_spec()  # Error: Missing positional argument "app"
```

**해결 방법:**
```python
# main.py:415
generate_openapi_spec(app)  # Add app argument
```

#### Task 4: reflection_engine.py sort key 타입 수정
**파일**: `apps/orchestration/src/reflection_engine.py:164`

**문제:**
```python
# Error: Argument "key" has incompatible return type
results.sort(key=lambda x: x.get("score", 0))
```

**해결 방법:**
```python
from typing import cast, Union

# Option 1: Type assertion
results.sort(key=lambda x: cast(float, x.get("score", 0)))

# Option 2: Type guard
def get_score(x: dict) -> float:
    score = x.get("score", 0)
    return float(score) if isinstance(score, (int, float)) else 0.0

results.sort(key=get_score)
```

#### Task 5: 기타 call-arg 오류 해결
**파일**: 여러 파일

1. `apps/evaluation/sample_data.py:165` - Add `ground_truth` argument
2. `apps/api/services/langgraph_service.py:70` - Remove `canonical_filter` argument
3. `apps/ingestion/batch/job_orchestrator.py:352` - Add `error_message` and `error_code`

---

## 📊 Priority 2: Import Path 표준화

**타임라인**: 1-2일
**목표**: import-not-found 오류 877개 해결

### 전략 A: pyproject.toml 설정 (권장)

```bash
# pyproject.toml 수정
cat >> pyproject.toml << 'EOF'

[tool.mypy]
mypy_path = "$MYPY_CONFIG_FILE_DIR"
namespace_packages = true
explicit_package_bases = true
EOF
```

### 전략 B: 상대 Import 변경 (보수적)

```python
# 패턴 변경
# Before: from cache.redis_manager import RedisManager
# After:  from .cache.redis_manager import RedisManager

# 일괄 변경 스크립트
find apps/ -name "*.py" -exec sed -i 's/from cache\./from .cache./g' {} +
find apps/ -name "*.py" -exec sed -i 's/from routers\./from .routers./g' {} +
# ... (추가 패턴)
```

---

## 🏗️ Priority 3: 프로젝트 구조 정리

**타임라인**: 1-2시간
**목표**: 루트 디렉토리 187개 파일 → <20개로 정리

### 정리 스크립트

```bash
# 1. 디렉토리 생성
mkdir -p docs/analysis
mkdir -p docs/session-reports
mkdir -p scripts/maintenance
mkdir -p scripts/analysis

# 2. 분석 파일 이동
mv FINAL_BRANCH_CLEANUP_REPORT.md docs/analysis/
mv MASTER_HEALTH_REPORT.md docs/analysis/
mv COMPREHENSIVE_BRANCH_ANALYSIS.md docs/analysis/
mv NEXT_SESSION_GUIDE.md docs/session-reports/
mv SESSION_SUMMARY.md docs/session-reports/
mv README_BRANCH_WORK.md docs/session-reports/
mv phase2_spec_metadata.md docs/analysis/
mv phase4_quick_scan.txt docs/analysis/

# 3. 스크립트 이동
mv phase2_review_helper.py scripts/analysis/
mv phase4_branch_review_script.py scripts/analysis/
mv analyze_remaining_branches.py scripts/maintenance/
mv analyze_large_branches.py scripts/maintenance/

# 4. 캐시 파일 삭제
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
rm -rf .mypy_cache

# 5. Git 커밋
git add -A
git commit -m "chore: reorganize project structure

- Move analysis reports to docs/analysis/
- Move session reports to docs/session-reports/
- Move scripts to scripts/ subdirectories
- Clean up cache files

Root directory: 187 files → ~15 files"

git push origin master
```

---

## 📈 Priority 4: Type Annotations 추가

**타임라인**: 2-3일
**목표**: no-untyped-def 오류 200개 해결

### MonkeyType 활용 (자동화)

```bash
# 1. MonkeyType 설치
pip install monkeytype

# 2. 테스트 실행하며 타입 수집
monkeytype run -m pytest tests/

# 3. 타입 힌트 자동 적용
monkeytype apply apps.api.main
monkeytype apply apps.orchestration.src.main
# ... (주요 파일들)

# 4. 수동 검토 및 조정
# MonkeyType이 생성한 타입 힌트 확인 후 필요시 수정

# 5. MyPy 검증
mypy apps/ --config-file=pyproject.toml

# 6. 커밋
git add -A
git commit -m "fix(types): add type annotations to 200+ functions

- Use MonkeyType for automatic type inference
- Manually reviewed and adjusted generated types
- Resolves no-untyped-def errors

MyPy errors: 1097 → ~800 (27% reduction)"

git push origin master
```

---

## 🎯 단계별 체크리스트

### Phase 1: Git 커밋 (오늘)
- [ ] Commit #1: Black formatting
- [ ] Commit #2: Type safety improvements
- [ ] Commit #3: Function complexity refactoring
- [ ] Commit #4: Gitignore update
- [ ] Push to origin/master

### Phase 2: MyPy Critical (오늘/내일)
- [ ] Task 1: EnvManager 메서드 추가
- [ ] Task 2: APIConfig redis_enabled 추가
- [ ] Task 3: generate_openapi_spec 수정
- [ ] Task 4: reflection_engine sort key 수정
- [ ] Task 5: 기타 call-arg 오류 해결
- [ ] MyPy 재검증 (1097 → ~1050 목표)

### Phase 3: Import Path 표준화 (이번 주)
- [ ] pyproject.toml 설정 추가
- [ ] MyPy 재검증 (import-not-found 해결 확인)
- [ ] 필요시 상대 import로 변경
- [ ] 커밋 및 푸시

### Phase 4: 프로젝트 정리 (이번 주)
- [ ] 디렉토리 구조 생성
- [ ] 파일 이동 스크립트 실행
- [ ] 캐시 파일 삭제
- [ ] 커밋 및 푸시

### Phase 5: Type Annotations (다음 주)
- [ ] MonkeyType 설치
- [ ] 테스트 실행 및 타입 수집
- [ ] 타입 힌트 자동 적용
- [ ] 수동 검토 및 조정
- [ ] 커밋 및 푸시

---

## 📊 성과 목표

| Phase | 목표 | 예상 결과 |
|-------|------|-----------|
| Phase 1 | 안전한 커밋 | 4개 커밋, 히스토리 정리 |
| Phase 2 | Critical 오류 해결 | MyPy 1097 → ~1050 (5% 개선) |
| Phase 3 | Import 표준화 | MyPy ~1050 → ~200 (81% 개선) |
| Phase 4 | 구조 정리 | 루트 187 → ~15 (92% 개선) |
| Phase 5 | 타입 힌트 추가 | MyPy ~200 → <50 (75% 개선) |
| **최종** | **전체 개선** | **MyPy 1097 → <50 (95% 개선)** |

---

## 💡 추가 권장사항

### 1. CI/CD 설정
```yaml
# .github/workflows/quality-check.yml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install black ruff mypy
      - name: Black check
        run: black --check .
      - name: Ruff check
        run: ruff check .
      - name: MyPy check
        run: mypy apps/ --config-file=pyproject.toml
```

### 2. Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash

# Black formatting
black apps/ --check
if [ $? -ne 0 ]; then
    echo "❌ Black formatting failed. Run: black apps/"
    exit 1
fi

# Ruff linting
ruff check apps/
if [ $? -ne 0 ]; then
    echo "❌ Ruff linting failed. Run: ruff check apps/ --fix"
    exit 1
fi

echo "✅ Pre-commit checks passed!"
```

### 3. 정기 품질 점검
```bash
# scripts/quality-check.sh
#!/bin/bash

echo "🔍 Running quality checks..."

# 1. Black
echo "1️⃣ Black formatting..."
black apps/ --check

# 2. Ruff
echo "2️⃣ Ruff linting..."
ruff check apps/

# 3. MyPy
echo "3️⃣ MyPy type checking..."
mypy apps/ --config-file=pyproject.toml | tail -5

# 4. Radon complexity
echo "4️⃣ Radon complexity..."
radon cc apps/ -a -s | grep "Average complexity"

# 5. Test coverage
echo "5️⃣ Test coverage..."
pytest --cov=apps tests/ --cov-report=term-missing:skip-covered | tail -10

echo "✅ Quality check complete!"
```

---

## 🚀 최종 목표

**타임라인**: 2주
**성공 기준**:
- ✅ MyPy 오류 <50개 (95% 개선)
- ✅ Ruff 오류 0개 (100% 해결)
- ✅ Function complexity <10 (모든 함수)
- ✅ 루트 디렉토리 <20개 파일
- ✅ Test coverage >85%

---

**작성자**: Claude Code
**다음 세션 시 우선 확인**: 이 파일과 COMPREHENSIVE_BRANCH_ANALYSIS.md
