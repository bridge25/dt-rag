# @DOC:MYPY-001 - Implementation Plan

## Overview

이 문서는 **SPEC-MYPY-001 (MyPy Strict Mode 완전 준수)** 의 구현 계획을 정의합니다.

**목표**: 1,008개 MyPy strict mode 타입 오류를 3단계(자동화 → 수동 수정 → 검증)로 제로화하여 CI/CD Quality Gate 통과

---

## 1. Implementation Strategy

### 1.1 Three-Phase Approach

| Phase | Target | Method | Expected Outcome |
|-------|--------|--------|------------------|
| **Phase 1: Automation** | ~600개 오류 | 자동화 스크립트 (`fix_mypy_auto.py`) | 단순 패턴 오류 제로화 |
| **Phase 2: Manual Correction** | ~400개 오류 | 파일별 수동 수정 + 테스트 검증 | 복잡한 타입 오류 해결 |
| **Phase 3: Verification & Integration** | CI/CD 통합 | Quality Gate 활성화 + 최종 검증 | Production-ready |

### 1.2 Prioritization Matrix

**P0 (Critical)**: 자동화 가능 오류 (즉시 처리)
- `no-untyped-def`: 함수 시그니처 타입 누락 (~300개)
- `var-annotated`: 변수 타입 어노테이션 누락 (~200개)

**P1 (High)**: 수동 수정 필수 (우선 처리)
- `assignment`: 타입 불일치 할당 (~150개)
- `arg-type`: 함수 인자 타입 불일치 (~120개)

**P2 (Medium)**: 수동 수정 권장 (순차 처리)
- `call-arg`: 함수 호출 인자 문제 (~100개)
- `attr-defined`, `no-redef`, `return-value`: 기타 (~138개)

---

## 2. Phase 1: Automation (자동화)

### 2.1 Automation Scope

**자동화 대상 오류 유형**:
1. **no-untyped-def** (함수 정의 타입 누락)
   - 패턴: 함수/메서드에 파라미터 또는 반환 타입 없음
   - 해결: 기본 타입 추가 (`Any`, `None`, 추론 가능한 경우 구체적 타입)

2. **var-annotated** (변수 어노테이션 누락)
   - 패턴: 변수 선언 시 타입 명시 없음
   - 해결: 우변 값 기반 타입 추론 또는 `Any` 사용

### 2.2 Automation Script Design

**Script**: `scripts/fix_mypy_auto.py`

```python
#!/usr/bin/env python3
"""
MyPy 자동화 수정 스크립트
- no-untyped-def: 함수 시그니처에 기본 타입 추가
- var-annotated: 변수에 타입 어노테이션 추가
"""
import re
import libcst as cst
from pathlib import Path
from typing import Dict, List, Tuple

class TypeAnnotationTransformer(cst.CSTTransformer):
    """AST 기반 타입 어노테이션 자동 추가"""

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        # 파라미터 타입 추가 (없는 경우)
        # 반환 타입 추가 (없는 경우)
        pass

    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        # 변수 어노테이션 추가
        pass

def parse_mypy_errors(error_file: Path) -> Dict[str, List[Tuple[int, str]]]:
    """mypy_errors.txt 파싱하여 파일별 오류 그룹핑"""
    pass

def apply_fixes(file_path: Path, errors: List[Tuple[int, str]]) -> bool:
    """파일에 자동 수정 적용"""
    pass

def verify_no_regression(file_path: Path) -> bool:
    """pytest 실행하여 regression 확인"""
    pass

if __name__ == "__main__":
    # 1. mypy_errors.txt 파싱
    # 2. 자동화 대상 오류 필터링
    # 3. 파일별 변환 적용
    # 4. pytest 검증
    # 5. 결과 리포트
    pass
```

### 2.3 Execution Plan

**Step 1: 스크립트 개발 및 테스트**
```bash
# 1. 스크립트 작성
touch scripts/fix_mypy_auto.py
chmod +x scripts/fix_mypy_auto.py

# 2. 샘플 파일로 테스트
python scripts/fix_mypy_auto.py --dry-run --file apps/api/main.py

# 3. 단일 파일 적용
python scripts/fix_mypy_auto.py --file apps/api/main.py
pytest tests/api/test_main.py  # regression 확인
```

**Step 2: 배치 실행**
```bash
# 자동화 대상 오류만 필터링
python scripts/fix_mypy_auto.py --errors no-untyped-def,var-annotated

# 진행 상황 모니터링
python scripts/fix_mypy_auto.py --verbose --log-file phase1.log

# 최종 검증
mypy --strict . --exclude venv | tee mypy_phase1_result.txt
pytest tests/ -v
```

**Step 3: Commit**
```bash
git add .
git commit -m "fix(mypy): apply automated type annotations (Phase 1)

- Apply fixes for no-untyped-def (~300 errors)
- Apply fixes for var-annotated (~200 errors)
- All tests passing, zero regression

Refs: @SPEC:MYPY-001 @CODE:MYPY-001:PHASE1"
```

**Expected Outcome**:
- ✅ ~600개 오류 제거
- ✅ 모든 기존 테스트 통과
- ✅ MyPy 오류 개수: 1,008 → ~400

---

## 3. Phase 2: Manual Correction (수동 수정)

### 3.1 Manual Correction Workflow

**파일별 수정 프로세스**:
1. **오류 그룹핑**: 동일 파일의 모든 오류 한 번에 처리
2. **사전 테스트**: 수정 전 해당 파일 테스트 실행
3. **타입 수정**: 구체적 타입 지정 (`Any` 최소화)
4. **사후 검증**: 수정 후 테스트 재실행
5. **Commit**: 10개 파일마다 체크포인트 commit

### 3.2 Error Type Handling Guide

#### 3.2.1 assignment (타입 불일치 할당)
```python
# 문제: 반환 타입과 변수 타입 불일치
def get_timeout() -> int:
    return "30"  # error: str not assignable to int

# 해결 방법 1: 반환 타입 수정
def get_timeout() -> Union[int, str]:
    return "30"

# 해결 방법 2: 값 수정
def get_timeout() -> int:
    return 30
```

#### 3.2.2 arg-type (인자 타입 불일치)
```python
# 문제: 함수 파라미터 타입 불일치
def process_id(user_id: int) -> None:
    pass

process_id("123")  # error: str not assignable to int

# 해결 방법 1: 호출부 수정
process_id(int("123"))

# 해결 방법 2: 시그니처 확장
def process_id(user_id: Union[int, str]) -> None:
    if isinstance(user_id, str):
        user_id = int(user_id)
    pass
```

#### 3.2.3 call-arg (함수 호출 인자 문제)
```python
# 문제: 인자 개수 불일치
def send_email(to: str, subject: str, body: str) -> None:
    pass

send_email("user@example.com", "Hello")  # error: missing argument

# 해결: 필수 인자 추가 또는 기본값 지정
def send_email(to: str, subject: str, body: str = "") -> None:
    pass
```

#### 3.2.4 attr-defined (존재하지 않는 속성)
```python
# 문제: 클래스에 정의되지 않은 속성 접근
class Config:
    def __init__(self):
        self.timeout = 30

config = Config()
print(config.host)  # error: Config has no attribute "host"

# 해결: 속성 정의 추가
class Config:
    def __init__(self):
        self.timeout: int = 30
        self.host: str = "localhost"
```

### 3.3 Checkpoint Strategy

**Checkpoint 주기**: 10개 파일마다 commit 및 CI 검증

```bash
# Checkpoint Commit Template
git commit -m "fix(mypy): resolve type errors in <module_name> (Phase 2)

- Fix assignment errors in file1.py, file2.py
- Fix arg-type errors in file3.py
- Fix call-arg errors in file4.py
- All tests passing

Refs: @SPEC:MYPY-001 @CODE:MYPY-001:PHASE2
Progress: X/92 files completed"
```

**Checkpoint 검증**:
```bash
# 1. MyPy 재실행
mypy --strict . --exclude venv | tee mypy_checkpoint.txt

# 2. 오류 개수 확인
grep "error:" mypy_checkpoint.txt | wc -l

# 3. 테스트 실행
pytest tests/ -v --tb=short
```

---

## 4. Phase 3: Verification & CI Integration (검증 및 통합)

### 4.1 Local Verification

**Step 1: 최종 MyPy 검증**
```bash
# 전체 프로젝트 strict mode 검증
mypy --strict . --exclude venv

# 예상 출력: "Success: no issues found in X source files"
```

**Step 2: 전체 테스트 스위트 실행**
```bash
# 모든 테스트 실행
pytest tests/ -v --cov --cov-report=term-missing

# Coverage 비교
pytest --cov --cov-report=html
open htmlcov/index.html  # Coverage report 확인
```

**Step 3: 타입 커버리지 검증**
```bash
# scripts/verify_types.py: 타입 힌트 누락 검증
python scripts/verify_types.py --strict

# 예상 출력: "Type coverage: 100%"
```

### 4.2 CI/CD Quality Gate Update

**Before (현재 상태)**:
```yaml
# .github/workflows/ci.yml
- name: MyPy Type Check
  run: |
    mypy --strict . --exclude venv
  continue-on-error: true  # ⚠️ 오류 무시
```

**After (Phase 3 완료 후)**:
```yaml
# .github/workflows/ci.yml
- name: MyPy Type Check
  run: |
    mypy --strict . --exclude venv
  # continue-on-error: false (default) ✅ Quality Gate 활성화
```

**PR Description Template**:
```markdown
## SPEC-MYPY-001 Phase 3: CI/CD Quality Gate 활성화

### Changes
- ✅ MyPy strict mode 오류 0개 달성
- ✅ CI/CD Quality Gate에서 `continue-on-error` 제거
- ✅ 모든 테스트 통과 (zero regression)

### Verification
- MyPy: `mypy --strict . --exclude venv` → exit code 0
- Pytest: `pytest tests/ -v` → 100% pass
- Coverage: X% → Y% (maintained/improved)

### Refs
@SPEC:MYPY-001 @CODE:MYPY-001:PHASE3
```

### 4.3 Final Acceptance Criteria

**Phase 3 완료 조건**:
- ✅ `mypy --strict . --exclude venv` exit code 0
- ✅ `pytest tests/ -v` 모든 테스트 통과
- ✅ Coverage 현재 수준 유지 또는 향상
- ✅ CI/CD Quality Gate 통과 (3회 연속)
- ✅ `# type: ignore` 사용 0건 (또는 문서화된 예외만)

---

## 5. Risk Management

### 5.1 Known Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **R1**: 자동화 스크립트 오류 | Medium | High | Dry-run 테스트, 파일별 pytest 검증 |
| **R2**: 타입 변경 시 API 호환성 문제 | Low | Critical | 시그니처 변경 시 모든 호출부 확인 |
| **R3**: Phase 3에서 새로운 오류 발견 | High | Medium | Phase 1, 2 완료 후 즉시 수정 |
| **R4**: Coverage 감소 | Low | Medium | 수정 전후 coverage 비교, 테스트 추가 |
| **R5**: CI 빌드 시간 증가 | Low | Low | MyPy 캐시 활용, 병렬 실행 |

### 5.2 Rollback Plan

**문제 발생 시 대응**:
1. **Phase 1 실패**: 스크립트 수정 후 재실행 (commit 전 dry-run)
2. **Phase 2 실패**: 해당 파일만 revert 후 재수정
3. **Phase 3 실패**: CI Quality Gate 재활성화 연기, 원인 분석 후 재시도

**Rollback Command**:
```bash
# 특정 commit으로 복구
git revert <commit-hash>

# Phase별 브랜치 복구
git checkout -b fix/mypy-phase1-retry origin/fix/mypy-phase1
```

---

## 6. Timeline & Milestones (Priority-based)

### 6.1 Milestone Structure

| Milestone | Priority | Deliverable | Exit Criteria |
|-----------|----------|-------------|---------------|
| **M1: Automation** | Critical | ~600개 오류 제거 | MyPy 오류 < 450개, 모든 테스트 통과 |
| **M2: Manual Correction** | High | ~400개 오류 제거 | MyPy 오류 0개, 모든 테스트 통과 |
| **M3: CI Integration** | Critical | Quality Gate 활성화 | CI 3회 연속 통과 |

### 6.2 Dependency Chain

```
M1 (Automation)
    ↓
M2 (Manual Correction)
    ↓
M3 (CI Integration)
    ↓
Production Ready
```

**Critical Path**: M1 → M2 → M3 순차 진행 필수

---

## 7. Success Metrics

### 7.1 Quantitative Metrics

- **Type Error Count**: 1,008 → 0 (100% reduction)
- **Type Coverage**: 0% → 100% (모든 함수, 변수, 속성)
- **Test Pass Rate**: 100% (before) → 100% (after)
- **Coverage**: 현재 수준 유지 또는 향상
- **CI Build Time**: +X분 (MyPy 추가 시간)

### 7.2 Qualitative Metrics

- **Code Quality**: 타입 안전성 향상, 런타임 오류 감소 예상
- **Developer Experience**: IDE 자동완성 및 타입 체크 개선
- **Maintainability**: 타입 힌트로 코드 이해도 향상

---

## 8. Next Steps

### 8.1 Immediate Actions

1. **Create Automation Script**: `scripts/fix_mypy_auto.py` 작성
2. **Test on Sample Files**: 3-5개 파일로 스크립트 검증
3. **Run Phase 1**: 자동화 실행 및 commit

### 8.2 Command to Execute

```bash
/alfred:2-run SPEC-MYPY-001
```

**Expected Workflow**:
1. **RED**: CI에서 MyPy 오류 확인 (현재 상태)
2. **GREEN**: Phase 1-3 실행하여 오류 제로화
3. **REFACTOR**: 타입 정확도 향상 (`Any` 최소화)

---

**Plan Owner**: spec-builder agent
**Status**: Draft
**Last Updated**: 2025-01-25
**Next Review**: Phase 1 완료 후
